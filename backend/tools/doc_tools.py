import os
import re
import csv
import io
import httpx
from typing import Dict, Any, Optional
from backend.config import settings
from backend.memory.token_optimizer import TokenOptimizer

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PdfReader = None
    PYPDF_AVAILABLE = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_AVAILABLE = True
except ImportError:
    YouTubeTranscriptApi = None
    YOUTUBE_AVAILABLE = False

class DocumentTools:
    """
    Outils d'analyse de documents (PDF, Excel, CSV) et de vidéos YouTube pour Hercul.
    """

    @staticmethod
    def read_pdf(file_path_or_bytes: Any, max_pages: int = 20) -> Dict[str, Any]:
        """Extrait le texte d'un fichier PDF."""
        if not PYPDF_AVAILABLE:
            return {"status": "error", "message": "Le module pypdf n'est pas encore installé."}

        try:
            reader = None
            if isinstance(file_path_or_bytes, (str, os.PathLike)):
                p = settings.WORKSPACE_PATH / file_path_or_bytes if not os.path.isabs(file_path_or_bytes) else file_path_or_bytes
                reader = PdfReader(str(p))
            else:
                reader = PdfReader(io.BytesIO(file_path_or_bytes))

            total_pages = len(reader.pages)
            pages_to_read = min(total_pages, max_pages)
            
            extracted_text = []
            for i in range(pages_to_read):
                page_text = reader.pages[i].extract_text() or ""
                if page_text.strip():
                    extracted_text.append(f"--- [Page {i+1}] ---\n{page_text.strip()}")

            full_text = "\n\n".join(extracted_text)
            compressed = TokenOptimizer.compress_text(full_text, max_chars=8000)

            return {
                "status": "success",
                "total_pages": total_pages,
                "pages_extracted": pages_to_read,
                "content": compressed
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur lecture PDF : {str(e)}"}

    @staticmethod
    def read_csv_or_table(file_path_or_bytes: Any, max_rows: int = 100) -> Dict[str, Any]:
        """Lit et extrait les données d'un fichier CSV ou tableau."""
        try:
            content = ""
            if isinstance(file_path_or_bytes, (str, os.PathLike)):
                p = settings.WORKSPACE_PATH / file_path_or_bytes if not os.path.isabs(file_path_or_bytes) else file_path_or_bytes
                with open(p, mode="r", encoding="utf-8", errors="replace") as f:
                    reader = csv.reader(f)
                    rows = [", ".join(row) for i, row in enumerate(reader) if i < max_rows]
                    content = "\n".join(rows)
            else:
                text_stream = io.StringIO(file_path_or_bytes.decode("utf-8", errors="replace"))
                reader = csv.reader(text_stream)
                rows = [", ".join(row) for i, row in enumerate(reader) if i < max_rows]
                content = "\n".join(rows)

            return {
                "status": "success",
                "total_rows_preview": len(rows),
                "content": TokenOptimizer.compress_text(content, max_chars=5000)
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur lecture tableau : {str(e)}"}

    @staticmethod
    def get_youtube_transcript(url_or_id: str) -> Dict[str, Any]:
        """Extrait la transcription d'une vidéo YouTube."""
        if not YOUTUBE_AVAILABLE:
            return {"status": "error", "message": "Le module youtube-transcript-api n'est pas encore installé."}

        try:
            video_id = url_or_id
            if "youtube.com" in url_or_id or "youtu.be" in url_or_id:
                match = re.search(r"(?:v=|\/|youtu\.be\/)([a-zA-Z0-9_-]{11})", url_or_id)
                if match:
                    video_id = match.group(1)

            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            transcript = None
            try:
                transcript = transcript_list.find_transcript(['fr', 'en'])
            except Exception:
                transcript = transcript_list.find_generated_transcript(['fr', 'en'])

            data = transcript.fetch()
            full_text = " ".join([entry.get('text', '') for entry in data])
            compressed = TokenOptimizer.compress_text(full_text, max_chars=8000)

            return {
                "status": "success",
                "video_id": video_id,
                "language": transcript.language,
                "transcript": compressed
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Impossible d'extraire la transcription : {str(e)}"
            }
