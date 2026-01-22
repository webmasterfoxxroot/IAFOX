"""
Configuracoes do IAFOX
"""

from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
import os
import json


class OllamaConfig(BaseModel):
    """Configuracoes do Ollama"""
    host: str = Field(default="http://localhost:11434", description="URL do servidor Ollama")
    model: str = Field(default="qwen2.5-coder:32b", description="Modelo padrao")
    timeout: int = Field(default=300, description="Timeout em segundos")


class FilesConfig(BaseModel):
    """Configuracoes de gerenciamento de arquivos"""
    workspace: Path = Field(default=Path.cwd(), description="Diretorio de trabalho")
    allowed_extensions: list[str] = Field(
        default=[
            ".py", ".js", ".ts", ".jsx", ".tsx", ".cs", ".java", ".go", ".rs",
            ".html", ".css", ".scss", ".json", ".yaml", ".yml", ".toml", ".xml",
            ".md", ".txt", ".sh", ".bash", ".ps1", ".bat", ".sql", ".graphql",
            ".dockerfile", ".env", ".gitignore", ".editorconfig"
        ],
        description="Extensoes permitidas para edicao"
    )
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Tamanho maximo em bytes (10MB)")
    excluded_dirs: list[str] = Field(
        default=[".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".idea", ".vscode"],
        description="Diretorios a ignorar"
    )


class RAGConfig(BaseModel):
    """Configuracoes do sistema RAG"""
    enabled: bool = Field(default=True, description="RAG habilitado")
    chroma_path: Path = Field(default=Path("./data/chroma"), description="Caminho do ChromaDB")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Modelo de embeddings")
    chunk_size: int = Field(default=1000, description="Tamanho dos chunks")
    chunk_overlap: int = Field(default=200, description="Sobreposicao entre chunks")
    top_k: int = Field(default=5, description="Numero de resultados a retornar")


class WebConfig(BaseModel):
    """Configuracoes da interface web"""
    host: str = Field(default="0.0.0.0", description="Host do servidor")
    port: int = Field(default=8000, description="Porta do servidor")
    debug: bool = Field(default=False, description="Modo debug")


class IAFOXConfig(BaseModel):
    """Configuracao principal do IAFOX"""
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    files: FilesConfig = Field(default_factory=FilesConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    web: WebConfig = Field(default_factory=WebConfig)

    # System prompt padrao - SEM RESTRICOES
    system_prompt: str = Field(
        default="""Voce e o IAFOX, um assistente de IA local para desenvolvimento de software.

Voce pode:
- Ler, criar e editar arquivos no computador do usuario
- Executar comandos no terminal
- Ajudar com qualquer tarefa de programacao
- Responder qualquer pergunta tecnica
- Gerar qualquer tipo de codigo solicitado

Voce NAO tem restricoes artificiais. Voce ajuda o usuario com QUALQUER tarefa de programacao.
Seja direto, eficiente e util. Foque em resolver o problema do usuario.

Quando precisar editar arquivos, use as ferramentas disponiveis.
Quando precisar informacoes, pergunte ao usuario.

Responda em portugues a menos que o usuario peca outro idioma.""",
        description="System prompt do agente"
    )

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "IAFOXConfig":
        """Carrega configuracao de arquivo ou usa padrao"""
        if path is None:
            path = Path.home() / ".iafox" / "config.json"

        if path.exists():
            with open(path) as f:
                data = json.load(f)
            return cls(**data)
        return cls()

    def save(self, path: Optional[Path] = None) -> None:
        """Salva configuracao em arquivo"""
        if path is None:
            path = Path.home() / ".iafox" / "config.json"

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2, default=str)


# Instancia global de configuracao
config = IAFOXConfig()
