"""
API REST do IAFOX - FastAPI
"""

import asyncio
from pathlib import Path
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

from ..core.agent import IAFOXAgent
from ..core.config import config
from ..llm.ollama_client import OllamaClient
from ..files.manager import FileManager


# Modelos de request/response
class ChatRequest(BaseModel):
    message: str
    workspace: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    success: bool


class FileRequest(BaseModel):
    path: str
    content: Optional[str] = None


class EditRequest(BaseModel):
    path: str
    old_content: str
    new_content: str


class CommandRequest(BaseModel):
    command: str
    workspace: Optional[str] = None


# Estado global
agents: dict[str, IAFOXAgent] = {}


def get_or_create_agent(workspace: str = ".") -> IAFOXAgent:
    """Obtem ou cria agente para workspace"""
    workspace_path = Path(workspace).resolve()
    key = str(workspace_path)

    if key not in agents:
        client = OllamaClient()
        file_manager = FileManager(workspace=workspace_path)
        agents[key] = IAFOXAgent(llm=client, file_manager=file_manager)

    return agents[key]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle da aplicacao"""
    yield
    # Cleanup
    for agent in agents.values():
        await agent.llm.close()


# Cria app
app = FastAPI(
    title="IAFOX API",
    description="IA Local sem Restricoes para Desenvolvimento",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ ROTAS ============

@app.get("/", response_class=HTMLResponse)
async def root():
    """Pagina inicial - serve interface HTML"""
    template_path = Path(__file__).parent / "templates" / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(), status_code=200)
    return HTMLResponse(content="<h1>IAFOX API</h1><p>Interface nao encontrada</p>")


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok"}


# ---- Chat ----

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Envia mensagem para o agente"""
    try:
        agent = get_or_create_agent(request.workspace or ".")

        response_text = ""
        async for chunk in agent.chat(request.message, stream=False):
            response_text += chunk

        return ChatResponse(response=response_text, success=True)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Envia mensagem com streaming"""
    agent = get_or_create_agent(request.workspace or ".")

    async def generate():
        async for chunk in agent.chat(request.message, stream=True):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket para chat em tempo real"""
    await websocket.accept()

    workspace = "."
    agent = get_or_create_agent(workspace)

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                message = data.get("content", "")

                async for chunk in agent.chat(message, stream=True):
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk
                    })

                await websocket.send_json({"type": "done"})

            elif data.get("type") == "clear":
                agent.clear_conversation()
                await websocket.send_json({"type": "cleared"})

            elif data.get("type") == "workspace":
                workspace = data.get("path", ".")
                agent = get_or_create_agent(workspace)
                await websocket.send_json({
                    "type": "workspace_changed",
                    "path": workspace
                })

    except WebSocketDisconnect:
        pass


@app.delete("/api/chat/clear")
async def clear_chat(workspace: Optional[str] = None):
    """Limpa historico de conversa"""
    agent = get_or_create_agent(workspace or ".")
    agent.clear_conversation()
    return {"success": True}


# ---- Arquivos ----

@app.get("/api/files")
async def list_files(
    path: str = ".",
    recursive: bool = False,
    workspace: Optional[str] = None
):
    """Lista arquivos"""
    agent = get_or_create_agent(workspace or ".")
    files = await agent.file_manager.list_directory(path, recursive)
    return {
        "files": [f.model_dump() for f in files]
    }


@app.get("/api/files/read")
async def read_file(path: str, workspace: Optional[str] = None):
    """Le conteudo de arquivo"""
    agent = get_or_create_agent(workspace or ".")
    try:
        content = await agent.file_manager.read_file(path)
        return content.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")


@app.post("/api/files/write")
async def write_file(request: FileRequest, workspace: Optional[str] = None):
    """Escreve arquivo"""
    agent = get_or_create_agent(workspace or ".")
    if not request.content:
        raise HTTPException(status_code=400, detail="Conteudo obrigatorio")

    info = await agent.file_manager.write_file(request.path, request.content)
    return info.model_dump()


@app.post("/api/files/edit")
async def edit_file(request: EditRequest, workspace: Optional[str] = None):
    """Edita arquivo"""
    agent = get_or_create_agent(workspace or ".")
    try:
        content = await agent.file_manager.edit_file(
            request.path,
            request.old_content,
            request.new_content
        )
        return content.model_dump()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/files")
async def delete_file(path: str, workspace: Optional[str] = None):
    """Deleta arquivo"""
    agent = get_or_create_agent(workspace or ".")
    result = await agent.file_manager.delete_file(path)
    return {"success": result}


@app.get("/api/files/tree")
async def file_tree(
    path: str = ".",
    max_depth: int = 3,
    workspace: Optional[str] = None
):
    """Arvore de arquivos"""
    agent = get_or_create_agent(workspace or ".")
    tree = await agent.file_manager.get_file_tree(path, max_depth)
    return tree


@app.get("/api/files/search")
async def search_files(
    pattern: str,
    path: str = ".",
    content: Optional[str] = None,
    workspace: Optional[str] = None
):
    """Busca arquivos"""
    agent = get_or_create_agent(workspace or ".")
    files = await agent.file_manager.search_files(pattern, path, content)
    return {"files": [f.model_dump() for f in files]}


# ---- Comandos ----

@app.post("/api/execute")
async def execute_command(request: CommandRequest):
    """Executa comando no terminal"""
    import asyncio

    workspace = Path(request.workspace or ".").resolve()

    process = await asyncio.create_subprocess_shell(
        request.command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(workspace)
    )

    stdout, stderr = await process.communicate()

    return {
        "stdout": stdout.decode() if stdout else "",
        "stderr": stderr.decode() if stderr else "",
        "exit_code": process.returncode
    }


# ---- Modelos ----

@app.get("/api/models")
async def list_models():
    """Lista modelos do Ollama"""
    client = OllamaClient()
    try:
        models = await client.list_models()
        return {"models": models}
    finally:
        await client.close()


@app.post("/api/models/pull/{model_name}")
async def pull_model(model_name: str):
    """Baixa modelo"""
    client = OllamaClient()

    async def generate():
        async for progress in client.pull_model(model_name):
            yield f"data: {progress}\n\n"
        yield "data: [DONE]\n\n"
        await client.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


# ---- Config ----

@app.get("/api/config")
async def get_config():
    """Retorna configuracao atual"""
    return config.model_dump()


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Inicia servidor"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
