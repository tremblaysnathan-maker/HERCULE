import os
import io
import json
import asyncio
import httpx
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Request, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
import edge_tts

from backend.config import settings
from backend.core.agent import HerculAgent
from backend.memory.memory_manager import MemoryManager

try:
    from backend.discord_bot import start_discord_bot
    DISCORD_MODULE_AVAILABLE = True
except Exception as e:
    print(f"[Warning] Discord bot non disponible : {e}")
    DISCORD_MODULE_AVAILABLE = False
    start_discord_bot = None

app = FastAPI(
    title="Hercul AI Agent Core",
    description="Backend API de l'agent autonome Hercul (Gemini, Mémoire, TTS Humain, Tasker, Discord)",
    version="2.0.0"
)

# Lancement automatique du bot Discord, du Secrétaire Proactif, du Chasseur Web et du Bilan Dimanche
@app.on_event("startup")
async def on_startup():
    if DISCORD_MODULE_AVAILABLE and start_discord_bot and settings.DISCORD_BOT_TOKEN:
        asyncio.create_task(start_discord_bot())
    
    # 🤖 1. Secrétaire Proactif Autonome 24/7
    try:
        from backend.services.proactive_secretary import proactive_secretary
        asyncio.create_task(proactive_secretary.run_loop())
    except Exception as e:
        print(f"[Secrétaire] Erreur lancement : {e}")

    # 🕵️ 2. Chasseur & Veilleur Web 24/7
    try:
        from backend.services.web_hunter import web_hunter
        asyncio.create_task(web_hunter.run_loop())
    except Exception as e:
        print(f"[Web Hunter] Erreur lancement : {e}")

    # 📊 3. Bilan Exécutif du Dimanche Soir
    try:
        from backend.services.life_report import sunday_report_service
        asyncio.create_task(sunday_report_service.run_sunday_loop())
    except Exception as e:
        print(f"[Bilan Dimanche] Erreur lancement : {e}")

    # ☕ 4. Briefing Matinal de 08h00
    try:
        from backend.services.morning_briefing import morning_briefing_service
        asyncio.create_task(morning_briefing_service.run_morning_loop())
    except Exception as e:
        print(f"[Morning Briefing] Erreur lancement : {e}")

    # 🌙 5. Point d'Habitudes du Soir à 22h00
    try:
        from backend.services.habit_tracker import habit_tracker
        asyncio.create_task(habit_tracker.run_evening_loop())
    except Exception as e:
        print(f"[Habit Tracker] Erreur lancement : {e}")

    # 🔄 6. Moteur d'Objectifs Autonomes Continus 24/7
    try:
        from backend.services.continuous_goals import continuous_goal_engine
        asyncio.create_task(continuous_goal_engine.run_continuous_loop())
    except Exception as e:
        print(f"[Continuous Goals] Erreur lancement : {e}")

# CORS universel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_manager = MemoryManager()
agent = HerculAgent(memory_manager=memory_manager)

# ----------------- SÉCURITÉ & AUTHENTIFICATION VPS -----------------

def verify_api_key(
    x_hercul_key: Optional[str] = Header(None, alias="X-Hercul-Key"),
    authorization: Optional[str] = Header(None),
    key: Optional[str] = Query(None)
):
    secret = settings.HERCUL_SECRET_KEY
    if not secret or secret == "hercul_secret_key_default":
        return True

    provided_key = x_hercul_key or key
    if not provided_key and authorization and authorization.startswith("Bearer "):
        provided_key = authorization.replace("Bearer ", "").strip()

    if provided_key != secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé d'authentification Hercul invalide ou manquante."
        )
    return True

# ----------------- MODÈLES DE REQUÊTES -----------------

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default_session"
    fast_mode: Optional[bool] = False
    model: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "fr-FR-VivienneMultilingualNeural"

# ----------------- ENDPOINTS CHAT & TASKER -----------------

