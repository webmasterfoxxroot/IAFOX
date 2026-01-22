"""
Modulo de busca web usando DuckDuckGo
"""

from duckduckgo_search import DDGS
from typing import Optional


class WebSearch:
    """Ferramenta de busca na web usando DuckDuckGo"""

    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Busca na web usando DuckDuckGo

        Args:
            query: Termo de busca
            max_results: Numero maximo de resultados

        Returns:
            Lista de resultados com titulo, link e descricao
        """
        try:
            results = []
            for r in self.ddgs.text(query, max_results=max_results):
                results.append({
                    "titulo": r.get("title", ""),
                    "link": r.get("href", ""),
                    "descricao": r.get("body", "")
                })
            return results
        except Exception as e:
            return [{"erro": str(e)}]

    def search_news(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Busca noticias usando DuckDuckGo

        Args:
            query: Termo de busca
            max_results: Numero maximo de resultados

        Returns:
            Lista de noticias
        """
        try:
            results = []
            for r in self.ddgs.news(query, max_results=max_results):
                results.append({
                    "titulo": r.get("title", ""),
                    "link": r.get("url", ""),
                    "fonte": r.get("source", ""),
                    "data": r.get("date", ""),
                    "descricao": r.get("body", "")
                })
            return results
        except Exception as e:
            return [{"erro": str(e)}]

    def search_images(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Busca imagens usando DuckDuckGo

        Args:
            query: Termo de busca
            max_results: Numero maximo de resultados

        Returns:
            Lista de imagens
        """
        try:
            results = []
            for r in self.ddgs.images(query, max_results=max_results):
                results.append({
                    "titulo": r.get("title", ""),
                    "link": r.get("image", ""),
                    "fonte": r.get("url", ""),
                    "tamanho": f"{r.get('width', '')}x{r.get('height', '')}"
                })
            return results
        except Exception as e:
            return [{"erro": str(e)}]


# Instancia global
web_search = WebSearch()


def buscar_web(query: str, max_results: int = 10) -> str:
    """
    Funcao auxiliar para buscar na web

    Args:
        query: Termo de busca
        max_results: Numero maximo de resultados

    Returns:
        Resultados formatados como string
    """
    results = web_search.search(query, max_results)

    if not results:
        return "Nenhum resultado encontrado."

    if "erro" in results[0]:
        return f"Erro na busca: {results[0]['erro']}"

    output = f"Resultados para '{query}':\n\n"
    for i, r in enumerate(results, 1):
        output += f"{i}. **{r['titulo']}**\n"
        output += f"   Link: {r['link']}\n"
        output += f"   {r['descricao']}\n\n"

    return output


def buscar_noticias(query: str, max_results: int = 10) -> str:
    """
    Funcao auxiliar para buscar noticias
    """
    results = web_search.search_news(query, max_results)

    if not results:
        return "Nenhuma noticia encontrada."

    if "erro" in results[0]:
        return f"Erro na busca: {results[0]['erro']}"

    output = f"Noticias sobre '{query}':\n\n"
    for i, r in enumerate(results, 1):
        output += f"{i}. **{r['titulo']}**\n"
        output += f"   Fonte: {r['fonte']} | Data: {r['data']}\n"
        output += f"   Link: {r['link']}\n"
        output += f"   {r['descricao']}\n\n"

    return output
