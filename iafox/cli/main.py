"""
Interface CLI do IAFOX - Similar ao Claude Code
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

from ..core.agent import IAFOXAgent
from ..core.config import config, IAFOXConfig
from ..llm.ollama_client import OllamaClient

app = typer.Typer(
    name="iafox",
    help="IAFOX - IA Local sem Restricoes para Desenvolvimento",
    add_completion=False
)

console = Console()


def print_banner():
    """Exibe banner do IAFOX"""
    banner = """
██╗ █████╗ ███████╗ ██████╗ ██╗  ██╗
██║██╔══██╗██╔════╝██╔═══██╗╚██╗██╔╝
██║███████║█████╗  ██║   ██║ ╚███╔╝
██║██╔══██║██╔══╝  ██║   ██║ ██╔██╗
██║██║  ██║██║     ╚██████╔╝██╔╝ ██╗
╚═╝╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝
    """
    console.print(Panel(
        banner + "\n[bold cyan]IA Local sem Restricoes para Desenvolvimento[/bold cyan]",
        border_style="cyan"
    ))


def print_help():
    """Exibe comandos disponiveis"""
    help_text = """
[bold]Comandos:[/bold]
  /help     - Mostra esta ajuda
  /clear    - Limpa conversa
  /model    - Mostra/troca modelo
  /config   - Mostra configuracao
  /tree     - Mostra arvore de arquivos
  /exit     - Sai do IAFOX

[bold]Dicas:[/bold]
  - Digite sua mensagem e pressione Enter
  - A IA pode ler, criar e editar arquivos
  - A IA pode executar comandos no terminal
  - Use Ctrl+C para cancelar uma resposta
