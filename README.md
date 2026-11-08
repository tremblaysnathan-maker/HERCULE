# 🏛️ HERCUL AI - Système d'Exploitation & Agent Personnel Autonome

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-3.7_Flash-8E75B2.svg)](https://aistudio.google.com/)
[![Discord Bot](https://img.shields.io/badge/Discord.py-2.3+-5865F2.svg)](https://discord.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Hercul** est un agent d'intelligence artificielle personnel et autonome, conçu pour tourner **24h/24 sur un serveur VPS**, interactif directement via **Discord**, le **Web** ou **Tasker (Android)**.

Il allie la puissance de réflexion de **Google Gemini** à une suite d'outils connectés (Google Workspace, Deezer, Suivi de colis universel) et des utilitaires **100 % locaux et gratuits** (navigation web furtive, vision par ordinateur, cartes mentales Obsidian Canvas, sécurité Guardrails).

---

## 🌟 Fonctionnalités Principales (v3.0 — Architecture Multi-Agents Continue)

```mermaid
flowchart TD
    User["👤 Opérateur (Discord / Web / Tasker)"] --> Guard["🛡️ Local Guardrails (<5ms)"]
    Guard --> Core["🧠 HERCUL CORE v3.0 (Hub Orchestrator)"]
    Core --> Swarm["🐝 Swarm Multi-Agents Parallèle (asyncio.gather)"]
    Swarm --> R["🕵️ Agent Chercheur (Web Live)"]
    Swarm --> A["💻 Agent Architecte (Code & Structure)"]
    Swarm --> S["📊 Agent Stratège (LifeOps & Plan)"]
    R & A & S --> C["🛡️ Agent Critique (Reflection Loop)"]
    Core --> Goals["🔄 Moteur d'Objectifs Continus 24/7"]
    Core --> Forge["🧬 Skill Forge Auto-Évolutif (Python AST + Soul Memory)"]
```

### 🐝 1. Escouade Multi-Agents Asynchrone ("Hub-and-Spoke Swarm + Reflection Loop")
* Inspiré des architectures de pointe (*LangGraph Open Deep Research*, *Meta Muse*, *Hermes Agent*).
* Déploie **en parallèle (`asyncio.gather`)** 3 sous-agents spécialisés (🕵️ **Chercheur Web**, 💻 **Architecte Builder**, 📊 **Stratège LifeOps**), suivis d'un 4ème **🛡️ Agent Critique (Reflection Loop)** qui vérifie les faits, corrige les angles morts et génère un rapport Markdown certifié dans `/workspace/swarm_reports/`.

### 🔄 2. Moteur d'Objectifs Autonomes Continus 24/7 ("Continuous Goal Engine")
* Ne s'endort jamais après un message : confiez-lui un objectif de fond, il le découpe en étapes séquentielles, travaille dessus **en tâche de fond 24h/24**, sauvegarde les livrables dans `/workspace/goals/` et vous notifie sur Discord à chaque étape accomplie.

### 🧬 3. Auto-Évolution & Forge de Compétences Dynamiques ("Dynamic Skill Forge")
* Hercul peut **coder, compiler (validation AST), enregistrer et exécuter ses propres nouveaux outils Python à la volée** dans `/workspace/custom_skills/`.
* **Mémoire Procédurale (`Soul Lessons`)** : Mémorise ses leçons d'auto-amélioration et les réinjecte automatiquement dans sa conscience système.

### 🧠 4. Cerveau Hybride, Auto-Healing & Optimisation de Tokens
* **Double Moteur Gemini Non-Bloquant** :
  * `gemini-3.5-flash-lite` : Réponses instantanées pour les salutations et les discussions légères.
  * `gemini-3.7-flash` : Raisonnement approfondi, orchestration des 51 outils (Function Calling) et supervision du Swarm, avec **Auto-Healing** (bascule automatique de modèle en cas de surcharge).
* **Token Optimizer** : Désactivation intelligente des outils sur les messages simples et compression automatique des résultats d'outils (`< 1500 chars`) pour diviser drastiquement la consommation de tokens.
* **Mémoire Totale (ChromaDB & Profil)** : Mémorisation sémantique permanente de vos préférences, projets et habitudes sans polluer le contexte actif.

### 💼 Suite Google Workspace Complète
* 📧 **Gmail** : Résumé des e-mails non lus, recherche précise et rédaction de brouillons.
* 📅 **Google Agenda** : Consultation de l'emploi du temps, création et modification d'événements.
* ✅ **Google Tasks** : Gestion intégrale des to-do lists (création, complétion, suppression, listes dédiées).
* 📊 **Google Sheets** : Enregistrement automatique des métriques et suivi quotidien des habitudes.

### 📦 Suivi Universel de Colis (Zero-Config)
* Détection automatique du transporteur (Colissimo, Amazon, UPS, DHL, Chronopost, Mondial Relay) via expressions régulières.
* Génération de liens directs de suivi universel 17TRACK sans abonnement ni clé API tierce.

### 🎵 Musique & Divertissement (Deezer)
* Recherche d'artistes, albums et morceaux.
* Gestion des playlists et recommandations musicales personnalisées.

### 🛡️ Sécurité & Confidentialité Locale (Guardrails)
* **Local Guardrail (< 5 ms)** : Détection et blocage en amont des tentatives de prompt injection et protection contre la fuite de clés API et secrets.
* **Coffre-fort local chiffré (Vault)** : Stockage sécurisé de tokens éphémères.

### 🎨 Outils Créatifs & Second Cerveau
* 🗺️ **Obsidian Canvas (`.canvas`)** : Génération de véritables cartes mentales et mindmaps visuelles au format JSON local.
* 📊 **Compilateur Mermaid.js** : Conversion de descriptions textuelles en schémas d'architecture et diagrammes de flux.
* 🌐 **Navigation Furtive & Scraping** : Contrôle de navigateur via Playwright pour passer les protections légères (FlareSolverr).
* 📷 **Vision & QR Codes** : Analyse locale d'images et décodage de codes-barres/QR codes via Pillow / OpenCV.
* 📻 **Capteurs & SDR** : Prise en charge des signaux radio 433 MHz (IoT météo) et radar ADS-B 1090 MHz.

---

## 📁 Architecture du Projet

```text
hercul/
├── backend/
│   ├── bot/
│   │   └── discord_bot.py      # Bot Discord interactif (MP, cartes, boutons)
│   ├── core/
│   │   ├── agent.py            # Boucle ReAct & coordination
│   │   └── gemini_client.py    # Client Google GenAI SDK officiel
│   ├── memory/
│   │   ├── memory_manager.py   # Gestion de la mémoire
│   │   ├── token_optimizer.py  # Économiseur & compresseur de tokens
│   │   └── vector_store.py     # Base vectorielle ChromaDB
│   ├── services/               # 25+ services modulaires (Google, Colis, Deezer, Briefing, etc.)
│   ├── tools/
│   │   └── registry.py         # Registre unifié des 48 outils Function Calling
│   ├── config.py               # Paramètres et validation Pydantic
│   └── server.py               # Serveur FastAPI principal
├── frontend/                   # Interface Web Futuriste & Cyber-Dashboard
├── data/                       # Stockage persistant (ignoré par Git)
├── workspace/                  # Dossier de travail (documents, canvas, etc.)
├── docker-compose.yml          # Déploiement Docker pour VPS
├── Dockerfile                  # Image conteneurisée Python 3.11 + Playwright
├── requirements.txt            # Dépendances Python
└── start.py                    # Script de démarrage local
```

---

## 🚀 Démarrage Rapide

### 1. Cloner le dépôt
```bash
git clone https://github.com/VOTRE_NOM/hercul.git
cd hercul
```

### 2. Configuration de l'environnement
Copiez le modèle de configuration et éditez vos identifiants :
```bash
cp .env.example .env
```

Renseignez au minimum votre clé Google Gemini dans le fichier `.env` :
```ini
GEMINI_API_KEY=votre_cle_api_ici
HERCUL_SECRET_KEY=votre_cle_secrete_ici
DISCORD_BOT_TOKEN=votre_token_discord_ici
```

*(Optionnel)* Pour Google Workspace, placez vos identifiants OAuth `google_credentials.json` dans le dossier `data/` (voir [google_credentials.example.json](google_credentials.example.json)).

---

### 3. Option A : Lancer en local (Développement)

```bash
# 1. Installer les dépendances
pip install -r requirements.txt
playwright install chromium

# 2. Démarrer Hercul
python start.py
```
L'interface Web sera accessible sur : **http://localhost:8000**

---

### 4. Option B : Déployer sur VPS avec Docker (Production 24/7)

```bash
# Lancement en tâche de fond avec redémarrage automatique
docker compose up -d --build
```

Pour consulter les logs en direct :
```bash
docker compose logs -f
```

---

## 🤖 Interaction & Interfaces

1. **Discord (Recommandé)** :
   * Ajoutez votre bot Discord à votre serveur ou discutez avec lui directement en Message Privé.
   * Il réagit instantanément, envoie des embeds stylisés et exécute les outils en temps réel.
2. **Dashboard Web** :
   * Accessible sur le port `8000` avec télémétrie en direct, synthèse vocale Vivienne HD et terminal interactif.
3. **Application Mobile Tasker (Android)** :
   * Importez le profil `Hercul_Voix.tsk.xml` dans Tasker pour piloter votre serveur au doigt et à la voix depuis votre smartphone.

---

## 🔐 Sécurité & Bonnes Pratiques

* Aucun secret ni clé API n'est stocké dans le dépôt (`.gitignore` strict).
* Toutes les routes sensibles de l'API sont protégées par l'en-tête `X-Hercul-Key`.
* Les données de ChromaDB, tokens Google et fichiers temporaires sont cantonnés dans les dossiers exclus `./data` et `./workspace`.

---

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.
