"""
Agente principal do IAFOX - Orquestra LLM + Ferramentas
"""

import json
import re
from typing import AsyncGenerator, Optional, Callable, Any
from pydantic import BaseModel
from ..llm.ollama_client import OllamaClient, Message
from ..files.manager import FileManager, FileContent
from ..tools.web_search import buscar_web, buscar_noticias
from .config import config


class ToolCall(BaseModel):
    """Representacao de uma chamada de ferramenta"""
    name: str
    arguments: dict


class ToolResult(BaseModel):
    """Resultado de uma ferramenta"""
    success: bool
    result: Any
    error: Optional[str] = None


class ConversationMessage(BaseModel):
    """Mensagem na conversa"""
    role: str
    content: str
    tool_calls: Optional[list[ToolCall]] = None
    tool_results: Optional[list[ToolResult]] = None


class IAFOXAgent:
    """
    Agente principal do IAFOX

    Combina:
    - LLM (Ollama)
    - Gerenciador de arquivos
    - Sistema de ferramentas
    """

    # Definicao das ferramentas disponiveis
    TOOLS_DESCRIPTION = """
## Ferramentas Disponiveis

Voce tem acesso as seguintes ferramentas. Use-as quando necessario:

### read_file
Le o conteudo de um arquivo.
Uso: <tool>read_file</tool><args>{"path": "caminho/do/arquivo.py"}</args>

### write_file
Cria ou sobrescreve um arquivo.
Uso: <tool>write_file</tool><args>{"path": "caminho/do/arquivo.py", "content": "conteudo do arquivo"}</args>

### edit_file
Edita parte de um arquivo, substituindo texto.
Uso: <tool>edit_file</tool><args>{"path": "arquivo.py", "old_content": "codigo antigo", "new_content": "codigo novo"}</args>

### list_files
Lista arquivos em um diretorio.
Uso: <tool>list_files</tool><args>{"path": ".", "recursive": false}</args>

### search_files
Busca arquivos por padrao ou conteudo.
Uso: <tool>search_files</tool><args>{"pattern": "*.py", "content_search": "def main"}</args>

### execute_command
Executa comando no terminal.
Uso: <tool>execute_command</tool><args>{"command": "pip install requests"}</args>

### file_tree
Mostra arvore de arquivos do projeto.
Uso: <tool>file_tree</tool><args>{"path": ".", "max_depth": 3}</args>

### web_search
Busca na internet usando DuckDuckGo. Use para encontrar links, sites, informacoes atuais.
Uso: <tool>web_search</tool><args>{"query": "farmacias em cuiaba", "max_results": 10}</args>

### search_news
Busca noticias recentes na internet.
Uso: <tool>search_news</tool><args>{"query": "noticias brasil", "max_results": 10}</args>

---

IMPORTANTE:
- Sempre use as ferramentas quando precisar ler/modificar arquivos
- Apos usar uma ferramenta, espere o resultado antes de continuar
- Seja preciso nos caminhos de arquivo
- Use edit_file para modificacoes pequenas, write_file para criar/reescrever arquivos
"""

    def __init__(
        self,
        llm: Optional[OllamaClient] = None,
        file_manager: Optional[FileManager] = None,
        system_prompt: Optional[str] = None
    ):
        self.llm = llm or OllamaClient()
        self.file_manager = file_manager or FileManager()
        self.system_prompt = system_prompt or config.system_prompt
        self.conversation: list[ConversationMessage] = []
        self.tools: dict[str, Callable] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Registra ferramentas padrao"""
        self.tools = {
            "read_file": self._tool_read_file,
            "write_file": self._tool_write_file,
            "edit_file": self._tool_edit_file,
            "list_files": self._tool_list_files,
            "search_files": self._tool_search_files,
            "execute_command": self._tool_execute_command,
            "file_tree": self._tool_file_tree,
            "web_search": self._tool_web_search,
            "search_news": self._tool_search_news,
        }

    async def _tool_read_file(self, path: str) -> ToolResult:
        """Ferramenta: ler arquivo"""
        try:
            content = await self.file_manager.read_file(path)
            return ToolResult(
                success=True,
                result=f"Arquivo: {content.path}\nLinhas: {content.lines}\n\n```\n{content.content}\n```"
            )
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    async def _tool_write_file(self, path: str, content: str) -> ToolResult:
        """Ferramenta: escrever arquivo"""
        try:
            info = await self.file_manager.write_file(path, content)
            return ToolResult(
                success=True,
                result=f"Arquivo criado/atualizado: {info.path} ({info.size} bytes)"
            )
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    async def _tool_edit_file(
        self,
        path: str,
        old_content: str,
        new_content: str
    ) -> ToolResult:
        """Ferramenta: editar arquivo"""
        try:
            content = await self.file_manager.edit_file(path, old_content, new_content)
            return ToolResult(
                success=True,
                result=f"Arquivo editado: {content.path}\nNovas linhas: {content.lines}"
            )
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    async def _tool_list_files(
        self,
        path: str = ".",
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> ToolResult:
        """Ferramenta: listar arquivos"""
        try:
            files = await self.file_manager.list_directory(path, recursive, pattern)
            result = "\n".join(
                f"{'[DIR] ' if f.is_dir else '      '}{f.name}"
                for f in files
            )
            return ToolResult(success=True, result=result or "Diretorio vazio")
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    async def _tool_search_files(
        self,
        pattern: str,
        path: str = ".",
        content_search: Optional[str] = None
    ) -> ToolResult:
        """Ferramenta: buscar arquivos"""
        try:
            files = await self.file_manager.search_files(pattern, path, content_search)
            result = "\n".join(f.path for f in files)
            return ToolResult(
                success=True,
                result=result or "Nenhum arquivo encontrado"
            )
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    async def _tool_execute_command(self, command: str) -> ToolResult:
        """Ferramenta: executar comando"""
        import asyncio

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.file_manager.workspace)
            )
            stdout, stderr = await process.communicate()

            output = stdout.decode() if stdout else ""
            errors = stderr.decode() if stderr else ""

            result = ""
            if output:
                result += f"STDOUT:\n{output}\n"
            if errors:
                result += f"STDERR:\n{errors}\n"
            result += f"Exit code: {process.returncode}"

            return ToolResult(
                success=process.returncode == 0,
                result=result
            )
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    async def _tool_file_tree(
        self,
        path: str = ".",
        max_depth: int = 3
    ) -> ToolResult:
        """Ferramenta: arvore de arquivos"""
        try:
            tree = await self.file_manager.get_file_tree(path, max_depth)

            def format_tree(node: dict, prefix: str = "") -> str:
                lines = [f"{prefix}{node['name']}/"] if node.get("type") == "dir" else [f"{prefix}{node['name']}"]

                children = node.get("children", [])
                for i, child in enumerate(children):
                    is_last = i == len(children) - 1
                    child_prefix = prefix + ("    " if is_last else "│   ")
                    connector = "└── " if is_last else "├── "
                    child_lines = format_tree(child, child_prefix)
                    lines.append(f"{prefix}{connector}{child_lines.split(prefix + '    ', 1)[-1] if child_prefix in child_lines else child_lines.lstrip()}")

                return "\n".join(lines)

            return ToolResult(success=True, result=format_tree(tree))
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    async def _tool_web_search(self, query: str, max_results: int = 10) -> ToolResult:
        """Ferramenta: busca na web"""
        try:
            result = buscar_web(query, max_results)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    async def _tool_search_news(self, query: str, max_results: int = 10) -> ToolResult:
        """Ferramenta: busca noticias"""
        try:
            result = buscar_noticias(query, max_results)
            return ToolResult(success=True, result=result)
        except Exception as e:
            return ToolResult(success=False, result=None, error=str(e))

    def _parse_tool_calls(self, text: str) -> list[ToolCall]:
        """Extrai chamadas de ferramentas do texto"""
        pattern = r"<tool>(\w+)</tool><args>(.*?)</args>"
        matches = re.findall(pattern, text, re.DOTALL)

        calls = []
        for name, args_str in matches:
            try:
                args = json.loads(args_str)
                calls.append(ToolCall(name=name, arguments=args))
            except json.JSONDecodeError:
                continue

        return calls

    async def _execute_tool(self, call: ToolCall) -> ToolResult:
        """Executa uma ferramenta"""
        if call.name not in self.tools:
            return ToolResult(
                success=False,
                result=None,
                error=f"Ferramenta desconhecida: {call.name}"
            )

        tool_fn = self.tools[call.name]
        try:
            return await tool_fn(**call.arguments)
        except TypeError as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Argumentos invalidos: {e}"
            )

    def _build_system_prompt(self) -> str:
        """Constroi system prompt completo"""
        return f"{self.system_prompt}\n\n{self.TOOLS_DESCRIPTION}"

    async def chat(
        self,
        user_message: str,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Processa mensagem do usuario

        Args:
            user_message: Mensagem do usuario
            stream: Se deve fazer streaming da resposta

        Yields:
            Chunks da resposta
        """
        # Adiciona mensagem do usuario
        self.conversation.append(ConversationMessage(
            role="user",
            content=user_message
        ))

        # Prepara mensagens para o LLM
        messages = [
            Message(role=msg.role, content=msg.content)
            for msg in self.conversation
        ]

        # Gera resposta
        full_response = ""

        if stream:
            gen = await self.llm.chat(
                messages=messages,
                system=self._build_system_prompt(),
                stream=True
            )
            async for chunk in gen:
                full_response += chunk
                yield chunk
        else:
            full_response = await self.llm.chat(
                messages=messages,
                system=self._build_system_prompt(),
                stream=False
            )
            yield full_response

        # Verifica se ha chamadas de ferramentas
        tool_calls = self._parse_tool_calls(full_response)

        if tool_calls:
            # Adiciona resposta do assistente
            self.conversation.append(ConversationMessage(
                role="assistant",
                content=full_response,
                tool_calls=tool_calls
            ))

            # Executa ferramentas
            results = []
            for call in tool_calls:
                yield f"\n\n[Executando {call.name}...]\n"
                result = await self._execute_tool(call)
                results.append(result)

                if result.success:
                    yield f"[Resultado: {result.result[:500]}{'...' if len(str(result.result)) > 500 else ''}]\n"
                else:
                    yield f"[Erro: {result.error}]\n"

            # Adiciona resultados como mensagem
            results_text = "\n\n".join(
                f"Resultado de {call.name}: {'Sucesso' if r.success else 'Erro'}\n{r.result or r.error}"
                for call, r in zip(tool_calls, results)
            )

            self.conversation.append(ConversationMessage(
                role="user",
                content=f"[Resultados das ferramentas]\n{results_text}"
            ))

            # Continua a conversa com os resultados
            async for chunk in self.chat("Continue com base nos resultados das ferramentas.", stream=stream):
                yield chunk
        else:
            # Adiciona resposta do assistente
            self.conversation.append(ConversationMessage(
                role="assistant",
                content=full_response
            ))

    def clear_conversation(self):
        """Limpa historico de conversa"""
        self.conversation = []

    def get_conversation_history(self) -> list[dict]:
        """Retorna historico formatado"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.conversation
        ]
