"""
Gerenciador de arquivos - Ler, criar, editar arquivos
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
import aiofiles
from pydantic import BaseModel
from ..core.config import config


class FileInfo(BaseModel):
    """Informacoes de um arquivo"""
    path: str
    name: str
    extension: str
    size: int
    is_dir: bool
    modified: float


class FileContent(BaseModel):
    """Conteudo de um arquivo"""
    path: str
    content: str
    encoding: str = "utf-8"
    lines: int


class FileManager:
    """Gerenciador de operacoes com arquivos"""

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or config.files.workspace
        self.allowed_extensions = config.files.allowed_extensions
        self.max_file_size = config.files.max_file_size
        self.excluded_dirs = config.files.excluded_dirs

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve caminho relativo para absoluto"""
        p = Path(path)
        if not p.is_absolute():
            p = self.workspace / p
        return p.resolve()

    def _is_allowed(self, path: Path) -> bool:
        """Verifica se arquivo pode ser acessado"""
        # Verifica extensao
        if path.suffix.lower() not in self.allowed_extensions:
            # Permite arquivos sem extensao se for texto
            if path.suffix:
                return False

        # Verifica se esta em diretorio excluido
        for part in path.parts:
            if part in self.excluded_dirs:
                return False

        return True

    def _should_exclude_dir(self, path: Path) -> bool:
        """Verifica se diretorio deve ser excluido"""
        return path.name in self.excluded_dirs

    async def read_file(self, path: str | Path) -> FileContent:
        """Le conteudo de um arquivo"""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

        if not full_path.is_file():
            raise ValueError(f"Nao e um arquivo: {path}")

        # Verifica tamanho
        size = full_path.stat().st_size
        if size > self.max_file_size:
            raise ValueError(f"Arquivo muito grande: {size} bytes (max: {self.max_file_size})")

        # Tenta ler como texto
        try:
            async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                content = await f.read()
        except UnicodeDecodeError:
            # Tenta latin-1 como fallback
            async with aiofiles.open(full_path, "r", encoding="latin-1") as f:
                content = await f.read()

        return FileContent(
            path=str(full_path),
            content=content,
            lines=content.count("\n") + 1
        )

    async def write_file(self, path: str | Path, content: str) -> FileInfo:
        """Escreve conteudo em arquivo (cria ou sobrescreve)"""
        full_path = self._resolve_path(path)

        # Cria diretorio pai se nao existir
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
            await f.write(content)

        return self._get_file_info(full_path)

    async def edit_file(
        self,
        path: str | Path,
        old_content: str,
        new_content: str,
        create_if_missing: bool = False
    ) -> FileContent:
        """
        Edita arquivo substituindo old_content por new_content
        Similar ao Edit tool do Claude Code
        """
        full_path = self._resolve_path(path)

        if not full_path.exists():
            if create_if_missing:
                await self.write_file(path, new_content)
                return await self.read_file(path)
            else:
                raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

        # Le conteudo atual
        current = await self.read_file(path)

        # Verifica se old_content existe
        if old_content not in current.content:
            raise ValueError(
                f"Conteudo a substituir nao encontrado no arquivo.\n"
                f"Buscando: {old_content[:100]}..."
            )

        # Substitui
        new_file_content = current.content.replace(old_content, new_content, 1)

        # Salva
        await self.write_file(path, new_file_content)

        return await self.read_file(path)

    async def append_file(self, path: str | Path, content: str) -> FileContent:
        """Adiciona conteudo ao final do arquivo"""
        full_path = self._resolve_path(path)

        async with aiofiles.open(full_path, "a", encoding="utf-8") as f:
            await f.write(content)

        return await self.read_file(path)

    async def delete_file(self, path: str | Path) -> bool:
        """Deleta arquivo"""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            return False

        if full_path.is_dir():
            import shutil
            shutil.rmtree(full_path)
        else:
            full_path.unlink()

        return True

    async def create_directory(self, path: str | Path) -> FileInfo:
        """Cria diretorio"""
        full_path = self._resolve_path(path)
        full_path.mkdir(parents=True, exist_ok=True)
        return self._get_file_info(full_path)

    def _get_file_info(self, path: Path) -> FileInfo:
        """Obtem informacoes de um arquivo"""
        stat = path.stat()
        return FileInfo(
            path=str(path),
            name=path.name,
            extension=path.suffix,
            size=stat.st_size,
            is_dir=path.is_dir(),
            modified=stat.st_mtime
        )

    async def list_directory(
        self,
        path: str | Path = ".",
        recursive: bool = False,
        pattern: Optional[str] = None
    ) -> list[FileInfo]:
        """Lista arquivos em diretorio"""
        full_path = self._resolve_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"Diretorio nao encontrado: {path}")

        if not full_path.is_dir():
            raise ValueError(f"Nao e um diretorio: {path}")

        files = []

        if recursive:
            for item in full_path.rglob(pattern or "*"):
                # Pula diretorios excluidos
                skip = False
                for part in item.relative_to(full_path).parts:
                    if part in self.excluded_dirs:
                        skip = True
                        break
                if skip:
                    continue

                if item.is_file():
                    files.append(self._get_file_info(item))
        else:
            for item in full_path.iterdir():
                if self._should_exclude_dir(item):
                    continue
                if pattern and not item.match(pattern):
                    continue
                files.append(self._get_file_info(item))

        return sorted(files, key=lambda f: (not f.is_dir, f.name.lower()))

    async def search_files(
        self,
        pattern: str,
        path: str | Path = ".",
        content_search: Optional[str] = None
    ) -> list[FileInfo]:
        """Busca arquivos por nome ou conteudo"""
        full_path = self._resolve_path(path)
        results = []

        for item in full_path.rglob(pattern):
            # Pula diretorios excluidos
            skip = False
            for part in item.relative_to(full_path).parts:
                if part in self.excluded_dirs:
                    skip = True
                    break
            if skip:
                continue

            if not item.is_file():
                continue

            # Se busca por conteudo
            if content_search:
                try:
                    file_content = await self.read_file(item)
                    if content_search.lower() not in file_content.content.lower():
                        continue
                except:
                    continue

            results.append(self._get_file_info(item))

        return results

    async def get_file_tree(
        self,
        path: str | Path = ".",
        max_depth: int = 3
    ) -> dict:
        """Retorna arvore de arquivos"""
        full_path = self._resolve_path(path)

        def build_tree(p: Path, depth: int) -> dict:
            if depth > max_depth:
                return {"name": p.name, "type": "dir", "truncated": True}

            result = {
                "name": p.name,
                "path": str(p),
                "type": "dir" if p.is_dir() else "file"
            }

            if p.is_dir() and not self._should_exclude_dir(p):
                children = []
                try:
                    for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        if self._should_exclude_dir(item):
                            continue
                        children.append(build_tree(item, depth + 1))
                except PermissionError:
                    pass
                result["children"] = children

            return result

        return build_tree(full_path, 0)


# Instancia global
file_manager = FileManager()