"""
    console.print(Panel(help_text, title="Ajuda", border_style="blue"))


async def check_ollama(client: OllamaClient) -> bool:
    """Verifica conexao com Ollama"""
    try:
        models = await client.list_models()
        return True
    except Exception as e:
        console.print(f"[red]Erro ao conectar com Ollama: {e}[/red]")
        console.print("[yellow]Certifique-se que o Ollama esta rodando: ollama serve[/yellow]")
        return False


async def check_model(client: OllamaClient, model: str) -> bool:
    """Verifica se modelo esta disponivel"""
    try:
        models = await client.list_models()
        model_names = [m.get("name", "") for m in models]

        # Verifica se modelo existe
        model_base = model.split(":")[0]
        for m in model_names:
            if m.startswith(model_base):
                return True

        console.print(f"[yellow]Modelo '{model}' nao encontrado.[/yellow]")
        console.print(f"[yellow]Modelos disponiveis: {', '.join(model_names)}[/yellow]")

        # Oferece baixar
        if Prompt.ask(f"Deseja baixar o modelo '{model}'?", choices=["s", "n"], default="s") == "s":
            console.print(f"[cyan]Baixando {model}...[/cyan]")
            async for progress in client.pull_model(model):
                status = progress.get("status", "")
                if "pulling" in status:
                    completed = progress.get("completed", 0)
                    total = progress.get("total", 1)
                    pct = (completed / total * 100) if total else 0
                    console.print(f"\r[cyan]{status}: {pct:.1f}%[/cyan]", end="")
            console.print("\n[green]Modelo baixado com sucesso![/green]")
            return True
        return False

    except Exception as e:
        console.print(f"[red]Erro ao verificar modelo: {e}[/red]")
        return False


async def run_chat(workspace: Path, model: str):
    """Loop principal de chat"""
    # Inicializa cliente e agente
    client = OllamaClient(model=model)

    # Verifica Ollama
    if not await check_ollama(client):
        return

    # Verifica modelo
    if not await check_model(client, model):
        return

    # Cria agente
    from ..files.manager import FileManager
    file_manager = FileManager(workspace=workspace)
    agent = IAFOXAgent(llm=client, file_manager=file_manager)

    console.print(f"\n[green]Conectado![/green] Modelo: [cyan]{model}[/cyan]")
    console.print(f"Workspace: [cyan]{workspace}[/cyan]")
    console.print("Digite [bold]/help[/bold] para ver comandos\n")

    while True:
        try:
            # Prompt
            user_input = Prompt.ask("\n[bold cyan]voce[/bold cyan]")

            if not user_input.strip():
                continue

            # Comandos especiais
            if user_input.startswith("/"):
                cmd = user_input.lower().strip()

                if cmd == "/exit" or cmd == "/quit":
                    console.print("[yellow]Ate mais![/yellow]")
                    break

                elif cmd == "/help":
                    print_help()
                    continue

                elif cmd == "/clear":
                    agent.clear_conversation()
                    console.print("[green]Conversa limpa![/green]")
                    continue

                elif cmd == "/model":
                    models = await client.list_models()
                    console.print("[bold]Modelos disponiveis:[/bold]")
                    for m in models:
                        name = m.get("name", "")
                        size = m.get("size", 0) / (1024**3)
                        console.print(f"  - {name} ({size:.1f} GB)")
                    continue

                elif cmd == "/config":
                    console.print(Panel(
                        f"Ollama: {config.ollama.host}\n"
                        f"Modelo: {model}\n"
                        f"Workspace: {workspace}",
                        title="Configuracao"
                    ))
                    continue

                elif cmd == "/tree":
                    tree = await file_manager.get_file_tree(".", max_depth=2)
                    console.print(Panel(str(tree), title="Arvore de Arquivos"))
                    continue

                else:
                    console.print(f"[red]Comando desconhecido: {cmd}[/red]")
                    continue

            # Processa mensagem
            console.print("\n[bold magenta]iafox[/bold magenta]")

            response_text = ""
            async for chunk in agent.chat(user_input, stream=True):
                console.print(chunk, end="")
                response_text += chunk

            console.print()  # Nova linha no final

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelado[/yellow]")
            continue

        except Exception as e:
            console.print(f"\n[red]Erro: {e}[/red]")
            continue

    await client.close()


@app.command()
def chat(
    workspace: Optional[Path] = typer.Option(
        None,
        "--workspace", "-w",
        help="Diretorio de trabalho"
    ),
    model: str = typer.Option(
        "qwen2.5-coder:32b",
        "--model", "-m",
        help="Modelo Ollama a usar"
    )
):
    """Inicia chat interativo com IAFOX"""
    print_banner()

    # Define workspace
    if workspace is None:
        workspace = Path.cwd()
    workspace = workspace.resolve()

    if not workspace.exists():
        console.print(f"[red]Diretorio nao existe: {workspace}[/red]")
        raise typer.Exit(1)

    # Roda chat
    asyncio.run(run_chat(workspace, model))


@app.command()
def models():
    """Lista modelos disponiveis no Ollama"""
    async def list_models():
        client = OllamaClient()
        try:
            models = await client.list_models()
            console.print("[bold]Modelos instalados:[/bold]\n")
            for m in models:
                name = m.get("name", "")
                size = m.get("size", 0) / (1024**3)
                modified = m.get("modified_at", "")
                console.print(f"  [cyan]{name}[/cyan]")
                console.print(f"    Tamanho: {size:.1f} GB")
                console.print(f"    Modificado: {modified}\n")
        except Exception as e:
            console.print(f"[red]Erro: {e}[/red]")
        finally:
            await client.close()

    asyncio.run(list_models())


@app.command()
def pull(
    model: str = typer.Argument(..., help="Nome do modelo para baixar")
):
    """Baixa um modelo do Ollama"""
    async def download():
        client = OllamaClient()
        try:
            console.print(f"[cyan]Baixando {model}...[/cyan]")
            async for progress in client.pull_model(model):
                status = progress.get("status", "")
                if "pulling" in status:
                    completed = progress.get("completed", 0)
                    total = progress.get("total", 1)
                    pct = (completed / total * 100) if total else 0
                    console.print(f"\r{status}: {pct:.1f}%", end="")
                else:
                    console.print(status)
            console.print("\n[green]Concluido![/green]")
        except Exception as e:
            console.print(f"[red]Erro: {e}[/red]")
        finally:
            await client.close()

    asyncio.run(download())


@app.command()
def config_cmd(
    show: bool = typer.Option(False, "--show", "-s", help="Mostra configuracao atual"),
    init: bool = typer.Option(False, "--init", "-i", help="Cria configuracao inicial")
):
    """Gerencia configuracao do IAFOX"""
    config_path = Path.home() / ".iafox" / "config.json"

    if show:
        if config_path.exists():
            console.print(Panel(config_path.read_text(), title="Configuracao"))
        else:
            console.print("[yellow]Nenhuma configuracao encontrada[/yellow]")

    elif init:
        cfg = IAFOXConfig()
        cfg.save()
        console.print(f"[green]Configuracao criada em: {config_path}[/green]")


@app.command()
def version():
    """Mostra versao do IAFOX"""
    from .. import __version__
    console.print(f"IAFOX v{__version__}")


def main():
    """Entrypoint principal"""
    app()


if __name__ == "__main__":
    main()
