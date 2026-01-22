"""
Sistema RAG (Retrieval Augmented Generation) para IAFOX.
Permite a IA consultar livros e documentos PDF.
"""

from .buscar import buscar_nos_livros, verificar_index_existe

__all__ = ["buscar_nos_livros", "verificar_index_existe"]
