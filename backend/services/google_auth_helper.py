import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from backend.config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets"
]

CREDENTIALS_FILE = settings.DATA_PATH / "google_credentials.json"
TOKEN_FILE = settings.DATA_PATH / "google_token.json"

def authenticate_google():
    print("=" * 60)
    print("🔑 [HERCUL] Authentification Google Workspace (Gmail, Calendar, Drive)")
    print("=" * 60)

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Fichier d'identifiants introuvable : {CREDENTIALS_FILE}")
        return

    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Rafraîchissement du jeton d'accès existant...")
            creds.refresh(Request())
        else:
            print("\n🌐 Une page web Google va s'ouvrir dans votre navigateur...")
            print("👉 Choisissez votre compte Google et cliquez sur 'Autoriser' / 'Continuer'.\n")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        print(f"\n✅ Authentification réussie ! Jeton sauvegardé dans : {TOKEN_FILE}")
        print("🎉 Hercul a désormais accès direct à votre Gmail, Google Calendar, Drive, Docs et Sheets !")
    else:
        print("✅ Le compte Google est déjà connecté et valide !")

if __name__ == "__main__":
    authenticate_google()