@app.post("/api/chat", dependencies=[Depends(verify_api_key)])
async def api_chat(req: ChatRequest):
    """Endpoint de chat et d'exécution agentique."""
    try:
        result = await agent.chat(
            message=req.message,
            session_id=req.session_id or "default_session",
            fast_mode=req.fast_mode or False,
            model_override=req.model
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tasker/ask", dependencies=[Depends(verify_api_key)])
async def tasker_ask_post(req: ChatRequest):
    """Endpoint ultra-rapide pour Tasker (POST)."""
    result = await agent.chat(
        message=req.message,
        session_id=req.session_id or "tasker_session",
        fast_mode=True
    )
    return {"reply": result["response"]}

@app.get("/api/tasker/ask", dependencies=[Depends(verify_api_key)])
async def tasker_ask_get(q: str = Query(..., description="Message utilisateur")):
    """Endpoint direct pour Tasker (GET)."""
    result = await agent.chat(
        message=q,
        session_id="tasker_session",
        fast_mode=True
    )
    return PlainTextResponse(result["response"])

@app.get("/api/tasker/command", dependencies=[Depends(verify_api_key)])
async def tasker_command_get(q: str = Query(..., description="Message ou commande vocale Tasker")):
    """
    Endpoint intelligent pour Tasker qui renvoie une action système Android précise (Minuteur, Alarme, etc.)
    """
    import re
    q_lower = q.lower().strip()
    
    # 1. Détection de Minuteur Android
    is_timer = any(w in q_lower for w in ["minuteur", "minuterie", "timer", "chrono"])
    timer_seconds = 0
    timer_label = "Hercul"

    if is_timer:
        # Extraction des minutes (ex: 2 min, 10 minutes, 1 heure)
        min_match = re.search(r"(\d+)\s*(?:min|minute|minutes|m\b)", q_lower)
        sec_match = re.search(r"(\d+)\s*(?:sec|seconde|secondes|s\b)", q_lower)
        hour_match = re.search(r"(\d+)\s*(?:h|heure|heures)", q_lower)

        if min_match:
            timer_seconds += int(min_match.group(1)) * 60
        if sec_match:
            timer_seconds += int(sec_match.group(1))
        if hour_match:
            timer_seconds += int(hour_match.group(1)) * 3600

        # Si aucun chiffre extrait mais mot présent, défaut à 5 min
        if timer_seconds == 0:
            timer_seconds = 300

        # Label éventuel (ex: "pour les pâtes")
        for prep in ["pour ", "sur ", "de "]:
            if prep in q_lower:
                parts = q_lower.split(prep, 1)
                if len(parts) > 1 and len(parts[1].strip()) > 1:
                    timer_label = parts[1].strip()[:20].capitalize()
                    break

        minutes_disp = timer_seconds // 60
        secs_disp = timer_seconds % 60
        d_str = f"{minutes_disp} minute{'s' if minutes_disp > 1 else ''}" if minutes_disp > 0 else ""
        if secs_disp > 0:
            d_str += f" {secs_disp} seconde{'s' if secs_disp > 1 else ''}"
        d_str = d_str.strip()

        voice_msg = f"C'est fait Nathan, minuteur de {d_str} réglé sur ton téléphone."

        return {
            "action": "timer",
            "seconds": timer_seconds,
            "label": timer_label,
            "reply": voice_msg
        }

    # 2. Question classique / Recherche
    result = await agent.chat(message=q, session_id="tasker_session", fast_mode=True)
    return {
        "action": "speak",
        "seconds": 0,
        "label": "",
        "reply": result["response"]
    }

# ----------------- SYNTHÈSE VOCALE HUMAINE RÉALISTE (NEURAL TTS) -----------------

@app.post("/api/voice/tts")
async def voice_tts_post(req: TTSRequest):
    """Génère un flux audio MP3 avec une vraie voix humaine réaliste."""
    clean_text = req.text.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Texte vide")

    try:
        communicate = edge_tts.Communicate(clean_text, voice=req.voice or "fr-FR-HenriNeural", rate="+5%")
        
        async def audio_stream():
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]

        return StreamingResponse(audio_stream(), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")

@app.get("/api/voice/tts")
async def voice_tts_get(text: str = Query(..., description="Texte à vocaliser"), voice: Optional[str] = "fr-FR-VivienneMultilingualNeural"):
    """Endpoint GET pour écoute audio directe."""
    try:
        communicate = edge_tts.Communicate(text, voice=voice or "fr-FR-VivienneMultilingualNeural", rate="+4%")
        
        async def audio_stream():
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]

        return StreamingResponse(audio_stream(), media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur TTS : {str(e)}")

# ----------------- AUTHENTIFICATION GOOGLE WORKSPACE EN 1 CLIC -----------------

import secrets
import hashlib
import base64
import urllib.parse
from backend.services.google_workspace import SCOPES, TOKEN_FILE, find_credentials_file

@app.get("/api/google/login")
async def google_login(request: Request):
    """Génère le lien officiel de connexion Google avec PKCE intégré."""
    cred_file = find_credentials_file()
    if not cred_file or not os.path.exists(cred_file):
        raise HTTPException(
            status_code=400,
            detail="Fichier d'identifiants Google introuvable sur le serveur."
        )

    with open(cred_file, "r", encoding="utf-8") as f:
        cred_data = json.load(f)

    cfg = cred_data.get("web") or cred_data.get("installed") or {}
    client_id = cfg.get("client_id")
    cfg_redirects = cfg.get("redirect_uris", [])
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or (
        cfg_redirects[0] if cfg_redirects else f"{request.base_url}api/google/callback"
    )

    # Génération PKCE (Code Verifier & Code Challenge S256)
    code_verifier = secrets.token_urlsafe(64)
    hashed = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(hashed).decode("utf-8").rstrip("=")

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": code_verifier # Le code_verifier nous est renvoyé intact par Google
    }

    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    from fastapi.responses import RedirectResponse
    return RedirectResponse(auth_url)

