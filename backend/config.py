import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Charger les variables depuis le fichier .env
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / os.getenv("DATA_DIR", "data")
WORKSPACE_DIR = BASE_DIR / os.getenv("WORKSPACE_DIR", "workspace")

# Créer les dossiers de données si non existants
DATA_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "chroma").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "screenshots").mkdir(parents=True, exist_ok=True)

class Settings:
    # Clés API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    HERCUL_SECRET_KEY: str = os.getenv("HERCUL_SECRET_KEY", "hercul_secret_key_default")
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Paris")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    DEFAULT_ALERT_EMAIL: str = os.getenv("DEFAULT_ALERT_EMAIL", "")

    # Téléphonie & Appels (Twilio / VoIP)
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")
    USER_PHONE_NUMBER: str = os.getenv("USER_PHONE_NUMBER", "")

    # Domotique & Maison Connectée (Home Assistant)
    HOME_ASSISTANT_URL: str = os.getenv("HOME_ASSISTANT_URL", "http://homeassistant.local:8123")
    HOME_ASSISTANT_TOKEN: str = os.getenv("HOME_ASSISTANT_TOKEN", "")
    
    # Réseau & Serveur
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Modèles Gemini
    GEMINI_PRO_MODEL: str = os.getenv("GEMINI_PRO_MODEL", "gemini-3.7-flash")
    GEMINI_FLASH_MODEL: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-3.7-flash")
    GEMINI_FLASH_LITE_MODEL: str = os.getenv("GEMINI_FLASH_LITE_MODEL", "gemini-3.5-flash-lite")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    
    # Optimisation de tokens
    MAX_WORKING_MEMORY_TOKENS: int = int(os.getenv("MAX_WORKING_MEMORY_TOKENS", "8000"))
    MAX_LONG_TERM_RECALL_RESULTS: int = int(os.getenv("MAX_LONG_TERM_RECALL_RESULTS", "5"))
    
    # Chemins
    BASE_PATH: Path = BASE_DIR
    DATA_PATH: Path = DATA_DIR
    WORKSPACE_PATH: Path = WORKSPACE_DIR
    CHROMA_PATH: Path = DATA_DIR / "chroma"
    PROFILE_FILE_PATH: Path = DATA_DIR / "user_profile.json"
    SCREENSHOTS_PATH: Path = DATA_DIR / "screenshots"

settings = Settings()
