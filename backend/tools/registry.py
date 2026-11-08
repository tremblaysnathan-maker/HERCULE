from typing import Dict, Any, List
from backend.tools.search_tools import SearchTools
from backend.tools.browser_tools import BrowserController
from backend.tools.system_tools import SystemTools
from backend.tools.doc_tools import DocumentTools
from backend.services.sentinel import SystemSentinel
from backend.services.scheduler import scheduler
from backend.services.google_workspace import google_workspace
from backend.services.phone_service import phone_service
from backend.services.browser_agent import browser_agent
from backend.services.smart_home import smart_home
from backend.services.cyber_sentinel import cyber_sentinel
from backend.services.deezer_service import deezer_service
from backend.services.media_factory import media_factory
from backend.services.budget_tracker import budget_tracker
from backend.services.web_hunter import web_hunter
from backend.services.life_report import sunday_report_service
from backend.services.travel_copilot import travel_copilot
from backend.services.morning_briefing import morning_briefing_service
from backend.services.voicemail_ai import voicemail_service
from backend.services.habit_tracker import habit_tracker
from backend.services.mirror_sync import mirror_sync_service
from backend.services.radio_sdr import radio_sdr
from backend.services.stealth_scraper import stealth_scraper
from backend.services.meal_planner import meal_planner
from backend.services.obsidian_canvas import obsidian_canvas
from backend.services.style_rewriter import style_rewriter
from backend.services.event_planner import event_planner
from backend.services.diy_planner import diy_planner
from backend.services.gui_controller import gui_controller
from backend.services.vision_analyzer import vision_analyzer
from backend.services.guardrails import guardrails_service
from backend.services.vault_manager import vault_manager
from backend.services.diagram_compiler import diagram_compiler
from backend.services.semantic_rag import semantic_rag
from backend.services.media_archiver import media_archiver
from backend.services.mobile_bridge import mobile_bridge
from backend.services.pdf_factory import pdf_factory
from backend.services.osm_geocoder import osm_geocoder
from backend.services.local_translator import local_translator
from backend.services.terminal_session import terminal_session
from backend.services.package_tracker import package_tracker
from backend.services.fitness_coach import fitness_coach
from backend.services.smart_finance import smart_finance
from backend.services.anti_waste import anti_waste
from backend.services.learning_anki import learning_anki
from backend.services.infra_manager import infra_manager
from backend.services.ultimate_hub import ultimate_hub

