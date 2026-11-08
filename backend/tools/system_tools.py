import os
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from backend.config import settings

class SystemTools:
    """
    Outils de gestion de fichiers et d'exécution système pour Hercul.
    """

    @staticmethod
    def execute_command(command: str, timeout_seconds: int = 30) -> Dict[str, Any]:
        """
        Exécute une commande shell / powershell de manière sécurisée et retourne stdout et stderr.
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=str(settings.WORKSPACE_PATH)
            )
            return {
                "status": "success",
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"La commande a dépassé le délai de {timeout_seconds}s"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur d'exécution : {str(e)}"}

    @staticmethod
    def list_files(subdirectory: str = "") -> Dict[str, Any]:
        """Liste les fichiers et dossiers dans l'espace de travail."""
        try:
            target_path = settings.WORKSPACE_PATH / subdirectory
            if not target_path.exists():
                return {"status": "error", "message": f"Le dossier {subdirectory} n'existe pas."}

            items = []
            for item in target_path.iterdir():
                items.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size_bytes": item.stat().st_size if item.is_file() else None
                })
            return {"status": "success", "path": str(target_path), "items": items}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def write_file(filename: str, content: str) -> Dict[str, Any]:
        """Crée ou modifie un fichier dans l'espace de travail."""
        try:
            filepath = settings.WORKSPACE_PATH / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "file": filename, "bytes_written": len(content)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def read_file(filename: str, max_chars: int = 5000) -> Dict[str, Any]:
        """Lit le contenu d'un fichier dans l'espace de travail."""
        try:
            filepath = settings.WORKSPACE_PATH / filename
            if not filepath.exists():
                return {"status": "error", "message": f"Le fichier '{filename}' n'existe pas."}

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read(max_chars)
            return {"status": "success", "file": filename, "content": content}
        except Exception as e:
            return {"status": "error", "message": str(e)}
