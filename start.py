import os
import sys
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

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print("\n" + "="*50)
    print("🏛️   LANCEMENT DE L'AGENT HERCUL   🏛️")
    print(f"📡  Interface Web : http://localhost:{port}")
    print(f"📱  Endpoint Tasker : http://localhost:{port}/api/tasker/ask")
    print("="*50 + "\n")

    uvicorn.run("backend.server:app", host=host, port=port, reload=True)
