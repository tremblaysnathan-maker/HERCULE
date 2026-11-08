import os
import sys
import webbrowser
import threading
import uvicorn
from pathlib import Path
from dotenv import load_dotenv

# Vérification du fichier .env
env_file = Path(".env")
if not env_file.exists():
    print("⚠️ Fichier .env non trouvé ! Création automatique depuis .env.example...")
    example = Path(".env.example")
    if example.exists():
        with open(example, "r", encoding="utf-8") as f_in, open(".env", "w", encoding="utf-8") as f_out:
            f_out.write(f_in.read())
        print("✅ Fichier .env créé. Pensez à y renseigner votre GEMINI_API_KEY !")

load_dotenv()

def open_browser_delayed(port: int):
    import time
    time.sleep(2.0)
    try:
        webbrowser.open(f"http://localhost:{port}")
    except Exception:
        pass

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print("\n" + "=" * 60)
    print("🏛️   LANCEMENT DE L'AGENT HERCULE v3.0 (100% LOCAL)   🏛️")
    print(f"📡  Interface Web Locale : http://localhost:{port}")
    print(f"🐝  Escouade Multi-Agents : Active (Chercheur + Architecte + Stratège + Critique)")
    print(f"🔄  Objectifs Continus 24/7 : Actifs")
    print(f"📱  Endpoint Tasker Local : http://localhost:{port}/api/tasker/ask")
    print("=" * 60 + "\n")

    if os.getenv("AUTO_OPEN_BROWSER", "true").lower() == "true":
        threading.Thread(target=open_browser_delayed, args=(port,), daemon=True).start()

    uvicorn.run("backend.server:app", host=host, port=port, reload=False)
