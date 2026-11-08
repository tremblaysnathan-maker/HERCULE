import os
import io
import asyncio
from typing import Optional, Dict, Any, List
import discord
from discord.ext import commands
import edge_tts
import httpx

from backend.config import settings
from backend.core.agent import HerculAgent
from backend.memory.memory_manager import MemoryManager
from backend.services.scheduler import scheduler
from backend.services.sentinel import SystemSentinel
from backend.tools.doc_tools import DocumentTools

intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
memory = MemoryManager()
agent = HerculAgent(memory_manager=memory)

_last_dm_user_id: Optional[int] = None

def get_active_user_id() -> Optional[int]:
    """Retourne l'ID Discord actif de Nathan."""
    saved_id = memory.profile.get_preference("discord_user_id")
    if saved_id:
        try:
            return int(saved_id)
        except ValueError:
            pass
    return _last_dm_user_id

@bot.event
async def on_ready():
    print(f"\n🤖 [Discord] Hercul Bot connecté : {bot.user} (ID: {bot.user.id})")
    print(f"💬 [Discord] Prêt en Message Privé avec Minuteurs Proactifs & Vocal !\n")
    await bot.change_presence(activity=discord.Game(name="Opérateur Autonome 🔮"))

    # Lancement des boucles du Scheduler et de la Sentinelle
    asyncio.create_task(scheduler.run_scheduler_loop(
        reminder_notifier=handle_due_reminder,
        briefing_generator=handle_morning_briefing
    ))
    asyncio.create_task(SystemSentinel.run_sentinel_loop(
        alert_callback=handle_sentinel_alert
    ))

async def handle_due_reminder(reminder: dict):
    """Déclenche la notification Discord en Message Privé à la seconde près."""
    saved_id = memory.profile.get_preference("discord_user_id")
    target_id = reminder.get("user_id") or saved_id or _last_dm_user_id
    
    if not target_id:
        print("[Discord] Aucun ID utilisateur pour envoyer le rappel.")
        return

    try:
        user_id_int = int(target_id)
        user = bot.get_user(user_id_int)
        if not user:
            user = await bot.fetch_user(user_id_int)

        if user:
            dm = user.dm_channel or await user.create_dm()
            alert_text = f"⏰ **RAPPEL HERCUL** ⏰\n« {reminder['message']} »"
            await dm.send(alert_text)
            print(f"✅ [Discord] Rappel envoyé avec succès à {user.name} : '{reminder['message']}'")

            # Synthèse vocale de rappel avec la voix Vivienne
            try:
                vocal_prompt = f"Nathan, voici ton rappel : {reminder['message']}"
                communicate = edge_tts.Communicate(vocal_prompt, voice="fr-FR-VivienneMultilingualNeural", rate="+4%")
                audio_data = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_data.write(chunk["data"])
                audio_data.seek(0)
                await dm.send(file=discord.File(fp=audio_data, filename="rappel_hercul.mp3"))
            except Exception as e:
                print(f"[Discord] Erreur audio rappel : {e}")

    except Exception as e:
        print(f"[Discord] Erreur notification rappel : {e}")

async def handle_morning_briefing(cfg: dict):
    """Génère et envoie le Morning Briefing quotidien à 8h."""
    saved_id = memory.profile.get_preference("discord_user_id")
    target_id = saved_id or _last_dm_user_id
    if not target_id:
        return

    try:
        user_id_int = int(target_id)
        user = bot.get_user(user_id_int) or await bot.fetch_user(user_id_int)
        if not user:
            return

        dm = user.dm_channel or await user.create_dm()
        city = cfg.get("city", "Paris")
        topics = cfg.get("topics", "IA et Tech")

        briefing_prompt = (
            f"Génère un Morning Briefing matinal très élégant et concis pour Nathan. "
            f"1. Fais un point météo rapide pour {city}. "
            f"2. Fais une veille synthétique des 3 actus majeures du jour sur {topics}. "
            f"3. Termine par un mot d'encouragement dynamique pour la journée."
        )

        result = await agent.chat(message=briefing_prompt, session_id="morning_briefing", fast_mode=False)
        response_text = result.get("response", "Bonjour Nathan, voici votre briefing du jour.")

        await dm.send(f"☀️ **MORNING BRIEFING HERCUL** ☀️\n\n{response_text}")

        try:
            communicate = edge_tts.Communicate(response_text, voice="fr-FR-VivienneMultilingualNeural", rate="+4%")
            audio_data = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.write(chunk["data"])
            audio_data.seek(0)
            await dm.send(file=discord.File(fp=audio_data, filename="briefing_matin.mp3"))
        except Exception:
            pass

    except Exception as e:
        print(f"[Discord] Erreur briefing matinal : {e}")

