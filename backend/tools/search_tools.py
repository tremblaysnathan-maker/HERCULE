import asyncio
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from duckduckgo_search import DDGS
from backend.memory.token_optimizer import TokenOptimizer

class SearchTools:
    """
    Outils de recherche Web de Niveau 1 (Rapide / API).
    Idéal pour les questions factuelles, actualités, données textuelles légères.
    """

    @staticmethod
    def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Effectue une recherche rapide sur le web et retourne les titres, liens et extraits.
        """
        try:
            results = []
            with DDGS() as ddgs:
                ddgs_gen = ddgs.text(query, max_results=max_results)
                for r in ddgs_gen:
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
            
            if not results:
                return {"status": "success", "query": query, "results": "Aucun résultat trouvé."}

            formatted = []
            for i, res in enumerate(results, 1):
                formatted.append(f"[{i}] {res['title']}\nURL: {res['url']}\nExtrait: {res['snippet']}")

            return {
                "status": "success",
                "query": query,
                "count": len(results),
                "items": results,
                "results": "\n\n".join(formatted)
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur lors de la recherche : {str(e)}"}

    @staticmethod
    async def fetch_page_content(url: str, max_chars: int = 3000) -> Dict[str, Any]:
        """
        Récupère et nettoie le texte d'une page web sans ouvrir de navigateur lourd.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=headers) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    return {"status": "error", "code": response.status_code, "message": "Impossible de charger la page"}

                soup = BeautifulSoup(response.text, "html.parser")
                # Supprimer scripts, styles, navigations
                for elem in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    elem.decompose()

                text = soup.get_text(separator="\n")
                cleaned_text = TokenOptimizer.compress_text(text, max_chars=max_chars)

                return {
                    "status": "success",
                    "url": url,
                    "title": soup.title.string.strip() if soup.title else "",
                    "content": cleaned_text
                }
        except Exception as e:
            return {"status": "error", "message": f"Erreur lors de l'extraction de la page : {str(e)}"}
