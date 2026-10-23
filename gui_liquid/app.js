// FS Media Downloader - Liquid Glass Engine & Animation Controller
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

// Update & System DOM Elements
const updateBtn = document.getElementById('updateBtn');
const updateBtnIcon = document.getElementById('updateBtnIcon');
const updateBtnLabel = document.getElementById('updateBtnLabel');
const updateNoticeDot = document.getElementById('updateNoticeDot');

const footerYtdlpVer = document.getElementById('footerYtdlpVer');
const footerAppVer = document.getElementById('footerAppVer');

const updateModalOverlay = document.getElementById('updateModalOverlay');
const closeUpdateModalBtn = document.getElementById('closeUpdateModalBtn');
const dismissModalBtn = document.getElementById('dismissModalBtn');
const recheckUpdatesBtn = document.getElementById('recheckUpdatesBtn');
const recheckIcon = document.getElementById('recheckIcon');

const ytdlpStatusBadge = document.getElementById('ytdlpStatusBadge');
const modalYtdlpInstalled = document.getElementById('modalYtdlpInstalled');
const modalYtdlpLatest = document.getElementById('modalYtdlpLatest');
const ytdlpProgressBox = document.getElementById('ytdlpProgressBox');
const ytdlpProgressFill = document.getElementById('ytdlpProgressFill');
const ytdlpProgressMsg = document.getElementById('ytdlpProgressMsg');
const runYtdlpUpdateBtn = document.getElementById('runYtdlpUpdateBtn');
const restartAppBtn = document.getElementById('restartAppBtn');

const appStatusBadge = document.getElementById('appStatusBadge');
const modalAppInstalled = document.getElementById('modalAppInstalled');
const modalAppLatest = document.getElementById('modalAppLatest');
const appNotesBox = document.getElementById('appNotesBox');
const appNotesContent = document.getElementById('appNotesContent');
const appProgressBox = document.getElementById('appProgressBox');
const appProgressFill = document.getElementById('appProgressFill');
const appProgressMsg = document.getElementById('appProgressMsg');
const runAppUpdateBtn = document.getElementById('runAppUpdateBtn');

let lastCheckedUpdates = null;

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
    // Load installed versions into UI
    loadInstalledVersions();
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