async def handle_sentinel_alert(alert_msg: str):
    saved_id = memory.profile.get_preference("discord_user_id")
    target_id = saved_id or _last_dm_user_id
    if not target_id:
        return
    try:
        user_id_int = int(target_id)
        user = bot.get_user(user_id_int) or await bot.fetch_user(user_id_int)
        if user:
            dm = user.dm_channel or await user.create_dm()
            await dm.send(alert_msg)
    except Exception:
        pass

@bot.event
async def on_message(message: discord.Message):
    global _last_dm_user_id

    if message.author == bot.user:
        return

    is_dm = isinstance(message.channel, discord.DMChannel)
    is_mentioned = bot.user in message.mentions

    if is_dm or is_mentioned:
        _last_dm_user_id = message.author.id
        # Mémorisation permanente de l'ID Discord de Nathan
        memory.profile.set_preference("discord_user_id", str(message.author.id))

        user_content = message.content.replace(f"<@{bot.user.id}>", "").strip()

        async with message.channel.typing():
            try:
                attached_context = []

                if message.attachments:
                    for att in message.attachments:
                        fname = att.filename.lower()
                        if att.content_type and att.content_type.startswith("image/"):
                            attached_context.append(f"[Image jointe : {att.url}]")
                        elif fname.endswith(".pdf"):
                            async with httpx.AsyncClient() as client:
                                res = await client.get(att.url)
                                if res.status_code == 200:
                                    pdf_data = DocumentTools.read_pdf(res.content)
                                    attached_context.append(f"[Contenu extrait du PDF '{att.filename}'] :\n{pdf_data.get('content', '')}")
                        elif fname.endswith((".csv", ".tsv", ".txt", ".json")):
                            async with httpx.AsyncClient() as client:
                                res = await client.get(att.url)
                                if res.status_code == 200:
                                    table_data = DocumentTools.read_csv_or_table(res.content)
                                    attached_context.append(f"[Contenu extrait de '{att.filename}'] :\n{table_data.get('content', '')}")

                full_prompt = f"{user_content}\n" + "\n".join(attached_context)
                if not full_prompt.strip():
                    full_prompt = "Bonjour Hercul"

                session_id = f"discord_{message.author.id}"
                result = await agent.chat(
                    message=full_prompt.strip(),
                    session_id=session_id,
                    fast_mode=False
                )

                response_text = result.get("response", "Action accomplie.")

                if len(response_text) <= 1950:
                    await message.reply(response_text)
                else:
                    chunks = [response_text[i:i+1900] for i in range(0, len(response_text), 1900)]
                    for chunk in chunks:
                        await message.channel.send(chunk)

                # Envoi automatique des fichiers générés (PDF Drive, Captures d'écran, Conversions MP3)
                for t in result.get("tools_executed", []):
                    res_data = t.get("result", {})
                    if isinstance(res_data, dict):
                        local_p = res_data.get("local_path") or res_data.get("output_path") or res_data.get("screenshot_path")
                        if local_p and os.path.exists(local_p):
                            try:
                                await message.channel.send(file=discord.File(local_p))
                            except Exception as e:
                                print(f"[Discord] Erreur envoi pièce jointe : {e}")

                if any(w in user_content.lower() for w in ["vocal", "audio", "dis-moi", "parle", "voix", "envoie un vocal"]):
                    communicate = edge_tts.Communicate(response_text, voice="fr-FR-VivienneMultilingualNeural", rate="+4%")
                    audio_data = io.BytesIO()
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            audio_data.write(chunk["data"])
                    audio_data.seek(0)
                    await message.channel.send(file=discord.File(fp=audio_data, filename="hercul_vocal.mp3"))

            except Exception as e:
                await message.reply(f"⚠️ Erreur : {str(e)}")

    await bot.process_commands(message)

async def start_discord_bot():
    token = settings.DISCORD_BOT_TOKEN
    if not token:
        print("[Discord] Aucun DISCORD_BOT_TOKEN configuré dans .env.")
        return

    try:
        await bot.start(token)
    except Exception as e:
        print(f"[Discord] Erreur au lancement du bot : {e}")
