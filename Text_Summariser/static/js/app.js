/**
 * URIAS AI TEXT SUMMARIZER - CLIENT CONTROLLER
 * Real-time SPA logic, multi-engine routing, URL scraping, audio playback & export
 */

document.addEventListener('DOMContentLoaded', () => {
  // State
  const state = {
    engine: 'local', // 'local' | 'gemini'
    format: 'paragraph', // 'paragraph' | 'bullets' | 'tldr'
    ratio: 0.35,
    geminiApiKey: localStorage.getItem('urias_gemini_api_key') || '',
    currentSummary: '',
    speechSynth: window.speechSynthesis || null,
    speechUtterance: null,
    isSpeaking: false
  };

  // Sample Presets
  const SAMPLES = {
    ai: `Artificial intelligence and machine learning platforms have transitioned from academic research laboratories into mission-critical production infrastructure across global enterprises. Modern deep learning architectures, such as deep convolutional vision networks fused with recurrent Long Short-Term Memory units, have demonstrated unprecedented diagnostic capabilities in computational pathology and behavioral phenotyping. Concurrently, privacy-preserving techniques such as federated learning enable distributed nodes to collaboratively train neural networks without transmitting raw decentralized training data to a central repository. By combining federated averaging rounds with homomorphic encryption, institutions can mathematically guarantee zero gradient leakage while achieving competitive convergence and high area-under-the-ROC-curve precision. As organizations scale these heterogeneous multi-cloud pipelines, engineering robust low-latency inference gateways becomes vital to ensure zero downtime and cost-effective accelerator resource utilization.`,
    
    tech: `Quantum computing hardware companies announced a major leap in fault-tolerant logical qubit stabilization this week. Researchers demonstrated quantum error-correction codes capable of suppressing physical decoherence noise by two orders of magnitude across superconducting multi-qubit processor topologies. This breakthrough paves the way for commercial quantum simulation of complex molecular binding affinities and catalytic chemical reactions, tasks that remain intractable for classical supercomputers. Silicon manufacturing consortiums have pledged over $4 billion to construct specialized cryogenic fabrication cleanrooms capable of mass-producing quantum interconnects. While practical universal quantum advantage remains several milestones away, industry experts predict initial domain-specific quantum accelerators will integrate directly into cloud datacenters by late 2028.`,
    
    business: `The global transition toward sovereign enterprise AI infrastructure has accelerated corporate cloud capital expenditures in Q3. Enterprise leadership teams report that data privacy compliance, regulatory governance, and predictable latency SLAs are now the foremost criteria driving infrastructure procurement. Consequently, hybrid multi-cloud deployment patterns—combining localized on-premise compute nodes with high-throughput cloud accelerators—have become the preferred architecture for Fortune 500 engineering teams. Financial forecasting models project a 34% annual growth rate in serverless edge inference services through 2030. To optimize operational margins, engineering leaders must prioritize continuous model quantization, intelligent request batching, and automated elastic autoscaling policies across their distributed platform workloads.`
  };

  // DOM Elements
  const sourceText = document.getElementById('source-text');
  const wordCount = document.getElementById('word-count');
  const charCount = document.getElementById('char-count');
  const readEstimate = document.getElementById('read-estimate');
  const clearTextBtn = document.getElementById('clear-text-btn');

  const engineBtnLocal = document.getElementById('engine-btn-local');
  const engineBtnGemini = document.getElementById('engine-btn-gemini');
  const formatChips = document.querySelectorAll('.format-chip');
  const ratioSlider = document.getElementById('ratio-slider');
  const ratioDisplay = document.getElementById('ratio-display');
  const densityControlGroup = document.getElementById('density-control-group');

  const summarizeBtn = document.getElementById('summarize-btn');
  const btnSpinner = document.getElementById('btn-spinner');

  const summaryContentBox = document.getElementById('summary-content-box');
  const emptyState = document.getElementById('empty-state');
  const skeletonView = document.getElementById('skeleton-view');
  const summaryText = document.getElementById('summary-text');
  const badgeEngine = document.getElementById('badge-engine');
  const metricsRibbon = document.getElementById('metrics-ribbon');
  const metricCompression = document.getElementById('metric-compression');
  const metricTimeSaved = document.getElementById('metric-time-saved');
  const metricWords = document.getElementById('metric-words');
  const actionToolbar = document.getElementById('action-toolbar');

  const copySummaryBtn = document.getElementById('copy-summary-btn');
  const readAloudBtn = document.getElementById('read-aloud-btn');
  const speechBtnLabel = document.getElementById('speech-btn-label');
  const downloadSummaryBtn = document.getElementById('download-summary-btn');

  const keywordsPanel = document.getElementById('keywords-panel');
  const keywordsChips = document.getElementById('keywords-chips');

  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  const urlInput = document.getElementById('url-input');
  const fetchUrlBtn = document.getElementById('fetch-url-btn');
  const urlStatus = document.getElementById('url-status');

  const fileDropZone = document.getElementById('file-drop-zone');
  const fileInput = document.getElementById('file-input');
  const browseFileBtn = document.getElementById('browse-file-btn');
  const fileInfo = document.getElementById('file-info');

  const openSettingsBtn = document.getElementById('open-settings-btn');
  const closeSettingsBtn = document.getElementById('close-settings-btn');
  const settingsModal = document.getElementById('settings-modal');
  const geminiApiKeyInput = document.getElementById('gemini-api-key');
  const saveSettingsBtn = document.getElementById('save-settings-btn');
  const modalCancelBtn = document.getElementById('modal-cancel-btn');

  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const themeIcon = document.getElementById('theme-icon');
  const themeText = document.getElementById('theme-text');
  const themeRadios = document.querySelectorAll('input[name="theme-pref"]');

  // Theme Controller
  function applyTheme(theme, showNotification = false) {
    let effectiveTheme = theme;
    if (theme === 'system') {
      const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      effectiveTheme = prefersDark ? 'dark' : 'light';
    }

    document.documentElement.setAttribute('data-theme', effectiveTheme);
    localStorage.setItem('urias_theme', theme);

    if (effectiveTheme === 'dark') {
      if (themeIcon) themeIcon.textContent = '🌙';
      if (themeText) themeText.textContent = 'Dark Mode';
      if (showNotification) showToast('🌙 Switched to Dark Mode', 'success');
    } else {
      if (themeIcon) themeIcon.textContent = '☀️';
      if (themeText) themeText.textContent = 'Light Mode';
      if (showNotification) showToast('☀️ Switched to Light Mode', 'success');
    }

    // Synchronize settings modal radio
    const activeRadio = document.querySelector(`input[name="theme-pref"][value="${theme}"]`);
    if (activeRadio) activeRadio.checked = true;
  }

  // Initial theme load
  const initialTheme = localStorage.getItem('urias_theme') || 'dark';
  applyTheme(initialTheme, false);

  // Listen to OS system color scheme changes if set to auto
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if ((localStorage.getItem('urias_theme') || 'dark') === 'system') {
        applyTheme('system', false);
      }
    });
  }

  if (state.geminiApiKey) {
    geminiApiKeyInput.value = state.geminiApiKey;
  }

  // ==========================================================================
  // Ingestion Tab Switching
  // ==========================================================================
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const target = document.getElementById(btn.dataset.tab);
      if (target) target.classList.add('active');
    });
  });

  // ==========================================================================
  // Text Stats & Input Events
  // ==========================================================================
  function updateTextStats() {
    const text = sourceText.value.trim();
    const words = text ? text.split(/\s+/).length : 0;
    const chars = text.length;
    const estMinutes = Math.max(1, Math.round(words / 200));

    wordCount.textContent = `${words.toLocaleString()} words`;
    charCount.textContent = `${chars.toLocaleString()} chars`;
    readEstimate.textContent = words > 0 ? `~${estMinutes} min read` : '~0 min read';
  }

  sourceText.addEventListener('input', updateTextStats);
  clearTextBtn.addEventListener('click', () => {
    sourceText.value = '';
    updateTextStats();
    sourceText.focus();
  });

  // ==========================================================================
  // Presets
  // ==========================================================================
  document.querySelectorAll('.preset-tag').forEach(tag => {
    tag.addEventListener('click', () => {
      const sampleKey = tag.dataset.sample;
      if (SAMPLES[sampleKey]) {
        sourceText.value = SAMPLES[sampleKey];
        updateTextStats();
        // Switch to text tab if not active
        document.querySelector('.tab-btn[data-tab="tab-text"]').click();
        showToast('Sample text loaded.', 'success');
      }
    });
  });

  // ==========================================================================
  // Engine Selection
  // ==========================================================================
  engineBtnLocal.addEventListener('click', () => {
    state.engine = 'local';
    engineBtnLocal.classList.add('active');
    engineBtnGemini.classList.remove('active');
    badgeEngine.textContent = '⚡ Local NLP';
    densityControlGroup.style.display = 'flex';
  });

  engineBtnGemini.addEventListener('click', () => {
    state.engine = 'gemini';
    engineBtnGemini.classList.add('active');
    engineBtnLocal.classList.remove('active');
    badgeEngine.textContent = '🧠 Gemini AI';
    
    if (!state.geminiApiKey) {
      showToast('Tip: Configure your Gemini API key in settings, or leave blank to use server environment.', 'success');
    }
  });

  // ==========================================================================
  // Format Selection
  // ==========================================================================
  formatChips.forEach(chip => {
    chip.addEventListener('click', () => {
      formatChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.format = chip.dataset.format;

      if (state.format === 'tldr') {
        densityControlGroup.style.opacity = '0.4';
        densityControlGroup.style.pointerEvents = 'none';
      } else {
        densityControlGroup.style.opacity = '1';
        densityControlGroup.style.pointerEvents = 'auto';
      }
    });
  });

  // ==========================================================================
  // Density Slider
  // ==========================================================================
  ratioSlider.addEventListener('input', (e) => {
    const val = parseInt(e.target.value, 10);
    state.ratio = val / 100.0;
    let label = 'Balanced';
    if (val <= 25) label = 'Concise';
    else if (val >= 45) label = 'Detailed';
    ratioDisplay.textContent = `${label} (${val}%)`;
  });

  // ==========================================================================
  // URL Ingestion
  // ==========================================================================
  fetchUrlBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) {
      showToast('Please enter a web article URL.', 'error');
      return;
    }

    fetchUrlBtn.disabled = true;
    urlStatus.style.color = 'var(--text-muted)';
    urlStatus.textContent = 'Scraping article contents...';

    try {
      const res = await fetch('/api/extract-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to extract URL');

      sourceText.value = data.text;
      updateTextStats();
      urlStatus.style.color = 'var(--accent-emerald)';
      urlStatus.textContent = `✓ Extracted "${data.title}" (${data.word_count} words)`;
      
      // Switch to text tab
      setTimeout(() => {
        document.querySelector('.tab-btn[data-tab="tab-text"]').click();
        showToast('Article imported into editor.', 'success');
      }, 600);

    } catch (err) {
      urlStatus.style.color = '#ef4444';
      urlStatus.textContent = `Error: ${err.message}`;
      showToast(err.message, 'error');
    } finally {
      fetchUrlBtn.disabled = false;
    }
  });

  // ==========================================================================
  // File Upload Ingestion
  // ==========================================================================
  browseFileBtn.addEventListener('click', () => fileInput.click());
  fileDropZone.addEventListener('click', (e) => {
    if (e.target !== browseFileBtn) fileInput.click();
  });

  ['dragenter', 'dragover'].forEach(name => {
    fileDropZone.addEventListener(name, (e) => {
      e.preventDefault();
      fileDropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    fileDropZone.addEventListener(name, (e) => {
      e.preventDefault();
      fileDropZone.classList.remove('dragover');
    });
  });

  fileDropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileUpload(e.target.files[0]);
    }
  });

  async function handleFileUpload(file) {
    fileInfo.style.display = 'block';
    fileInfo.style.color = 'var(--text-muted)';
    fileInfo.textContent = `Reading ${file.name}...`;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to parse file');

      sourceText.value = data.text;
      updateTextStats();
      fileInfo.style.color = 'var(--accent-emerald)';
      fileInfo.textContent = `✓ Uploaded ${data.filename} (${data.word_count} words)`;

      setTimeout(() => {
        document.querySelector('.tab-btn[data-tab="tab-text"]').click();
        showToast(`Document ${data.filename} loaded.`, 'success');
      }, 500);

    } catch (err) {
      fileInfo.style.color = '#ef4444';
      fileInfo.textContent = `Error: ${err.message}`;
      showToast(err.message, 'error');
    }
  }

  // ==========================================================================
  // Summarization Execution
  // ==========================================================================
  summarizeBtn.addEventListener('click', executeSummarization);
  
  // Shortcut: Ctrl + Enter
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      executeSummarization();
    }
  });

  async function executeSummarization() {
    const text = sourceText.value.trim();
    if (!text) {
      showToast('Please enter or paste text to summarize.', 'error');
      sourceText.focus();
      return;
    }

    if (text.split(/\s+/).length < 10) {
      showToast('Text is too short. Please provide at least 10 words.', 'error');
      return;
    }

    // Stop ongoing audio
    stopAudio();

    // UI Loading State
    summarizeBtn.disabled = true;
    btnSpinner.style.display = 'inline-block';
    emptyState.style.display = 'none';
    summaryText.style.display = 'none';
    skeletonView.style.display = 'flex';
    metricsRibbon.style.display = 'none';
    keywordsPanel.style.display = 'none';
    actionToolbar.style.display = 'none';

    try {
      const payload = {
        text: text,
        engine: state.engine,
        format: state.format,
        ratio: state.ratio,
        api_key: state.geminiApiKey || undefined
      };

      const res = await fetch('/api/summarize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Summarization request failed');

      state.currentSummary = data.summary;

      // Update engine badge
      if (data.fallback) {
        badgeEngine.textContent = '⚡ Local (Gemini Fallback)';
        badgeEngine.style.background = 'rgba(234, 179, 8, 0.15)';
        badgeEngine.style.color = '#eab308';
        showToast('Gemini API unreachable. Handled via Local NLP.', 'success');
      } else if (data.engine.includes('gemini')) {
        badgeEngine.textContent = '🧠 Gemini 2.5 Flash';
        badgeEngine.style.background = 'var(--accent-glow)';
        badgeEngine.style.color = 'var(--accent-primary)';
      } else {
        badgeEngine.textContent = '⚡ Local NLP';
        badgeEngine.style.background = 'var(--accent-emerald-subtle)';
        badgeEngine.style.color = 'var(--accent-emerald)';
      }

      // Render Summary Text
      summaryText.textContent = data.summary;
      skeletonView.style.display = 'none';
      summaryText.style.display = 'block';

      // Render Metrics Ribbon
      if (data.metrics) {
        metricCompression.textContent = `${data.metrics.compression_percent}%`;
        metricTimeSaved.textContent = data.metrics.time_saved_display;
        metricWords.textContent = `${data.metrics.original_words} → ${data.metrics.summary_words}`;
        metricsRibbon.style.display = 'grid';
      }

      // Render Keywords
      if (data.keywords && data.keywords.length > 0) {
        keywordsChips.innerHTML = data.keywords
          .map(kw => `<span class="keyword-chip">#${escapeHtml(kw)}</span>`)
          .join('');
        keywordsPanel.style.display = 'block';
      } else {
        keywordsPanel.style.display = 'none';
      }

      actionToolbar.style.display = 'flex';
      showToast('Summary synthesized successfully!', 'success');

    } catch (err) {
      skeletonView.style.display = 'none';
      emptyState.style.display = 'block';
      showToast(err.message, 'error');
    } finally {
      summarizeBtn.disabled = false;
      btnSpinner.style.display = 'none';
    }
  }

  // ==========================================================================
  // Action Toolbar: Copy, Audio, Export
  // ==========================================================================
  copySummaryBtn.addEventListener('click', async () => {
    if (!state.currentSummary) return;
    try {
      await navigator.clipboard.writeText(state.currentSummary);
      showToast('Summary copied to clipboard!', 'success');
    } catch {
      showToast('Failed to copy to clipboard.', 'error');
    }
  });

  readAloudBtn.addEventListener('click', () => {
    if (!state.currentSummary || !state.speechSynth) return;

    if (state.isSpeaking) {
      stopAudio();
    } else {
      state.speechUtterance = new SpeechSynthesisUtterance(state.currentSummary);
      state.speechUtterance.rate = 1.0;
      state.speechUtterance.pitch = 1.0;

      state.speechUtterance.onend = () => stopAudio();
      state.speechUtterance.onerror = () => stopAudio();

      state.speechSynth.speak(state.speechUtterance);
      state.isSpeaking = true;
      speechBtnLabel.textContent = 'Stop';
      readAloudBtn.style.color = 'var(--accent-primary)';
    }
  });

  function stopAudio() {
    if (state.speechSynth && state.isSpeaking) {
      state.speechSynth.cancel();
    }
    state.isSpeaking = false;
    speechBtnLabel.textContent = 'Listen';
    readAloudBtn.style.color = '';
  }

  downloadSummaryBtn.addEventListener('click', () => {
    if (!state.currentSummary) return;

    const ext = state.format === 'bullets' ? 'md' : 'txt';
    const content = `# AI Text Summary (${new Date().toLocaleDateString()})\n\n${state.currentSummary}\n\n---\nSynthesized via AI Text Summarizer`;
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `summary_${Date.now()}.${ext}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Summary downloaded.', 'success');
  });

  // ==========================================================================
  // Settings & Theme Handlers
  // ==========================================================================
  openSettingsBtn.addEventListener('click', () => {
    settingsModal.style.display = 'flex';
  });

  const closeModal = () => { settingsModal.style.display = 'none'; };
  closeSettingsBtn.addEventListener('click', closeModal);
  modalCancelBtn.addEventListener('click', closeModal);
  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) closeModal();
  });

  saveSettingsBtn.addEventListener('click', () => {
    const key = geminiApiKeyInput.value.trim();
    state.geminiApiKey = key;
    if (key) {
      localStorage.setItem('urias_gemini_api_key', key);
      showToast('Gemini API key saved.', 'success');
    } else {
      localStorage.removeItem('urias_gemini_api_key');
      showToast('Gemini API key cleared. Operating in Local mode.', 'success');
    }

    // Save Theme Preference from Modal
    const selectedRadio = document.querySelector('input[name="theme-pref"]:checked');
    if (selectedRadio) {
      applyTheme(selectedRadio.value, true);
    }

    closeModal();
  });

  // Direct toggle on theme pill button
  themeToggleBtn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'dark';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next, true);
  });

  // Quick keyboard shortcut: Alt + T to toggle theme anytime
  document.addEventListener('keydown', (e) => {
    if (e.altKey && (e.key === 't' || e.key === 'T')) {
      e.preventDefault();
      const current = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next, true);
    }
  });

  // ==========================================================================
  // Utilities
  // ==========================================================
  function showToast(msg, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  function escapeHtml(str) {
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  }
});
