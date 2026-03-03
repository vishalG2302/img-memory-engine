/* ============================================
   IMAGE MEMORY ENGINE — APP LOGIC
   Tab switching, Upload, Search, Graph
   ============================================ */

// ========================
// TAB SWITCHING
// ========================
function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-panel');

  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;

      // Deactivate all
      tabBtns.forEach(b => b.classList.remove('active'));
      tabPanels.forEach(p => p.classList.remove('active'));

      // Activate selected
      btn.classList.add('active');
      const panel = document.getElementById(`panel-${target}`);
      if (panel) {
        panel.classList.add('active');
      }

      // Load graph data when switching to graph tab
      if (target === 'graph') {
        loadGraph();
      }
    });
  });
}

// ========================
// TOAST NOTIFICATIONS
// ========================
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  toast.innerHTML = `<span>${icons[type] || ''}</span><span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s forwards';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ========================
// IMAGE UPLOAD
// ========================
let selectedFile = null;

function initUpload() {
  const zone = document.getElementById('upload-zone');
  const input = document.getElementById('upload-input');
  const preview = document.getElementById('upload-preview');
  const previewThumb = document.getElementById('preview-thumb');
  const previewName = document.getElementById('preview-name');
  const previewSize = document.getElementById('preview-size');
  const removeBtn = document.getElementById('preview-remove');
  const uploadBtn = document.getElementById('btn-upload');

  // Click to select
  zone.addEventListener('click', () => input.click());

  // File selected
  input.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  });

  // Drag & drop
  zone.addEventListener('dragover', (e) => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });

  zone.addEventListener('dragleave', () => {
    zone.classList.remove('drag-over');
  });

  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
    }
  });

  // Remove file
  removeBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    clearFile();
  });

  // Upload button
  uploadBtn.addEventListener('click', () => uploadImage());

  function setFile(file) {
    // Validate image types
    if (!file.type.startsWith('image/')) {
      showToast('Please pick an image file! 🖼️', 'error');
      return;
    }

    selectedFile = file;
    previewName.textContent = file.name;
    previewSize.textContent = formatFileSize(file.size);

    // Show thumbnail
    const reader = new FileReader();
    reader.onload = (e) => {
      previewThumb.src = e.target.result;
    };
    reader.readAsDataURL(file);

    preview.classList.add('visible');
    uploadBtn.disabled = false;
  }

  function clearFile() {
    selectedFile = null;
    input.value = '';
    preview.classList.remove('visible');
    previewThumb.src = '';
    uploadBtn.disabled = true;
  }
}

async function uploadImage() {
  if (!selectedFile) {
    showToast('Please pick an image first! 📷', 'error');
    return;
  }

  const userId = document.getElementById('input-userid').value.trim() || 'kid_user';
  const source = document.getElementById('input-source').value.trim() || 'browser_upload';

  const status = document.getElementById('upload-status');
  const uploadBtn = document.getElementById('btn-upload');

  // Show loading
  status.className = 'upload-status visible loading';
  status.innerHTML = `
    <div class="spinner"></div>
    <div class="status-text">🧠 Processing your image...</div>
    <div class="status-sub">Our AI is reading, understanding, and memorizing it!</div>
  `;
  uploadBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append('image', selectedFile);
    formData.append('user_id', userId);
    formData.append('source', source);

    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) throw new Error(`Upload failed: ${response.status}`);

    const data = await response.json();

    // Success
    status.className = 'upload-status visible success';
    status.innerHTML = `
      <span class="status-icon">🎉</span>
      <div class="status-text">Memory saved!</div>
      <div class="status-sub">Image ID: ${data.image_id ? data.image_id.substring(0, 8) + '...' : 'saved'}</div>
    `;

    showToast('Image memorized successfully! 🧠✨', 'success');

    // Clear after delay
    setTimeout(() => {
      selectedFile = null;
      document.getElementById('upload-input').value = '';
      document.getElementById('upload-preview').classList.remove('visible');
      status.className = 'upload-status';
      uploadBtn.disabled = true;
    }, 4000);

  } catch (error) {
    status.className = 'upload-status visible error';
    status.innerHTML = `
      <span class="status-icon">😕</span>
      <div class="status-text">Something went wrong</div>
      <div class="status-sub">${error.message}</div>
    `;
    showToast('Upload failed. Please try again!', 'error');
    uploadBtn.disabled = false;
  }
}

// ========================
// SEARCH
// ========================
function initSearch() {
  const searchInput = document.getElementById('search-input');
  const searchBtn = document.getElementById('btn-search');

  searchBtn.addEventListener('click', () => performSearch());

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') performSearch();
  });
}

async function performSearch() {
  const query = document.getElementById('search-input').value.trim();
  const resultsContainer = document.getElementById('search-results');

  if (!query) {
    showToast('Type something to search! 🔍', 'info');
    return;
  }

  // Show loading
  resultsContainer.innerHTML = `
    <div class="search-empty">
      <div class="spinner"></div>
      <div style="margin-top: 16px;">Searching your memories...</div>
    </div>
  `;

  try {
    const response = await fetch(`/api/search?query=${encodeURIComponent(query)}&limit=10`);
    if (!response.ok) throw new Error(`Search failed: ${response.status}`);

    const data = await response.json();
    const results = data.results || [];

    if (results.length === 0) {
      resultsContainer.innerHTML = `
        <div class="search-empty">
          <span class="search-empty-icon">🔮</span>
          <div>No memories found for "<strong>${escapeHtml(query)}</strong>"</div>
          <div style="font-size: 0.85rem; margin-top: 4px;">Try uploading more images or using different words!</div>
        </div>
      `;
      return;
    }

    resultsContainer.innerHTML = '';
    results.forEach((result, index) => {
      const card = createResultCard(result, index);
      resultsContainer.appendChild(card);
    });

    showToast(`Found ${results.length} memor${results.length === 1 ? 'y' : 'ies'}! ✨`, 'success');

  } catch (error) {
    resultsContainer.innerHTML = `
      <div class="search-empty">
        <span class="search-empty-icon">😕</span>
        <div>Search failed: ${escapeHtml(error.message)}</div>
      </div>
    `;
    showToast('Search failed. Is the server running?', 'error');
  }
}

function createResultCard(result, index) {
  const card = document.createElement('div');
  card.className = 'result-card';
  card.style.animationDelay = `${index * 0.08}s`;

  // Build image src — try to serve from /uploads/
  const imagePath = result.image_path || '';
  const filename = imagePath.split(/[/\\]/).pop();
  const imgSrc = filename ? `/uploads/${filename}` : '';

  const timeStr = result.timestamp
    ? new Date(result.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : '';

  card.innerHTML = `
    ${imgSrc ? `<img class="result-card-image" src="${imgSrc}" alt="Memory image" onerror="this.style.display='none'">` : ''}
    <div class="result-card-body">
      <div class="result-card-summary">${escapeHtml(result.summary || 'No summary available')}</div>
      <div class="result-card-meta">
        ${result.intent ? `<span class="result-card-intent">${escapeHtml(result.intent)}</span>` : ''}
        ${timeStr ? `<span class="result-card-time">📅 ${timeStr}</span>` : ''}
      </div>
    </div>
  `;

  return card;
}

// ========================
// KNOWLEDGE GRAPH
// ========================
let graphNetwork = null;

async function loadGraph() {
  const canvas = document.getElementById('graph-canvas');
  const statsEl = document.getElementById('graph-stats');

  // Show loading
  canvas.innerHTML = `
    <div class="graph-loading">
      <div class="spinner"></div>
      <div>Building your memory map...</div>
    </div>
  `;

  try {
    const response = await fetch('/api/graph');
    if (!response.ok) throw new Error(`Graph failed: ${response.status}`);

    const data = await response.json();
    const nodesData = data.nodes || [];
    const edgesData = data.edges || [];

    if (nodesData.length === 0) {
      canvas.innerHTML = `
        <div class="graph-empty">
          <span class="graph-empty-icon">🌌</span>
          <div>Your memory universe is empty!</div>
          <div style="font-size: 0.85rem;">Upload some images to see your knowledge graph light up ✨</div>
        </div>
      `;
      statsEl.innerHTML = '';
      return;
    }

    // Clear loading
    canvas.innerHTML = '';

    // Prepare vis.js data
    const imageCount = nodesData.filter(n => n.type === 'image').length;
    const entityCount = nodesData.filter(n => n.type === 'entity').length;

    const nodes = new vis.DataSet(
      nodesData.map(n => ({
        id: n.id,
        label: n.label,
        color: {
          background: n.type === 'image' ? '#3b82f6' : '#22c55e',
          border: n.type === 'image' ? '#60a5fa' : '#4ade80',
          highlight: {
            background: n.type === 'image' ? '#60a5fa' : '#4ade80',
            border: '#fff'
          },
          hover: {
            background: n.type === 'image' ? '#60a5fa' : '#4ade80',
            border: '#fff'
          }
        },
        font: {
          color: '#e2e8f0',
          size: n.type === 'image' ? 12 : 14,
          face: 'Outfit',
          strokeWidth: 2,
          strokeColor: '#0a0a1a'
        },
        size: n.type === 'image' ? 18 : 22,
        shape: n.type === 'image' ? 'dot' : 'diamond',
        shadow: {
          enabled: true,
          color: n.type === 'image' ? 'rgba(59, 130, 246, 0.4)' : 'rgba(34, 197, 94, 0.4)',
          size: 12
        },
        borderWidth: 2
      }))
    );

    const edges = new vis.DataSet(
      edgesData.map(e => ({
        from: e.from,
        to: e.to,
        color: {
          color: e.type === 'entity_entity' ? 'rgba(249, 115, 22, 0.5)' : 'rgba(148, 163, 184, 0.3)',
          highlight: '#fff',
          hover: 'rgba(255, 255, 255, 0.6)'
        },
        width: e.type === 'entity_entity' ? Math.min((e.weight || 1) * 2, 6) : 1.5,
        smooth: {
          type: 'continuous',
          roundness: 0.3
        },
        arrows: e.type === 'image_entity' ? { to: { enabled: true, scaleFactor: 0.5 } } : {}
      }))
    );

    const options = {
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -4000,
          centralGravity: 0.2,
          springLength: 120,
          springConstant: 0.02,
          damping: 0.15
        },
        stabilization: {
          iterations: 200,
          fit: true
        }
      },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        navigationButtons: false,
        keyboard: true,
        zoomSpeed: 0.6
      },
      nodes: {
        borderWidthSelected: 3
      },
      layout: {
        improvedLayout: true
      }
    };

    graphNetwork = new vis.Network(canvas, { nodes, edges }, options);

    // Update stats
    statsEl.innerHTML = `
      <span class="graph-stat">🖼️ Images: <span class="graph-stat-value">${imageCount}</span></span>
      <span class="graph-stat">💎 Concepts: <span class="graph-stat-value">${entityCount}</span></span>
      <span class="graph-stat">🔗 Connections: <span class="graph-stat-value">${edgesData.length}</span></span>
    `;

  } catch (error) {
    canvas.innerHTML = `
      <div class="graph-empty">
        <span class="graph-empty-icon">😕</span>
        <div>Could not load the memory graph</div>
        <div style="font-size: 0.85rem;">${escapeHtml(error.message)}</div>
      </div>
    `;
    showToast('Graph loading failed', 'error');
  }
}

// ========================
// UTILITIES
// ========================
function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

// ========================
// INIT
// ========================
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  initUpload();
  initSearch();
});