// ================= LIQUID GLASS TOAST SYSTEM =================
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `glass-toast toast-${type}`;
  
  const iconMap = {
    success: '✓',
    error: '✗',
    info: '⚡'
  };
  const icon = iconMap[type] || 'ℹ️';

  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <span class="toast-message">${message}</span>
    <span class="toast-close">✕</span>
  `;

  toast.querySelector('.toast-close').addEventListener('click', (e) => {
    e.stopPropagation();
    dismissToast(toast);
  });

  toast.addEventListener('click', () => dismissToast(toast));

  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  if (duration > 0) {
    setTimeout(() => {
      dismissToast(toast);
    }, duration);
  }
}

function dismissToast(toast) {
  if (!toast || toast.classList.contains('hide')) return;
  toast.classList.remove('show');
  toast.classList.add('hide');
  setTimeout(() => {
    if (toast.parentElement) toast.remove();
  }, 320);
}

// ================= SYSTEM & UPDATE CONTROLLER =================

async function loadInstalledVersions() {
  if (!window.pywebview || !window.pywebview.api) return;
  try {
    const v = await window.pywebview.api.get_versions();
    if (v) {
      if (v.ytdlp_version && footerYtdlpVer) {
        footerYtdlpVer.textContent = `yt-dlp v${v.ytdlp_version}`;
        if (modalYtdlpInstalled) {
          modalYtdlpInstalled.textContent = `v${v.ytdlp_version}` + (v.ytdlp_is_custom ? ' (Updated)' : '');
        }
      }
      if (v.app_version && footerAppVer) {
        footerAppVer.textContent = `App v${v.app_version}`;
        if (modalAppInstalled) {
          modalAppInstalled.textContent = `v${v.app_version}`;
        }
      }
    }
  } catch (err) {
    console.error("Failed to load versions:", err);
  }
}

function openUpdateModal() {
  if (updateModalOverlay) {
    updateModalOverlay.classList.add('show');
  }
}

function closeUpdateModal() {
  if (updateModalOverlay) {
    updateModalOverlay.classList.remove('show');
  }
}

// Modal closing handlers
if (closeUpdateModalBtn) closeUpdateModalBtn.addEventListener('click', closeUpdateModal);
if (dismissModalBtn) dismissModalBtn.addEventListener('click', closeUpdateModal);
if (updateModalOverlay) {
  updateModalOverlay.addEventListener('click', (e) => {
    if (e.target === updateModalOverlay) {
      closeUpdateModal();
    }
  });
}

async function checkUpdates(openModal = true) {
  if (!window.pywebview || !window.pywebview.api) {
    showToast("Application engine is initializing...", "info");
    return;
  }

  // Set loading states
  if (updateBtn) updateBtn.disabled = true;
  if (updateBtnIcon) updateBtnIcon.classList.add('spinning');
  if (updateBtnLabel) updateBtnLabel.textContent = 'Checking...';
  if (recheckIcon) recheckIcon.classList.add('spinning');
  if (recheckUpdatesBtn) recheckUpdatesBtn.disabled = true;

  if (ytdlpStatusBadge) {
    ytdlpStatusBadge.className = 'status-badge checking';
    ytdlpStatusBadge.textContent = 'Checking PyPI...';
  }
  if (appStatusBadge) {
    appStatusBadge.className = 'status-badge checking';
    appStatusBadge.textContent = 'Checking GitHub...';
  }

  if (openModal) {
    openUpdateModal();
  }

  try {
    const res = await window.pywebview.api.check_updates();
    lastCheckedUpdates = res;

    // 1. Process yt-dlp status
    const ytdlp = res.ytdlp || {};
    if (modalYtdlpInstalled && ytdlp.current) {
      modalYtdlpInstalled.textContent = `v${ytdlp.current}`;
    }
    if (modalYtdlpLatest && ytdlp.latest) {
      modalYtdlpLatest.textContent = `v${ytdlp.latest}`;
    }

    if (ytdlp.error) {
      ytdlpStatusBadge.className = 'status-badge error';
      ytdlpStatusBadge.textContent = 'Check Failed';
      runYtdlpUpdateBtn.style.display = 'none';
      showToast("yt-dlp check: " + ytdlp.error, "error");
    } else if (ytdlp.update_available) {
      ytdlpStatusBadge.className = 'status-badge available';
      ytdlpStatusBadge.textContent = `Update Available (v${ytdlp.latest})`;
      runYtdlpUpdateBtn.style.display = 'inline-flex';
      restartAppBtn.style.display = 'none';
      if (updateNoticeDot) updateNoticeDot.style.display = 'block';
    } else {
      ytdlpStatusBadge.className = 'status-badge uptodate';
      ytdlpStatusBadge.textContent = 'Up to date ✓';
      runYtdlpUpdateBtn.style.display = 'none';
      restartAppBtn.style.display = 'none';
    }

    // 2. Process App release status
    const app = res.app || {};
    if (modalAppInstalled && app.current) {
      modalAppInstalled.textContent = `v${app.current}`;
    }
    if (modalAppLatest && app.latest) {
      modalAppLatest.textContent = `v${app.latest}`;
    }

    if (app.error) {
      appStatusBadge.className = 'status-badge error';
      appStatusBadge.textContent = 'Check Failed';
      runAppUpdateBtn.style.display = 'none';
      if (appNotesBox) appNotesBox.style.display = 'none';
      showToast("App check: " + app.error, "error");
    } else if (app.update_available) {
      appStatusBadge.className = 'status-badge available';
      appStatusBadge.textContent = `New Version Available (v${app.latest})`;
      runAppUpdateBtn.style.display = 'inline-flex';
      if (app.notes && appNotesBox && appNotesContent) {
        appNotesContent.textContent = app.notes;
        appNotesBox.style.display = 'block';
      }
      if (updateNoticeDot) updateNoticeDot.style.display = 'block';
    } else {
      appStatusBadge.className = 'status-badge uptodate';
      appStatusBadge.textContent = "You're up to date ✓";
      runAppUpdateBtn.style.display = 'none';
      if (appNotesBox) appNotesBox.style.display = 'none';
    }

    // Toast feedback if up to date
    if (!ytdlp.update_available && !app.update_available && !ytdlp.error && !app.error) {
      showToast("You're up to date! yt-dlp core and App are on the latest versions.", "success");
      if (updateNoticeDot) updateNoticeDot.style.display = 'none';
    } else if (ytdlp.update_available || app.update_available) {
      showToast("Updates available! See the dialog to update.", "info");
    }

  } catch (err) {
    showToast("Update check failed: " + err, "error");
    if (ytdlpStatusBadge) {
      ytdlpStatusBadge.className = 'status-badge error';
      ytdlpStatusBadge.textContent = 'Error';
    }
    if (appStatusBadge) {
      appStatusBadge.className = 'status-badge error';
      appStatusBadge.textContent = 'Error';
    }
  } finally {
    if (updateBtn) updateBtn.disabled = false;
    if (updateBtnIcon) updateBtnIcon.classList.remove('spinning');
    if (updateBtnLabel) updateBtnLabel.textContent = 'Update';
    if (recheckIcon) recheckIcon.classList.remove('spinning');
    if (recheckUpdatesBtn) recheckUpdatesBtn.disabled = false;
  }
}

// Bind Update & Recheck Buttons
if (updateBtn) {
  updateBtn.addEventListener('click', () => checkUpdates(true));
}
if (recheckUpdatesBtn) {
  recheckUpdatesBtn.addEventListener('click', () => checkUpdates(false));
}

// Global Progress Hooks invoked from Python
window.update_ytdlp_progress = function(percent, message) {
  if (ytdlpProgressFill) ytdlpProgressFill.style.width = `${percent}%`;
  if (ytdlpProgressMsg && message) ytdlpProgressMsg.textContent = message;
};

window.update_app_progress = function(percent, message) {
  if (appProgressFill) appProgressFill.style.width = `${percent}%`;
  if (appProgressMsg && message) appProgressMsg.textContent = message;
};

// yt-dlp Update Execution
if (runYtdlpUpdateBtn) {
  runYtdlpUpdateBtn.addEventListener('click', async () => {
    runYtdlpUpdateBtn.disabled = true;
    runYtdlpUpdateBtn.innerHTML = '<span>⏳</span> Updating...';
    if (ytdlpProgressBox) ytdlpProgressBox.style.display = 'flex';
    if (ytdlpProgressFill) ytdlpProgressFill.style.width = '10%';
    if (ytdlpProgressMsg) ytdlpProgressMsg.textContent = 'Connecting to PyPI...';

    try {
      const res = await window.pywebview.api.update_ytdlp();
      if (res && res.success) {
        if (ytdlpProgressFill) ytdlpProgressFill.style.width = '100%';
        if (ytdlpProgressMsg) ytdlpProgressMsg.textContent = `✓ Successfully updated to v${res.version}!`;
        runYtdlpUpdateBtn.style.display = 'none';
        if (restartAppBtn) restartAppBtn.style.display = 'inline-flex';
        if (ytdlpStatusBadge) {
          ytdlpStatusBadge.className = 'status-badge uptodate';
          ytdlpStatusBadge.textContent = `Updated to v${res.version}`;
        }
        showToast(`yt-dlp updated to v${res.version}. Please restart the app.`, "success", 6000);
      } else {
        const err = (res && res.error) ? res.error : "Unknown error";
        if (ytdlpProgressMsg) ytdlpProgressMsg.textContent = "Update failed: " + err;
        runYtdlpUpdateBtn.disabled = false;
        runYtdlpUpdateBtn.innerHTML = '<span>⚡</span> Retry Update';
        showToast("yt-dlp update failed: " + err, "error");
      }
    } catch (err) {
      if (ytdlpProgressMsg) ytdlpProgressMsg.textContent = "Update failed: " + err;
      runYtdlpUpdateBtn.disabled = false;
      runYtdlpUpdateBtn.innerHTML = '<span>⚡</span> Retry Update';
      showToast("Error updating yt-dlp: " + err, "error");
    }
  });
}

// Restart Application Handler
if (restartAppBtn) {
  restartAppBtn.addEventListener('click', async () => {
    restartAppBtn.disabled = true;
    restartAppBtn.innerHTML = '<span>⏳</span> Restarting App...';
    showToast("Restarting FS Media Downloader...", "info", 3000);
    try {
      await window.pywebview.api.restart_app();
    } catch (err) {
      console.error("Restart error:", err);
    }
  });
}

// App Update Execution
if (runAppUpdateBtn) {
  runAppUpdateBtn.addEventListener('click', async () => {
    if (!lastCheckedUpdates || !lastCheckedUpdates.app || !lastCheckedUpdates.app.asset_url) {
      showToast("Download URL not found.", "error");
      return;
    }
    const assetUrl = lastCheckedUpdates.app.asset_url;
    const assetName = lastCheckedUpdates.app.asset_name || "FS Media Downloader.exe";

    runAppUpdateBtn.disabled = true;
    runAppUpdateBtn.innerHTML = '<span>⏳</span> Downloading...';
    if (appProgressBox) appProgressBox.style.display = 'flex';
    if (appProgressFill) appProgressFill.style.width = '5%';
    if (appProgressMsg) appProgressMsg.textContent = 'Connecting to GitHub...';

    try {
      const res = await window.pywebview.api.download_app_update(assetUrl, assetName);
      if (res && res.success) {
        if (appProgressFill) appProgressFill.style.width = '100%';
        if (appProgressMsg) appProgressMsg.textContent = `✓ Downloaded to: ${res.file_path}`;
        runAppUpdateBtn.style.display = 'none';
        showToast("New version downloaded to Downloads folder!", "success", 7000);
      } else {
        const err = (res && res.error) ? res.error : "Unknown error";
        if (appProgressMsg) appProgressMsg.textContent = "Download failed: " + err;
        runAppUpdateBtn.disabled = false;
        runAppUpdateBtn.innerHTML = '<span>📥</span> Retry Download';
        showToast("App update download failed: " + err, "error");
      }
    } catch (err) {
      if (appProgressMsg) appProgressMsg.textContent = "Download failed: " + err;
      runAppUpdateBtn.disabled = false;
      runAppUpdateBtn.innerHTML = '<span>📥</span> Retry Download';
      showToast("Error downloading app update: " + err, "error");
    }
  });
}
