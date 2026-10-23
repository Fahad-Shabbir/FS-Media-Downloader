// Universal Media Downloader - Liquid Glass Engine & Animation Controller
// Handcrafted with Liquid Glass UI by Fahad Shabbir

let currentMode = 'single'; // 'single' | 'bulk'
let selectedMediaType = 'video'; // 'video' | 'audio'
let selectedVideoQuality = 'best';
let selectedAudioQuality = 'MP3';
let currentSingleData = null;
let currentBulkData = null;
let isDownloading = false;
let isPaused = false;

// DOM Elements
const docEl = document.documentElement;
const themeToggleBtn = document.getElementById('themeToggleBtn');
const themeIcon = document.getElementById('themeIcon');
const themeLabel = document.getElementById('themeLabel');

const tabSingleBtn = document.getElementById('tabSingleBtn');
const tabBulkBtn = document.getElementById('tabBulkBtn');
const tabGlider = document.getElementById('tabGlider');
const singleSection = document.getElementById('singleSection');
const bulkSection = document.getElementById('bulkSection');

const singleUrlInput = document.getElementById('singleUrlInput');
const pasteBtn = document.getElementById('pasteBtn');
const analyzeBtn = document.getElementById('analyzeBtn');

const previewCard = document.getElementById('previewCard');
const previewThumb = document.getElementById('previewThumb');
const previewPlatform = document.getElementById('previewPlatform');
const previewDuration = document.getElementById('previewDuration');
const previewTitle = document.getElementById('previewTitle');
const previewChannel = document.getElementById('previewChannel');

const formatNav = document.getElementById('formatNav');
const formatGlider = document.getElementById('formatGlider');
const typeVideoBtn = document.getElementById('typeVideoBtn');
const typeAudioBtn = document.getElementById('typeAudioBtn');
const videoResolutionsSection = document.getElementById('videoResolutionsSection');
const resolutionsGrid = document.getElementById('resolutionsGrid');
const audioQualitySection = document.getElementById('audioQualitySection');
const audioMp3Btn = document.getElementById('audioMp3Btn');
const audioWavBtn = document.getElementById('audioWavBtn');

const destPathText = document.getElementById('destPathText');
const browseDestBtn = document.getElementById('browseDestBtn');
const openDestBtn = document.getElementById('openDestBtn');

const turboCheck = document.getElementById('turboCheck');
const cookiesBtn = document.getElementById('cookiesBtn');
const cookiesLabel = document.getElementById('cookiesLabel');

const bulkTextarea = document.getElementById('bulkTextarea');
const bulkPasteBtn = document.getElementById('bulkPasteBtn');
const analyzeBulkBtn = document.getElementById('analyzeBulkBtn');
const bulkOptionsCard = document.getElementById('bulkOptionsCard');
const bulkSummaryText = document.getElementById('bulkSummaryText');
const bulkItemsList = document.getElementById('bulkItemsList');
const bulkTypeVideo = document.getElementById('bulkTypeVideo');
const bulkTypeMp3 = document.getElementById('bulkTypeMp3');
const bulkTypeWav = document.getElementById('bulkTypeWav');

const progressCard = document.getElementById('progressCard');
const progressTitle = document.getElementById('progressTitle');
const progressPercent = document.getElementById('progressPercent');
const progressFill = document.getElementById('progressFill');
const progressSpeed = document.getElementById('progressSpeed');
const progressEta = document.getElementById('progressEta');
const progressSize = document.getElementById('progressSize');

const startDownloadBtn = document.getElementById('startDownloadBtn');
const downloadBtnIcon = document.getElementById('downloadBtnIcon');
const downloadBtnText = document.getElementById('downloadBtnText');

const downloadControlsRow = document.getElementById('downloadControlsRow');
const pauseDownloadBtn = document.getElementById('pauseDownloadBtn');
const pauseBtnIcon = document.getElementById('pauseBtnIcon');
const pauseBtnText = document.getElementById('pauseBtnText');
const cancelDownloadBtn = document.getElementById('cancelDownloadBtn');
const miniPauseBtn = document.getElementById('miniPauseBtn');
const miniCancelBtn = document.getElementById('miniCancelBtn');

// ================= LIQUID GLASS PHYSICS & ANIMATIONS =================

