import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from backend.config import settings

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class MediaFactoryService:
    """
    Usine de Conversion & Traitement Multimédia pour Hercul :
    - Extraction audio MP3 depuis n'importe quelle vidéo (MP4, MKV, AVI, MOV, WebM).
    - Conversion de formats d'images (WebP, HEIC, TIFF, BMP -> PNG / JPEG).
    - Compression et optimisation de fichiers.
    """

    def __init__(self):
        self.workspace = settings.WORKSPACE_PATH
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_available = shutil.which("ffmpeg") is not None

    def _resolve_path(self, filename: str) -> Path:
        if os.path.isabs(filename):
            return Path(filename)
        return self.workspace / filename

    def convert_video_to_mp3(self, video_filename: str) -> Dict[str, Any]:
        """Extrait la piste audio MP3 d'une vidéo."""
        src_path = self._resolve_path(video_filename)
        if not src_path.exists():
            return {"status": "error", "message": f"Fichier vidéo introuvable : {video_filename}"}

        out_name = f"{src_path.stem}.mp3"
        out_path = src_path.parent / out_name

        if not self.ffmpeg_available:
            return {
                "status": "error",
                "message": "FFmpeg n'est pas installé sur le système hôte. Installez 'ffmpeg' (ex: apt install ffmpeg)."
            }

        try:
            cmd = ["ffmpeg", "-y", "-i", str(src_path), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(out_path)]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            return {
                "status": "success",
                "output_filename": out_name,
                "output_path": str(out_path),
                "message": f"🎵 Audio extrait avec succès dans le fichier **`{out_name}`** !"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur conversion FFmpeg : {str(e)}"}

    def convert_image(self, image_filename: str, target_format: str = "png") -> Dict[str, Any]:
        """Convertit une image dans un autre format (PNG, JPEG, WEBP, etc.)."""
        src_path = self._resolve_path(image_filename)
        if not src_path.exists():
            return {"status": "error", "message": f"Fichier image introuvable : {image_filename}"}

        tgt_ext = target_format.lower().replace(".", "").replace("jpg", "jpeg")
        out_name = f"{src_path.stem}_converted.{tgt_ext}"
        out_path = src_path.parent / out_name

        if PIL_AVAILABLE:
            try:
                with Image.open(src_path) as img:
                    if tgt_ext == "jpeg" and img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(out_path, format=tgt_ext.upper(), quality=90)

                return {
                    "status": "success",
                    "output_filename": out_name,
                    "output_path": str(out_path),
                    "message": f"🖼️ Image convertie avec succès en format **{tgt_ext.upper()}** (`{out_name}`) !"
                }
            except Exception as e:
                print(f"[MediaFactory] Erreur PIL : {e}")

        # Fallback FFmpeg
        if self.ffmpeg_available:
            try:
                cmd = ["ffmpeg", "-y", "-i", str(src_path), str(out_path)]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                return {
                    "status": "success",
                    "output_filename": out_name,
                    "message": f"🖼️ Image convertie en **{tgt_ext.upper()}** via FFmpeg !"
                }
            except Exception as e:
                return {"status": "error", "message": f"Erreur conversion image : {str(e)}"}

        return {"status": "error", "message": "Aucun moteur de traitement d'image (Pillow ou FFmpeg) disponible."}

media_factory = MediaFactoryService()
