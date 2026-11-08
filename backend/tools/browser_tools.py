import asyncio
import uuid
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, Playwright
from backend.config import settings
from backend.memory.token_optimizer import TokenOptimizer

class BrowserController:
    """
    Contrôleur Playwright haute performance pour Hercul.
    Optimisé pour la vitesse avec blocage des ressources lourdes et navigation asynchrone rapide.
    """
    _instance: Optional["BrowserController"] = None
    _playwright: Optional[Playwright] = None
    _browser: Optional[Browser] = None
    _page: Optional[Page] = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_instance(cls) -> "BrowserController":
        if cls._instance is None:
            cls._instance = BrowserController()
        return cls._instance

    async def _ensure_page(self) -> Page:
        async with self._lock:
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            if self._browser is None:
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--no-first-run",
                        "--disable-extensions"
                    ]
                )
            if self._page is None or self._page.is_closed():
                context = await self._browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                self._page = await context.new_page()
            return self._page

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Ouvre une URL avec chargement rapide."""
        try:
            page = await self._ensure_page()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            
            # Timeout réduit à 12s pour une réactivité maximale
            await page.goto(url, wait_until="domcontentloaded", timeout=12000)
            title = await page.title()
            
            # Screenshot automatique
            screenshot_path = await self.take_screenshot()

            return {
                "status": "success",
                "url": page.url,
                "title": title,
                "screenshot": screenshot_path.get("screenshot_path", ""),
                "message": f"Navigation OK : {title} ({page.url})"
            }
        except Exception as e:
            return {"status": "error", "message": f"Échec navigation vers {url} : {str(e)}"}

    async def click(self, selector: str) -> Dict[str, Any]:
        """Clique sur un élément ou texte."""
        try:
            page = await self._ensure_page()
            try:
                await page.click(selector, timeout=3000)
            except Exception:
                await page.get_by_text(selector).first.click(timeout=3000)

            await page.wait_for_timeout(600)
            title = await page.title()
            screenshot = await self.take_screenshot()

            return {
                "status": "success",
                "clicked": selector,
                "current_url": page.url,
                "title": title,
                "screenshot": screenshot.get("screenshot_path", "")
            }
        except Exception as e:
            return {"status": "error", "message": f"Impossible de cliquer sur '{selector}' : {str(e)}"}

    async def type_text(self, selector: str, text: str, press_enter: bool = False) -> Dict[str, Any]:
        """Saisie de texte accélérée."""
        try:
            page = await self._ensure_page()
            await page.fill(selector, text, timeout=3000)
            if press_enter:
                await page.press(selector, "Enter")
                await page.wait_for_timeout(800)

            screenshot = await self.take_screenshot()
            return {
                "status": "success",
                "typed_into": selector,
                "text": text,
                "current_url": page.url,
                "screenshot": screenshot.get("screenshot_path", "")
            }
        except Exception as e:
            return {"status": "error", "message": f"Impossible d'écrire dans '{selector}' : {str(e)}"}

    async def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Capture d'écran optimisée."""
        try:
            page = await self._ensure_page()
            fname = filename or f"screenshot_{uuid.uuid4().hex[:8]}.png"
            full_path = settings.SCREENSHOTS_PATH / fname
            
            await page.screenshot(path=str(full_path), full_page=False)
            return {
                "status": "success",
                "filename": fname,
                "screenshot_path": str(full_path)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_content(self, max_chars: int = 2500) -> Dict[str, Any]:
        """Extrait le texte visible condensé."""
        try:
            page = await self._ensure_page()
            text = await page.evaluate("() => document.body.innerText")
            cleaned = TokenOptimizer.compress_text(text, max_chars=max_chars)
            return {
                "status": "success",
                "url": page.url,
                "title": await page.title(),
                "content": cleaned
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def close(self):
        async with self._lock:
            if self._page:
                await self._page.close()
                self._page = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
