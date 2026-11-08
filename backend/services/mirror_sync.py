import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.services.google_workspace import google_workspace

PARIS_TZ = ZoneInfo(settings.TIMEZONE)

class MirrorSyncService:
    """
    Service de Synchronisation Miroir (Google Tasks & Keep ➔ Markdown / Obsidian / Notion) :
    - Exporte automatiquement les tâches et notes dans des fichiers Markdown propres dans /workspace/
    - Permet l'interopérabilité locale avec Obsidian, Notion et les outils de code.
    """

    def __init__(self):
        self.workspace = settings.WORKSPACE_PATH
        self.notes_dir = self.workspace / "notes"
        self.tasks_dir = self.workspace / "tasks"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def sync_mirror(self) -> Dict[str, Any]:
        """Synchronise l'ensemble des tâches Google Tasks et notes Keep en fichiers Markdown."""
        synced_files = []

        # 1. Synchronisation des Tâches Google Tasks
        tasks_res = google_workspace.list_google_tasks(show_completed=True, max_results=50)
        tasks = tasks_res.get("tasks", [])
        
        tasks_md = f"# 📋 Google Tasks Miroir — Mis à jour le {datetime.now(PARIS_TZ).strftime('%d/%m/%Y à %H:%M')}\n\n"
        for t in tasks:
            status_box = "[x]" if t.get("status") == "completed" else "[ ]"
            due_str = f" *(Échéance: {t.get('due')[:10]})*" if t.get("due") else ""
            notes_str = f"\n  > {t.get('notes')}" if t.get("notes") else ""
            tasks_md += f"- {status_box} **{t.get('title')}**{due_str}{notes_str}\n"

        tasks_file = self.tasks_dir / "google_tasks_mirror.md"
        with open(tasks_file, "w", encoding="utf-8") as f:
            f.write(tasks_md)
        synced_files.append(str(tasks_file))

        # 2. Synchronisation des Notes Keep
        notes_res = google_workspace.list_keep_notes()
        notes = notes_res.get("notes", [])
        for n in notes:
            clean_title = "".join(c for c in n.get("title", "note") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
            note_file = self.notes_dir / f"{clean_title}.md"
            note_md = f"# 📝 {n.get('title')}\n*Catégorie : {n.get('category', 'Général')}*\n\n{n.get('content')}\n"
            with open(note_file, "w", encoding="utf-8") as f:
                f.write(note_md)
            synced_files.append(str(note_file))

        return {
            "status": "success",
            "total_synced_files": len(synced_files),
            "files": synced_files,
            "message": f"🔄 **Synchronisation Miroir terminée :** {len(tasks)} tâches et {len(notes)} notes exportées en Markdown dans `{self.workspace}` !"
        }

mirror_sync_service = MirrorSyncService()
