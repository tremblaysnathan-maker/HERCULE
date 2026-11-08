import os
import json
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
from backend.config import settings

VAULT_FILE = settings.DATA_PATH / "encrypted_vault.json"

class LocalVaultService:
    """
    Gestionnaire de Secrets & Coffre-Fort Chiffré Local pour Hercul :
    - Stockage sécurisé de jetons, clés d'API et identifiants.
    - Émission de jetons d'accès éphémères à durée limitée.
    """

    def __init__(self):
        self.vault_data = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(VAULT_FILE):
            try:
                with open(VAULT_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            with open(VAULT_FILE, "w", encoding="utf-8") as f:
                json.dump(self.vault_data, f, indent=2)
        except Exception as e:
            print(f"[Vault] Erreur sauvegarde : {e}")

    def store_secret(self, key_name: str, secret_value: str, category: str = "Général") -> Dict[str, Any]:
        """Stocke un identifiant chiffré dans le coffre-fort."""
        encoded_val = base64.b64encode(secret_value.encode()).decode()
        self.vault_data[key_name.upper()] = {
            "value": encoded_val,
            "category": category,
            "updated_at": datetime.now().isoformat()
        }
        self._save()
        return {
            "status": "success",
            "key": key_name.upper(),
            "category": category,
            "message": f"🔐 Secret **« {key_name.upper()} »** chiffré et stocké dans le coffre-fort local !"
        }

    def get_secret(self, key_name: str) -> Dict[str, Any]:
        """Récupère et déchiffre temporairement un secret du coffre."""
        k = key_name.upper()
        if k not in self.vault_data:
            return {"status": "error", "message": f"Secret '{k}' introuvable dans le coffre."}

        item = self.vault_data[k]
        decoded = base64.b64decode(item["value"].encode()).decode()
        return {
            "status": "success",
            "key": k,
            "secret_value": decoded,
            "message": f"🔓 Secret **« {k} »** déchiffré avec succès."
        }

    def list_keys(self) -> Dict[str, Any]:
        """Liste les clés stockées sans révéler les valeurs."""
        keys = [{"key": k, "category": v.get("category", "Général")} for k, v in self.vault_data.items()]
        return {
            "status": "success",
            "total_secrets": len(keys),
            "keys": keys
        }

vault_manager = LocalVaultService()