@app.get("/api/google/callback")
async def google_callback(request: Request, code: Optional[str] = Query(None), state: Optional[str] = Query(None)):
    """Reçoit la validation de Google et échange le code avec le code_verifier."""
    if not code:
        raise HTTPException(status_code=400, detail="Code d'autorisation manquant")

    try:
        cred_file = find_credentials_file()
        with open(cred_file, "r", encoding="utf-8") as f:
            cred_data = json.load(f)

        cfg = cred_data.get("web") or cred_data.get("installed") or {}
        client_id = cfg.get("client_id")
        client_secret = cfg.get("client_secret")
        cfg_redirects = cfg.get("redirect_uris", [])
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI") or (
            cfg_redirects[0] if cfg_redirects else f"{request.base_url}api/google/callback"
        )

        post_data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }

        # Injection du code_verifier PKCE renvoyé par Google
        if state:
            post_data["code_verifier"] = state

        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data=post_data
            )
            token_data = token_resp.json()

        if "error" in token_data:
            err_msg = token_data.get("error_description") or token_data.get("error")
            raise HTTPException(status_code=400, detail=f"Erreur Google OAuth : {err_msg}")

        # Sauvegarde du jeton au format officiel Google Credentials
        credentials_payload = {
            "token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": client_id,
            "client_secret": client_secret,
            "scopes": SCOPES
        }

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(credentials_payload, f, indent=2)

        print(f"✅ [Google] Authentification OAuth2 réussie ! Jeton sauvegardé dans : {TOKEN_FILE}")

        html_content = """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
          <meta charset="UTF-8">
          <title>Connexion Google Réussie</title>
          <style>
            body { background: #02040a; color: #fff; font-family: system-ui, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; text-align: center; }
            .card { background: rgba(6, 15, 35, 0.85); border: 1px solid #00f0ff; border-radius: 16px; padding: 40px; box-shadow: 0 0 30px rgba(0, 240, 255, 0.3); max-width: 450px; }
            h1 { color: #00f0ff; margin-bottom: 10px; }
            p { color: #94a3b8; font-size: 1.1rem; line-height: 1.5; }
            .btn { display: inline-block; margin-top: 20px; background: #00f0ff; color: #000; padding: 10px 24px; border-radius: 8px; text-decoration: none; font-weight: 700; }
          </style>
        </head>
        <body>
          <div class="card">
            <h1>✅ Compte Google Connecté !</h1>
            <p>Hercul a désormais accès direct à votre <strong>Gmail</strong>, <strong>Google Calendar</strong>, <strong>Drive</strong>, <strong>Docs</strong> et <strong>Sheets</strong>.</p>
            <a href="/" class="btn">Retourner sur Hercul</a>
          </div>
        </body>
        </html>
        """
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [Google] Erreur lors de l'échange OAuth : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur d'authentification Google : {str(e)}")

# ----------------- NOTIFICATIONS TEMPS RÉEL (WEB & DISCORD) -----------------

from backend.services.scheduler import scheduler

@app.get("/api/notifications/poll")
async def poll_notifications():
    """Permet au site web de récupérer les alertes de minuteurs échus."""
    notes = list(scheduler.pending_web_notifications)
    scheduler.pending_web_notifications.clear()
    return {"notifications": notes}

# ----------------- MÉMOIRE & STATUT -----------------

@app.get("/api/memory/profile", dependencies=[Depends(verify_api_key)])
async def get_profile():
    return memory_manager.profile.data

@app.get("/api/memory/stats", dependencies=[Depends(verify_api_key)])
async def get_memory_stats():
    return memory_manager.get_stats()

