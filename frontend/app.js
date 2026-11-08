/**
 * HERCUL NEURAL CORE 3D - Moteur d'Interaction 3D & HUD
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const container = document.getElementById('canvas-container');
  const chatForm = document.getElementById('chat-form');
  const userInput = document.getElementById('user-input');
  const messagesContainer = document.getElementById('messages-container');
  const clearChatBtn = document.getElementById('clear-chat-btn');
  const secretKeyInput = document.getElementById('secret-key-input');
  const ttsHudBtn = document.getElementById('tts-hud-btn');
  const micBtn = document.getElementById('mic-btn');
  const dockToggle = document.getElementById('dock-toggle');
  const cyberDock = document.getElementById('cyber-dock');
  const voiceWaves = document.getElementById('voice-waves');
  
  const hudMemoryCount = document.getElementById('hud-memory-count');
  const hudTokens = document.getElementById('hud-tokens');
  const coreStatus = document.getElementById('core-status');

  const nodeInspector = document.getElementById('node-inspector');
  const inspectorTitle = document.getElementById('inspector-title');
  const inspectorContent = document.getElementById('inspector-content');
  const closeInspectorBtn = document.getElementById('close-inspector-btn');
  const camBtns = document.querySelectorAll('.cam-target-btn');

  // Audio State
  let ttsEnabled = true;
  let isSpeaking = false;
  let isListening = false;
  let recognition = null;

  // Persistance de la clé secrète
  const savedKey = localStorage.getItem('hercul_api_key') || '';
  secretKeyInput.value = savedKey;
  secretKeyInput.addEventListener('input', () => {
    localStorage.setItem('hercul_api_key', secretKeyInput.value.trim());
    fetchTelemetry();
  });

  function getHeaders() {
    return {
      'Content-Type': 'application/json',
      'X-Hercul-Key': secretKeyInput.value.trim()
    };
  }

  // Toggle du Dock terminal
  dockToggle.addEventListener('click', (e) => {
    if (e.target.id === 'clear-chat-btn') return;
    cyberDock.classList.toggle('collapsed');
  });

  clearChatBtn.addEventListener('click', () => {
    messagesContainer.innerHTML = '';
  });

  closeInspectorBtn.addEventListener('click', () => {
    nodeInspector.classList.add('hidden');
  });

  // =================================================================
  // 🌌 MOTEUR 3D THREE.JS SANS DÉPENDANCE EXTERNE CRITIQUE
  // =================================================================

  let scene, camera, renderer;
  let brainGroup, nucleus, ring1, ring2;
  const nodes = [];
  let targetCamPos = { x: 0, y: 12, z: 40 };

  // Mouse interaction
  let isDragging = false;
  let prevMousePos = { x: 0, y: 0 };
  let spherical = { radius: 42, theta: 0, phi: Math.PI / 2.8 };

  function initThree() {
    if (!window.THREE) {
      console.warn("Three.js non chargé.");
      return;
    }

    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x040812, 0.015);

    camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
    updateCameraFromSpherical();

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // Lumières
    const ambLight = new THREE.AmbientLight(0x00f0ff, 0.7);
    scene.add(ambLight);

    const pLight1 = new THREE.PointLight(0x00f0ff, 2.5, 90);
    pLight1.position.set(0, 0, 0);
    scene.add(pLight1);

    const pLight2 = new THREE.PointLight(0xc084fc, 1.8, 80);
    pLight2.position.set(15, 20, 15);
    scene.add(pLight2);

    // 1. Étoiles
    createStars();

    // 2. Cœur Neuronal Central
    createBrainCore();

    // 3. Nœuds Orbitaux
    createNodes();

    // Resize
    window.addEventListener('resize', onResize);

    // Contrôles souris personnalisés et fiables
    setupMouseControls();
  }

  function updateCameraFromSpherical() {
    camera.position.x = spherical.radius * Math.sin(spherical.phi) * Math.sin(spherical.theta);
    camera.position.y = spherical.radius * Math.cos(spherical.phi);
    camera.position.z = spherical.radius * Math.sin(spherical.phi) * Math.cos(spherical.theta);
    camera.lookAt(0, 0, 0);
  }

  function setupMouseControls() {
    window.addEventListener('mousedown', (e) => {
      if (e.target.closest('.top-nav') || e.target.closest('.cyber-dock') || e.target.closest('.inspector-panel') || e.target.closest('.camera-panel')) return;
      isDragging = true;
      prevMousePos = { x: e.clientX, y: e.clientY };
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - prevMousePos.x;
      const dy = e.clientY - prevMousePos.y;

      spherical.theta -= dx * 0.006;
      spherical.phi -= dy * 0.006;
      spherical.phi = Math.max(0.2, Math.min(Math.PI - 0.2, spherical.phi));

      prevMousePos = { x: e.clientX, y: e.clientY };
      updateCameraFromSpherical();
    });

    window.addEventListener('mouseup', () => { isDragging = false; });

    // Zoom molette
    window.addEventListener('wheel', (e) => {
      if (e.target.closest('.messages-log') || e.target.closest('.inspector-content')) return;
      spherical.radius += e.deltaY * 0.04;
      spherical.radius = Math.max(12, Math.min(90, spherical.radius));
      updateCameraFromSpherical();
    });

    // Clic sur nœud (Raycasting)
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    window.addEventListener('click', (e) => {
      if (e.target.closest('.top-nav') || e.target.closest('.cyber-dock') || e.target.closest('.inspector-panel') || e.target.closest('.camera-panel')) return;

      mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
      raycaster.setFromCamera(mouse, camera);

      const meshes = nodes.map(n => n.mesh);
      const hits = raycaster.intersectObjects(meshes);
      if (hits.length > 0) {
        const id = hits[0].object.userData.id;
        openInspector(id);
      }
    });
  }

  function createStars() {
    const geo = new THREE.BufferGeometry();
    const count = 1000;
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count * 3; i += 3) {
      pos[i] = (Math.random() - 0.5) * 220;
      pos[i + 1] = (Math.random() - 0.5) * 220;
      pos[i + 2] = (Math.random() - 0.5) * 220;
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    const mat = new THREE.PointsMaterial({ color: 0x38bdf8, size: 0.7, transparent: true, opacity: 0.65 });
    const stars = new THREE.Points(geo, mat);
    scene.add(stars);
  }

  function createBrainCore() {
    brainGroup = new THREE.Group();

    // Noyau maillé
    const nGeo = new THREE.IcosahedronGeometry(4.5, 3);
    const nMat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff,
      emissive: 0x00f0ff,
      emissiveIntensity: 0.6,
      wireframe: true
    });
    nucleus = new THREE.Mesh(nGeo, nMat);
    brainGroup.add(nucleus);

    // Particules synaptiques
    const pCount = 600;
    const pGeo = new THREE.BufferGeometry();
    const pPos = new Float32Array(pCount * 3);
    for (let i = 0; i < pCount * 3; i += 3) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const r = 4.8 + Math.random() * 3;
      pPos[i] = r * Math.sin(phi) * Math.cos(theta);
      pPos[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      pPos[i + 2] = r * Math.cos(phi);
    }
    pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));
    const pMat = new THREE.PointsMaterial({ color: 0x38bdf8, size: 0.4, transparent: true, opacity: 0.85 });
    const pMesh = new THREE.Points(pGeo, pMat);
    brainGroup.add(pMesh);

    // Anneaux orbitaux
    const rGeo = new THREE.TorusGeometry(8.5, 0.08, 16, 90);
    const rMat1 = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.5 });
    ring1 = new THREE.Mesh(rGeo, rMat1);
    ring1.rotation.x = Math.PI / 3;
    brainGroup.add(ring1);

    const rMat2 = new THREE.MeshBasicMaterial({ color: 0xc084fc, transparent: true, opacity: 0.4 });
    ring2 = new THREE.Mesh(rGeo, rMat2);
    ring2.rotation.y = Math.PI / 3.5;
    ring2.scale.set(1.2, 1.2, 1.2);
    brainGroup.add(ring2);

    scene.add(brainGroup);
  }

  function createNodes() {
    const list = [
      { id: 'memory', name: 'Mémoire', color: 0xc084fc, dist: 18, speed: 0.007, angle: 0 },
      { id: 'browser', name: 'Navigateur', color: 0x00f0ff, dist: 22, speed: 0.005, angle: Math.PI / 2 },
      { id: 'tools', name: 'Agent & OS', color: 0xf59e0b, dist: 26, speed: 0.004, angle: Math.PI },
      { id: 'tasker', name: 'Tasker', color: 0x10b981, dist: 20, speed: 0.006, angle: Math.PI * 1.5 }
    ];

    list.forEach(item => {
      const group = new THREE.Group();
      const sGeo = new THREE.SphereGeometry(1.6, 24, 24);
      const sMat = new THREE.MeshStandardMaterial({
        color: item.color,
        emissive: item.color,
        emissiveIntensity: 0.7,
        roughness: 0.3
      });
      const mesh = new THREE.Mesh(sGeo, sMat);
      mesh.userData = item;
      group.add(mesh);

      const ringGeo = new THREE.TorusGeometry(2.3, 0.05, 12, 40);
      const ringMat = new THREE.MeshBasicMaterial({ color: item.color, transparent: true, opacity: 0.6 });
      const r = new THREE.Mesh(ringGeo, ringMat);
      r.rotation.x = Math.PI / 2;
      group.add(r);

      scene.add(group);
      nodes.push({ group, mesh, data: item });
    });
  }

  function onResize() {
    if (!camera || !renderer) return;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  }

  function animate() {
    requestAnimationFrame(animate);
    const time = performance.now() * 0.001;

    if (brainGroup) {
      brainGroup.rotation.y = time * 0.15;
      if (ring1) ring1.rotation.z = time * 0.2;
      if (ring2) ring2.rotation.x = -time * 0.18;

      const scale = isSpeaking ? (1 + Math.sin(time * 12) * 0.07) : (1 + Math.sin(time * 2) * 0.02);
      if (nucleus) nucleus.scale.set(scale, scale, scale);
    }

    nodes.forEach(n => {
      n.data.angle += n.data.speed;
      n.group.position.x = Math.cos(n.data.angle) * n.data.dist;
      n.group.position.z = Math.sin(n.data.angle) * n.data.dist;
      n.group.position.y = Math.sin(n.data.angle * 2) * 2.5;
      n.group.rotation.y += 0.01;
    });

    if (renderer && scene && camera) {
      renderer.render(scene, camera);
    }
  }

  // =================================================================
  // 🎛️ NAVIGATION ET INSPECTEUR HOLOGRAPHIQUE
  // =================================================================

  camBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      camBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const target = btn.getAttribute('data-target');

      if (target === 'core') {
        spherical = { radius: 42, theta: 0, phi: Math.PI / 2.8 };
        updateCameraFromSpherical();
        nodeInspector.classList.add('hidden');
      } else {
        openInspector(target);
      }
    });
  });

  async function openInspector(nodeId) {
    nodeInspector.classList.remove('hidden');

    if (nodeId === 'memory') {
      inspectorTitle.textContent = "🧠 MÉMOIRE PERMANENTE & PROFIL";
      inspectorContent.innerHTML = "<p>Chargement des connaissances...</p>";

      try {
        const res = await fetch('/api/memory/profile', { headers: getHeaders() });
        const data = await res.json();
        const facts = data.facts || [];
        const prefs = data.user_preferences || {};

        let html = `
          <div class="node-card">
            <h4>PROFIL</h4>
            <p><strong>Nom :</strong> ${escapeHtml(prefs.name || 'Nathan')}</p>
            <p><strong>Environnement :</strong> ${escapeHtml(prefs.environment || 'VPS Debian / Tasker')}</p>
          </div>
          <div class="node-card">
            <h4>FAITS APPRIS SILENCIEUSEMENT (${facts.length})</h4>
        `;
        if (facts.length === 0) {
          html += `<p style="color:var(--text-muted)">Hercul apprendra de vos conversations automatiquement.</p>`;
        } else {
          facts.forEach(f => {
            html += `<p style="margin-bottom:6px">• ${escapeHtml(f.fact)}</p>`;
          });
        }
        html += `</div>`;
        inspectorContent.innerHTML = html;
      } catch (e) {
        inspectorContent.innerHTML = `<p style="color:var(--neon-red)">Erreur de chargement mémoire.</p>`;
      }

    } else if (nodeId === 'browser') {
      inspectorTitle.textContent = "🌐 NAVIGATEUR PLAYWRIGHT";
      inspectorContent.innerHTML = `
        <div class="node-card">
          <h4>ÉTAT DU NAVIGATEUR</h4>
          <p>Moteur Chromium autonome prêt pour l'interaction web.</p>
        </div>
        <div class="node-card">
          <h4>DERNIÈRE INSPECTION VISUELLE</h4>
          <div id="live-browser-view" style="color:var(--text-muted)">Aucune capture récente. Demandez à Hercul de visiter une page web !</div>
        </div>
      `;

    } else if (nodeId === 'tools') {
      inspectorTitle.textContent = "⚡ AGENT REACT & OUTILS";
      inspectorContent.innerHTML = `
        <div class="node-card">
          <h4>OUTILS DISPONIBLES</h4>
          <p>• <strong>web_search</strong> : Recherche Niv 1</p>
          <p>• <strong>fetch_page_content</strong> : Extraction HTTP</p>
          <p>• <strong>browser_navigate/click/type</strong> : Playwright</p>
          <p>• <strong>execute_command</strong> : Terminal Workspace</p>
          <p>• <strong>write/read_file</strong> : Fichiers</p>
        </div>
      `;

    } else if (nodeId === 'tasker') {
      inspectorTitle.textContent = "📱 PASSERELLE MOBILE TASKER";
      inspectorContent.innerHTML = `
        <div class="node-card">
          <h4>URL TASKER (GET)</h4>
          <pre style="background:rgba(0,0,0,0.5);padding:8px;border-radius:4px;font-size:0.78rem;color:var(--neon-green)">GET http://${window.location.host}/api/tasker/ask?q=%VOICE&key=VOTRE_CLE_SECRETE</pre>
        </div>
      `;
    }
  }

  // =================================================================
  // 🎙️ SYNTHÈSE & RECONNAISSANCE VOCALE
  // =================================================================

  function speak(text) {
    if (!ttsEnabled || !window.speechSynthesis) return;

    window.speechSynthesis.cancel();
    const clean = text
      .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
      .replace(/\*\*|\*|`|#/g, '')
      .trim();

    if (!clean) return;

    const u = new SpeechSynthesisUtterance(clean);
    u.lang = 'fr-FR';
    u.rate = 1.05;

    const voices = window.speechSynthesis.getVoices();
    const frVoice = voices.find(v => v.lang.startsWith('fr'));
    if (frVoice) u.voice = frVoice;

    u.onstart = () => {
      isSpeaking = true;
      voiceWaves.classList.remove('hidden');
    };
    u.onend = () => {
      isSpeaking = false;
      voiceWaves.classList.add('hidden');
    };
    u.onerror = () => {
      isSpeaking = false;
      voiceWaves.classList.add('hidden');
    };

    window.speechSynthesis.speak(u);
  }

  ttsHudBtn.addEventListener('click', () => {
    ttsEnabled = !ttsEnabled;
    if (ttsEnabled) {
      ttsHudBtn.classList.remove('muted');
      ttsHudBtn.innerHTML = '<span class="btn-icon">🔊</span> VOIX ACTIVE';
    } else {
      window.speechSynthesis.cancel();
      ttsHudBtn.classList.add('muted');
      ttsHudBtn.innerHTML = '<span class="btn-icon">🔇</span> VOIX COUPÉE';
      voiceWaves.classList.add('hidden');
      isSpeaking = false;
    }
  });

  const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRec) {
    recognition = new SpeechRec();
    recognition.lang = 'fr-FR';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('listening');
      if (window.speechSynthesis) window.speechSynthesis.cancel();
    };

    recognition.onresult = (e) => {
      let t = '';
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        t += e.results[i][0].transcript;
      }
      userInput.value = t;
    };

    recognition.onend = () => {
      isListening = false;
      micBtn.classList.remove('listening');
      if (userInput.value.trim().length > 0) {
        chatForm.dispatchEvent(new Event('submit'));
      }
    };

    recognition.onerror = () => {
      isListening = false;
      micBtn.classList.remove('listening');
    };

    micBtn.addEventListener('click', () => {
      if (isListening) recognition.stop();
      else recognition.start();
    });
  }

  // =================================================================
  // 💬 CHAT & EXÉCUTION
  // =================================================================

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = userInput.value.trim();
    if (!text) return;

    appendMsg('user', text);
    userInput.value = '';

    const thinking = appendMsg('assistant', '🧠 Analyse et exécution en cours...');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ message: text, session_id: 'web_session' })
      });

      if (!res.ok) {
        const err = await res.json();
        thinking.querySelector('.log-body').textContent = `❌ Erreur : ${err.detail || 'Problème de connexion'}`;
        return;
      }

      const data = await res.json();

      let toolsHtml = '';
      if (data.tools_executed && data.tools_executed.length > 0) {
        data.tools_executed.forEach(t => {
          toolsHtml += `<div class="tool-pill">⚡ Action : ${escapeHtml(t.tool)}</div>`;
          if (t.result && t.result.filename) {
            const v = document.getElementById('live-browser-view');
            if (v) v.innerHTML = `<img src="/screenshots/${t.result.filename}" style="width:100%;border-radius:4px;border:1px solid var(--neon-cyan)">`;
          }
        });
      }

      thinking.querySelector('.log-body').innerHTML = `
        ${toolsHtml}
        <div>${escapeHtml(data.response)}</div>
      `;

      speak(data.response);
      fetchTelemetry();
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

    } catch (err) {
      thinking.querySelector('.log-body').textContent = `❌ Erreur réseau : ${err.message}`;
    }
  });

  function appendMsg(role, text) {
    const d = document.createElement('div');
    d.className = `log-entry ${role}`;
    d.innerHTML = `
      <span class="log-sender">${role === 'user' ? 'NATHAN :' : 'HERCUL :'}</span>
      <span class="log-body">${escapeHtml(text)}</span>
    `;
    messagesContainer.appendChild(d);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return d;
  }

  function escapeHtml(str) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(str).replace(/[&<>"']/g, s => map[s]);
  }

  async function fetchTelemetry() {
    try {
      const res = await fetch('/api/memory/stats', { headers: getHeaders() });
      if (res.ok) {
        const s = await res.json();
        hudMemoryCount.textContent = (s.profile_facts_count || 0) + (s.episodic_memories_count || 0);
        coreStatus.innerHTML = '<span class="dot"></span> SYNCHRONISÉ';
      }
    } catch (e) {
      coreStatus.innerHTML = '<span class="dot" style="background:var(--neon-red)"></span> DÉCONNECTÉ';
    }
  }

  initThree();
  animate();
  fetchTelemetry();
  setInterval(fetchTelemetry, 15000);
});
