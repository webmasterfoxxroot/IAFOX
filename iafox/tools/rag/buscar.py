"""
Módulo de busca RAG para IAFOX.
Busca informações nos livros indexados.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional

# Diretórios
BASE_DIR = Path(__file__).parent.parent.parent.parent
INDEX_DIR = BASE_DIR / "conhecimento" / "index"


def verificar_index_existe() -> bool:
    """Verifica se o índice existe."""
    chroma_dir = INDEX_DIR / "chroma.sqlite3"
    return INDEX_DIR.exists() and any(INDEX_DIR.iterdir())


def buscar_nos_livros(query: str, materia: Optional[str] = None, max_results: int = 5) -> str:
    """
    Busca informações nos livros indexados.

    Args:
        query: Pergunta ou termo de busca
        materia: Filtrar por matéria (matematica, portugues, ciencias, etc.)
        max_results: Número máximo de resultados

    Returns:
        String formatada com os resultados encontrados
    """
    if not verificar_index_existe():
        return """❌ Índice não encontrado!

Para usar a busca nos livros, você precisa:
1. Colocar os PDFs na pasta: conhecimento/livros_8ano/
2. Rodar o indexador: python -m iafox.tools.rag.indexar

Ainda não há livros indexados no sistema."""

    try:
        import chromadb
        from chromadb.config import Settings

        # Conectar ao índice
        client = chromadb.PersistentClient(
            path=str(INDEX_DIR),
            settings=Settings(anonymized_telemetry=False)
        )

        # Obter coleção
        try:
            collection = client.get_collection("conhecimento_iafox")
        except:
            return "❌ Coleção não encontrada. Rode o indexador primeiro: python -m iafox.tools.rag.indexar"

        # Preparar filtro por matéria
        where_filter = None
        if materia:
            materia_normalizada = materia.lower().replace("ê", "e").replace("á", "a")
            where_filter = {"materia": materia_normalizada}

        # Fazer busca
        results = collection.query(
            query_texts=[query],
            n_results=max_results,
            where=where_filter
        )

        if not results["documents"] or not results["documents"][0]:
            if materia:
                return f"Nenhum resultado encontrado para '{query}' na matéria {materia}."
            return f"Nenhum resultado encontrado para '{query}'."

        # Formatar resultados
        output = f"**📚 Resultados para '{query}'**"
        if materia:
            output += f" (Matéria: {materia})"
        output += "\n\n"

        for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
            arquivo = metadata.get("arquivo", "Desconhecido")
            mat = metadata.get("materia", "geral")
            paginas = metadata.get("paginas", "?")

            output += f"---\n"
            output += f"**Resultado {i}** - {arquivo} ({mat}) - Páginas {paginas}\n\n"

            # Limitar tamanho do texto
            texto = doc[:800] + "..." if len(doc) > 800 else doc
            output += f"{texto}\n\n"

        output += "---\n"
        output += f"*{len(results['documents'][0])} resultados encontrados nos livros do 8° ano*"

        return output

    except Exception as e:
        return f"❌ Erro na busca: {str(e)}"


def listar_materias_disponiveis() -> str:
    """Lista as matérias disponíveis no índice."""
    if not verificar_index_existe():
        return "Índice não encontrado."

    try:
        import chromadb
        from chromadb.config import Settings

        client = chromadb.PersistentClient(
            path=str(INDEX_DIR),
            settings=Settings(anonymized_telemetry=False)
        )

        collection = client.get_collection("conhecimento_iafox")

        # Buscar todas as matérias únicas
        all_data = collection.get()
        materias = set()

        for metadata in all_data["metadatas"]:
            if metadata.get("materia"):
                materias.add(metadata["materia"])

        if not materias:
            return "Nenhuma matéria encontrada no índice."

        output = "**📖 Matérias disponíveis:**\n\n"
        for mat in sorted(materias):
            output += f"• {mat.capitalize()}\n"

        return output

    except Exception as e:
        return f"Erro ao listar matérias: {str(e)}"


# Teste rápido
if __name__ == "__main__":
    print("Testando busca RAG...")
    print(verificar_index_existe())
    if verificar_index_existe():
        print(buscar_nos_livros("equação"))