// 1. Jelly Elastic Glider Positioning
function updateGlider(gliderEl, targetBtn) {
  if (!gliderEl || !targetBtn) return;
  const parent = targetBtn.parentElement;
  const pRect = parent.getBoundingClientRect();
  const bRect = targetBtn.getBoundingClientRect();
  
  const left = bRect.left - pRect.left;
  const width = bRect.width;
  
  gliderEl.style.transform = `translateX(${left}px)`;
  gliderEl.style.width = `${width}px`;
}

// 2. Interactive 3D Liquid Glass Tilt & Specular Glare Tracking
function setupLiquidTilt() {
  const tiltPanels = document.querySelectorAll('.glass-panel[data-tilt="true"]');
  
  tiltPanels.forEach(panel => {
    panel.addEventListener('mousemove', (e) => {
      const rect = panel.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      // Calculate subtle tilt angle (-3 to +3 degrees)
      const tiltX = ((y - centerY) / centerY) * -2.5;
      const tiltY = ((x - centerX) / centerX) * 2.5;
      
      panel.style.setProperty('--mouse-x', `${x}px`);
      panel.style.setProperty('--mouse-y', `${y}px`);
      panel.style.setProperty('--tilt-x', `${tiltX.toFixed(2)}deg`);
      panel.style.setProperty('--tilt-y', `${tiltY.toFixed(2)}deg`);
      panel.style.setProperty('--specular-opacity', '1');
    });

    panel.addEventListener('mouseleave', () => {
      panel.style.setProperty('--tilt-x', '0deg');
      panel.style.setProperty('--tilt-y', '0deg');
      panel.style.setProperty('--specular-opacity', '0');
    });
  });
}

// 3. Viscous Fluid Click Ripple
function createLiquidRipple(e, target) {
  const rect = target.getBoundingClientRect();
  const ripple = document.createElement('span');
  ripple.className = 'liquid-ripple';
  
  const size = Math.max(rect.width, rect.height) * 1.5;
  ripple.style.width = `${size}px`;
  ripple.style.height = `${size}px`;
  
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  ripple.style.left = `${x}px`;
  ripple.style.top = `${y}px`;
  
  target.appendChild(ripple);
  setTimeout(() => ripple.remove(), 700);
}

document.addEventListener('click', (e) => {
  const target = e.target.closest('.glass-btn-icon, .glass-btn-primary, .tab-btn, .format-tab-btn, .quality-card, .audio-btn');
  if (target) {
    createLiquidRipple(e, target);
  }
});

// ================= PYWEBVIEW LIFECYCLE =================
window.addEventListener('pywebviewready', () => {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_default_download_dir().then(path => {
      if (path) destPathText.textContent = path;
    });
    window.pywebview.api.check_cookies().then(hasCookie => {
      if (hasCookie) {
        cookiesLabel.textContent = "Cookies Active ✓";
        cookiesBtn.style.borderColor = "rgba(74, 222, 128, 0.5)";
        cookiesBtn.style.color = "#4ade80";
      }
    });
  }
});

// Initialize physics on load
window.addEventListener('DOMContentLoaded', () => {
  setupLiquidTilt();
  setTimeout(() => {
    updateGlider(tabGlider, tabSingleBtn);
    updateGlider(formatGlider, typeVideoBtn);
  }, 100);
});

// Theme Switching
themeToggleBtn.addEventListener('click', () => {
  const current = docEl.getAttribute('data-theme');
  if (current === 'light') {
    docEl.setAttribute('data-theme', 'dark');
    themeIcon.textContent = '☀️';
    themeLabel.textContent = 'Light Mode';
  } else {
    docEl.setAttribute('data-theme', 'light');
    themeIcon.textContent = '🌙';
    themeLabel.textContent = 'Dark Mode';
  }
});

// Tabs Switching
tabSingleBtn.addEventListener('click', () => {
  currentMode = 'single';
  tabSingleBtn.classList.add('active');
  tabBulkBtn.classList.remove('active');
  updateGlider(tabGlider, tabSingleBtn);
  singleSection.style.display = 'flex';
  bulkSection.style.display = 'none';
  updateDownloadButtonState();
});

tabBulkBtn.addEventListener('click', () => {
  currentMode = 'bulk';
  tabBulkBtn.classList.add('active');
  tabSingleBtn.classList.remove('active');
  updateGlider(tabGlider, tabBulkBtn);
  singleSection.style.display = 'none';
  bulkSection.style.display = 'flex';
  updateDownloadButtonState();
});

