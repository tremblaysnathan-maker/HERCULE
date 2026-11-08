import subprocess
from typing import Dict, Any, List, Optional
from backend.config import settings

class TerminalSessionService:
    """
    Émulation & Interaction CLI / Terminal Linux (Node-PTY / SSH2) :
    - Exécute des sessions terminal interactives multi-étapes.
    - Gère les prompts de commandes et retourne les logs propres.
    """

    def __init__(self):
        self.workspace = settings.WORKSPACE_PATH

    def execute_terminal_command(self, command: str, timeout_seconds: int = 15) -> Dict[str, Any]:
        """Lance une commande dans le terminal du serveur avec capture de sortie."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            output = res.stdout or res.stderr or "Commande exécutée sans sortie."
            return {
                "status": "success",
                "command": command,
                "exit_code": res.returncode,
                "output": output[:1500],
                "message": f"💻 **Terminal :** `Exit code: {res.returncode}`\n```bash\n{output[:500]}\n```"
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": f"Délai d'attente dépassé ({timeout_seconds}s) pour : `{command}`"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur terminal : {str(e)}"}

terminal_session = TerminalSessionService()
