"""
Modulo de busca web usando DuckDuckGo
"""

from duckduckgo_search import DDGS


def buscar_web(query: str, max_results: int = 10) -> str:
    """
    Busca na web usando DuckDuckGo

    Args:
        query: Termo de busca
        max_results: Numero maximo de resultados

    Returns:
        Resultados formatados como string
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"Nenhum resultado encontrado para '{query}'."

        output = f"**Resultados para '{query}':**\n\n"
        for i, r in enumerate(results, 1):
            titulo = r.get("title", "Sem titulo")
            link = r.get("href", "")
            descricao = r.get("body", "")
            output += f"{i}. **{titulo}**\n"
            output += f"   Link: {link}\n"
            output += f"   {descricao}\n\n"

        return output

    except Exception as e:
        return f"Erro na busca: {str(e)}"


def buscar_noticias(query: str, max_results: int = 10) -> str:
    """
    Busca noticias usando DuckDuckGo

    Args:
        query: Termo de busca
        max_results: Numero maximo de resultados

    Returns:
        Noticias formatadas como string
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))

        if not results:
            return f"Nenhuma noticia encontrada para '{query}'."

        output = f"**Noticias sobre '{query}':**\n\n"
        for i, r in enumerate(results, 1):
            titulo = r.get("title", "Sem titulo")
            link = r.get("url", "")
            fonte = r.get("source", "")
            data = r.get("date", "")
            descricao = r.get("body", "")
            output += f"{i}. **{titulo}**\n"
            output += f"   Fonte: {fonte} | Data: {data}\n"
            output += f"   Link: {link}\n"
            output += f"   {descricao}\n\n"

        return output

    except Exception as e:
        return f"Erro na busca: {str(e)}"


def buscar_imagens(query: str, max_results: int = 10) -> str:
    """
    Busca imagens usando DuckDuckGo

    Args:
        query: Termo de busca
        max_results: Numero maximo de resultados

    Returns:
        Imagens formatadas como string
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=max_results))

        if not results:
            return f"Nenhuma imagem encontrada para '{query}'."

        output = f"**Imagens para '{query}':**\n\n"
        for i, r in enumerate(results, 1):
            titulo = r.get("title", "Sem titulo")
            link = r.get("image", "")
            fonte = r.get("url", "")
            output += f"{i}. **{titulo}**\n"
            output += f"   Imagem: {link}\n"
            output += f"   Fonte: {fonte}\n\n"

        return output

    except Exception as e:
        return f"Erro na busca: {str(e)}"
