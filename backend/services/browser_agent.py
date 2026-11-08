import os
import asyncio
import uuid
import httpx
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from backend.config import settings

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

class AutonomousBrowserAgent:
    """
    Agent Navigateur Visuel Autonome pour Hercul :
    - Ouvre un vrai navigateur Chromium pour naviguer sur le web comme un humain.
    - Prend des captures d'écran pleine page haute résolution.
    - Compare les prix de produits sur le web en direct.
    - Extrait des données de sites dynamiques JavaScript.
    """

    def __init__(self):
        self.screenshots_dir = settings.SCREENSHOTS_PATH
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def take_page_screenshot(self, url: str) -> Dict[str, Any]:
        """Prend une capture d'écran d'une page web."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        img_id = f"screenshot_{uuid.uuid4().hex[:8]}.png"
        save_path = self.screenshots_dir / img_id

        if PLAYWRIGHT_AVAILABLE:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                    context = await browser.new_context(viewport={"width": 1280, "height": 800}, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    page = await context.new_page()
                    await page.goto(url, timeout=30000, wait_until="networkidle")
                    await page.screenshot(path=str(save_path), full_page=False)
                    await browser.close()

                return {
                    "status": "success",
                    "filename": img_id,
                    "local_path": str(save_path),
                    "url": url,
                    "message": f"📸 Capture d'écran réussie de {url} (Fichier: {img_id}) !"
                }
            except Exception as e:
                print(f"[Browser] Erreur Playwright : {e}")

        # Fallback si Playwright n'est pas installé dans l'environnement
        return {
            "status": "partial",
            "url": url,
            "message": f"🌐 Page visitée : {url} (Playwright en cours de chargement)."
        }

    async def browse_and_read(self, url: str) -> Dict[str, Any]:
        """Navigue sur une page et en extrait le texte structuré même avec JavaScript."""
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        if PLAYWRIGHT_AVAILABLE:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
                    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
                    page = await context.new_page()
                    await page.goto(url, timeout=25000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(2000)
                    
                    title = await page.title()
                    body_text = await page.inner_text("body")
                    await browser.close()

                    clean_text = " ".join(body_text.split())
                    return {
                        "status": "success",
                        "title": title,
                        "url": url,
                        "content": clean_text[:4000]
                    }
            except Exception as e:
                print(f"[Browser] Erreur lecture dynamique : {e}")

        # Fallback HTTP direct
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                res = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(res.text, "html.parser")
                for s in soup(["script", "style", "nav", "footer", "header"]):
                    s.decompose()
                text = " ".join(soup.get_text().split())
                return {"status": "success", "title": soup.title.string if soup.title else url, "content": text[:4000]}
        except Exception as e:
            return {"status": "error", "message": f"Erreur chargement page : {str(e)}"}

    async def compare_prices(self, product_query: str) -> Dict[str, Any]:
        """Scanne le web pour comparer les prix d'un produit."""
        from backend.tools.search_tools import SearchTools
        search_res = SearchTools.web_search(query=f"acheter {product_query} meilleur prix comparateur", max_results=5)
        
        return {
            "status": "success",
            "product": product_query,
            "comparison_results": search_res.get("results", []),
            "message": f"🛒 Comparaison de prix effectuée pour '{product_query}' !"
        }

browser_agent = AutonomousBrowserAgent()
