<?php
/**
 * 🏛️ HERCULE v3.0 — INTERFACE WEB LOCALE PHP (AUTONOME & CONNECTEUR DISCORD FACILE)
 * - Fonctionne 100% en local (avec ou sans Discord).
 * - Se connecte automatiquement au coeur Python HERCULE (port 8000) pour le Swarm Multi-Agents & les 51 outils,
 *   OU bascule automatiquement en mode PHP autonome direct (API Gemini) si le serveur Python n'est pas lancé !
 * - Inclut un Assistant de Connexion Rapide Discord (sauvegarde dans .env + générateur de lien d'invitation).
 */

header('X-Content-Type-Options: nosniff');
$rootDir = dirname(__DIR__);
$envFile = $rootDir . DIRECTORY_SEPARATOR . '.env';
$envExampleFile = $rootDir . DIRECTORY_SEPARATOR . '.env.example';
$dataDir = $rootDir . DIRECTORY_SEPARATOR . 'data';
if (!is_dir($dataDir)) {
    @mkdir($dataDir, 0777, true);
}
$historyFile = $dataDir . DIRECTORY_SEPARATOR . 'php_local_chat.json';

// Lecture du fichier .env
function loadEnvVars(string $path): array {
    if (!file_exists($path)) return [];
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $vars = [];
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#')) continue;
        $parts = explode('=', $line, 2);
        if (count($parts) === 2) {
            $vars[trim($parts[0])] = trim($parts[1]);
        }
    }
    return $vars;
}

// Écriture / Mise à jour d'une clé dans .env
function updateEnvVars(string $envPath, string $examplePath, array $updates): bool {
    $source = file_exists($envPath) ? $envPath : (file_exists($examplePath) ? $examplePath : null);
    $lines = $source ? file($source, FILE_IGNORE_NEW_LINES) : [];
    foreach ($updates as $key => $val) {
        if ($val === null || $val === '') continue;
        $found = false;
        foreach ($lines as $i => $line) {
            if (preg_match('/^\s*' . preg_quote($key, '/') . '\s*=/', $line)) {
                $lines[$i] = $key . '=' . $val;
                $found = true;
                break;
            }
        }
        if (!$found) {
            $lines[] = $key . '=' . $val;
        }
    }
    return file_put_contents($envPath, implode("\n", $lines) . "\n") !== false;
}

$env = loadEnvVars($envFile);
$geminiKey = $env['GEMINI_API_KEY'] ?? '';
$discordToken = $env['DISCORD_BOT_TOKEN'] ?? '';
$backendUrl = 'http://127.0.0.1:8000';

