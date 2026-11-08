import os
import json
import base64
import email
import uuid
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.config import settings

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
    from google.oauth2.credentials import Credentials
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    build = None
    Credentials = None
    GOOGLE_LIBS_AVAILABLE = False

PARIS_TZ = ZoneInfo(settings.TIMEZONE)
TOKEN_FILE = settings.DATA_PATH / "google_token.json"
CREDENTIALS_FILE = settings.DATA_PATH / "google_credentials.json"
NOTES_FILE = settings.DATA_PATH / "google_keep_notes.json"

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def find_credentials_file() -> Optional[str]:
    candidates = [
        settings.DATA_PATH / "google_credentials.json",
        settings.BASE_PATH / "google_credentials.json",
        settings.BASE_PATH / "data" / "google_credentials.json",
    ]
    for p in [settings.BASE_PATH, settings.DATA_PATH]:
        if p.exists():
            for f in p.glob("client_secret*.json"):
                candidates.append(f)
            for f in p.glob("*google*.json"):
                if "token" not in f.name.lower():
                    candidates.append(f)

    for c in candidates:
        if c and os.path.exists(c):
            return str(c)
    return None

class GoogleWorkspaceService:
    """
    Suite Google Workspace Totale (De A à Z) pour Hercul :
    - 📧 GMAIL (Lecture, Recherche, Envoi, Brouillons, Corbeille, Pièces jointes)
    - 📅 CALENDAR (Agenda, Événements, Quick-Add, Suppression)
    - 🎥 MEET (Visioconférences avec liens meet.google.com automatiques)
    - 📂 DRIVE (Recherche, Upload, Dossiers, Suppression, Partage)
    - 📄 DOCS & 📊 SHEETS (Création, Ajout, Tableaux, Lignes)
    - 📍 MAPS & ITINÉRAIRES (Trafic en direct, Trajets, Lieux, Commerces)
    - 📋 FORMS (Formulaires & Questionnaires en direct)
    - 📈 YOUTUBE DATA (Statistiques de chaînes, Tendances)
    - ✅ TASKS & 👥 CONTACTS (Tâches officielles, Répertoire)
    - 📝 KEEP / NOTES (Mémos & Notes persistantes)
    """

    def __init__(self):
        self.api_key = settings.GOOGLE_API_KEY

    def _load_credentials(self) -> Optional[Any]:
        if not GOOGLE_LIBS_AVAILABLE or not Credentials:
            return None
        if os.path.exists(TOKEN_FILE):
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                if creds and creds.valid:
                    return creds
                if creds and creds.expired and creds.refresh_token:
                    try:
                        from google.auth.transport.requests import Request
                        creds.refresh(Request())
                        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                            f.write(creds.to_json())
                        return creds
                    except Exception:
                        pass
            except Exception as e:
                print(f"[Google] Erreur lecture token : {e}")
        return None

    def get_service(self, service_name: str, version: str):
        if not GOOGLE_LIBS_AVAILABLE or not build:
            return None
        try:
            creds = self._load_credentials()
            if creds:
                return build(service_name, version, credentials=creds, cache_discovery=False)
            elif self.api_key:
                return build(service_name, version, developerKey=self.api_key, cache_discovery=False)
        except Exception as e:
            print(f"[Google] Erreur service {service_name} : {e}")
        return None

    def is_oauth_authenticated(self) -> bool:
        creds = self._load_credentials()
        return creds is not None

    # =========================================================================
    # 📧 1. GMAIL (Messagerie, Recherche, Envoi & Pièces Jointes)
    # =========================================================================

    def list_gmail_messages(self, query: str = "is:unread", max_results: int = 5) -> Dict[str, Any]:
        service = self.get_service("gmail", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté. Veuillez vous connecter via le lien Google Connect."}

        try:
            results = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
            messages = results.get("messages", [])

            email_summaries = []
            for msg in messages:
                msg_data = service.users().messages().get(userId="me", id=msg["id"], format="metadata").execute()
                headers = msg_data.get("payload", {}).get("headers", [])
                
                subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "Sans sujet")
                sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Expéditeur inconnu")
                date_str = next((h["value"] for h in headers if h["name"].lower() == "date"), "")
                snippet = msg_data.get("snippet", "")

                email_summaries.append({
                    "id": msg["id"],
                    "from": sender,
                    "subject": subject,
                    "date": date_str,
                    "preview": snippet
                })

            return {"status": "success", "total_found": len(email_summaries), "messages": email_summaries}
        except Exception as e:
            return {"status": "error", "message": f"Erreur Gmail : {str(e)}"}

    def read_gmail_message(self, message_id: str) -> Dict[str, Any]:
        service = self.get_service("gmail", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
            headers = msg.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "Sans sujet")
            sender = next((h["value"] for h in headers if h["name"].lower() == "from"), "Expéditeur inconnu")
            
            body_text = ""
            payload = msg.get("payload", {})
            attachments = []

            def extract_parts(p):
                nonlocal body_text, attachments
                if p.get("filename") and p.get("body", {}).get("attachmentId"):
                    attachments.append({
                        "filename": p.get("filename"),
                        "mimeType": p.get("mimeType"),
                        "attachmentId": p.get("body", {}).get("attachmentId"),
                        "size": p.get("body", {}).get("size")
                    })
                if p.get("mimeType") == "text/plain" and "data" in p.get("body", {}):
                    body_text += base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8", errors="replace")
                if "parts" in p:
                    for sub in p["parts"]:
                        extract_parts(sub)

            extract_parts(payload)
            if not body_text:
                body_text = msg.get("snippet", "Aucun texte lisible.")

            return {
                "status": "success",
                "id": message_id,
                "subject": subject,
                "from": sender,
                "attachments": attachments,
                "content": body_text[:4000]
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur lecture email : {str(e)}"}

    def send_gmail_message(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        service = self.get_service("gmail", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            message = MIMEText(body, "plain", "utf-8")
            message["to"] = to
            message["subject"] = subject
            raw_msg = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            sent = service.users().messages().send(userId="me", body={"raw": raw_msg}).execute()
            return {"status": "success", "message_id": sent.get("id"), "message": f"📧 E-mail envoyé avec succès à {to} (Sujet : « {subject} ») !"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur envoi email : {str(e)}"}

    def create_gmail_draft(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        service = self.get_service("gmail", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            message = MIMEText(body, "plain", "utf-8")
            message["to"] = to
            message["subject"] = subject
            raw_msg = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

            draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw_msg}}).execute()
            return {"status": "success", "draft_id": draft.get("id"), "message": f"📝 Brouillon créé dans Gmail pour {to} (Sujet : « {subject} ») !"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur création brouillon : {str(e)}"}

    def trash_gmail_message(self, message_id: str) -> Dict[str, Any]:
        service = self.get_service("gmail", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            service.users().messages().trash(userId="me", id=message_id).execute()
            return {"status": "success", "message": f"🗑️ Email {message_id} déplacé dans la corbeille Gmail."}
        except Exception as e:
            return {"status": "error", "message": f"Erreur suppression email : {str(e)}"}

    # =========================================================================
    # 📅 2. CALENDAR & 🎥 MEET (Visioconférences Instantanées)
    # =========================================================================

    def list_calendar_events(self, max_results: int = 10, days_ahead: int = 7) -> Dict[str, Any]:
        service = self.get_service("calendar", "v3")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            now = datetime.now(PARIS_TZ)
            time_min = now.isoformat()
            time_max = (now + timedelta(days=days_ahead)).isoformat()

            events_result = service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()

            events = events_result.get("items", [])
            formatted = []
            for ev in events:
                start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date"))
                meet_link = ev.get("hangoutLink", "")
                formatted.append({
                    "id": ev.get("id"),
                    "summary": ev.get("summary", "Sans titre"),
                    "start": start,
                    "location": ev.get("location", ""),
                    "meet_link": meet_link
                })

            return {"status": "success", "total_events": len(formatted), "events": formatted}
        except Exception as e:
            return {"status": "error", "message": f"Erreur Calendar : {str(e)}"}

    def create_calendar_event(self, summary: str, start_time_iso: str, end_time_iso: Optional[str] = None, description: str = "", location: str = "") -> Dict[str, Any]:
        service = self.get_service("calendar", "v3")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            if not end_time_iso:
                try:
                    s_dt = datetime.fromisoformat(start_time_iso)
                    e_dt = s_dt + timedelta(hours=1)
                    end_time_iso = e_dt.isoformat()
                except Exception:
                    end_time_iso = start_time_iso

            event_body = {
                "summary": summary,
                "description": description,
                "location": location,
                "start": {"dateTime": start_time_iso, "timeZone": settings.TIMEZONE},
                "end": {"dateTime": end_time_iso, "timeZone": settings.TIMEZONE}
            }

            event = service.events().insert(calendarId="primary", body=event_body).execute()
            return {
                "status": "success",
                "event_id": event.get("id"),
                "summary": summary,
                "link": event.get("htmlLink"),
                "message": f"📅 Événement '{summary}' ajouté sur Google Calendar pour le {start_time_iso} !"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur ajout événement : {str(e)}"}

    def create_google_meet_event(self, summary: str, start_time_iso: str, attendees_emails: Optional[List[str]] = None, description: str = "") -> Dict[str, Any]:
        """Crée un événement avec un lien Google Meet officiel et invite les participants."""
        service = self.get_service("calendar", "v3")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            try:
                s_dt = datetime.fromisoformat(start_time_iso)
                e_dt = s_dt + timedelta(hours=1)
                end_time_iso = e_dt.isoformat()
            except Exception:
                end_time_iso = start_time_iso

            event_body = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start_time_iso, "timeZone": settings.TIMEZONE},
                "end": {"dateTime": end_time_iso, "timeZone": settings.TIMEZONE},
                "conferenceData": {
                    "createRequest": {
                        "requestId": str(uuid.uuid4()),
                        "conferenceSolutionKey": {"type": "hangoutsMeet"}
                    }
                }
            }

            if attendees_emails:
                event_body["attendees"] = [{"email": e.strip()} for e in attendees_emails]

            event = service.events().insert(
                calendarId="primary",
                body=event_body,
                conferenceDataVersion=1,
                sendUpdates="all" if attendees_emails else "none"
            ).execute()

            meet_link = event.get("hangoutLink", event.get("conferenceData", {}).get("entryPoints", [{}])[0].get("uri", ""))

            return {
                "status": "success",
                "event_id": event.get("id"),
                "summary": summary,
                "meet_url": meet_link,
                "start_time": start_time_iso,
                "message": f"🎥 Réunion Google Meet créée pour '{summary}' !\n🔗 Lien direct : {meet_link}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur création Google Meet : {str(e)}"}

    def delete_calendar_event(self, event_id_or_summary: str) -> Dict[str, Any]:
        """Supprime un événement de Google Calendar avec recherche intelligente et tolérante."""
        service = self.get_service("calendar", "v3")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            raw_target = event_id_or_summary.strip()
            # Nettoyage des mots parasites (articles, pronoms)
            stopwords = ["l'", "le ", "la ", "les ", "un ", "une ", "des ", "mon ", "ma ", "mes ", "du ", "de ", "d'", "événement ", "evenement ", "rendez-vous ", "rdv "]
            clean_target = raw_target.lower()
            for sw in stopwords:
                clean_target = clean_target.replace(sw, " ")
            clean_target = clean_target.strip()

            event_id_to_delete = None
            event_title = raw_target

            # 1. Tentative de recherche par mot clé direct
            events_res = service.events().list(calendarId="primary", q=clean_target or raw_target, maxResults=10).execute()
            items = events_res.get("items", [])

            # 2. Si non trouvé, scan étendu de -30 jours à +180 jours
            if not items:
                now = datetime.now(PARIS_TZ)
                t_min = (now - timedelta(days=30)).isoformat()
                t_max = (now + timedelta(days=180)).isoformat()
                scan_res = service.events().list(
                    calendarId="primary",
                    timeMin=t_min,
                    timeMax=t_max,
                    singleEvents=True,
                    maxResults=50,
                    orderBy="startTime"
                ).execute()
                all_events = scan_res.get("items", [])

                target_tokens = set(clean_target.split()) if clean_target else set(raw_target.lower().split())
                best_match = None
                best_score = 0

                for ev in all_events:
                    ev_sum = ev.get("summary", "").lower()
                    ev_id = ev.get("id", "")
                    if raw_target == ev_id:
                        best_match = ev
                        break
                    
                    ev_tokens = set(ev_sum.split())
                    overlap = len(target_tokens.intersection(ev_tokens))
                    if clean_target in ev_sum or ev_sum in clean_target:
                        overlap += 3

                    if overlap > best_score:
                        best_score = overlap
                        best_match = ev

                if best_match and best_score > 0:
                    items = [best_match]

            # 3. Si l'ID a été passé directement
            if not items and len(raw_target) >= 15 and " " not in raw_target:
                event_id_to_delete = raw_target
            elif items:
                event_id_to_delete = items[0]["id"]
                event_title = items[0].get("summary", raw_target)
            else:
                return {
                    "status": "error",
                    "message": f"Impossible de trouver l'événement '{raw_target}' sur ton agenda Google."
                }

            service.events().delete(calendarId="primary", eventId=event_id_to_delete).execute()
            return {
                "status": "success",
                "deleted_id": event_id_to_delete,
                "title": event_title,
                "message": f"🗑️ Événement '{event_title}' supprimé avec succès de ton Google Calendar !"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur lors de la suppression de l'événement : {str(e)}"}

    # =========================================================================
    # 📍 3. GOOGLE MAPS, TRAFIC EN TEMPS RÉEL & LIEUX
    # =========================================================================

    async def get_directions_and_traffic(self, origin: str, destination: str, mode: str = "driving") -> Dict[str, Any]:
        """Calcule l'itinéraire et le temps de trajet avec trafic en temps réel."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return {"status": "error", "message": "Clé Google API non configurée."}

        try:
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "departure_time": "now",
                "language": "fr",
                "key": api_key
            }
            async with httpx.AsyncClient() as client:
                res = await client.get(url, params=params)
                data = res.json()

            if data.get("status") != "OK":
                return {"status": "error", "message": f"Impossible de calculer l'itinéraire : {data.get('status')}"}

            route = data["routes"][0]
            leg = route["legs"][0]
            
            distance = leg.get("distance", {}).get("text", "")
            duration = leg.get("duration", {}).get("text", "")
            duration_in_traffic = leg.get("duration_in_traffic", {}).get("text", duration)
            summary = route.get("summary", "")

            steps = [s.get("html_instructions", "").replace("<b>", "").replace("</b>", "").replace('<div style="font-size:0.9em">', " (").replace("</div>", ")") for s in leg.get("steps", [])[:5]]

            return {
                "status": "success",
                "origin": leg.get("start_address", origin),
                "destination": leg.get("end_address", destination),
                "distance": distance,
                "duration_normal": duration,
                "duration_with_traffic": duration_in_traffic,
                "main_road": summary,
                "steps_preview": steps,
                "message": f"🚗 Trajet de {origin} à {destination} : {distance} en {duration_in_traffic} via {summary}."
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur Google Maps : {str(e)}"}

    async def search_places(self, query: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Recherche les meilleurs restaurants, services ou commerces avec avis et téléphones."""
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            return {"status": "error", "message": "Clé Google API non configurée."}

        try:
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            full_query = f"{query} {location}" if location else query
            params = {"query": full_query, "language": "fr", "key": api_key}

            async with httpx.AsyncClient() as client:
                res = await client.get(url, params=params)
                data = res.json()

            results = data.get("results", [])[:5]
            places = []
            for p in results:
                places.append({
                    "name": p.get("name"),
                    "address": p.get("formatted_address"),
                    "rating": p.get("rating", "N/A"),
                    "user_ratings_total": p.get("user_ratings_total", 0),
                    "open_now": p.get("opening_hours", {}).get("open_now", "Inconnu")
                })

            return {"status": "success", "total_found": len(places), "places": places}
        except Exception as e:
            return {"status": "error", "message": f"Erreur Places : {str(e)}"}

    # =========================================================================
    # 📋 4. GOOGLE FORMS (Créateur de Formulaires & Sondages)
    # =========================================================================

    def create_google_form(self, title: str, description: str = "", questions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Crée un formulaire Google Forms officiel."""
        service = self.get_service("forms", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            form_body = {
                "info": {
                    "title": title,
                    "documentTitle": title,
                    "description": description
                }
            }
            form = service.forms().create(body=form_body).execute()
            form_id = form.get("formId")
            responder_uri = form.get("responderUri")

            # Ajout des questions éventuelles
            if questions:
                requests = []
                for i, q in enumerate(questions):
                    q_title = q.get("title", f"Question {i+1}")
                    q_type = q.get("type", "text") # text ou choice
                    options = q.get("options", [])

                    item = {"title": q_title}
                    if q_type == "choice" and options:
                        item["questionItem"] = {
                            "question": {
                                "choiceQuestion": {
                                    "type": "RADIO",
                                    "options": [{"value": opt} for opt in options]
                                }
                            }
                        }
                    else:
                        item["questionItem"] = {
                            "question": {
                                "textQuestion": {"paragraph": False}
                            }
                        }

                    requests.append({"createItem": {"item": item, "location": {"index": i}}})

                service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()

            return {
                "status": "success",
                "form_id": form_id,
                "title": title,
                "responder_url": responder_uri,
                "edit_url": f"https://docs.google.com/forms/d/{form_id}/edit",
                "message": f"📋 Google Form '{title}' créé avec succès !\n🔗 Lien pour répondre : {responder_uri}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur création Google Form : {str(e)}"}

    # =========================================================================
    # 📈 5. YOUTUBE DATA API (Statistiques & Tendances)
    # =========================================================================

    def get_youtube_channel_stats(self, channel_username_or_id: str) -> Dict[str, Any]:
        """Consulte les statistiques complètes d'une chaîne YouTube (abonnés, vues, vidéos)."""
        service = self.get_service("youtube", "v3")
        if not service:
            return {"status": "error", "message": "Service YouTube indisponible."}

        try:
            res = service.channels().list(
                part="snippet,statistics",
                forHandle=channel_username_or_id if not channel_username_or_id.startswith("UC") else None,
                id=channel_username_or_id if channel_username_or_id.startswith("UC") else None
            ).execute()

            items = res.get("items", [])
            if not items:
                # Recherche alternative par mot clé
                s_res = service.search().list(part="snippet", q=channel_username_or_id, type="channel", maxResults=1).execute()
                s_items = s_res.get("items", [])
                if not s_items:
                    return {"status": "error", "message": f"Chaîne YouTube '{channel_username_or_id}' introuvable."}
                c_id = s_items[0]["id"]["channelId"]
                res = service.channels().list(part="snippet,statistics", id=c_id).execute()
                items = res.get("items", [])

            if not items:
                return {"status": "error", "message": "Chaîne introuvable."}

            ch = items[0]
            title = ch.get("snippet", {}).get("title", "")
            stats = ch.get("statistics", {})

            return {
                "status": "success",
                "channel_title": title,
                "subscribers": stats.get("subscriberCount", "Masqué"),
                "total_views": stats.get("viewCount", "0"),
                "total_videos": stats.get("videoCount", "0"),
                "message": f"📊 Chaîne '{title}' : {stats.get('subscriberCount', 'N/A')} abonnés, {stats.get('viewCount', '0')} vues, {stats.get('videoCount', '0')} vidéos."
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur YouTube Stats : {str(e)}"}

    # =========================================================================
    # 📂 6. GOOGLE DRIVE, DOCS, SHEETS, TASKS, CONTACTS & KEEP
    # =========================================================================

    def search_drive(self, query: str = "", max_results: int = 10) -> Dict[str, Any]:
        service = self.get_service("drive", "v3")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}
        try:
            q_filter = f"name contains '{query}' and trashed = false" if query else "trashed = false"
            results = service.files().list(q=q_filter, pageSize=max_results, fields="files(id, name, mimeType, webViewLink)").execute()
            return {"status": "success", "files": results.get("files", [])}
        except Exception as e:
            return {"status": "error", "message": f"Erreur Drive : {str(e)}"}

    def export_drive_file_as_pdf(self, file_id_or_title: str) -> Dict[str, Any]:
        """Télécharge ou exporte un Google Doc ou fichier Drive en PDF local prêt à l'envoi."""
        service = self.get_service("drive", "v3")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            target = file_id_or_title.strip()
            file_id = target
            clean_name = "document.pdf"

            if len(target) < 20 or " " in target:
                res = service.files().list(q=f"name contains '{target}' and trashed = false", pageSize=1, fields="files(id, name, mimeType)").execute()
                items = res.get("files", [])
                if not items:
                    return {"status": "error", "message": f"Fichier '{target}' introuvable sur ton Google Drive."}
                file_id = items[0]["id"]
                raw_n = items[0]["name"]
                clean_name = f"{raw_n}.pdf" if not raw_n.lower().endswith(".pdf") else raw_n

            out_path = settings.WORKSPACE_PATH / clean_name

            try:
                content = service.files().export(fileId=file_id, mimeType="application/pdf").execute()
            except Exception:
                content = service.files().get_media(fileId=file_id).execute()

            with open(out_path, "wb") as f:
                f.write(content)

            return {
                "status": "success",
                "filename": clean_name,
                "local_path": str(out_path),
                "message": f"📄 Le document Google Drive **« {clean_name} »** a été exporté en PDF !"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur export PDF : {str(e)}"}

    def upload_file_to_drive(self, local_filename: str, folder_name: Optional[str] = None) -> Dict[str, Any]:
        service = self.get_service("drive", "v3")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}
        try:
            p = settings.WORKSPACE_PATH / local_filename if not os.path.isabs(local_filename) else local_filename
            if not os.path.exists(p):
                return {"status": "error", "message": f"Fichier local introuvable : {local_filename}"}

            file_metadata = {"name": os.path.basename(p)}
            media = MediaFileUpload(str(p), resumable=True)
            uploaded = service.files().create(body=file_metadata, media_body=media, fields="id, webViewLink").execute()
            return {"status": "success", "file_id": uploaded.get("id"), "link": uploaded.get("webViewLink"), "message": f"📤 Fichier téléversé sur Google Drive : {uploaded.get('webViewLink')}"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur upload Drive : {str(e)}"}

    def create_google_doc(self, title: str, content: str = "") -> Dict[str, Any]:
        service = self.get_service("docs", "v1")
        if not service:
            return {"status": "error", "message": "Service Google Docs indisponible."}
        try:
            doc = service.documents().create(body={"title": title}).execute()
            doc_id = doc.get("documentId")
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            if content and content.strip():
                requests = [{"insertText": {"location": {"index": 1}, "text": content.strip() + "\n"}}]
                service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
            return {"status": "success", "document_id": doc_id, "title": title, "url": doc_url, "message": f"📄 Google Doc '{title}' créé : {doc_url}"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur Google Doc : {str(e)}"}

    def create_google_sheet(self, title: str, headers: Optional[List[str]] = None) -> Dict[str, Any]:
        service = self.get_service("sheets", "v4")
        if not service:
            return {"status": "error", "message": "Service Google Sheets indisponible."}
        try:
            sheet = service.spreadsheets().create(body={"properties": {"title": title}}, fields="spreadsheetId").execute()
            sheet_id = sheet.get("spreadsheetId")
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
            if headers:
                service.spreadsheets().values().update(spreadsheetId=sheet_id, range="A1", valueInputOption="USER_ENTERED", body={"values": [headers]}).execute()
            return {"status": "success", "spreadsheet_id": sheet_id, "title": title, "url": sheet_url, "message": f"📊 Google Sheet '{title}' créé : {sheet_url}"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur Google Sheet : {str(e)}"}

    # =========================================================================
    # ✅ 7. GOOGLE TASKS COMPLET (Tâches, Listes, Échéances & Validation)
    # =========================================================================

    def list_google_tasks(self, tasklist_id: str = "@default", show_completed: bool = False, max_results: int = 20) -> Dict[str, Any]:
        """Liste toutes les tâches de Google Tasks avec échéances et statut."""
        service = self.get_service("tasks", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            tasks_res = service.tasks().list(
                tasklist=tasklist_id,
                showCompleted=show_completed,
                showHidden=show_completed,
                maxResults=max_results
            ).execute()

            items = tasks_res.get("items", [])
            formatted = []
            for t in items:
                status_icon = "✅" if t.get("status") == "completed" else "⬜"
                formatted.append({
                    "id": t.get("id"),
                    "title": t.get("title", "Sans titre"),
                    "notes": t.get("notes", ""),
                    "due": t.get("due"),
                    "status": t.get("status"),
                    "icon": status_icon
                })

            summary = "\n".join([f"{t['icon']} **{t['title']}**" + (f" (Échéance : {t['due'][:10]})" if t.get('due') else "") for t in formatted]) or "Aucune tâche en cours."
            return {
                "status": "success",
                "total_tasks": len(formatted),
                "tasks": formatted,
                "message": f"📋 **Tes tâches Google Tasks :**\n{summary}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur Google Tasks : {str(e)}"}

    def create_google_task(self, title: str, notes: str = "", due_date_iso: Optional[str] = None, tasklist_id: str = "@default") -> Dict[str, Any]:
        """Crée une nouvelle tâche sur Google Tasks avec note et date d'échéance."""
        service = self.get_service("tasks", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            task_body = {
                "title": title.strip(),
                "notes": notes.strip() if notes else ""
            }
            if due_date_iso:
                # Format RFC 3339 requis par Google Tasks (ex: 2026-08-20T00:00:00.000Z)
                if "T" not in due_date_iso:
                    due_date_iso = f"{due_date_iso}T00:00:00.000Z"
                elif not due_date_iso.endswith("Z"):
                    due_date_iso = f"{due_date_iso}.000Z"
                task_body["due"] = due_date_iso

            created = service.tasks().insert(tasklist=tasklist_id, body=task_body).execute()
            return {
                "status": "success",
                "task_id": created.get("id"),
                "title": title,
                "due": due_date_iso,
                "message": f"✅ Tâche **« {title} »** ajoutée à ton Google Tasks !"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur création tâche Google Tasks : {str(e)}"}

    def complete_google_task(self, task_id_or_title: str, tasklist_id: str = "@default") -> Dict[str, Any]:
        """Marque une tâche comme terminée dans Google Tasks."""
        service = self.get_service("tasks", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            target = task_id_or_title.strip()
            task_id = target
            title_found = target

            # Recherche par titre si ce n'est pas un ID
            if len(target) < 20 or " " in target:
                all_tasks = service.tasks().list(tasklist=tasklist_id, showCompleted=False).execute().get("items", [])
                match = next((t for t in all_tasks if target.lower() in t.get("title", "").lower()), None)
                if not match:
                    return {"status": "error", "message": f"Tâche '{target}' introuvable dans Google Tasks."}
                task_id = match["id"]
                title_found = match.get("title", target)

            task = service.tasks().get(tasklist=tasklist_id, taskId=task_id).execute()
            task["status"] = "completed"
            updated = service.tasks().update(tasklist=tasklist_id, taskId=task_id, body=task).execute()

            return {
                "status": "success",
                "task_id": task_id,
                "title": title_found,
                "message": f"🎉 Tâche **« {title_found} »** validée et cochée comme terminée dans Google Tasks !"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur complétion tâche : {str(e)}"}

    def delete_google_task(self, task_id_or_title: str, tasklist_id: str = "@default") -> Dict[str, Any]:
        """Supprime une tâche de Google Tasks."""
        service = self.get_service("tasks", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            target = task_id_or_title.strip()
            task_id = target
            title_found = target

            if len(target) < 20 or " " in target:
                all_tasks = service.tasks().list(tasklist=tasklist_id, showCompleted=True).execute().get("items", [])
                match = next((t for t in all_tasks if target.lower() in t.get("title", "").lower()), None)
                if not match:
                    return {"status": "error", "message": f"Tâche '{target}' introuvable dans Google Tasks."}
                task_id = match["id"]
                title_found = match.get("title", target)

            service.tasks().delete(tasklist=tasklist_id, taskId=task_id).execute()
            return {
                "status": "success",
                "deleted_id": task_id,
                "title": title_found,
                "message": f"🗑️ Tâche **« {title_found} »** supprimée de ton Google Tasks !"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur suppression tâche : {str(e)}"}

    def list_google_task_lists(self) -> Dict[str, Any]:
        """Liste toutes les listes de tâches (ex: 'Mes tâches', 'Projets', 'Courses')."""
        service = self.get_service("tasks", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            res = service.tasklists().list().execute()
            lists = res.get("items", [])
            formatted = [{"id": l["id"], "title": l["title"]} for l in lists]
            return {"status": "success", "task_lists": formatted, "total": len(formatted)}
        except Exception as e:
            return {"status": "error", "message": f"Erreur lecture listes Tasks : {str(e)}"}

    def create_google_task_list(self, title: str) -> Dict[str, Any]:
        """Crée une nouvelle liste de tâches sur Google Tasks."""
        service = self.get_service("tasks", "v1")
        if not service or not self.is_oauth_authenticated():
            return {"status": "error", "message": "Compte Google non connecté."}

        try:
            res = service.tasklists().insert(body={"title": title.strip()}).execute()
            return {
                "status": "success",
                "list_id": res.get("id"),
                "title": title,
                "message": f"📁 Nouvelle liste de tâches **« {title} »** créée sur Google Tasks !"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur création liste Tasks : {str(e)}"}

    def save_keep_note(self, title: str, content: str, category: str = "Général") -> Dict[str, Any]:
        try:
            notes = []
            if os.path.exists(NOTES_FILE):
                try:
                    with open(NOTES_FILE, "r", encoding="utf-8") as f:
                        notes = json.load(f)
                except Exception: pass
            new_note = {"id": str(len(notes) + 1), "title": title, "content": content, "category": category}
            notes.insert(0, new_note)
            with open(NOTES_FILE, "w", encoding="utf-8") as f:
                json.dump(notes, f, indent=2, ensure_ascii=False)
            return {"status": "success", "title": title, "message": f"📝 Note '{title}' enregistrée dans Keep/Notes !"}
        except Exception as e:
            return {"status": "error", "message": f"Erreur note : {str(e)}"}

    def list_keep_notes(self, category: Optional[str] = None) -> Dict[str, Any]:
        if not os.path.exists(NOTES_FILE): return {"status": "success", "notes": []}
        try:
            with open(NOTES_FILE, "r", encoding="utf-8") as f: notes = json.load(f)
            if category: notes = [n for n in notes if n.get("category", "").lower() == category.lower()]
            return {"status": "success", "notes": notes[:20]}
        except Exception as e: return {"status": "error", "message": f"Erreur lecture notes : {str(e)}"}

google_workspace = GoogleWorkspaceService()