@app.get("/api/memory/graph")
async def get_memory_graph():
    """Renvoie les constellations neuronales de la mémoire et du Swarm v3.0 pour l'affichage 3D."""
    profile = memory_manager.profile.data
    nodes = [
        {"id": "core", "label": "HERCUL CORE v3.0", "group": "ai", "size": 26, "color": "#00f0ff"},
        {"id": "swarm", "label": "Swarm Multi-Agents", "group": "ai", "size": 20, "color": "#ec4899"},
        {"id": "goals", "label": "Objectifs Continus 24/7", "group": "ai", "size": 18, "color": "#14b8a6"},
        {"id": "skills", "label": "Skill Forge Auto-Évolutif", "group": "ai", "size": 18, "color": "#eab308"},
        {"id": "user", "label": profile.get("name", "Opérateur"), "group": "user", "size": 20, "color": "#c084fc"},
        {"id": "workspace", "label": "Google Workspace", "group": "tool", "size": 15, "color": "#3b82f6"},
        {"id": "gmail", "label": "Gmail & Factures", "group": "tool", "size": 12, "color": "#ef4444"},
        {"id": "calendar", "label": "Agenda & Tasks", "group": "tool", "size": 12, "color": "#10b981"},
        {"id": "deezer", "label": "Deezer Music", "group": "media", "size": 12, "color": "#f59e0b"},
        {"id": "smarthome", "label": "Maison & Colis", "group": "iot", "size": 12, "color": "#8b5cf6"},
        {"id": "sentinel", "label": "Guardrails & Vault", "group": "sec", "size": 12, "color": "#06b6d4"},
        {"id": "budget", "label": "Finance & Budget", "group": "fin", "size": 12, "color": "#22c55e"}
    ]
    links = [
        {"source": "core", "target": "user"},
        {"source": "core", "target": "swarm"},
        {"source": "core", "target": "goals"},
        {"source": "core", "target": "skills"},
        {"source": "core", "target": "workspace"},
        {"source": "workspace", "target": "gmail"},
        {"source": "workspace", "target": "calendar"},
        {"source": "core", "target": "deezer"},
        {"source": "core", "target": "smarthome"},
        {"source": "core", "target": "sentinel"},
        {"source": "gmail", "target": "budget"},
        {"source": "core", "target": "budget"}
    ]
    return {"nodes": nodes, "links": links}

@app.get("/api/swarm/status")
async def get_swarm_status():
    """Retourne l'état temps réel de l'escouade Multi-Agents (Hub-and-Spoke)."""
    from backend.core.swarm_orchestrator import swarm_orchestrator
    return swarm_orchestrator.get_swarm_status()

@app.get("/api/goals")
async def get_continuous_goals():
    """Retourne la liste et la progression des Objectifs Autonomes Continus 24/7."""
    from backend.services.continuous_goals import continuous_goal_engine
    return continuous_goal_engine.list_goals()

@app.get("/api/skills")
async def get_custom_skills():
    """Retourne le catalogue des compétences auto-forgées et les leçons d'auto-évolution."""
    from backend.services.skill_creator import skill_forge
    return skill_forge.list_skills()

# ----------------- TALKIE-WALKIE VOCAL ULTRA-RAPIDE -----------------

@app.post("/api/voice/walkie_talkie")
async def walkie_talkie_voice(req: ChatRequest):
    """Réponse vocale instantanée en streaming MP3 pour le mode Talkie-Walkie."""
    res = await agent.chat(message=req.message, session_id="walkie_talkie", fast_mode=True)
    text_out = res.get("response", "Entendu.")
    
    communicate = edge_tts.Communicate(text_out, voice="fr-FR-VivienneMultilingualNeural", rate="+10%")
    mp3_bytes = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_bytes.extend(chunk["data"])

    return StreamingResponse(io.BytesIO(mp3_bytes), media_type="audio/mpeg", headers={"X-Hercul-Response": urllib.parse.quote(text_out[:200])})

@app.get("/api/status")
async def health_check():
    return {
        "status": "online",
        "agent": "Hercul AI V3",
        "models": {
            "pro": settings.GEMINI_PRO_MODEL,
            "flash": settings.GEMINI_FLASH_MODEL
        }
    }

# ----------------- FICHIERS STATIQUES & FRONTEND -----------------

app.mount("/screenshots", StaticFiles(directory=str(settings.SCREENSHOTS_PATH)), name="screenshots")

frontend_dir = settings.BASE_PATH / "frontend"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="static_frontend")

    @app.get("/")
    async def serve_index():
        return FileResponse(str(frontend_dir / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.server:app", host=settings.HOST, port=settings.PORT, reload=True)