class ToolRegistry:
    """
    Registre d'outils complet pour Hercul :
    - 🌐 GOOGLE WORKSPACE TOTAL (Gmail, Calendar, Drive, Docs, Sheets, Tasks, Contacts, Keep)
    - 🔍 Recherche Web & Navigateur Playwright
    - ⏱️ Minuteurs & Rappels synchronisés Europe/Paris
    - 📄 Analyse Documents (PDF, Excel, YouTube)
    - 🛡️ Sentinelle VPS
    """
    
    @staticmethod
    def get_tool_declarations() -> List[Dict[str, Any]]:
        return [
            # =================================================================
            # 📧 GMAIL
            # =================================================================
            {
                "name": "list_gmail_messages",
                "description": "Consulte et résume les emails Gmail personnels (non lus ou par recherche).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Filtre (ex: 'is:unread', 'from:banque', 'subject:facture')"},
                        "max_results": {"type": "INTEGER", "description": "Nombre max d'emails (défaut 5)"}
                    }
                }
            },
            {
                "name": "read_gmail_message",
                "description": "Lit le texte complet d'un email Gmail par son ID.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "message_id": {"type": "STRING", "description": "ID de l'email"}
                    },
                    "required": ["message_id"]
                }
            },
            {
                "name": "send_gmail_message",
                "description": "Envoie un e-mail réel depuis ton compte Gmail.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "to": {"type": "STRING", "description": "Adresse e-mail du destinataire"},
                        "subject": {"type": "STRING", "description": "Sujet de l'email"},
                        "body": {"type": "STRING", "description": "Contenu du message"}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "create_gmail_draft",
                "description": "Prépare un brouillon d'e-mail dans Gmail sans l'envoyer.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "to": {"type": "STRING", "description": "Destinataire"},
                        "subject": {"type": "STRING", "description": "Sujet"},
                        "body": {"type": "STRING", "description": "Contenu"}
                    },
                    "required": ["to", "subject", "body"]
                }
            },
            {
                "name": "trash_gmail_message",
                "description": "Met un e-mail Gmail à la corbeille.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "message_id": {"type": "STRING", "description": "ID de l'email"}
                    },
                    "required": ["message_id"]
                }
            },

            # =================================================================
            # 📅 GOOGLE CALENDAR
            # =================================================================
            {
                "name": "list_google_calendar_events",
                "description": "Consulte les prochains événements et rendez-vous sur Google Calendar.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "max_results": {"type": "INTEGER", "description": "Nombre d'événements (défaut 10)"},
                        "days_ahead": {"type": "INTEGER", "description": "Nombre de jours à scanner (défaut 7)"}
                    }
                }
            },
            {
                "name": "create_google_calendar_event",
                "description": "Ajoute un événement ou rendez-vous sur l'agenda Google Calendar.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "summary": {"type": "STRING", "description": "Titre du rendez-vous (ex: 'Rendez-vous Dentiste')"},
                        "start_time_iso": {"type": "STRING", "description": "Date et heure de début ISO (ex: '2026-08-20T14:30:00')"},
                        "end_time_iso": {"type": "STRING", "description": "Date et heure de fin ISO (optionnel)"},
                        "description": {"type": "STRING", "description": "Notes ou description"},
                        "location": {"type": "STRING", "description": "Lieu ou adresse"}
                    },
                    "required": ["summary", "start_time_iso"]
                }
            },
            {
                "name": "quick_add_calendar_event",
                "description": "Crée un événement Google Calendar à partir d'une phrase naturelle (ex: 'Dîner demain à 20h avec Thomas').",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING", "description": "Description en langage naturel de l'événement"}
                    },
                    "required": ["text"]
                }
            },
            {
                "name": "create_google_meet_event",
                "description": "Crée une réunion visioconférence Google Meet officielle avec lien d'invitation et ajoute l'événement à Calendar.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "summary": {"type": "STRING", "description": "Titre ou objet de la réunion"},
                        "start_time_iso": {"type": "STRING", "description": "Date et heure de début ISO (ex: '2026-08-20T15:00:00')"},
                        "attendees_emails": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Liste d'adresses e-mail des invités"},
                        "description": {"type": "STRING", "description": "Ordre du jour ou notes"}
                    },
                    "required": ["summary", "start_time_iso"]
                }
            },
            {
                "name": "maps_get_directions",
                "description": "Calcule l'itinéraire et le temps de trajet avec trafic en direct via Google Maps.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "origin": {"type": "STRING", "description": "Point de départ ou adresse"},
                        "destination": {"type": "STRING", "description": "Point d'arrivée ou destination"},
                        "mode": {"type": "STRING", "description": "Mode de transport ('driving', 'walking', 'bicycling', 'transit')"}
                    },
                    "required": ["origin", "destination"]
                }
            },
            {
                "name": "maps_search_places",
                "description": "Recherche les meilleurs commerces, restaurants ou services avec avis, notes et horaires via Google Maps Places.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Recherche (ex: 'Meilleur restaurant italien', 'Pharmacie ouverte')"},
                        "location": {"type": "STRING", "description": "Ville ou quartier (ex: 'Paris 15', 'Lyon')"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_google_form",
                "description": "Crée un formulaire ou questionnaire Google Forms en direct.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Titre du formulaire"},
                        "description": {"type": "STRING", "description": "Description du formulaire"}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "get_youtube_channel_stats",
                "description": "Consulte les statistiques en direct d'une chaîne YouTube (abonnés, vues, vidéos).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "channel_username_or_id": {"type": "STRING", "description": "Nom d'utilisateur YouTube, identifiant ou @handle"}
                    },
                    "required": ["channel_username_or_id"]
                }
            },
            {
                "name": "trigger_proactive_scan",
                "description": "Force le Secrétaire Proactif à scanner immédiatement les emails pour créer les rendez-vous et classer les factures.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 📂 GOOGLE DRIVE
            # =================================================================
            {
                "name": "search_google_drive",
                "description": "Recherche des fichiers, documents et tableurs sur Google Drive.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Mots-clés de recherche"},
                        "max_results": {"type": "INTEGER", "description": "Nombre max de résultats"}
                    }
                }
            },
            {
                "name": "export_drive_file_as_pdf",
                "description": "Télécharge ou exporte un Google Doc ou fichier Drive au format PDF pour l'envoyer ou le lire.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "file_id_or_title": {"type": "STRING", "description": "Nom ou ID du document Drive"}
                    },
                    "required": ["file_id_or_title"]
                }
            },
            {
                "name": "upload_file_to_drive",
                "description": "Téléverse un fichier du workspace local directement sur Google Drive.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "local_filename": {"type": "STRING", "description": "Nom du fichier local"}
                    },
                    "required": ["local_filename"]
                }
            },
            {
                "name": "create_drive_folder",
                "description": "Crée un nouveau dossier sur Google Drive.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "folder_name": {"type": "STRING", "description": "Nom du dossier"}
                    },
                    "required": ["folder_name"]
                }
            },
            {
                "name": "delete_drive_file",
                "description": "Supprime un fichier sur Google Drive par son ID.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "file_id": {"type": "STRING", "description": "ID du fichier Drive"}
                    },
                    "required": ["file_id"]
                }
            },

            # =================================================================
            # 📄 GOOGLE DOCS & 📊 GOOGLE SHEETS
            # =================================================================
            {
                "name": "create_google_doc",
                "description": "Crée un nouveau document Google Docs avec un titre et du texte.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Titre du Google Doc"},
                        "content": {"type": "STRING", "description": "Contenu initial"}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "append_to_google_doc",
                "description": "Ajoute du texte à la fin d'un Google Doc existant.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "document_id": {"type": "STRING", "description": "ID du document"},
                        "text_to_append": {"type": "STRING", "description": "Texte à ajouter"}
                    },
                    "required": ["document_id", "text_to_append"]
                }
            },
            {
                "name": "create_google_sheet",
                "description": "Crée une nouvelle feuille de calcul Google Sheets avec colonnes d'en-tête.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Titre du tableau"},
                        "headers": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Liste des noms de colonnes"}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "append_rows_to_sheet",
                "description": "Ajoute des lignes de données dans un tableau Google Sheets existant.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "spreadsheet_id": {"type": "STRING", "description": "ID du tableur"},
                        "rows": {"type": "ARRAY", "items": {"type": "ARRAY", "items": {"type": "STRING"}}, "description": "Lignes à insérer"}
                    },
                    "required": ["spreadsheet_id", "rows"]
                }
            },

            # =================================================================
            # ✅ GOOGLE TASKS & 👥 CONTACTS
            # =================================================================
            {
                "name": "list_google_tasks",
                "description": "Consulte les tâches en cours sur Google Tasks.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "create_google_task",
                "description": "Ajoute une tâche dans Google Tasks avec date limite optionnelle.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Titre de la tâche"},
                        "notes": {"type": "STRING", "description": "Détails ou notes"},
                        "due_date_iso": {"type": "STRING", "description": "Date limite ISO (ex: '2026-08-25T18:00:00Z')"}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "complete_google_task",
                "description": "Coche une tâche comme terminée dans Google Tasks.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_id_or_title": {"type": "STRING", "description": "Titre ou ID de la tâche"}
                    },
                    "required": ["task_id_or_title"]
                }
            },
            {
                "name": "delete_google_task",
                "description": "Supprime définitivement une tâche de Google Tasks.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_id_or_title": {"type": "STRING", "description": "Titre ou ID de la tâche à supprimer"}
                    },
                    "required": ["task_id_or_title"]
                }
            },
            {
                "name": "list_google_task_lists",
                "description": "Liste toutes les listes de tâches personnalisées de Google Tasks.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "create_google_task_list",
                "description": "Crée une nouvelle liste de tâches sur Google Tasks (ex: 'Projets', 'Courses').",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Titre de la nouvelle liste"}
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "search_google_contacts",
                "description": "Recherche les coordonnées (e-mail, téléphone) d'un contact dans Google Contacts.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Nom ou prénom du contact"}
                    },
                    "required": ["query"]
                }
            },

            # =================================================================
            # 📝 GOOGLE KEEP / NOTES
            # =================================================================
            {
                "name": "save_google_keep_note",
                "description": "Enregistre une note ou un mémo (Google Keep / Notes).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Titre de la note"},
                        "content": {"type": "STRING", "description": "Contenu du mémo"},
                        "category": {"type": "STRING", "description": "Catégorie (ex: 'Idées', 'Courses')"}
                    },
                    "required": ["title", "content"]
                }
            },
            {
                "name": "list_google_keep_notes",
                "description": "Consulte les notes et mémos enregistrés.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "category": {"type": "STRING", "description": "Catégorie optionnelle"}
                    }
                }
            },

            # =================================================================
            # ⏱️ TEMPS, WEB & SYSTÈME
            # =================================================================
            {
                "name": "get_current_time",
                "description": "Retourne l'heure et la date exactes réelles de France (Europe/Paris).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "set_timer_or_reminder",
                "description": "Règle un minuteur précis ou un rappel programmé.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "message": {"type": "STRING", "description": "Contenu du rappel ou motif"},
                        "delay_seconds": {"type": "INTEGER", "description": "Délai en secondes"},
                        "delay_minutes": {"type": "INTEGER", "description": "Délai en minutes"},
                        "target_time_str": {"type": "STRING", "description": "Heure cible au format HH:MM"}
                    },
                    "required": ["message"]
                }
            },
            {
                "name": "list_reminders",
                "description": "Consulte la liste des minuteurs et rappels actifs.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "web_search",
                "description": "Recherche web rapide pour infos, actualités, météo.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Requête de recherche"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "fetch_page_content",
                "description": "Lit le texte nettoyé d'un article ou page web.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "URL cible"}
                    },
                    "required": ["url"]
                }
            },
            # =================================================================
            # 📞 TÉLÉPHONIE & APPELS VOCAUX
            # =================================================================
            {
                "name": "make_phone_call",
                "description": "Passe un véritable appel téléphonique vers un numéro avec la voix de synthèse d'Hercul.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "to_phone_number": {"type": "STRING", "description": "Numéro de téléphone au format international (ex: '+33612345678')"},
                        "text_to_speak": {"type": "STRING", "description": "Message vocal à lire lors de l'appel"}
                    },
                    "required": ["to_phone_number", "text_to_speak"]
                }
            },
            {
                "name": "trigger_emergency_call",
                "description": "Déclenche un appel vocal urgent de réveil ou d'alerte vers Nathan.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "reason": {"type": "STRING", "description": "Motif de l'alerte d'urgence"},
                        "phone_number": {"type": "STRING", "description": "Numéro de téléphone optionnel"}
                    },
                    "required": ["reason"]
                }
            },

            # =================================================================
            # 🌐 NAVIGATEUR VISUEL AUTONOME PLAYWRIGHT
            # =================================================================
            {
                "name": "take_web_screenshot",
                "description": "Ouvre une page web avec Chromium et prend une capture d'écran HD.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "URL de la page web"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "browse_and_read_webpage",
                "description": "Navigue sur une page web dynamique (JavaScript / SPA) et extrait son contenu textuel.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "URL de la page"}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "compare_product_prices",
                "description": "Scanne le web pour comparer les prix d'un article et trouver la meilleure offre.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "product_query": {"type": "STRING", "description": "Nom du produit ou modèle"}
                    },
                    "required": ["product_query"]
                }
            },

            # =================================================================
            # 🏠 DOMOTIQUE & MAISON CONNECTÉE
            # =================================================================
            {
                "name": "control_smart_device",
                "description": "Contrôle un équipement de la maison (lumière, prise, volet, chauffage).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "device_name": {"type": "STRING", "description": "Nom de l'équipement (ex: 'Lumière Salon', 'Prise Bureau')"},
                        "action": {"type": "STRING", "description": "Action ('on', 'off', 'allumer', 'eteindre', 'ouvrir', 'fermer')"},
                        "brightness": {"type": "INTEGER", "description": "Luminosité en % (0-100)"},
                        "color": {"type": "STRING", "description": "Couleur ou ambiance ('warm_white', 'deep_blue', 'red')"}
                    },
                    "required": ["device_name", "action"]
                }
            },
            {
                "name": "activate_smart_scene",
                "description": "Active une ambiance ou un mode de maison complet (Cinéma, Nuit, Focus, Départ).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "scene_name": {"type": "STRING", "description": "Nom de la scène ('cinema', 'nuit', 'focus')"}
                    },
                    "required": ["scene_name"]
                }
            },
            {
                "name": "get_smart_home_status",
                "description": "Consulte l'état des lumières, prises, température et équipements de la maison.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 🛡️ SENTINELLE CYBERSÉCURITÉ & DARK WEB
            # =================================================================
            {
                "name": "check_password_leak",
                "description": "Vérifie si un mot de passe a fuité sur le Dark Web via protocole cryptographique K-Anonymity.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "password": {"type": "STRING", "description": "Mot de passe à tester"}
                    },
                    "required": ["password"]
                }
            },
            {
                "name": "check_email_breaches",
                "description": "Vérifie si une adresse e-mail a été exposée dans des fuites de données de sites piratés.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "email_address": {"type": "STRING", "description": "Adresse e-mail à vérifier"}
                    },
                    "required": ["email_address"]
                }
            },
            {
                "name": "run_security_audit",
                "description": "Exécute un audit de sécurité complet et fournit les recommandations de protection.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "email_address": {"type": "STRING", "description": "Email cible optionnel"}
                    }
                }
            },

            # =================================================================
            # 🎵 DEEZER MUSIC
            # =================================================================
            {
                "name": "search_deezer_music",
                "description": "Recherche un morceau, album ou titre sur Deezer et donne le lien direct et l'extrait audio.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Titre de musique ou nom d'artiste"},
                        "limit": {"type": "INTEGER", "description": "Nombre de résultats (défaut 5)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_deezer_top_charts",
                "description": "Affiche les musiques les plus populaires et écoutées du moment sur Deezer.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "limit": {"type": "INTEGER", "description": "Nombre de morceaux (défaut 10)"}
                    }
                }
            },
            {
                "name": "get_deezer_artist_tracks",
                "description": "Récupère les meilleurs titres d'un artiste sur Deezer.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "artist_name": {"type": "STRING", "description": "Nom de l'artiste"}
                    },
                    "required": ["artist_name"]
                }
            },

            # =================================================================
            # 📁 USINE DE MÉDIAS & CONVERSIONS
            # =================================================================
            {
                "name": "convert_video_to_mp3",
                "description": "Extrait la piste audio MP3 haute qualité d'un fichier vidéo (MP4, MKV, WebM).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "video_filename": {"type": "STRING", "description": "Nom du fichier vidéo"}
                    },
                    "required": ["video_filename"]
                }
            },
            {
                "name": "convert_image_format",
                "description": "Convertit une image dans un autre format (PNG, JPEG, WEBP, etc.).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "image_filename": {"type": "STRING", "description": "Nom du fichier image"},
                        "target_format": {"type": "STRING", "description": "Format cible ('png', 'jpeg', 'webp')"}
                    },
                    "required": ["image_filename", "target_format"]
                }
            },

            # =================================================================
            # 💶 ASSISTANT BUDGET & DÉPENSES
            # =================================================================
            {
                "name": "log_budget_expense",
                "description": "Enregistre une dépense dans la feuille Google Sheets 'Hercul_Suivi_Budget_2026'.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "amount": {"type": "NUMBER", "description": "Montant en euros (€)"},
                        "vendor": {"type": "STRING", "description": "Nom du magasin, commerçant ou service"},
                        "category": {"type": "STRING", "description": "Catégorie ('Transports', 'Alimentation', 'Abonnements', 'Santé', 'Loisirs')"},
                        "date_str": {"type": "STRING", "description": "Date optionnelle (ex: '19/08/2026')"},
                        "notes": {"type": "STRING", "description": "Notes ou détails"}
                    },
                    "required": ["amount", "vendor"]
                }
            },

            # =================================================================
            # 🕵️ CHASSEUR & VEILLEUR WEB 24/7
            # =================================================================
            {
                "name": "add_web_watch_task",
                "description": "Ajoute une surveillance de page web (prix, stock, mot clé, nouvelle annonce).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "URL de la page à surveiller"},
                        "condition": {"type": "STRING", "description": "Texte, mot clé ou état déclencheur (ex: 'En stock', 'Promo', '399€')"},
                        "label": {"type": "STRING", "description": "Nom descriptif de l'alerte"}
                    },
                    "required": ["url", "condition", "label"]
                }
            },
            {
                "name": "list_web_watch_tasks",
                "description": "Liste toutes les surveillances web actives du Chasseur 24/7.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "remove_web_watch_task",
                "description": "Supprime une surveillance web par son identifiant.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_id": {"type": "STRING", "description": "ID de la tâche ou 'all'"}
                    },
                    "required": ["task_id"]
                }
            },

            # =================================================================
            # 📊 BILAN EXÉCUTIF DU DIMANCHE SOIR
            # =================================================================
            {
                "name": "generate_life_weekly_report",
                "description": "Génère immédiatement le bilan exécutif de la semaine (budget, calendrier, e-mails en attente et vocal).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 🚗 COPILOTE DE VOYAGE INTELLIGENT
            # =================================================================
            {
                "name": "plan_smart_trip",
                "description": "Organise un voyage complet : itinéraire Google Maps avec trafic, météo, calage agenda et playlist Deezer de route.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "destination": {"type": "STRING", "description": "Ville ou adresse d'arrivée"},
                        "origin": {"type": "STRING", "description": "Ville ou adresse de départ (défaut 'Paris')"},
                        "departure_time": {"type": "STRING", "description": "Date et heure de départ (ex: '2026-08-20T09:00:00')"}
                    },
                    "required": ["destination"]
                }
            },

            # =================================================================
            # ☕ BRIEFING MATINAL DE 08H00
            # =================================================================
            {
                "name": "generate_morning_briefing",
                "description": "Génère immédiatement le briefing matinal (météo, Google Calendar, Google Tasks et boîte mail).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 🎙️ RÉPONDEUR & SECRÉTAIRE VOCAL IA
            # =================================================================
            {
                "name": "record_voicemail",
                "description": "Traite et enregistre un message vocal laissé par un correspondant avec analyse d'urgence.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "caller": {"type": "STRING", "description": "Nom ou numéro du correspondant"},
                        "transcript_or_text": {"type": "STRING", "description": "Transcription ou message vocal"},
                        "audio_url": {"type": "STRING", "description": "Lien optionnel vers l'audio"}
                    },
                    "required": ["caller", "transcript_or_text"]
                }
            },
            {
                "name": "list_voicemails",
                "description": "Consulte les messages vocaux enregistrés sur le répondeur Hercul.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 📊 TRAQUEUR D'HABITUDES & BILAN 22H00
            # =================================================================
            {
                "name": "log_daily_habit",
                "description": "Enregistre la validation d'une habitude du jour (Sport, Lecture, Code) dans Google Sheets.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "habit_name": {"type": "STRING", "description": "Nom de l'habitude (ex: 'Sport', 'Lecture', 'Code')"},
                        "completed": {"type": "BOOLEAN", "description": "True si validé, False sinon"},
                        "notes": {"type": "STRING", "description": "Notes optionnelles"}
                    },
                    "required": ["habit_name"]
                }
            },

            # =================================================================
            # 🔄 SYNCHRONISATION MIROIR NOTES & TASKS
            # =================================================================
            {
                "name": "sync_notes_and_tasks_mirror",
                "description": "Exporte l'ensemble des tâches Google Tasks et notes Keep au format Markdown dans le workspace.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 📻 RADIO SDR & SPECTRE 433MHZ / ADS-B
            # =================================================================
            {
                "name": "scan_radio_sensors_433",
                "description": "Écoute le spectre radio 433 MHz local pour intercepter les capteurs météo et sondes sans passer par internet.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "track_aircrafts_adsb",
                "description": "Intercepte les signaux ADS-B 1090 MHz des avions en vol au-dessus de toi.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 🛡️ SCRAPING FURTIF FLARESOLVERR
            # =================================================================
            {
                "name": "stealth_scrape_url",
                "description": "Contourne les protections anti-bot (Cloudflare, Turnstile) pour lire le contenu propre d'un site web.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "URL à scraper"}
                    },
                    "required": ["url"]
                }
            },

            # =================================================================
            # 🍳 ASSISTANT CULINAIRE & LISTE DE COURSES
            # =================================================================
            {
                "name": "generate_weekly_menu",
                "description": "Génère un planning de repas équilibré et rapide pour la semaine.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "days": {"type": "INTEGER", "description": "Nombre de jours (ex: 5 ou 7)"}
                    }
                }
            },
            {
                "name": "generate_and_sync_grocery_list",
                "description": "Compile la liste de courses optimisée par rayon et la synchronise dans Google Tasks.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 🧠 CARTES MENTALES OBSIDIAN CANVAS (.canvas)
            # =================================================================
            {
                "name": "create_obsidian_mindmap",
                "description": "Génère une carte mentale visuelle au format .canvas ouvrable dans Obsidian.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Nom du fichier canvas"},
                        "central_topic": {"type": "STRING", "description": "Sujet central"},
                        "subtopics": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Liste des branches et sous-idées"}
                    },
                    "required": ["title", "central_topic", "subtopics"]
                }
            },

            # =================================================================
            # ✍️ ASSISTANT DE RÉDACTION & MULTI-STYLE
            # =================================================================
            {
                "name": "rewrite_text_style",
                "description": "Corrige et propose instantanément 3 variantes de reformulation (Naturel, Formel, Synthétique).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING", "description": "Texte brut à corriger et reformuler"}
                    },
                    "required": ["text"]
                }
            },

            # =================================================================
            # 🎉 GESTIONNAIRE D'ÉVÉNEMENTS & SOIRÉES
            # =================================================================
            {
                "name": "plan_party_event",
                "description": "Calcule la logistique d'une soirée (quantités boissons/nourriture, feuille de route, agenda).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Nom de l'événement"},
                        "guests_count": {"type": "INTEGER", "description": "Nombre d'invités"},
                        "theme": {"type": "STRING", "description": "Thème de la soirée"}
                    },
                    "required": ["title", "guests_count"]
                }
            },

            # =================================================================
            # 🔨 ASSISTANT BRICOLAGE & DIY
            # =================================================================
            {
                "name": "plan_diy_project",
                "description": "Calcule le métrage de matériaux, la quincaillerie, les outils et les étapes d'assemblage d'un projet DIY.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "project_name": {"type": "STRING", "description": "Nom du projet de bricolage (ex: 'Étagère en bois')"},
                        "dimensions": {"type": "STRING", "description": "Dimensions ou précisions"}
                    },
                    "required": ["project_name"]
                }
            },

            # =================================================================
            # 🖱️ CONTRÔLE VISUEL GUI SOURIS & CLAVIER
            # =================================================================
            {
                "name": "gui_click_at",
                "description": "Simule un clic de souris matériel sur l'écran hôte aux coordonnées (x, y).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "x": {"type": "INTEGER", "description": "Coordonnée X"},
                        "y": {"type": "INTEGER", "description": "Coordonnée Y"}
                    },
                    "required": ["x", "y"]
                }
            },
            {
                "name": "gui_type_text",
                "description": "Tape du texte au clavier sur l'application active.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING", "description": "Texte à saisir"}
                    },
                    "required": ["text"]
                }
            },

            # =================================================================
            # 👁️ VISION OPENCV & QR CODES
            # =================================================================
            {
                "name": "analyze_image_file",
                "description": "Analyse les dimensions, format et métadonnées d'une image en local.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "image_filename": {"type": "STRING", "description": "Nom du fichier image"}
                    },
                    "required": ["image_filename"]
                }
            },
            {
                "name": "decode_qr_code",
                "description": "Décode le contenu d'un QR code ou code-barre présent dans une image.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "image_filename": {"type": "STRING", "description": "Nom du fichier image contenant le QR code"}
                    },
                    "required": ["image_filename"]
                }
            },

            # =================================================================
            # 🛡️ GARDE-FOU & SÉCURITÉ LOCALE
            # =================================================================
            {
                "name": "inspect_prompt_guardrails",
                "description": "Analyse la sécurité d'un texte (détection d'injections, fuites de clés, niveau d'urgence).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING", "description": "Texte à inspecter"}
                    },
                    "required": ["text"]
                }
            },

            # =================================================================
            # 🔐 COFFRE-FORT DE SECRETS CHIFFRÉ
            # =================================================================
            {
                "name": "store_vault_secret",
                "description": "Enregistre un secret chiffré dans le coffre-fort local.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "key_name": {"type": "STRING", "description": "Nom de la clé"},
                        "secret_value": {"type": "STRING", "description": "Valeur du secret"},
                        "category": {"type": "STRING", "description": "Catégorie"}
                    },
                    "required": ["key_name", "secret_value"]
                }
            },
            {
                "name": "get_vault_secret",
                "description": "Récupère et déchiffre temporairement un secret du coffre.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "key_name": {"type": "STRING", "description": "Nom de la clé"}
                    },
                    "required": ["key_name"]
                }
            },

            # =================================================================
            # 📊 COMPILATEUR MERMAID.JS
            # =================================================================
            {
                "name": "generate_mermaid_diagram",
                "description": "Génère un schéma d'architecture ou diagramme Mermaid.js.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "title": {"type": "STRING", "description": "Titre du diagramme"},
                        "elements": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Liste des composants"}
                    },
                    "required": ["title"]
                }
            },

            # =================================================================
            # 🔍 RECHERCHE SÉMANTIQUE RAG LOCAL
            # =================================================================
            {
                "name": "local_semantic_search",
                "description": "Recherche sémantique instantanée dans l'ensemble des documents PDF, Markdown et code du workspace.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Question ou mots-clés"}
                    },
                    "required": ["query"]
                }
            },

            # =================================================================
            # 📥 ARCHIVAGE MEDIA YT-DLP
            # =================================================================
            {
                "name": "archive_web_media",
                "description": "Télécharge et archive une vidéo ou audio (YouTube, Twitch, SoundCloud).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url": {"type": "STRING", "description": "Lien de la vidéo/audio"},
                        "extract_audio_only": {"type": "BOOLEAN", "description": "True pour MP3 uniquement"}
                    },
                    "required": ["url"]
                }
            },

            # =================================================================
            # 📱 PASSERELLE MOBILE TASKER
            # =================================================================
            {
                "name": "send_mobile_command",
                "description": "Déclenche une action d'automatisation directe sur ton smartphone Android (Tasker).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "action": {"type": "STRING", "description": "Action (ex: 'vibrate', 'silence', 'battery', 'sms')"},
                        "value": {"type": "STRING", "description": "Valeur optionnelle"}
                    },
                    "required": ["action"]
                }
            },

            # =================================================================
            # 📄 USINE PDF & FUSION
            # =================================================================
            {
                "name": "merge_pdf_files",
                "description": "Fusionne plusieurs fichiers PDF du workspace en un seul document.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "pdf_filenames": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Liste des fichiers PDF"},
                        "output_filename": {"type": "STRING", "description": "Nom du fichier PDF fusionné"}
                    },
                    "required": ["pdf_filenames"]
                }
            },

            # =================================================================
            # 🗺️ GÉOCODAGE OPENSTREETMAP
            # =================================================================
            {
                "name": "geocode_address_osm",
                "description": "Convertit une adresse en coordonnées GPS réelles via OpenStreetMap (100% gratuit).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Adresse, ville ou monument"}
                    },
                    "required": ["query"]
                }
            },

            # =================================================================
            # 🌐 TRADUCTION LOCALE
            # =================================================================
            {
                "name": "translate_text_local",
                "description": "Traduit un texte en local sans fuite de données.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "text": {"type": "STRING", "description": "Texte à traduire"},
                        "target_lang": {"type": "STRING", "description": "Langue cible ('en', 'es', 'de', 'it')"}
                    },
                    "required": ["text"]
                }
            },

            # =================================================================
            # 💻 TERMINAL INTERACTIF
            # =================================================================
            {
                "name": "execute_terminal_interactive",
                "description": "Exécute une commande terminal Linux dans le serveur.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {"type": "STRING", "description": "Commande shell à exécuter"}
                    },
                    "required": ["command"]
                }
            },

            # =================================================================
            # 📦 SUIVI UNIVERSEL DE COLIS
            # =================================================================
            {
                "name": "track_parcel",
                "description": "Ajoute ou consulte le suivi en temps réel d'un colis (Colissimo, Amazon, UPS, DHL).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "tracking_number": {"type": "STRING", "description": "Numéro de suivi"},
                        "item_name": {"type": "STRING", "description": "Nom du colis ou objet"}
                    },
                    "required": ["tracking_number"]
                }
            },
            {
                "name": "list_active_parcels",
                "description": "Liste tous les colis actuellement surveillés par Hercul.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },

            # =================================================================
            # 🏃 COACH SPORT & RÉCUPÉRATION
            # =================================================================
            {
                "name": "analyze_workout",
                "description": "Analyse une séance sportive récente (Course, Vélo, Musculation).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "activity_type": {"type": "STRING", "description": "Type d'activité"},
                        "distance_km": {"type": "NUMBER", "description": "Distance parcourue en km"},
                        "duration_min": {"type": "INTEGER", "description": "Durée en minutes"}
                    },
                    "required": ["activity_type"]
                }
            },
            {
                "name": "assess_fitness_recovery",
                "description": "Calcule le score de forme et de récupération selon le sommeil et la fatigue.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "sleep_hours": {"type": "NUMBER", "description": "Heures de sommeil"}
                    }
                }
            },

            # =================================================================
            # 💳 CHASSEUR D'ABONNEMENTS & SPLITWISE
            # =================================================================
            {
                "name": "audit_subscriptions",
                "description": "Analyse les dépenses récurrentes et détecte les abonnements potentiellement inutiles.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "split_group_expense",
                "description": "Calcule la répartition exacte d'une dépense de groupe (qui doit combien à qui).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "total_eur": {"type": "NUMBER", "description": "Montant total en €"},
                        "people": {"type": "ARRAY", "items": {"type": "STRING"}, "description": "Noms des participants"},
                        "paid_by": {"type": "STRING", "description": "Nom de la personne qui a payé"}
                    },
                    "required": ["total_eur", "people"]
                }
            },

            # =================================================================
            # 🥦 ANTI-GASPI & TOO GOOD TO GO
            # =================================================================
            {
                "name": "check_fridge_expirations",
                "description": "Vérifie les aliments proches de la date limite et propose des recettes anti-gaspillage.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "track_too_good_to_go",
                "description": "Surveille les paniers repas Too Good To Go disponibles dans le quartier.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "neighborhood": {"type": "STRING", "description": "Nom du quartier ou ville"}
                    }
                }
            },

            # =================================================================
            # 🧠 FLASHCARDS ANKI & PAPERLESS OCR
            # =================================================================
            {
                "name": "generate_anki_cards",
                "description": "Génère des flashcards mémoires recto/verso optimisées pour Anki.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "topic": {"type": "STRING", "description": "Sujet ou concept à réviser"}
                    },
                    "required": ["topic"]
                }
            },
            {
                "name": "search_paperless_docs",
                "description": "Retrouve instantanément une facture, contrat ou document administratif par OCR.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Nom ou mots-clés du document recherché"}
                    },
                    "required": ["query"]
                }
            },

            # =================================================================
            # 🌐 INFRASTRUCTURE & MULTI-AGENTS
            # =================================================================
            {
                "name": "check_infra_health",
                "description": "Supervise l'état des conteneurs Docker et des certificats SSL.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "orchestrate_subagents",
                "description": "Déploie une escouade de sous-agents spécialisés pour accomplir une mission complexe.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task_goal": {"type": "STRING", "description": "Objectif de la mission"}
                    },
                    "required": ["task_goal"]
                }
            },

            # =================================================================
            # 🎯 HUB ULTIME : TODOIST, LBC, FLIGHTS, TRAFIC, OTTER, PLAID, OCR, TRIPIT
            # =================================================================
            {
                "name": "breakdown_goal_into_tasks",
                "description": "Découpe une grosse idée en 5 à 10 sous-tâches concrètes avec échéances (style Todoist / TickTick).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "goal_title": {"type": "STRING", "description": "Titre du projet ou de l'objectif"},
                        "target_days": {"type": "INTEGER", "description": "Nombre de jours pour réaliser"}
                    },
                    "required": ["goal_title"]
                }
            },
            {
                "name": "hunt_classified_ads",
                "description": "Surveille les annonces Leboncoin et Vinted pour trouver les meilleures affaires à bas prix.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "query": {"type": "STRING", "description": "Recherche d'objet"},
                        "max_price_eur": {"type": "NUMBER", "description": "Budget max en €"}
                    },
                    "required": ["query", "max_price_eur"]
                }
            },
            {
                "name": "watch_flight_deals",
                "description": "Surveille les prix des billets d'avion et analyse les baisses de tarifs (Google Flights).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "origin": {"type": "STRING", "description": "Ville de départ"},
                        "destination": {"type": "STRING", "description": "Ville d'arrivée"},
                        "target_period": {"type": "STRING", "description": "Mois ou période visée"},
                        "max_budget_eur": {"type": "NUMBER", "description": "Budget max"}
                    },
                    "required": ["origin", "destination", "target_period", "max_budget_eur"]
                }
            },
            {
                "name": "calculate_smart_departure_time",
                "description": "Calcule l'heure exacte de départ selon le trafic en direct pour arriver à l'heure à un rendez-vous.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "destination": {"type": "STRING", "description": "Lieu ou adresse d'arrivée"},
                        "appointment_time": {"type": "STRING", "description": "Heure du rendez-vous (ex: '14h30')"}
                    },
                    "required": ["destination", "appointment_time"]
                }
            },
            {
                "name": "voice_memo_to_actions",
                "description": "Extrait les actions à faire d'une note vocale et crée les tâches dans Google Tasks (style Otter.ai).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "transcript": {"type": "STRING", "description": "Transcription de la note vocale"}
                    },
                    "required": ["transcript"]
                }
            },
            {
                "name": "audit_savings_and_cashflow",
                "description": "Calcule le taux d'épargne réel et anticipe les dépenses (style Plaid / Bridge API).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "monthly_income": {"type": "NUMBER", "description": "Revenus du mois"},
                        "fixed_charges": {"type": "NUMBER", "description": "Charges fixes"},
                        "variable_spend": {"type": "NUMBER", "description": "Dépenses variables"}
                    }
                }
            },
            {
                "name": "scan_receipt_ocr",
                "description": "Scanne et extrait les montants d'un ticket de caisse ou d'une facture par OCR.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "receipt_image_or_text": {"type": "STRING", "description": "Image ou texte du ticket"}
                    },
                    "required": ["receipt_image_or_text"]
                }
            },
            {
                "name": "generate_trip_itinerary",
                "description": "Génère un carnet de voyage complet heure par heure avec activités (style TripIt).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "destination": {"type": "STRING", "description": "Ville de vacances"},
                        "days_count": {"type": "INTEGER", "description": "Nombre de jours"}
                    },
                    "required": ["destination"]
                }
            },

            # =================================================================
            # 📄 SYSTEME & FICHIERS
            # =================================================================
            {
                "name": "summarize_youtube_video",
                "description": "Extrait la transcription d'une vidéo YouTube pour la résumer.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "url_or_id": {"type": "STRING", "description": "Lien YouTube ou ID"}
                    },
                    "required": ["url_or_id"]
                }
            },
            {
                "name": "get_system_health",
                "description": "Sentinelle VPS : consulte l'état du serveur (CPU, RAM, Disque).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "execute_command",
                "description": "Exécute une commande shell dans le workspace.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {"type": "STRING", "description": "Commande shell"}
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "write_file",
                "description": "Crée ou modifie un fichier dans le workspace.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filename": {"type": "STRING", "description": "Nom du fichier"},
                        "content": {"type": "STRING", "description": "Contenu"}
                    },
                    "required": ["filename", "content"]
                }
            },
            {
                "name": "read_file",
                "description": "Lit le contenu texte d'un fichier du workspace.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "filename": {"type": "STRING", "description": "Nom du fichier"}
                    },
                    "required": ["filename"]
                }
            }
        ]

    @classmethod
    async def execute_tool(cls, name: str, args: Dict[str, Any], memory_manager=None) -> Dict[str, Any]:
        try:
            # 1. Gmail
            if name == "list_gmail_messages":
                return google_workspace.list_gmail_messages(
                    query=args.get("query", "is:unread"),
                    max_results=args.get("max_results", 5)
                )
            elif name == "read_gmail_message":
                return google_workspace.read_gmail_message(message_id=args.get("message_id", ""))
            elif name == "send_gmail_message":
                return google_workspace.send_gmail_message(
                    to=args.get("to", ""),
                    subject=args.get("subject", ""),
                    body=args.get("body", "")
                )
            elif name == "create_gmail_draft":
                return google_workspace.create_gmail_draft(
                    to=args.get("to", ""),
                    subject=args.get("subject", ""),
                    body=args.get("body", "")
                )
            elif name == "trash_gmail_message":
                return google_workspace.trash_gmail_message(message_id=args.get("message_id", ""))

            # 2. Google Calendar & Meet
            elif name == "list_google_calendar_events":
                return google_workspace.list_calendar_events(
                    max_results=args.get("max_results", 10),
                    days_ahead=args.get("days_ahead", 7)
                )
            elif name == "create_google_calendar_event":
                return google_workspace.create_calendar_event(
                    summary=args.get("summary", ""),
                    start_time_iso=args.get("start_time_iso", ""),
                    end_time_iso=args.get("end_time_iso"),
                    description=args.get("description", ""),
                    location=args.get("location", "")
                )
            elif name == "create_google_meet_event":
                return google_workspace.create_google_meet_event(
                    summary=args.get("summary", ""),
                    start_time_iso=args.get("start_time_iso", ""),
                    attendees_emails=args.get("attendees_emails"),
                    description=args.get("description", "")
                )
            elif name == "quick_add_calendar_event":
                return google_workspace.quick_add_calendar_event(text=args.get("text", ""))
            elif name == "delete_google_calendar_event":
                return google_workspace.delete_calendar_event(event_id_or_summary=args.get("event_id_or_summary", ""))

            # 3. Google Maps & Trafic
            elif name == "maps_get_directions":
                return await google_workspace.get_directions_and_traffic(
                    origin=args.get("origin", ""),
                    destination=args.get("destination", ""),
                    mode=args.get("mode", "driving")
                )
            elif name == "maps_search_places":
                return await google_workspace.search_places(
                    query=args.get("query", ""),
                    location=args.get("location")
                )

            # 4. Google Forms
            elif name == "create_google_form":
                return google_workspace.create_google_form(
                    title=args.get("title", ""),
                    description=args.get("description", "")
                )

            # 5. YouTube Stats
            elif name == "get_youtube_channel_stats":
                return google_workspace.get_youtube_channel_stats(
                    channel_username_or_id=args.get("channel_username_or_id", "")
                )

            # 6. Secrétaire Proactif Scan Forcé
            elif name == "trigger_proactive_scan":
                from backend.services.proactive_secretary import proactive_secretary
                actions = await proactive_secretary.scan_and_automate()
                return {"status": "success", "actions_performed": len(actions), "details": actions}

            # 3. Google Drive
            elif name == "search_google_drive":
                return google_workspace.search_drive(query=args.get("query", ""), max_results=args.get("max_results", 10))
            elif name == "export_drive_file_as_pdf":
                return google_workspace.export_drive_file_as_pdf(file_id_or_title=args.get("file_id_or_title", ""))
            elif name == "upload_file_to_drive":
                return google_workspace.upload_file_to_drive(local_filename=args.get("local_filename", ""))
            elif name == "create_drive_folder":
                return google_workspace.create_drive_folder(folder_name=args.get("folder_name", ""))
            elif name == "delete_drive_file":
                return google_workspace.delete_drive_file(file_id=args.get("file_id", ""))

            # 4. Google Docs & Sheets
            elif name == "create_google_doc":
                return google_workspace.create_google_doc(title=args.get("title", "Document Hercul"), content=args.get("content", ""))
            elif name == "append_to_google_doc":
                return google_workspace.append_to_google_doc(document_id=args.get("document_id", ""), text_to_append=args.get("text_to_append", ""))
            elif name == "create_google_sheet":
                return google_workspace.create_google_sheet(title=args.get("title", "Feuille Hercul"), headers=args.get("headers"))
            elif name == "append_rows_to_sheet":
                return google_workspace.append_rows_to_sheet(spreadsheet_id=args.get("spreadsheet_id", ""), rows=args.get("rows", []))

            # 5. Google Tasks & Contacts
            elif name == "list_google_tasks":
                return google_workspace.list_google_tasks(
                    show_completed=args.get("show_completed", False),
                    max_results=args.get("max_results", 20)
                )
            elif name == "create_google_task":
                return google_workspace.create_google_task(
                    title=args.get("title", ""),
                    notes=args.get("notes", ""),
                    due_date_iso=args.get("due_date_iso")
                )
            elif name == "complete_google_task":
                return google_workspace.complete_google_task(task_id_or_title=args.get("task_id_or_title", ""))
            elif name == "delete_google_task":
                return google_workspace.delete_google_task(task_id_or_title=args.get("task_id_or_title", ""))
            elif name == "list_google_task_lists":
                return google_workspace.list_google_task_lists()
            elif name == "create_google_task_list":
                return google_workspace.create_google_task_list(title=args.get("title", ""))
            elif name == "search_google_contacts":
                return google_workspace.search_google_contacts(query=args.get("query", ""))

            # 6. Google Keep / Notes
            elif name == "save_google_keep_note":
                return google_workspace.save_keep_note(title=args.get("title", "Note"), content=args.get("content", ""), category=args.get("category", "Général"))
            elif name == "list_google_keep_notes":
                return google_workspace.list_keep_notes(category=args.get("category"))

            # 7. Temps, Recherche & Sentinelle
            elif name == "get_current_time":
                return scheduler.get_current_time_details()
            elif name == "set_timer_or_reminder":
                return await scheduler.add_timer_or_reminder(
                    message=args.get("message", "Minuteur"),
                    delay_seconds=args.get("delay_seconds"),
                    delay_minutes=args.get("delay_minutes"),
                    target_time_str=args.get("target_time_str"),
                    user_id=args.get("user_id")
                )
            elif name == "list_reminders":
                return {"status": "success", "reminders": scheduler.list_reminders()}
            elif name == "web_search":
                return SearchTools.web_search(query=args.get("query", ""))
            elif name == "fetch_page_content":
                return await SearchTools.fetch_page_content(url=args.get("url", ""))
            elif name == "summarize_youtube_video":
                return DocumentTools.get_youtube_transcript(url_or_id=args.get("url_or_id", ""))
            # 8. Téléphonie Vocale
            elif name == "make_phone_call":
                return await phone_service.make_phone_call(
                    to_phone_number=args.get("to_phone_number", ""),
                    text_to_speak=args.get("text_to_speak", "")
                )
            elif name == "trigger_emergency_call":
                return await phone_service.trigger_emergency_call(
                    reason=args.get("reason", "Alerte Hercul"),
                    phone_number=args.get("phone_number")
                )

            # 9. Navigateur Visuel Autonome Playwright
            elif name == "take_web_screenshot":
                return await browser_agent.take_page_screenshot(url=args.get("url", ""))
            elif name == "browse_and_read_webpage":
                return await browser_agent.browse_and_read(url=args.get("url", ""))
            elif name == "compare_product_prices":
                return await browser_agent.compare_prices(product_query=args.get("product_query", ""))

            # 10. Domotique & Maison Connectée
            elif name == "control_smart_device":
                return await smart_home.control_device(
                    device_name=args.get("device_name", ""),
                    action=args.get("action", "turn_on"),
                    brightness=args.get("brightness"),
                    color=args.get("color"),
                    temperature=args.get("temperature")
                )
            elif name == "activate_smart_scene":
                return await smart_home.activate_scene(scene_name=args.get("scene_name", "cinema"))
            elif name == "get_smart_home_status":
                return smart_home.get_home_status()

            # 11. Sentinelle Cybersécurité & Dark Web
            elif name == "check_password_leak":
                return await cyber_sentinel.check_password_leak(password=args.get("password", ""))
            elif name == "check_email_breaches":
                return await cyber_sentinel.check_email_breaches(email_address=args.get("email_address", ""))
            elif name == "run_security_audit":
                return await cyber_sentinel.run_full_security_audit(email_address=args.get("email_address"))

            # 12. Musique Deezer
            elif name == "search_deezer_music":
                return await deezer_service.search_deezer(
                    query=args.get("query", ""),
                    limit=args.get("limit", 5)
                )
            elif name == "get_deezer_top_charts":
                return await deezer_service.get_top_charts(limit=args.get("limit", 10))
            elif name == "get_deezer_artist_tracks":
                return await deezer_service.get_artist_top_tracks(artist_name=args.get("artist_name", ""))

            # 13. Usine de Médias (FFmpeg / Pillow)
            elif name == "convert_video_to_mp3":
                return media_factory.convert_video_to_mp3(video_filename=args.get("video_filename", ""))
            elif name == "convert_image_format":
                return media_factory.convert_image(
                    image_filename=args.get("image_filename", ""),
                    target_format=args.get("target_format", "png")
                )

            # 14. Suivi de Budget Google Sheets
            elif name == "log_budget_expense":
                return budget_tracker.log_expense(
                    amount=float(args.get("amount", 0)),
                    vendor=args.get("vendor", "Inconnu"),
                    category=args.get("category", "Général"),
                    date_str=args.get("date_str"),
                    notes=args.get("notes", "")
                )

            # 15. Chasseur & Veilleur Web 24/7
            elif name == "add_web_watch_task":
                return web_hunter.add_watch_task(
                    url=args.get("url", ""),
                    condition=args.get("condition", ""),
                    label=args.get("label", "Alerte Web")
                )
            elif name == "list_web_watch_tasks":
                return web_hunter.list_watch_tasks()
            elif name == "remove_web_watch_task":
                return web_hunter.remove_watch_task(task_id=args.get("task_id", ""))

            # 16. Bilan Exécutif Dimanche Soir
            elif name == "generate_life_weekly_report":
                return await sunday_report_service.generate_weekly_report()

            # 17. Copilote de Voyage Intelligent
            elif name == "plan_smart_trip":
                return await travel_copilot.plan_trip(
                    destination=args.get("destination", ""),
                    origin=args.get("origin", "Paris"),
                    departure_time_str=args.get("departure_time")
                )

            # 18. Briefing Matinal 08h00
            elif name == "generate_morning_briefing":
                return await morning_briefing_service.generate_briefing()

            # 19. Répondeur & Secrétaire Vocal IA
            elif name == "record_voicemail":
                return await voicemail_service.record_voicemail(
                    caller=args.get("caller", "Inconnu"),
                    transcript_or_text=args.get("transcript_or_text", ""),
                    audio_url=args.get("audio_url")
                )
            elif name == "list_voicemails":
                return voicemail_service.list_voicemails()

            # 20. Traqueur d'Habitudes & Bilan 22h00
            elif name == "log_daily_habit":
                return habit_tracker.log_habit(
                    habit_name=args.get("habit_name", "Objectif"),
                    completed=args.get("completed", True),
                    notes=args.get("notes", "")
                )

            # 21. Synchronisation Miroir Notes & Tâches
            elif name == "sync_notes_and_tasks_mirror":
                return mirror_sync_service.sync_mirror()

            # 22. Radio SDR & Spectre
            elif name == "scan_radio_sensors_433":
                return radio_sdr.scan_sensors_433mhz()
            elif name == "track_aircrafts_adsb":
                return radio_sdr.track_aircrafts_adsb()

            # 23. Scraping Furtif FlareSolverr
            elif name == "stealth_scrape_url":
                return await stealth_scraper.scrape_url(url=args.get("url", ""))

            # 24. Assistant Culinaire & Repas
            elif name == "generate_weekly_menu":
                return meal_planner.generate_weekly_menu(days=args.get("days", 5))
            elif name == "generate_and_sync_grocery_list":
                return meal_planner.generate_and_sync_grocery_list()

            # 25. Cartes Mentales Obsidian Canvas
            elif name == "create_obsidian_mindmap":
                return obsidian_canvas.create_mindmap(
                    title=args.get("title", "mindmap"),
                    central_topic=args.get("central_topic", "Idée"),
                    subtopics=args.get("subtopics", [])
                )

            # 26. Assistant de Rédaction Multi-Style
            elif name == "rewrite_text_style":
                return style_rewriter.rewrite(text=args.get("text", ""))

            # 27. Organisateur d'Événements & Soirées
            elif name == "plan_party_event":
                return event_planner.plan_event(
                    title=args.get("title", "Soirée"),
                    guests_count=args.get("guests_count", 8),
                    theme=args.get("theme", "Conviviale")
                )

            # 28. Assistant Bricolage & DIY
            elif name == "plan_diy_project":
                return diy_planner.plan_project(
                    project_name=args.get("project_name", "Projet Bricolage"),
                    dimensions=args.get("dimensions", "Standard")
                )

            # 29. Contrôle Visuel GUI (Souris & Clavier)
            elif name == "gui_click_at":
                return gui_controller.click_at(x=int(args.get("x", 0)), y=int(args.get("y", 0)))
            elif name == "gui_type_text":
                return gui_controller.type_text(text=args.get("text", ""))

            # 30. Vision OpenCV & QR Codes
            elif name == "analyze_image_file":
                return vision_analyzer.analyze_image(image_filename=args.get("image_filename", ""))
            elif name == "decode_qr_code":
                return vision_analyzer.decode_qr_code(image_filename=args.get("image_filename", ""))

            # 31. Garde-Fou Local & Sécurité
            elif name == "inspect_prompt_guardrails":
                return guardrails_service.inspect_text(text=args.get("text", ""))

            # 32. Coffre-Fort de Secrets Chiffré
            elif name == "store_vault_secret":
                return vault_manager.store_secret(
                    key_name=args.get("key_name", ""),
                    secret_value=args.get("secret_value", ""),
                    category=args.get("category", "Général")
                )
            elif name == "get_vault_secret":
                return vault_manager.get_secret(key_name=args.get("key_name", ""))

            # 33. Compilateur Mermaid.js
            elif name == "generate_mermaid_diagram":
                return diagram_compiler.generate_diagram(
                    title=args.get("title", "Architecture"),
                    elements=args.get("elements")
                )

            # 34. Recherche Sémantique RAG Locale
            elif name == "local_semantic_search":
                return semantic_rag.semantic_search(query=args.get("query", ""))

            # 35. Archivage Média Web yt-dlp
            elif name == "archive_web_media":
                return media_archiver.archive_media(
                    url=args.get("url", ""),
                    extract_audio_only=args.get("extract_audio_only", True)
                )

            # 36. Passerelle Mobile Tasker
            elif name == "send_mobile_command":
                return await mobile_bridge.send_command(
                    action=args.get("action", ""),
                    value=args.get("value")
                )

            # 37. Usine PDF & Fusion
            elif name == "merge_pdf_files":
                return pdf_factory.merge_pdfs(
                    pdf_filenames=args.get("pdf_filenames", []),
                    output_filename=args.get("output_filename", "fusion.pdf")
                )

            # 38. Géocodage OpenStreetMap
            elif name == "geocode_address_osm":
                return await osm_geocoder.geocode(query=args.get("query", ""))

            # 39. Traduction Locale Anonymisée
            elif name == "translate_text_local":
                return local_translator.translate(
                    text=args.get("text", ""),
                    target_lang=args.get("target_lang", "en")
                )

            # 40. Terminal Interactif
            elif name == "execute_terminal_interactive":
                return terminal_session.execute_terminal_command(command=args.get("command", ""))

            # 41. Suivi de Colis Universel
            elif name == "track_parcel":
                return package_tracker.add_or_track_parcel(
                    tracking_number=args.get("tracking_number", ""),
                    item_name=args.get("item_name", "Colis")
                )
            elif name == "list_active_parcels":
                return package_tracker.list_parcels()

            # 42. Coach Sportif & Récupération
            elif name == "analyze_workout":
                return fitness_coach.analyze_workout(
                    activity_type=args.get("activity_type", "Course"),
                    distance_km=float(args.get("distance_km", 5.0)),
                    duration_min=int(args.get("duration_min", 30))
                )
            elif name == "assess_fitness_recovery":
                return fitness_coach.assess_recovery(
                    sleep_hours=float(args.get("sleep_hours", 7.5))
                )

            # 43. Finances & Splitwise
            elif name == "audit_subscriptions":
                return smart_finance.detect_subscriptions()
            elif name == "split_group_expense":
                return smart_finance.split_expense(
                    total_eur=float(args.get("total_eur", 0.0)),
                    people=args.get("people", []),
                    paid_by=args.get("paid_by", "Nathan")
                )

            # 44. Anti-Gaspillage & Too Good To Go
            elif name == "check_fridge_expirations":
                return anti_waste.check_fridge_expirations()
            elif name == "track_too_good_to_go":
                return anti_waste.track_too_good_to_go(
                    neighborhood=args.get("neighborhood", "Quartier")
                )

            # 45. Flashcards Anki & Paperless OCR
            elif name == "generate_anki_cards":
                return learning_anki.generate_anki_cards(
                    topic=args.get("topic", "Général")
                )
            elif name == "search_paperless_docs":
                return learning_anki.search_paperless_docs(
                    query=args.get("query", "")
                )

            # 46. Infrastructure & Multi-Agents
            elif name == "check_infra_health":
                return infra_manager.check_infra_health()
            elif name == "orchestrate_subagents":
                return infra_manager.orchestrate_subagents(
                    task_goal=args.get("task_goal", "")
                )

            # 47. Hub Ultime (Todoist, LBC, Flights, Trafic, Otter, Plaid, OCR, TripIt)
            elif name == "breakdown_goal_into_tasks":
                return ultimate_hub.breakdown_goal(
                    goal_title=args.get("goal_title", "Projet"),
                    target_days=int(args.get("target_days", 7))
                )
            elif name == "hunt_classified_ads":
                return ultimate_hub.hunt_classified_ads(
                    query=args.get("query", ""),
                    max_price_eur=float(args.get("max_price_eur", 100.0))
                )
            elif name == "watch_flight_deals":
                return ultimate_hub.watch_flight_deals(
                    origin=args.get("origin", "Paris"),
                    destination=args.get("destination", ""),
                    target_period=args.get("target_period", "Prochainement"),
                    max_budget_eur=float(args.get("max_budget_eur", 500.0))
                )
            elif name == "calculate_smart_departure_time":
                return ultimate_hub.calculate_smart_departure_time(
                    destination=args.get("destination", ""),
                    appointment_time_str=args.get("appointment_time", "12h00")
                )
            elif name == "voice_memo_to_actions":
                return ultimate_hub.voice_memo_to_actions(
                    transcript=args.get("transcript", "")
                )
            elif name == "audit_savings_and_cashflow":
                return ultimate_hub.audit_savings_and_cashflow(
                    monthly_income=float(args.get("monthly_income", 2500.0)),
                    fixed_charges=float(args.get("fixed_charges", 1100.0)),
                    variable_spend=float(args.get("variable_spend", 650.0))
                )
            elif name == "scan_receipt_ocr":
                return ultimate_hub.scan_receipt_ocr(
                    receipt_image_or_text=args.get("receipt_image_or_text", "")
                )
            elif name == "generate_trip_itinerary":
                return ultimate_hub.generate_trip_itinerary(
                    destination=args.get("destination", "Destination"),
                    days_count=int(args.get("days_count", 3))
                )

            # 48. Système & Fichiers
            elif name == "get_system_health":
                return SystemSentinel.get_system_health()
            elif name == "execute_command":
                return SystemTools.execute_command(command=args.get("command", ""))
            elif name == "write_file":
                return SystemTools.write_file(filename=args.get("filename", ""), content=args.get("content", ""))
            elif name == "read_file":
                return SystemTools.read_file(filename=args.get("filename", ""))

            raw_result = {"status": "error", "message": f"Outil inconnu : {name}"}
            return cls._compress_output(raw_result)

        except Exception as e:
            return {"status": "error", "message": f"Erreur outil {name} : {str(e)}"}

    @classmethod
    def _compress_output(cls, raw: Any) -> Any:
        """Compresse et tronque les données renvoyées au LLM pour économiser jusqu'à 80% de tokens."""
        if isinstance(raw, str):
            if len(raw) > 1500:
                return raw[:1500] + " ... [Contenu tronqué]"
            return raw
        if isinstance(raw, dict):
            compressed = {}
            for k, v in raw.items():
                if isinstance(v, list) and len(v) > 6:
                    compressed[k] = [cls._compress_output(item) for item in v[:6]]
                else:
                    compressed[k] = cls._compress_output(v)
            return compressed
        if isinstance(raw, list):
            return [cls._compress_output(item) for item in raw[:6]]
        return raw