// Paste Buttons
pasteBtn.addEventListener('click', async () => {
  try {
    const text = await navigator.clipboard.readText();
    singleUrlInput.value = text.trim();
  } catch (e) {
    if (window.pywebview && window.pywebview.api) {
      const text = await window.pywebview.api.get_clipboard_text();
      if (text) singleUrlInput.value = text.trim();
    }
  }
});

bulkPasteBtn.addEventListener('click', async () => {
  try {
    const text = await navigator.clipboard.readText();
    bulkTextarea.value = text.trim();
  } catch (e) {
    if (window.pywebview && window.pywebview.api) {
      const text = await window.pywebview.api.get_clipboard_text();
      if (text) bulkTextarea.value = text.trim();
    }
  }
});

// Cookies / Anti-Bot Importer
cookiesBtn.addEventListener('click', async () => {
  if (!window.pywebview || !window.pywebview.api) return;
  const res = await window.pywebview.api.import_cookies();
  if (res && res.success) {
    cookiesLabel.textContent = "Cookies Loaded ✓";
    cookiesBtn.style.borderColor = "rgba(74, 222, 128, 0.5)";
    cookiesBtn.style.color = "#4ade80";
    alert("Anti-bot bypass cookies.txt imported successfully!");
  } else if (res && res.error) {
    alert("Notice: " + res.error);
  }
});

// Browse & Open Output Folder
browseDestBtn.addEventListener('click', async () => {
  if (!window.pywebview || !window.pywebview.api) return;
  const folder = await window.pywebview.api.select_directory();
  if (folder) destPathText.textContent = folder;
});

openDestBtn.addEventListener('click', async () => {
  if (!window.pywebview || !window.pywebview.api) return;
  await window.pywebview.api.open_directory(destPathText.textContent);
});

// Format Type Selection (Video vs Audio)
function selectMediaType(type) {
  selectedMediaType = type;
  if (type === 'video') {
    typeVideoBtn.classList.add('active');
    typeAudioBtn.classList.remove('active');
    updateGlider(formatGlider, typeVideoBtn);
    videoResolutionsSection.style.display = 'block';
    audioQualitySection.style.display = 'none';
  } else {
    typeAudioBtn.classList.add('active');
    typeVideoBtn.classList.remove('active');
    updateGlider(formatGlider, typeAudioBtn);
    videoResolutionsSection.style.display = 'none';
    audioQualitySection.style.display = 'block';
  }
}
typeVideoBtn.addEventListener('click', () => selectMediaType('video'));
typeAudioBtn.addEventListener('click', () => selectMediaType('audio'));

// Audio Format Selection
audioMp3Btn.addEventListener('click', () => {
  selectedAudioQuality = 'MP3';
  audioMp3Btn.classList.add('selected');
  audioWavBtn.classList.remove('selected');
});
audioWavBtn.addEventListener('click', () => {
  selectedAudioQuality = 'WAV';
  audioWavBtn.classList.add('selected');
  audioMp3Btn.classList.remove('selected');
});

// Bulk Format Selector Buttons
function setBulkFormat(type, quality) {
  selectedMediaType = type;
  if (type === 'video') {
    selectedVideoQuality = 'best';
    bulkTypeVideo.style.background = 'var(--accent-gradient)';
    bulkTypeVideo.style.color = '#fff';
    bulkTypeMp3.style.background = 'var(--glass-bg)';
    bulkTypeMp3.style.color = 'var(--text-main)';
    bulkTypeWav.style.background = 'var(--glass-bg)';
    bulkTypeWav.style.color = 'var(--text-main)';
  } else if (quality === 'MP3') {
    selectedAudioQuality = 'MP3';
    bulkTypeMp3.style.background = 'var(--accent-gradient)';
    bulkTypeMp3.style.color = '#fff';
    bulkTypeVideo.style.background = 'var(--glass-bg)';
    bulkTypeVideo.style.color = 'var(--text-main)';
    bulkTypeWav.style.background = 'var(--glass-bg)';
    bulkTypeWav.style.color = 'var(--text-main)';
  } else {
    selectedAudioQuality = 'WAV';
    bulkTypeWav.style.background = 'var(--accent-gradient)';
    bulkTypeWav.style.color = '#fff';
    bulkTypeVideo.style.background = 'var(--glass-bg)';
    bulkTypeVideo.style.color = 'var(--text-main)';
    bulkTypeMp3.style.background = 'var(--glass-bg)';
    bulkTypeMp3.style.color = 'var(--text-main)';
  }
}
bulkTypeVideo.addEventListener('click', () => setBulkFormat('video', 'best'));
bulkTypeMp3.addEventListener('click', () => setBulkFormat('audio', 'MP3'));
bulkTypeWav.addEventListener('click', () => setBulkFormat('audio', 'WAV'));

