import os
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.services.google_workspace import google_workspace

PARIS_TZ = ZoneInfo(settings.TIMEZONE)
BUDGET_STATE_FILE = settings.DATA_PATH / "budget_state.json"

class SmartBudgetTracker:
    """
    Assistant Budget & Gestionnaire de Dépenses Automatisé pour Hercul :
    - Enregistre automatiquement les dépenses dans Google Sheets ('Hercul_Suivi_Budget_2026').
    - Extrait les montants et marchands depuis les factures et e-mails reçus.
    - Calcule les bilans et totaux mensuels par catégorie (Abonnements, Courses, Transports, etc.).
    """

    def __init__(self):
        self.spreadsheet_title = "Hercul_Suivi_Budget_2026"
        self.spreadsheet_id = self._load_sheet_id()

    def _load_sheet_id(self) -> Optional[str]:
        if os.path.exists(BUDGET_STATE_FILE):
            try:
                with open(BUDGET_STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("spreadsheet_id")
            except Exception:
                pass
        return None

    def _save_sheet_id(self, sheet_id: str):
        self.spreadsheet_id = sheet_id
        try:
            with open(BUDGET_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"spreadsheet_id": sheet_id, "updated_at": datetime.now(PARIS_TZ).isoformat()}, f, indent=2)
        except Exception as e:
            print(f"[Budget] Erreur sauvegarde ID Sheet : {e}")

    def _ensure_budget_sheet(self) -> Optional[str]:
        """Crée le Google Sheet de budget s'il n'existe pas encore."""
        if self.spreadsheet_id:
            return self.spreadsheet_id

        # Recherche sur Drive
        drive_res = google_workspace.search_drive(query=self.spreadsheet_title, max_results=1)
        files = drive_res.get("files", [])
        if files:
            self._save_sheet_id(files[0]["id"])
            return files[0]["id"]

        # Création du tableur
        headers = ["Date", "Fournisseur / Commerçant", "Catégorie", "Montant (€)", "Notes"]
        sheet_res = google_workspace.create_google_sheet(title=self.spreadsheet_title, headers=headers)
        
        if sheet_res.get("status") == "success":
            new_id = sheet_res.get("spreadsheet_id")
            self._save_sheet_id(new_id)
            return new_id
        return None

    def log_expense(self, amount: float, vendor: str, category: str = "Général", date_str: Optional[str] = None, notes: str = "") -> Dict[str, Any]:
        """Enregistre une dépense dans Google Sheets."""
        sheet_id = self._ensure_budget_sheet()
        if not sheet_id:
            return {"status": "error", "message": "Impossible d'accéder au Google Sheet de budget (compte Google non connecté)."}

        date_val = date_str or datetime.now(PARIS_TZ).strftime("%d/%m/%Y")
        row = [[date_val, vendor.strip(), category.strip(), f"{amount:.2f} €", notes.strip()]]

        res = google_workspace.append_rows_to_sheet(spreadsheet_id=sheet_id, rows=row)
        if res.get("status") == "success":
            return {
                "status": "success",
                "vendor": vendor,
                "amount": amount,
                "category": category,
                "date": date_val,
                "spreadsheet_id": sheet_id,
                "message": f"💶 **Dépense enregistrée :** {amount:.2f} € chez **{vendor}** (Catégorie : {category}) dans ton Google Sheet Budget !"
            }
        return res

    def extract_expense_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrait automatiquement le montant et le marchand d'un texte de facture/e-mail."""
        # Recherche du montant (ex: 24.99 €, 120,50 EUR, Total TTC : 59€)
        match = re.search(r'(\d+[\.,]\d{2}|\d+)\s*(?:€|EUR|euros?)', text, flags=re.IGNORECASE)
        if not match:
            return None

        raw_num = match.group(1).replace(",", ".")
        try:
            amount = float(raw_num)
        except ValueError:
            return None

        # Catégorisation intelligente
        t_lower = text.lower()
        if any(k in t_lower for k in ["sncf", "train", "uber", "essence", "péage", "vol"]):
            category = "Transports"
        elif any(k in t_lower for k in ["netflix", "spotify", "deezer", "chatgpt", "ovh", "abonnement", "serveur"]):
            category = "Abonnements & Tech"
        elif any(k in t_lower for k in ["restaurant", "uber eats", "deliveroo", "carrefour", "leclerc", "courses"]):
            category = "Alimentation"
        elif any(k in t_lower for k in ["doctolib", "pharmacie", "santé", "médecin"]):
            category = "Santé"
        else:
            category = "Factures & Services"

        return {"amount": amount, "category": category}

budget_tracker = SmartBudgetTracker()
