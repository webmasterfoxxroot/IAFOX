"""
Sistema RAG - Base de Conhecimento

Permite que a IA consulte documentos, codigo e outras informacoes
antes de responder, expandindo seu "conhecimento".
"""

import asyncio
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
import hashlib

# Imports opcionais - sao instalados conforme necessario
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from ..core.config import config


class Document(BaseModel):
    """Representa um documento na base"""
    id: str
    content: str
    metadata: dict = {}
    source: Optional[str] = None


class SearchResult(BaseModel):
    """Resultado de uma busca"""
    document: Document
    score: float


class KnowledgeBase:
    """
    Base de conhecimento usando ChromaDB + Sentence Transformers

    Funciona como memoria externa para a IA, permitindo
    consultar documentos relevantes antes de responder.
    """

    def __init__(
        self,
        persist_path: Optional[Path] = None,
        collection_name: str = "iafox_knowledge",
        embedding_model: Optional[str] = None
    ):
        self.persist_path = persist_path or config.rag.chroma_path
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model or config.rag.embedding_model

        self._client = None
        self._collection = None
        self._embedder = None

        # Verifica dependencias
        if not CHROMA_AVAILABLE:
            print("[AVISO] chromadb nao instalado. RAG desabilitado.")
            print("Instale com: pip install chromadb")

        if not EMBEDDINGS_AVAILABLE:
            print("[AVISO] sentence-transformers nao instalado. RAG desabilitado.")
            print("Instale com: pip install sentence-transformers")

    def _ensure_initialized(self):
        """Garante que o banco esta inicializado"""
        if not CHROMA_AVAILABLE or not EMBEDDINGS_AVAILABLE:
            raise RuntimeError("Dependencias do RAG nao instaladas")

        if self._client is None:
            self.persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.persist_path),
                anonymized_telemetry=False
            ))

        if self._collection is None:
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "IAFOX Knowledge Base"}
            )

        if self._embedder is None:
            self._embedder = SentenceTransformer(self.embedding_model_name)

    def _generate_id(self, content: str, source: Optional[str] = None) -> str:
        """Gera ID unico para documento"""
        text = f"{source or ''}{content}"
        return hashlib.md5(text.encode()).hexdigest()

    def _chunk_text(
        self,
        text: str,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[str]:
        """Divide texto em chunks menores"""
        chunk_size = chunk_size or config.rag.chunk_size
        overlap = overlap or config.rag.chunk_overlap

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Tenta quebrar em fim de linha ou espaco
            if end < len(text):
                # Procura quebra de linha
                newline_pos = text.rfind('\n', start, end)
                if newline_pos > start + chunk_size // 2:
                    end = newline_pos + 1
                else:
                    # Procura espaco
                    space_pos = text.rfind(' ', start, end)
                    if space_pos > start + chunk_size // 2:
                        end = space_pos + 1

            chunks.append(text[start:end])
            start = end - overlap

        return chunks

    async def add_document(
        self,
        content: str,
        source: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> List[str]:
        """
        Adiciona documento a base de conhecimento

        Args:
            content: Conteudo do documento
            source: Origem (caminho do arquivo, URL, etc)
            metadata: Metadados adicionais

        Returns:
            Lista de IDs dos chunks adicionados
        """
        self._ensure_initialized()

        # Divide em chunks
        chunks = self._chunk_text(content)

        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for i, chunk in enumerate(chunks):
            doc_id = self._generate_id(chunk, source)
            ids.append(doc_id)
            documents.append(chunk)

            meta = {
                "source": source or "unknown",
                "chunk_index": i,
                "total_chunks": len(chunks),
                **(metadata or {})
            }
            metadatas.append(meta)

            # Gera embedding
            embedding = self._embedder.encode(chunk).tolist()
            embeddings.append(embedding)

        # Adiciona ao ChromaDB
        self._collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )

        return ids

    async def add_file(self, path: Path | str) -> List[str]:
        """Adiciona arquivo a base de conhecimento"""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Arquivo nao encontrado: {path}")

        content = path.read_text(encoding="utf-8", errors="ignore")

        return await self.add_document(
            content=content,
            source=str(path),
            metadata={
                "filename": path.name,
                "extension": path.suffix,
                "type": "file"
            }
        )

    async def add_directory(
        self,
        path: Path | str,
        pattern: str = "*",
        recursive: bool = True
    ) -> int:
        """
        Adiciona todos arquivos de um diretorio

        Returns:
            Numero de arquivos adicionados
        """
        path = Path(path)
        count = 0

        glob_method = path.rglob if recursive else path.glob

        for file_path in glob_method(pattern):
            if file_path.is_file():
                try:
                    await self.add_file(file_path)
                    count += 1
                    print(f"Adicionado: {file_path}")
                except Exception as e:
                    print(f"Erro ao adicionar {file_path}: {e}")

        return count

    async def search(
        self,
        query: str,
        top_k: int = None,
        filter_metadata: Optional[dict] = None
    ) -> List[SearchResult]:
        """
        Busca documentos relevantes

        Args:
            query: Texto de busca
            top_k: Numero maximo de resultados
            filter_metadata: Filtro por metadados

        Returns:
            Lista de resultados ordenados por relevancia
        """
        self._ensure_initialized()

        top_k = top_k or config.rag.top_k

        # Gera embedding da query
        query_embedding = self._embedder.encode(query).tolist()

        # Busca
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata
        )

        # Formata resultados
        search_results = []

        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                result = SearchResult(
                    document=Document(
                        id=results['ids'][0][i],
                        content=doc,
                        metadata=results['metadatas'][0][i] if results['metadatas'] else {},
                        source=results['metadatas'][0][i].get('source') if results['metadatas'] else None
                    ),
                    score=1 - results['distances'][0][i] if results['distances'] else 0
                )
                search_results.append(result)

        return search_results

    async def get_context(
        self,
        query: str,
        max_tokens: int = 2000,
        top_k: int = None
    ) -> str:
        """
        Obtem contexto relevante para uma query

        Retorna texto formatado para ser inserido no prompt
        """
        results = await self.search(query, top_k)

        if not results:
            return ""

        context_parts = []
        total_length = 0

        for result in results:
            content = result.document.content
            source = result.document.source or "desconhecido"

            # Estima tokens (aproximado)
            estimated_tokens = len(content) // 4

            if total_length + estimated_tokens > max_tokens:
                break

            context_parts.append(f"[Fonte: {source}]\n{content}")
            total_length += estimated_tokens

        if not context_parts:
            return ""

        return "## Contexto Relevante\n\n" + "\n\n---\n\n".join(context_parts)

    async def delete_document(self, doc_id: str) -> bool:
        """Remove documento da base"""
        self._ensure_initialized()

        try:
            self._collection.delete(ids=[doc_id])
            return True
        except:
            return False

    async def clear(self) -> bool:
        """Limpa toda a base de conhecimento"""
        self._ensure_initialized()

        try:
            self._client.delete_collection(self.collection_name)
            self._collection = None
            return True
        except:
            return False

    def get_stats(self) -> dict:
        """Retorna estatisticas da base"""
        self._ensure_initialized()

        return {
            "collection": self.collection_name,
            "document_count": self._collection.count(),
            "persist_path": str(self.persist_path)
        }


# Instancia global
knowledge_base = KnowledgeBase()