// =========================================================================
// 📡 GESTION DES REQUÊTES AJAX (POST JSON)
// =========================================================================
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_GET['action'])) {
    header('Content-Type: application/json; charset=utf-8');
    $action = $_GET['action'];
    $rawInput = file_get_contents('php://input');
    $payload = json_decode($rawInput, true) ?: [];

    // 1. Sauvegarder la configuration (Clé Gemini + Token Discord)
    if ($action === 'save_config') {
        $newGemini = trim($payload['gemini_api_key'] ?? '');
        $newDiscord = trim($payload['discord_bot_token'] ?? '');
        $updates = [];
        if ($newGemini !== '') $updates['GEMINI_API_KEY'] = $newGemini;
        if ($newDiscord !== '') $updates['DISCORD_BOT_TOKEN'] = $newDiscord;

        updateEnvVars($envFile, $envExampleFile, $updates);

        // Notifier également le serveur Python local s'il tourne
        $ch = curl_init($backendUrl . '/api/config/setup');
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode([
                'gemini_api_key' => $newGemini,
                'discord_bot_token' => $newDiscord
            ]),
            CURLOPT_TIMEOUT => 3
        ]);
        $pyResp = @curl_exec($ch);
        curl_close($ch);

        echo json_encode([
            'status' => 'success',
            'message' => 'Configuration sauvegardée dans .env avec succès !',
            'python_synced' => (bool)$pyResp
        ]);
        exit;
    }

    // 2. Effacer l'historique local
    if ($action === 'clear_history') {
        @unlink($historyFile);
        echo json_encode(['status' => 'success']);
        exit;
    }

    // 3. Envoyer un message à HERCULE
    if ($action === 'chat') {
        $message = trim($payload['message'] ?? '');
        if ($message === '') {
            echo json_encode(['status' => 'error', 'response' => 'Message vide.']);
            exit;
        }

        // Chargement de l'historique local PHP
        $history = file_exists($historyFile) ? (json_decode(file_get_contents($historyFile), true) ?: []) : [];
        $history[] = ['role' => 'user', 'content' => $message, 'time' => date('H:i')];

        // A) Essayer d'abord le moteur complet HERCULE v3.0 Python (Swarm + 51 outils) sur localhost:8000
        $ch = curl_init($backendUrl . '/api/chat');
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode([
                'message' => $message,
                'session_id' => 'php_local_ui',
                'fast_mode' => false
            ]),
            CURLOPT_CONNECTTIMEOUT => 2,
            CURLOPT_TIMEOUT => 90
        ]);
        $respBody = @curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($respBody && $httpCode === 200) {
            $data = json_decode($respBody, true);
            $reply = $data['response'] ?? 'Action effectuée.';
            $tools = $data['tools_executed'] ?? [];
            $history[] = [
                'role' => 'assistant',
                'content' => $reply,
                'tools' => $tools,
                'engine' => 'HERCULE Core v3.0 (Python + Swarm)',
                'time' => date('H:i')
            ];
            file_put_contents($historyFile, json_encode(array_slice($history, -40), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
            echo json_encode([
                'status' => 'success',
                'response' => $reply,
                'tools_executed' => $tools,
                'engine' => 'HERCULE Core v3.0 (Python + Swarm)'
            ]);
            exit;
        }

        // B) Fallback 100% PHP Autonome (Appel direct à l'API Gemini si Python n'est pas lancé)
        $envNow = loadEnvVars($envFile);
        $activeKey = $envNow['GEMINI_API_KEY'] ?? '';
        if ($activeKey === '' || str_contains($activeKey, 'your_')) {
            $errReply = "⚠️ Aucune clé **GEMINI_API_KEY** configurée. Cliquez sur **« ⚙️ Configurer Discord & Clé API »** en haut à droite pour coller votre clé Gemini en 1 clic !";
            echo json_encode(['status' => 'error', 'response' => $errReply]);
            exit;
        }

        $geminiUrl = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" . urlencode($activeKey);
        $contents = [];
        foreach (array_slice($history, -10) as $h) {
            $contents[] = [
                'role' => ($h['role'] === 'assistant') ? 'model' : 'user',
                'parts' => [['text' => $h['content']]]
            ];
        }

        $geminiPayload = [
            'systemInstruction' => [
                'parts' => [[
                    'text' => "Tu es HERCULE v3.0, un agent d'intelligence artificielle personnel autonome qui tourne en local sur le PC de l'utilisateur via son interface PHP locale. Date et heure : " . date('d/m/Y H:i') . ". Réponds en français de façon claire, structurée et percutante."
                ]]
            ],
            'contents' => $contents
        ];

        $chGem = curl_init($geminiUrl);
        curl_setopt_array($chGem, [
            CURLOPT_POST => true,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS => json_encode($geminiPayload),
            CURLOPT_TIMEOUT => 45
        ]);
        $gemResp = @curl_exec($chGem);
        $gemCode = curl_getinfo($chGem, CURLINFO_HTTP_CODE);
        curl_close($chGem);

        if ($gemResp && $gemCode === 200) {
            $gemData = json_decode($gemResp, true);
            $reply = $gemData['candidates'][0]['content']['parts'][0]['text'] ?? 'Réponse reçue.';
            $history[] = [
                'role' => 'assistant',
                'content' => $reply,
                'tools' => [],
                'engine' => 'Moteur PHP Autonome (Direct Gemini)',
                'time' => date('H:i')
            ];
            file_put_contents($historyFile, json_encode(array_slice($history, -40), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));
            echo json_encode([
                'status' => 'success',
                'response' => $reply,
                'tools_executed' => [],
                'engine' => 'Moteur PHP Autonome (Direct Gemini)'
            ]);
            exit;
        } else {
            echo json_encode([
                'status' => 'error',
                'response' => "⚠️ Impossible de joindre Gemini ou le serveur local HERCULE (Code HTTP $gemCode). Vérifiez votre clé API dans la configuration."
            ]);
            exit;
        }
    }
    exit;
}