// Analyze Single URL
analyzeBtn.addEventListener('click', async () => {
  const url = singleUrlInput.value.trim();
  if (!url) {
    alert("Please paste a video or media link first.");
    return;
  }

  analyzeBtn.disabled = true;
  analyzeBtn.innerHTML = '<span>⏳</span> Analyzing...';
  previewCard.classList.remove('show');

  try {
    const res = await window.pywebview.api.analyze_url(url);
    if (res.error) {
      alert("Analysis Error: " + res.error);
    } else {
      currentSingleData = res;
      displaySinglePreview(res);
    }
  } catch (err) {
    alert("Failed to analyze: " + err);
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = '<span>🔍</span> Analyze Link';
  }
});

function displaySinglePreview(data) {
  previewTitle.textContent = data.title || "Video";
  previewChannel.textContent = data.channel || data.platform || "";
  previewPlatform.textContent = data.platform || "Video";
  previewDuration.textContent = data.duration || "";
  
  if (data.thumbnail) {
    previewThumb.src = data.thumbnail;
    previewThumb.style.display = 'block';
  } else {
    previewThumb.style.display = 'none';
  }

  // Populate resolutions grid
  resolutionsGrid.innerHTML = '';
  const resolutions = data.resolutions || [];
  
  if (resolutions.length === 0) {
    const card = document.createElement('div');
    card.className = 'quality-card selected';
    card.innerHTML = `<div class="quality-label">Best Quality</div><div class="quality-sub">Original Source</div>`;
    resolutionsGrid.appendChild(card);
    selectedVideoQuality = 'best';
  } else {
    resolutions.forEach((res, idx) => {
      const card = document.createElement('div');
      card.className = `quality-card ${idx === 0 ? 'selected' : ''}`;
      card.dataset.height = res.height;
      card.innerHTML = `
        <div class="quality-label">${res.label}</div>
        <div class="quality-sub">MP4 Video + Audio</div>
      `;
      card.addEventListener('click', () => {
        document.querySelectorAll('.quality-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        selectedVideoQuality = res.height;
      });
      resolutionsGrid.appendChild(card);
    });
    selectedVideoQuality = resolutions[0].height;
  }

  selectMediaType('video');
  previewCard.classList.add('show');
  updateDownloadButtonState();
}

// Analyze Bulk / Playlist
analyzeBulkBtn.addEventListener('click', async () => {
  const text = bulkTextarea.value.trim();
  if (!text) {
    alert("Please enter a playlist URL or list of video links.");
    return;
  }

  analyzeBulkBtn.disabled = true;
  analyzeBulkBtn.innerHTML = '<span>⏳</span> Analyzing Queue...';

  try {
    const res = await window.pywebview.api.analyze_bulk(text);
    if (res.error) {
      alert("Error: " + res.error);
    } else {
      currentBulkData = res;
      displayBulkQueue(res);
    }
  } catch (err) {
    alert("Bulk analysis failed: " + err);
  } finally {
    analyzeBulkBtn.disabled = false;
    analyzeBulkBtn.innerHTML = '<span>🔍</span> Analyze Playlist / Links';
  }
});

function displayBulkQueue(data) {
  bulkSummaryText.textContent = `${data.title} (${data.count} items)`;
  bulkItemsList.innerHTML = '';

  data.items.forEach((item, idx) => {
    const row = document.createElement('div');
    row.className = 'bulk-item-row';
    row.id = `bulk-item-${idx}`;
    row.innerHTML = `
      <div style="display: flex; align-items: center; gap: 10px;">
        <span style="color: var(--text-muted); font-size: 11px;">#${idx+1}</span>
        <span class="bulk-item-title" title="${item.title}">${item.title}</span>
      </div>
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="plat-chip" style="font-size: 11px;">${item.platform || 'Video'}</span>
        <span class="bulk-item-status" id="bulk-status-${idx}">Pending</span>
      </div>
    `;
    bulkItemsList.appendChild(row);
  });

  setBulkFormat('video', 'best');
  bulkOptionsCard.style.display = 'flex';
  updateDownloadButtonState();
}

function updateDownloadButtonState() {
  if (isDownloading) {
    startDownloadBtn.disabled = true;
    return;
  }
  if (currentMode === 'single') {
    startDownloadBtn.disabled = !currentSingleData;
    downloadBtnText.textContent = turboCheck.checked ? "Start Turbo Download (8x)" : "Start Download";
  } else {
    startDownloadBtn.disabled = !currentBulkData || !currentBulkData.items || currentBulkData.items.length === 0;
    downloadBtnText.textContent = turboCheck.checked 
      ? `Start Turbo Queue Download (${currentBulkData ? currentBulkData.count : 0} items)`
      : `Start Queue Download (${currentBulkData ? currentBulkData.count : 0} items)`;
  }
}

turboCheck.addEventListener('change', () => {
  const container = document.getElementById('turboToggleContainer');
  if (turboCheck.checked) {
    container.classList.add('active');
  } else {
    container.classList.remove('active');
  }
  updateDownloadButtonState();
});

// Pause & Cancel Handlers
async function togglePause() {
  if (!isDownloading || !window.pywebview || !window.pywebview.api) return;
  if (!isPaused) {
    await window.pywebview.api.pause_download();
    isPaused = true;
    pauseBtnIcon.textContent = '▶';
    pauseBtnText.textContent = 'Resume';
    pauseDownloadBtn.style.color = '#4ade80';
    pauseDownloadBtn.style.borderColor = 'rgba(74, 222, 128, 0.45)';
    miniPauseBtn.textContent = '▶';
    progressFill.classList.add('paused');
    progressSpeed.textContent = 'Paused';
    progressEta.textContent = 'Paused';
    progressTitle.textContent = 'Download Paused';
  } else {
    await window.pywebview.api.resume_download();
    isPaused = false;
    pauseBtnIcon.textContent = '⏸';
    pauseBtnText.textContent = 'Pause';
    pauseDownloadBtn.style.color = '';
    pauseDownloadBtn.style.borderColor = '';
    miniPauseBtn.textContent = '⏸';
    progressFill.classList.remove('paused');
    progressTitle.textContent = 'Downloading...';
  }
}

async function triggerCancel() {
  if (!isDownloading || !window.pywebview || !window.pywebview.api) return;
  await window.pywebview.api.cancel_download();
  isDownloading = false;
  isPaused = false;
  progressFill.classList.remove('paused');
  progressTitle.textContent = 'Download Cancelled ✗';
  progressSpeed.textContent = '-- MB/s';
  progressEta.textContent = 'ETA: --';
  downloadControlsRow.style.display = 'none';
  startDownloadBtn.style.display = 'inline-flex';
  miniPauseBtn.style.display = 'none';
  miniCancelBtn.style.display = 'none';
  updateDownloadButtonState();
}

pauseDownloadBtn.addEventListener('click', togglePause);
miniPauseBtn.addEventListener('click', togglePause);
cancelDownloadBtn.addEventListener('click', triggerCancel);
miniCancelBtn.addEventListener('click', triggerCancel);

// Download Execution
startDownloadBtn.addEventListener('click', async () => {
  if (isDownloading) return;
  const isTurbo = turboCheck.checked;
  const outDir = destPathText.textContent.trim();

  isDownloading = true;
  isPaused = false;
  startDownloadBtn.style.display = 'none';
  downloadControlsRow.style.display = 'flex';
  miniPauseBtn.style.display = 'inline-flex';
  miniCancelBtn.style.display = 'inline-flex';
  pauseBtnIcon.textContent = '⏸';
  pauseBtnText.textContent = 'Pause';
  pauseDownloadBtn.style.color = '';
  pauseDownloadBtn.style.borderColor = '';
  miniPauseBtn.textContent = '⏸';

  progressCard.classList.add('show');
  resetProgress();

  if (currentMode === 'single') {
    if (!currentSingleData) {
      alert("Please enter and analyze a video link first.");
      isDownloading = false;
      downloadControlsRow.style.display = 'none';
      startDownloadBtn.style.display = '';
      return;
    }
    const url = currentSingleData.webpage_url || singleUrlInput.value.trim();
    const quality = selectedMediaType === 'video' ? selectedVideoQuality : selectedAudioQuality;
    progressTitle.textContent = `Downloading: ${currentSingleData.title}`;

    try {
      const res = await window.pywebview.api.download_single(
        url,
        selectedMediaType,
        quality,
        outDir,
        isTurbo
      );
      if (res && res.cancelled) {
        progressTitle.textContent = "Download Cancelled ✗";
      } else if (res && res.error) {
        alert("Download Failed: " + res.error);
        progressTitle.textContent = "Download Error";
      } else {
        progressTitle.textContent = "Download Complete ✓";
        progressFill.style.width = '100%';
        progressPercent.textContent = '100%';
      }
    } catch (err) {
      if (isDownloading) {
        alert("Error: " + err);
        progressTitle.textContent = "Error";
      }
    } finally {
      isDownloading = false;
      isPaused = false;
      downloadControlsRow.style.display = 'none';
      startDownloadBtn.style.display = 'inline-flex';
      miniPauseBtn.style.display = 'none';
      miniCancelBtn.style.display = 'none';
      progressFill.classList.remove('paused');
      updateDownloadButtonState();
    }
  } else {
    // Bulk queue download
    if (!currentBulkData || !currentBulkData.items || currentBulkData.items.length === 0) {
      alert("Please paste and analyze your playlist or links first.");
      isDownloading = false;
      downloadControlsRow.style.display = 'none';
      startDownloadBtn.style.display = '';
      return;
    }
    const quality = selectedMediaType === 'video' ? 'best' : selectedAudioQuality;
    progressTitle.textContent = `Processing Queue (0 / ${currentBulkData.count})`;

    try {
      const res = await window.pywebview.api.download_bulk(
        currentBulkData.items,
        selectedMediaType,
        quality,
        outDir,
        isTurbo
      );
      if (res && res.cancelled) {
        progressTitle.textContent = "Queue Cancelled ✗";
      } else if (res && res.error) {
        alert("Bulk Download Error: " + res.error);
      } else {
        progressTitle.textContent = `Queue Complete: ${res.successful}/${res.total} downloaded`;
      }
    } catch (err) {
      if (isDownloading) {
        alert("Bulk download error: " + err);
      }
    } finally {
      isDownloading = false;
      isPaused = false;
      downloadControlsRow.style.display = 'none';
      startDownloadBtn.style.display = 'inline-flex';
      miniPauseBtn.style.display = 'none';
      miniCancelBtn.style.display = 'none';
      progressFill.classList.remove('paused');
      updateDownloadButtonState();
    }
  }
});

function resetProgress() {
  progressFill.style.width = '0%';
  progressPercent.textContent = '0%';
  progressSpeed.textContent = '-- MB/s';
  progressEta.textContent = 'ETA: --';
  progressSize.textContent = '0 MB / 0 MB';
}

// Global functions invoked from Python via webview.evaluate_js
window.update_progress = function(percent, speed, eta, downloaded, total, status) {
  progressFill.style.width = `${percent}%`;
  progressPercent.textContent = `${Math.round(percent)}%`;
  if (speed) progressSpeed.textContent = speed;
  if (eta) progressEta.textContent = `ETA: ${eta}`;
  if (downloaded && total) progressSize.textContent = `${downloaded} / ${total}`;
  if (status) progressTitle.textContent = status;
};

window.update_bulk_progress = function(idx, total, title, status) {
  progressTitle.textContent = `[${idx}/${total}] ${title}`;
  const statusEl = document.getElementById(`bulk-status-${idx - 1}`);
  if (statusEl) {
    if (status === 'downloading') {
      statusEl.textContent = 'Downloading...';
      statusEl.style.background = 'rgba(6, 182, 212, 0.25)';
      statusEl.style.color = '#22d3ee';
    } else if (status === 'finished') {
      statusEl.textContent = 'Done ✓';
      statusEl.style.background = 'rgba(74, 222, 128, 0.25)';
      statusEl.style.color = '#4ade80';
    } else if (status === 'error') {
      statusEl.textContent = 'Failed ✗';
      statusEl.style.background = 'rgba(239, 68, 68, 0.25)';
      statusEl.style.color = '#f87171';
    }
  }
};
