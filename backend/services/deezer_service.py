import httpx
from typing import Dict, Any, List, Optional

class DeezerMusicService:
    """
    Service Deezer Music Intégral pour Hercul :
    - Recherche de musiques, albums, artistes.
    - Liens de lecture directe sur l'application Deezer ou le web.
    - Top Charts France & Monde.
    - Écoute d'extraits audio HD 30s.
    """

    BASE_URL = "https://api.deezer.com"

    async def search_deezer(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Recherche des morceaux sur Deezer."""
        try:
            url = f"{self.BASE_URL}/search"
            params = {"q": query, "limit": limit}

            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(url, params=params)
                data = res.json()

            tracks = data.get("data", [])
            if not tracks:
                return {"status": "error", "message": f"Aucun morceau trouvé sur Deezer pour « {query} »."}

            results = []
            for t in tracks:
                results.append({
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "artist": t.get("artist", {}).get("name"),
                    "album": t.get("album", {}).get("title"),
                    "cover": t.get("album", {}).get("cover_medium"),
                    "deezer_link": t.get("link"),
                    "preview_mp3": t.get("preview"),
                    "duration_seconds": t.get("duration")
                })

            top_track = results[0]
            return {
                "status": "success",
                "top_result": top_track,
                "total_found": len(results),
                "tracks": results,
                "message": (
                    f"🎵 **{top_track['title']}** par **{top_track['artist']}**\n"
                    f"💿 Album : {top_track['album']}\n"
                    f"🔗 Écouter sur Deezer : {top_track['deezer_link']}\n"
                    f"🔊 Extrait audio HD : {top_track['preview_mp3']}"
                )
            }

        except Exception as e:
            return {"status": "error", "message": f"Erreur recherche Deezer : {str(e)}"}

    async def get_top_charts(self, limit: int = 10) -> Dict[str, Any]:
        """Récupère les musiques les plus écoutées du moment sur Deezer."""
        try:
            url = f"{self.BASE_URL}/chart/0/tracks"
            params = {"limit": limit}

            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(url, params=params)
                data = res.json()

            tracks = data.get("data", [])
            formatted = []
            for i, t in enumerate(tracks):
                formatted.append({
                    "rank": i + 1,
                    "title": t.get("title"),
                    "artist": t.get("artist", {}).get("name"),
                    "link": t.get("link"),
                    "preview": t.get("preview")
                })

            summary = "\n".join([f"{t['rank']}. **{t['title']}** - {t['artist']}" for t in formatted[:5]])
            return {
                "status": "success",
                "top_tracks": formatted,
                "message": f"🔥 **Top Tendances Deezer :**\n{summary}"
            }

        except Exception as e:
            return {"status": "error", "message": f"Erreur Top Deezer : {str(e)}"}

    async def get_artist_top_tracks(self, artist_name: str) -> Dict[str, Any]:
        """Récupère les meilleures musiques d'un artiste spécifique."""
        try:
            # 1. Recherche de l'ID de l'artiste
            s_url = f"{self.BASE_URL}/search/artist"
            async with httpx.AsyncClient(timeout=10) as client:
                s_res = await client.get(s_url, params={"q": artist_name, "limit": 1})
                s_data = s_res.json().get("data", [])

                if not s_data:
                    return {"status": "error", "message": f"Artiste '{artist_name}' introuvable sur Deezer."}

                artist_id = s_data[0]["id"]
                artist_real_name = s_data[0]["name"]

                # 2. Récupération du Top Tracks
                t_url = f"{self.BASE_URL}/artist/{artist_id}/top"
                t_res = await client.get(t_url, params={"limit": 5})
                tracks = t_res.json().get("data", [])

            formatted = [{"title": t.get("title"), "album": t.get("album", {}).get("title"), "link": t.get("link")} for t in tracks]
            summary = "\n".join([f"• **{t['title']}** (Album: {t['album']}) - {t['link']}" for t in formatted])

            return {
                "status": "success",
                "artist": artist_real_name,
                "top_tracks": formatted,
                "message": f"⭐ **Top Morceaux de {artist_real_name} sur Deezer :**\n{summary}"
            }

        except Exception as e:
            return {"status": "error", "message": f"Erreur artiste Deezer : {str(e)}"}

deezer_service = DeezerMusicService()