// Vérification de l'état du serveur Python en arrière-plan pour l'affichage initial
$pythonOnline = false;
$chStatus = curl_init($backendUrl . '/api/status');
curl_setopt_array($chStatus, [CURLOPT_RETURNTRANSFER => true, CURLOPT_CONNECTTIMEOUT => 1, CURLOPT_TIMEOUT => 1]);
$stResp = @curl_exec($chStatus);
if ($stResp && curl_getinfo($chStatus, CURLINFO_HTTP_CODE) === 200) {
    $pythonOnline = true;
}
curl_close($chStatus);

$hasGemini = ($geminiKey !== '' && !str_contains($geminiKey, 'your_'));
$hasDiscord = ($discordToken !== '' && !str_contains($discordToken, 'your_'));
$savedHistory = file_exists($historyFile) ? (json_decode(file_get_contents($historyFile), true) ?: []) : [];
?>
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>HERCULE v3.0 — Interface Web Locale (PHP)</title>
  <style>
    :root {
      --bg-dark: #090d16;
      --bg-panel: #111827;
      --bg-card: #1e293b;
      --accent: #00f0ff;
      --accent-purple: #a855f7;
      --green: #10b981;
      --amber: #f59e0b;
      --text: #f8fafc;
      --muted: #94a3b8;
      --border: rgba(255,255,255,0.09);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background: var(--bg-dark);
      color: var(--text);
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    /* HEADER */
    header {
      background: rgba(17, 24, 39, 0.95);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 800;
      font-size: 1.25rem;
      letter-spacing: 1px;
      color: var(--accent);
    }
    .status-badges {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .badge {
      font-size: 0.78rem;
      padding: 5px 12px;
      border-radius: 999px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    .dot.green { background: var(--green); box-shadow: 0 0 8px var(--green); }
    .dot.amber { background: var(--amber); box-shadow: 0 0 8px var(--amber); }
    .btn {
      background: linear-gradient(135deg, #0284c7, #6366f1);
      color: #fff;
      border: none;
      padding: 8px 16px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.85rem;
      transition: transform 0.15s, opacity 0.15s;
    }
    .btn:hover { opacity: 0.92; transform: translateY(-1px); }
    .btn-outline {
      background: transparent;
      border: 1px solid var(--border);
      color: var(--muted);
    }
    .btn-outline:hover { color: #fff; border-color: var(--accent); }

    /* MAIN LAYOUT */
    .workspace {
      display: grid;
      grid-template-columns: 300px 1fr;
      flex: 1;
      overflow: hidden;
    }
    @media (max-width: 850px) {
      .workspace { grid-template-columns: 1fr; }
      aside { display: none; }
    }

    /* SIDEBAR */
    aside {
      background: var(--bg-panel);
      border-right: 1px solid var(--border);
      padding: 18px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      overflow-y: auto;
    }
    aside h3 {
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
      margin-bottom: 4px;
    }
    .quick-btn {
      width: 100%;
      text-align: left;
      background: var(--bg-card);
      color: var(--text);
      border: 1px solid var(--border);
      padding: 11px 13px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 0.86rem;
      transition: all 0.15s;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .quick-btn:hover {
      border-color: var(--accent);
      background: rgba(0, 240, 255, 0.08);
    }
    .info-box {
      margin-top: auto;
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 12px;
      border-radius: 10px;
      font-size: 0.8rem;
      line-height: 1.45;
      color: #d1fae5;
    }

    /* CHAT AREA */
    main {
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }
    #chat-box {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .msg {
      max-width: 82%;
      padding: 14px 18px;
      border-radius: 14px;
      line-height: 1.55;
      font-size: 0.95rem;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .msg.user {
      align-self: flex-end;
      background: linear-gradient(135deg, #2563eb, #4f46e5);
      color: #fff;
      border-bottom-right-radius: 3px;
    }
    .msg.assistant {
      align-self: flex-start;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-bottom-left-radius: 3px;
    }
    .msg-header {
      font-size: 0.72rem;
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 6px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
    }
    .tool-pill {
      display: inline-block;
      margin-top: 8px;
      margin-right: 6px;
      padding: 3px 9px;
      font-size: 0.74rem;
      border-radius: 6px;
      background: rgba(168, 85, 247, 0.18);
      border: 1px solid rgba(168, 85, 247, 0.45);
      color: #e9d5ff;
    }

    /* INPUT BAR */
    .input-bar {
      padding: 16px 24px;
      background: var(--bg-panel);
      border-top: 1px solid var(--border);
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .input-bar input {
      flex: 1;
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: #fff;
      padding: 13px 16px;
      border-radius: 10px;
      font-size: 0.95rem;
      outline: none;
    }
    .input-bar input:focus { border-color: var(--accent); }

    /* MODAL CONFIGURATION DISCORD & API */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.75);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
      padding: 16px;
    }
    .modal-backdrop.open { display: flex; }
    .modal {
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: 16px;
      max-width: 560px;
      width: 100%;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .modal h2 { color: var(--accent); font-size: 1.2rem; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    .form-group label { font-size: 0.85rem; font-weight: 600; color: var(--text); }
    .form-group small { font-size: 0.76rem; color: var(--muted); }
    .form-group input {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: #fff;
      padding: 10px 12px;
      border-radius: 8px;
      font-size: 0.9rem;
    }
    .steps-card {
      background: rgba(59, 130, 246, 0.1);
      border: 1px solid rgba(59, 130, 246, 0.3);
      border-radius: 10px;
      padding: 12px;
      font-size: 0.8rem;
      line-height: 1.5;
      color: #dbeafe;
    }
    .steps-card a { color: var(--accent); text-decoration: underline; }
  </style>
</head>
<body>

  <!-- BARRE SUPÉRIEURE -->
  <header>
    <div class="brand">
      <span>🏛️ HERCULE v3.0</span>
      <span style="font-size:0.75rem;color:var(--muted);font-weight:500;">Interface Web Locale PHP</span>
    </div>

    <div class="status-badges">
      <div class="badge" title="Moteur d'exécution">
        <span class="dot <?php echo $pythonOnline ? 'green' : 'amber'; ?>"></span>
        <span><?php echo $pythonOnline ? 'Coeur Python + Swarm Actif (Port 8000)' : 'Mode PHP Autonome Actif'; ?></span>
      </div>

      <div class="badge" title="État de la clé Gemini">
        <span class="dot <?php echo $hasGemini ? 'green' : 'amber'; ?>"></span>
        <span>Gemini : <?php echo $hasGemini ? 'Configuré' : 'Clé requise'; ?></span>
      </div>

      <div class="badge" title="État du Bot Discord">
        <span class="dot <?php echo $hasDiscord ? 'green' : 'amber'; ?>"></span>
        <span>Discord : <?php echo $hasDiscord ? 'Token Prêt' : 'Optionnel (Mode Web Actif)'; ?></span>
      </div>

      <button class="btn" onclick="openModal()">⚙️ Connecter Discord & Clé API</button>
      <button class="btn btn-outline" onclick="clearChat()">🗑️ Effacer</button>
    </div>
  </header>

  <!-- ESPACE DE TRAVAIL -->
  <div class="workspace">
    <!-- BARRE LATÉRALE : MISSIONS EN 1 CLIC -->
    <aside>
      <h3>🐝 Missions Multi-Agents & Continues</h3>
      <button class="quick-btn" onclick="sendQuickPrompt('Hercule, déploie l\'escouade multi-agents (Swarm) pour analyser et structurer ce projet : ')">
        <span>🐝</span> <span>Déployer l'Escouade Swarm</span>
      </button>
      <button class="quick-btn" onclick="sendQuickPrompt('Hercule, crée un nouvel objectif continu en 4 étapes : ')">
        <span>🔄</span> <span>Nouvel Objectif Continu 24/7</span>
      </button>
      <button class="quick-btn" onclick="sendQuickPrompt('Hercule, montre-moi la liste et la progression de mes objectifs continus')">
        <span>📊</span> <span>Progression des Objectifs</span>
      </button>
      <button class="quick-btn" onclick="sendQuickPrompt('Hercule, exécute la prochaine étape de mon objectif continu')">
        <span>⚡</span> <span>Avancer d'une Étape</span>
      </button>
      <button class="quick-btn" onclick="sendQuickPrompt('Hercule, liste toutes tes compétences auto-évolutives et leçons')">
        <span>🧬</span> <span>Catalogue Skill Forge</span>
      </button>

      <h3 style="margin-top:10px;">🛠️ Outils du Quotidien</h3>
      <button class="quick-btn" onclick="sendQuickPrompt('Hercule, fais mon briefing matinal complet')">
        <span>☀️</span> <span>Briefing Matinal</span>
      </button>
      <button class="quick-btn" onclick="sendQuickPrompt('Hercule, suis mon colis : ')">
        <span>📦</span> <span>Suivre un Colis (17TRACK)</span>
      </button>
      <button class="quick-btn" onclick="sendQuickPrompt('Hercule, vérifie l\'état de santé du système local (CPU, RAM, Disque)')">
        <span>🖥️</span> <span>Santé du PC Local</span>
      </button>

      <div class="info-box">
        💡 <strong>Sans Discord ? Aucun souci !</strong><br>
        Cette interface PHP locale remplace intégralement Discord sur votre PC. Et si vous souhaitez aussi brancher Discord plus tard, cliquez sur <strong>« Connecter Discord & Clé API »</strong> !
      </div>
    </aside>

    <!-- ZONE DE DISCUSSION -->
    <main>
      <div id="chat-box">
        <div class="msg assistant">
          <div class="msg-header">
            <span>🏛️ HERCULE v3.0</span>
            <span>Prêt en Local</span>
          </div>
          <div>Bonjour ! Je suis <strong>Hercule</strong>, ton agent autonome multi-agents local. Tu peux me parler directement ici en PHP (sans avoir besoin de Discord) ou connecter ton bot Discord en 1 clic via le bouton en haut à droite. Quelle est notre mission ?</div>
        </div>

        <?php foreach ($savedHistory as $item): ?>
          <div class="msg <?php echo $item['role'] === 'user' ? 'user' : 'assistant'; ?>">
            <div class="msg-header">
              <span><?php echo $item['role'] === 'user' ? '👤 VOUS' : '🏛️ HERCULE'; ?></span>
              <span><?php echo htmlspecialchars($item['time'] ?? ''); ?></span>
            </div>
            <div><?php echo nl2br(htmlspecialchars($item['content'] ?? '')); ?></div>
            <?php if (!empty($item['tools'])): ?>
              <div>
                <?php foreach ($item['tools'] as $t): ?>
                  <span class="tool-pill">⚡ <?php echo htmlspecialchars($t['tool'] ?? 'outil'); ?></span>
                <?php endforeach; ?>
              </div>
            <?php endif; ?>
          </div>
        <?php endforeach; ?>
      </div>

      <form class="input-bar" onsubmit="handleSend(event)">
        <button type="button" class="btn btn-outline" onclick="toggleVoiceInput()" id="mic-btn" title="Dictée vocale">🎙️</button>
        <input type="text" id="chat-input" placeholder="Parlez à Hercule (ex: Déploie l'escouade multi-agents, suis mon colis, crée un objectif...)" autocomplete="off">
        <button type="submit" class="btn" id="send-btn">Envoyer 🚀</button>
      </form>
    </main>
  </div>

  <!-- MODAL CONNEXION FACILE DISCORD & GEMINI -->
  <div class="modal-backdrop" id="config-modal">
    <div class="modal">
      <h2>⚙️ Connexion Facile : Gemini & Discord (En 1 Clic)</h2>

      <div class="form-group">
        <label>1. Clé API Google Gemini (Obligatoire pour l'IA)</label>
        <small>Obtenez une clé gratuite sur <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:var(--accent)">Google AI Studio</a></small>
        <input type="password" id="cfg-gemini" placeholder="AIzaSy... ou votre clé Gemini" value="<?php echo htmlspecialchars($hasGemini ? $geminiKey : ''); ?>">
      </div>

      <div class="form-group">
        <label>2. Token du Bot Discord (Optionnel — laissez vide si vous utilisez uniquement cette interface PHP)</label>
        <input type="password" id="cfg-discord" placeholder="MTUz... (Token de votre bot Discord)" value="<?php echo htmlspecialchars($hasDiscord ? $discordToken : ''); ?>">
      </div>

      <div class="steps-card">
        <strong>🤖 Comment connecter Discord en 30 secondes :</strong><br>
        1. Ouvrez le <a href="https://discord.com/developers/applications" target="_blank">Portail Développeur Discord</a> et cliquez sur <em>New Application</em> (nommez-la <strong>Hercule</strong>).<br>
        2. Allez dans l'onglet <strong>Bot</strong> ➔ cliquez sur <em>Reset Token</em>, copiez le Token et collez-le ci-dessus.<br>
        3. Plus bas dans <strong>Bot</strong>, activez <strong>Message Content Intent</strong>.<br>
        4. Entrez votre <em>Application ID</em> ci-dessous pour générer le lien d'invitation en 1 clic :
        <div style="display:flex;gap:8px;margin-top:8px;">
          <input type="text" id="discord-client-id" placeholder="ID Application Discord (ex: 123456789012345678)" style="flex:1;padding:6px 10px;border-radius:6px;border:1px solid var(--border);background:var(--bg-card);color:#fff;">
          <button type="button" class="btn" onclick="openDiscordInvite()">Inviter le Bot 🔗</button>
        </div>
      </div>

      <div id="cfg-feedback" style="font-size:0.85rem;color:var(--green);display:none;"></div>

      <div style="display:flex;justify-content:flex-end;gap:10px;">
        <button type="button" class="btn btn-outline" onclick="closeModal()">Fermer</button>
        <button type="button" class="btn" onclick="saveConfig()">💾 Enregistrer & Activer</button>
      </div>
    </div>
  </div>

  <script>
    const chatBox = document.getElementById('chat-box');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    chatBox.scrollTop = chatBox.scrollHeight;

    function openModal() {
      document.getElementById('config-modal').classList.add('open');
    }
    function closeModal() {
      document.getElementById('config-modal').classList.remove('open');
    }

    function openDiscordInvite() {
      const clientId = document.getElementById('discord-client-id').value.trim();
      if (!clientId) {
        alert("Entrez l'Application ID (Client ID) de votre application Discord pour générer le lien d'invitation.");
        return;
      }
      const inviteUrl = `https://discord.com/oauth2/authorize?client_id=${encodeURIComponent(clientId)}&permissions=274878221312&scope=bot`;
      window.open(inviteUrl, '_blank');
    }

    async function saveConfig() {
      const gemini = document.getElementById('cfg-gemini').value.trim();
      const discord = document.getElementById('cfg-discord').value.trim();
      const fb = document.getElementById('cfg-feedback');
      fb.style.display = 'block';
      fb.textContent = '⏳ Enregistrement en cours...';

      try {
        const res = await fetch('?action=save_config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ gemini_api_key: gemini, discord_bot_token: discord })
        });
        const data = await res.json();
        fb.textContent = '✅ ' + (data.message || 'Enregistré !');
        setTimeout(() => location.reload(), 900);
      } catch (e) {
        fb.style.color = '#ef4444';
        fb.textContent = '❌ Erreur : ' + e.message;
      }
    }

    async function clearChat() {
      await fetch('?action=clear_history', { method: 'POST' });
      location.reload();
    }

    function sendQuickPrompt(text) {
      chatInput.value = text;
      chatInput.focus();
    }

    function appendMessage(role, text, tools = [], engine = '') {
      const div = document.createElement('div');
      div.className = 'msg ' + (role === 'user' ? 'user' : 'assistant');
      const now = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

      let toolsHtml = '';
      if (tools && tools.length > 0) {
        toolsHtml = '<div>' + tools.map(t => `<span class="tool-pill">⚡ ${t.tool}</span>`).join('') + '</div>';
      }

      div.innerHTML = `
        <div class="msg-header">
          <span>${role === 'user' ? '👤 VOUS' : '🏛️ HERCULE'}</span>
          <span>${engine ? engine + ' • ' : ''}${now}</span>
        </div>
        <div class="msg-body"></div>
        ${toolsHtml}
      `;
      div.querySelector('.msg-body').textContent = text;
      chatBox.appendChild(div);
      chatBox.scrollTop = chatBox.scrollHeight;
      return div;
    }

    async function handleSend(e) {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;

      appendMessage('user', text);
      chatInput.value = '';
      sendBtn.disabled = true;

      const loader = appendMessage('assistant', '🔮 Hercule réfléchit et coordonne ses outils...');

      try {
        const res = await fetch('?action=chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text })
        });
        const data = await res.json();
        loader.remove();
        appendMessage('assistant', data.response || 'Action terminée.', data.tools_executed || [], data.engine || '');
      } catch (err) {
        loader.querySelector('.msg-body').textContent = '❌ Erreur de connexion locale : ' + err.message;
      } finally {
        sendBtn.disabled = false;
      }
    }

    // Reconnaissance vocale navigateur
    function toggleVoiceInput() {
      const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRec) {
        alert("La reconnaissance vocale nécessite Chrome ou Edge.");
        return;
      }
      const rec = new SpeechRec();
      rec.lang = 'fr-FR';
      rec.onresult = (e) => {
        chatInput.value = e.results[0][0].transcript;
      };
      rec.start();
    }
  </script>
</body>
</html>
