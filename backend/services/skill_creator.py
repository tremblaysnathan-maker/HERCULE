import json
import sys
import subprocess
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.config import settings

PARIS_TZ = ZoneInfo("Europe/Paris")
SKILLS_DIR = settings.WORKSPACE_PATH / "custom_skills"
SKILLS_DIR.mkdir(parents=True, exist_ok=True)
SKILLS_REGISTRY_FILE = settings.DATA_PATH / "custom_skills_registry.json"
SOUL_LESSONS_FILE = settings.DATA_PATH / "soul_lessons.json"


class DynamicSkillForge:
    """
    🧬 MOTEUR D'AUTO-ÉVOLUTION & FORGE DE COMPÉTENCES DYNAMIQUES (Inspiré de Hermes Agent & Letta)
    - Permet à Hercul de créer, valider, sauvegarder et exécuter ses propres nouveaux outils Python à la volée.
    - Gère la mémoire procédurale et l'auto-amélioration continue (Soul Lessons) injectée dans sa conscience.
    """

    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = self._load_skills()
        self.lessons: List[Dict[str, Any]] = self._load_lessons()

    def _load_skills(self) -> Dict[str, Dict[str, Any]]:
        if SKILLS_REGISTRY_FILE.exists():
            try:
                with open(SKILLS_REGISTRY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_skills(self):
        try:
            with open(SKILLS_REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.skills, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SkillForge] Erreur sauvegarde skills : {e}")

    def _load_lessons(self) -> List[Dict[str, Any]]:
        if SOUL_LESSONS_FILE.exists():
            try:
                with open(SOUL_LESSONS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_lessons(self):
        try:
            with open(SOUL_LESSONS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.lessons[-30:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SkillForge] Erreur sauvegarde leçons : {e}")

    def create_skill(self, skill_name: str, description: str, python_code: str) -> Dict[str, Any]:
        """
        Crée et compile une nouvelle compétence Python réutilisable dans workspace/custom_skills/.
        """
        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in skill_name.lower()).strip("_")
        if not clean_name:
            clean_name = f"skill_{int(time.time())}"

        # Nettoyage des balises markdown éventuelles
        code_clean = python_code.strip()
        if code_clean.startswith("```"):
            lines = code_clean.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            code_clean = "\n".join(lines).strip()

        # Validation syntaxique AST / Compile avant enregistrement
        try:
            compile(code_clean, f"{clean_name}.py", "exec")
        except SyntaxError as se:
            return {
                "status": "error",
                "message": f"⚠️ Erreur de syntaxe dans la compétence `{clean_name}` (ligne {se.lineno}) : {se.msg}"
            }

        skill_path = SKILLS_DIR / f"{clean_name}.py"
        try:
            with open(skill_path, "w", encoding="utf-8") as f:
                f.write(code_clean + "\n")
        except Exception as e:
            return {"status": "error", "message": f"Erreur écriture fichier skill : {str(e)}"}

        now_str = datetime.now(PARIS_TZ).strftime("%d/%m/%Y %H:%M")
        self.skills[clean_name] = {
            "name": clean_name,
            "description": description,
            "path": str(skill_path),
            "created_at": now_str,
            "runs_count": 0
        }
        self._save_skills()

        return {
            "status": "success",
            "skill_name": clean_name,
            "local_path": str(skill_path),
            "message": (
                f"🧬 **Nouvelle Compétence Forgée avec Succès : `{clean_name}`**\n"
                f"• **Description** : {description}\n"
                f"• **Fichier** : `{skill_path.name}` (Syntaxe Python validée ✅)\n"
                f"• Prête à être exécutée à tout moment !"
            )
        }

    def execute_skill(self, skill_name: str, args_json: str = "{}") -> Dict[str, Any]:
        """Exécute une compétence dynamique précédemment forgée par Hercul."""
        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in skill_name.lower()).strip("_")
        skill_info = self.skills.get(clean_name)

        if not skill_info:
            # Chercher si le fichier existe quand même dans le dossier
            candidate = SKILLS_DIR / f"{clean_name}.py"
            if not candidate.exists():
                available = ", ".join(self.skills.keys()) or "Aucune"
                return {
                    "status": "error",
                    "message": f"⚠️ Compétence `{clean_name}` introuvable. Compétences disponibles : {available}"
                }
            skill_path = candidate
        else:
            skill_path = Path(skill_info["path"])

        try:
            res = subprocess.run(
                [sys.executable, str(skill_path), args_json],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(SKILLS_DIR)
            )
            stdout = (res.stdout or "").strip()
            stderr = (res.stderr or "").strip()

            if clean_name in self.skills:
                self.skills[clean_name]["runs_count"] = self.skills[clean_name].get("runs_count", 0) + 1
                self._save_skills()

            if res.returncode != 0:
                return {
                    "status": "error",
                    "skill_name": clean_name,
                    "stderr": stderr[:800],
                    "message": f"⚠️ Erreur lors de l'exécution de `{clean_name}` :\n```\n{stderr[:600]}\n```"
                }

            return {
                "status": "success",
                "skill_name": clean_name,
                "output": stdout[:1200],
                "message": f"⚡ **Résultat de la Compétence `{clean_name}` :**\n```\n{stdout[:1000] or 'Exécuté sans sortie console.'}\n```"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur d'exécution `{clean_name}` : {str(e)}"}

    def list_skills(self) -> Dict[str, Any]:
        """Liste toutes les compétences dynamiques forgées par Hercul et ses leçons d'auto-amélioration."""
        if not self.skills:
            skills_txt = "Aucune compétence personnalisée forgée pour le moment."
        else:
            skills_txt = "\n".join([
                f"• **`{k}`** : {v['description']} *(Exécutée {v.get('runs_count', 0)} fois)*"
                for k, v in self.skills.items()
            ])

        lessons_txt = "\n".join([
            f"• [{l['date']}] {l['lesson']}" for l in self.lessons[-5:]
        ]) or "Aucune règle d'auto-évolution enregistrée."

        return {
            "status": "success",
            "skills_count": len(self.skills),
            "skills": self.skills,
            "lessons": self.lessons[-10:],
            "message": (
                f"🧬 **Catalogue de Compétences Auto-Évolutives ({len(self.skills)}) :**\n{skills_txt}\n\n"
                f"🧠 **Dernières Leçons Procédurales (Soul Memory) :**\n{lessons_txt}"
            )
        }

    def record_lesson(self, lesson: str, category: str = "optimization") -> Dict[str, Any]:
        """Enregistre une leçon d'auto-amélioration permanente dans la mémoire procédurale d'Hercul."""
        now_str = datetime.now(PARIS_TZ).strftime("%d/%m/%Y")
        entry = {
            "date": now_str,
            "category": category,
            "lesson": lesson.strip()
        }
        self.lessons.append(entry)
        self._save_lessons()
        return {
            "status": "success",
            "entry": entry,
            "message": f"🧠 **Auto-Évolution Enregistrée ({category}) :** « {lesson.strip()} »"
        }

    def get_procedural_context_for_prompt(self) -> str:
        """Retourne le résumé des compétences dynamiques et leçons pour injection dans le prompt système."""
        parts = []
        if self.skills:
            skill_names = ", ".join([f"`{k}` ({v['description'][:40]})" for k, v in list(self.skills.items())[:8]])
            parts.append(f"- Compétences dynamiques forgées disponibles : {skill_names}")
        if self.lessons:
            recent = "; ".join([l["lesson"] for l in self.lessons[-5:]])
            parts.append(f"- Règles d'auto-évolution apprises : {recent}")
        if not parts:
            return ""
        return "### 🧬 Mémoire Procédurale & Auto-Évolution :\n" + "\n".join(parts)


skill_forge = DynamicSkillForge()
