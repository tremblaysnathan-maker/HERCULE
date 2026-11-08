import httpx
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

class StealthScraperService:
    """
    Service de Scraping Furtif & Contournement Anti-Bot (FlareSolverr / Playwright) :
    - Résout automatiquement les protections Cloudflare / Turnstile.
    - Récupère le HTML propre et les cookies de session.
    """

    def __init__(self, flaresolverr_url: str = "http://localhost:8191/v1"):
        self.flaresolverr_url = flaresolverr_url

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Tente de scraper l'URL via FlareSolverr, sinon fallback Playwright."""
        # 1. Tentative FlareSolverr si actif
        try:
            payload = {"cmd": "request.get", "url": url, "maxTimeout": 60000}
            async with httpx.AsyncClient(timeout=30) as client:
                res = await client.post(self.flaresolverr_url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    solution = data.get("solution", {})
                    html = solution.get("response", "")
                    soup = BeautifulSoup(html, "html.parser")
                    text = " ".join([p.get_text() for p in soup.find_all(["p", "h1", "h2", "h3", "li"])])
                    return {
                        "status": "success",
                        "engine": "FlareSolverr Anti-Bot Bypass",
                        "cookies_count": len(solution.get("cookies", [])),
                        "content": text[:1500],
                        "message": f"🛡️ Protection anti-bot contournée avec succès pour `{url}` !"
                    }
        except Exception:
            pass

        # 2. Fallback Navigateur Playwright Intégré
        try:
            from backend.services.browser_agent import browser_agent
            page_data = await browser_agent.browse_and_read(url)
            return {
                "status": "success",
                "engine": "Playwright Stealth Browser",
                "content": page_data.get("content", "")[:1500],
                "message": f"🌐 Page lue avec succès via le navigateur autonome pour `{url}`."
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur scraping furtif : {str(e)}"}

stealth_scraper = StealthScraperService()
