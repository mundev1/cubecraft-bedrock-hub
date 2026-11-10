/**
 * CubeCraft Bedrock Community Hub - Client Application
 * Modular ES6 architecture handling Leaderboards, Bundles Showcase,
 * Playable Medal Clips Theatre, and Player Encounter Reviews.
 */

// Application State
const state = {
  currentView: 'leaderboards',
  selectedGame: 'EggWars',
  selectedMode: 'All Modes',
  leaderboardSort: 'wins',
  leaderboardSearch: '',
  bundles: [],
  clips: [],
  clipsFilterGame: 'all',
  clipsSort: 'recent',
  activePlayer: null,
  recentEncounters: [],
  encounterTagFilter: 'all',
  activeModal: null,
  activeVideoClip: null
};

// Utilities
function showToast(message, duration = 3000) {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerText = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, duration);
}

function copyToClipboard(text, msg = 'Copied to clipboard!') {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => showToast(msg));
  } else {
    showToast(msg);
  }
}

function formatNumber(num) {
  return (num || 0).toLocaleString();
}

function sanitizeHTML(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}

// ==========================================================================
// Initialization & Navigation
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initServerPill();
  loadGlobalStats();
  loadGamesList();
  loadLeaderboards();
  loadBundles();
  loadClips();
  loadRecentEncounters();
  initModalListeners();
  initSearchAutocomplete();
  startBundleCountdownTimer();

  // Handle URL hash changes
  window.addEventListener('hashchange', handleHashRouting);
  handleHashRouting();
});

function handleHashRouting() {
  const hash = window.location.hash.slice(1);
  if (!hash) {
    switchView('leaderboards');
    return;
  }

  if (hash.startsWith('player/')) {
    const gamertag = decodeURIComponent(hash.split('/')[1]);
    switchView('encounters');
    loadPlayerProfile(gamertag);
  } else if (['leaderboards', 'bundles', 'clips', 'encounters'].includes(hash)) {
    switchView(hash);
  }
}

function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = item.getAttribute('data-view');
      window.location.hash = targetView;
    });
  });
}

function switchView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.view-section').forEach(sec => sec.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('data-view') === viewName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  const activeSection = document.getElementById(`view-${viewName}`);
  if (activeSection) {
    activeSection.classList.add('active');
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function initServerPill() {
  const serverPill = document.getElementById('server-pill');
  if (serverPill) {
    serverPill.addEventListener('click', () => {
      copyToClipboard('play.cubecraft.net', 'Copied play.cubecraft.net (Port 19132) to clipboard!');
    });
  }
}

async function loadGlobalStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    if (data.success) {
      const s = data.stats;
      document.getElementById('stat-players-count').innerText = formatNumber(s.total_players);
      document.getElementById('stat-encounters-count').innerText = formatNumber(s.total_encounters);
      document.getElementById('stat-clips-count').innerText = formatNumber(s.total_clips);
      document.getElementById('stat-bundles-count').innerText = s.active_bundles;
    }
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

// ==========================================================================
// Leaderboards View
// ==========================================================================

async function loadGamesList() {
  try {
    const res = await fetch('/api/games');
    const data = await res.json();
    if (!data.success) return;

    const container = document.getElementById('game-selector-grid');
    if (!container) return;

    container.innerHTML = data.games.map(game => `
      <div class="game-card-btn ${game.name === state.selectedGame ? 'active' : ''}" data-game="${game.name}">
        <span class="game-card-icon">${game.icon}</span>
        <span class="game-card-name">${game.name}</span>
      </div>
    `).join('');

    container.querySelectorAll('.game-card-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        container.querySelectorAll('.game-card-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.selectedGame = btn.getAttribute('data-game');
        state.selectedMode = 'All Modes';
        loadLeaderboards();
      });
    });
  } catch (err) {
    console.error('Failed to load games:', err);
  }
}

async function loadLeaderboards() {
  const tableBody = document.getElementById('leaderboard-table-body');
  const podiumContainer = document.getElementById('podium-container');
  if (!tableBody || !podiumContainer) return;

  tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-subtle);">Fetching Bedrock leaderboards...</td></tr>`;

  try {
    const url = `/api/leaderboards?game=${encodeURIComponent(state.selectedGame)}&mode=${encodeURIComponent(state.selectedMode)}&sort_by=${state.leaderboardSort}&search=${encodeURIComponent(state.leaderboardSearch)}`;
    const res = await fetch(url);
    const data = await res.json();

    if (!data.success || data.leaderboard.length === 0) {
      podiumContainer.innerHTML = '';
      tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem; color: var(--text-subtle);">No players found matching current filters.</td></tr>`;
      return;
    }

    renderPodium(data.podium);
    renderLeaderboardTable(data.leaderboard);
  } catch (err) {
    console.error('Failed to load leaderboards:', err);
    tableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 2rem; color: #f43f5e;">Error loading leaderboards.</td></tr>`;
  }
}

function renderPodium(podium) {
  const container = document.getElementById('podium-container');
  if (!container) return;

  if (podium.length < 3) {
    container.innerHTML = '';
    return;
  }

  container.innerHTML = podium.map((p, index) => {
    const rank = index + 1;
    const initial = p.player_gamertag.charAt(0).toUpperCase();
    return `
      <div class="podium-card rank-${rank}">
        <div class="podium-rank-badge">#${rank}</div>
        <div class="player-avatar-box" style="background: ${p.avatar_color || '#00e5ff'};">
          ${initial}
        </div>
        <a href="#player/${encodeURIComponent(p.player_gamertag)}" class="podium-name">
          ${sanitizeHTML(p.player_gamertag)}
        </a>
        <div>
          <span class="podium-rank-title">${p.rank_title || 'Player'}</span>
        </div>
        <div class="podium-stats">
          <div class="stat-item">
            <span class="stat-val">${formatNumber(p.wins)}</span>
            <span class="stat-lbl">Wins</span>
          </div>
          <div class="stat-item">
            <span class="stat-val">${formatNumber(p.kills)}</span>
            <span class="stat-lbl">Kills</span>
          </div>
          <div class="stat-item">
            <span class="stat-val">${p.streak}🔥</span>
            <span class="stat-lbl">Streak</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderLeaderboardTable(rows) {
  const tableBody = document.getElementById('leaderboard-table-body');
  if (!tableBody) return;

  tableBody.innerHTML = rows.map((r) => {
    const initial = r.player_gamertag.charAt(0).toUpperCase();
    return `
      <tr>
        <td class="td-rank">#${r.dynamic_rank}</td>
        <td>
          <div class="td-player">
            <div class="player-mini-avatar" style="background: ${r.avatar_color || '#00e5ff'};">
              ${initial}
            </div>
            <div class="player-info-meta">
              <a href="#player/${encodeURIComponent(r.player_gamertag)}" class="player-link">
                ${sanitizeHTML(r.player_gamertag)}
              </a>
              <div>
                <span class="rep-pill positive">⭐ ${r.reputation_score || 100}% Rep (${r.encounter_count || 0})</span>
              </div>
            </div>
          </div>
        </td>
        <td><span class="podium-rank-title">${r.rank_title || 'Player'}</span></td>
        <td style="font-weight: 700; color: #fff;">${formatNumber(r.wins)}</td>
        <td>${formatNumber(r.kills)}</td>
        <td>${r.streak ? `${r.streak} W` : '-'}</td>
        <td style="color: var(--accent-cyan); font-weight: 600;">${r.favorite_kit || 'Standard'}</td>
      </tr>
    `;
  }).join('');
}

// Leaderboard Sort & Search Listeners
document.querySelectorAll('.lb-sort-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.lb-sort-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.leaderboardSort = btn.getAttribute('data-sort');
    loadLeaderboards();
  });
});

const lbSearchInput = document.getElementById('lb-search-input');
if (lbSearchInput) {
  lbSearchInput.addEventListener('input', (e) => {
    state.leaderboardSearch = e.target.value;
    loadLeaderboards();
  });
}

// ==========================================================================
// Bundles Showcase View
// ==========================================================================

async function loadBundles() {
  const container = document.getElementById('bundles-grid');
  if (!container) return;

  try {
    const res = await fetch('/api/bundles');
    const data = await res.json();
    if (!data.success) return;

    state.bundles = data.bundles;
    renderBundles();
  } catch (err) {
    console.error('Failed to load bundles:', err);
  }
}

function renderBundles() {
  const container = document.getElementById('bundles-grid');
  if (!container) return;

  // Modern abstract fallback backgrounds for bundles
  const bgGradients = {
    'Mythic': 'linear-gradient(135deg, #2e1065 0%, #0b0f19 100%)',
    'Legendary': 'linear-gradient(135deg, #451a03 0%, #0b0f19 100%)',
    'Epic': 'linear-gradient(135deg, #083344 0%, #0b0f19 100%)',
    'Rare': 'linear-gradient(135deg, #064e3b 0%, #0b0f19 100%)'
  };

  container.innerHTML = state.bundles.map(b => {
    const rarityClass = `rarity-${(b.rarity || 'epic').toLowerCase()}`;
    const gradient = bgGradients[b.rarity] || bgGradients['Epic'];

    return `
      <div class="bundle-card">
        <div class="bundle-banner" style="background: ${gradient};">
          <span class="bundle-badge ${b.is_featured ? 'featured' : 'new'}">${sanitizeHTML(b.badge || 'Store Drop')}</span>
          <div class="bundle-timer" data-expiry="${b.expiry_date}">
            ⏳ <span class="timer-display">Calculating...</span>
          </div>
        </div>
        <div class="bundle-content">
          <div class="bundle-rarity ${rarityClass}">${b.rarity} Bedrock Cosmetic</div>
          <h3 class="bundle-title">${sanitizeHTML(b.title)}</h3>
          <p class="bundle-desc">${sanitizeHTML(b.tagline || b.description)}</p>

          <div class="bundle-items-preview">
            ${(b.items || []).slice(0, 3).map(i => `
              <span class="bundle-item-pill">✨ ${sanitizeHTML(i.name)} (${i.type})</span>
            `).join('')}
            ${(b.items || []).length > 3 ? `<span class="bundle-item-pill">+${b.items.length - 3} more</span>` : ''}
          </div>

          <div class="bundle-footer">
            <div class="bundle-price">
              <span class="price-current">🪙 ${formatNumber(b.price_minecoins)}</span>
              ${b.original_price ? `<span class="price-orig">🪙 ${formatNumber(b.original_price)}</span>` : ''}
            </div>
            <button class="btn btn-outline btn-sm inspect-bundle-btn" data-id="${b.id}">
              Inspect Bundle
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  container.querySelectorAll('.inspect-bundle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const bundleId = btn.getAttribute('data-id');
      inspectBundle(bundleId);
    });
  });

  updateCountdownDisplays();
}

function startBundleCountdownTimer() {
  setInterval(updateCountdownDisplays, 1000);
}

function updateCountdownDisplays() {
  document.querySelectorAll('.bundle-timer').forEach(timerEl => {
    const expiryStr = timerEl.getAttribute('data-expiry');
    if (!expiryStr) return;
    const diff = new Date(expiryStr).getTime() - Date.now();
    const display = timerEl.querySelector('.timer-display');
    if (!display) return;

    if (diff <= 0) {
      display.innerText = 'Vaulted';
      timerEl.style.color = '#f43f5e';
    } else {
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);
      display.innerText = `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }
  });
}

function inspectBundle(bundleId) {
  const bundle = state.bundles.find(b => b.id === bundleId);
  if (!bundle) return;

  const modal = document.getElementById('bundle-modal');
  const title = document.getElementById('bundle-modal-title');
  const body = document.getElementById('bundle-modal-body');

  title.innerText = bundle.title;
  body.innerHTML = `
    <div style="margin-bottom: 1.25rem;">
      <span class="bundle-rarity rarity-${(bundle.rarity || 'epic').toLowerCase()}">${bundle.rarity} Edition</span>
      <p style="color: var(--text-muted); margin-top: 0.5rem; font-size: 0.92rem;">${sanitizeHTML(bundle.description)}</p>
    </div>
    
    <h4 style="font-size: 0.95rem; margin-bottom: 0.75rem; text-transform: uppercase; color: var(--text-subtle); letter-spacing: 0.05em;">Cosmetics Included</h4>
    <div style="display: flex; flex-direction: column; gap: 0.75rem;">
      ${(bundle.items || []).map(item => `
        <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 0.85rem 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem;">
            <strong style="color: var(--accent-cyan); font-size: 0.95rem;">${sanitizeHTML(item.name)}</strong>
            <span class="bundle-item-pill">${item.type}</span>
          </div>
          <p style="font-size: 0.82rem; color: var(--text-muted);">${sanitizeHTML(item.desc)}</p>
        </div>
      `).join('')}
    </div>

    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border-subtle);">
      <div>
        <span style="font-size: 0.75rem; color: var(--text-subtle); text-transform: uppercase;">Store Price:</span>
        <div style="font-size: 1.35rem; font-weight: 800; color: #fbbf24;">🪙 ${formatNumber(bundle.price_minecoins)} Minecoins</div>
      </div>
      <button class="btn btn-primary" onclick="showToast('Available in CubeCraft Bedrock Marketplace store!')">
        Get in Minecraft Bedrock
      </button>
    </div>
  `;

  openModal(modal);
}

// ==========================================================================
// Medal Clips Theatre View
// ==========================================================================

async function loadClips() {
  const container = document.getElementById('clips-grid');
  if (!container) return;

  try {
    const url = `/api/clips?game=${encodeURIComponent(state.clipsFilterGame)}&sort=${state.clipsSort}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) return;

    state.clips = data.clips;
    renderClips();
  } catch (err) {
    console.error('Failed to load clips:', err);
  }
}

function renderClips() {
  const container = document.getElementById('clips-grid');
  if (!container) return;

  if (state.clips.length === 0) {
    container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-subtle);">No Bedrock clips found. Be the first to submit a clip!</div>`;
    return;
  }

  container.innerHTML = state.clips.map(clip => `
    <div class="clip-card" data-id="${clip.id}">
      <div class="clip-thumb-box" style="background-image: url('${clip.thumbnail_url}');" data-id="${clip.id}">
        <span class="clip-game-badge">${sanitizeHTML(clip.game)}</span>
        <div class="play-overlay-btn">▶</div>
        <span class="clip-duration-badge">${clip.duration || '0:30'}</span>
      </div>
      <div class="clip-body">
        <h4 class="clip-title" title="${sanitizeHTML(clip.title)}">${sanitizeHTML(clip.title)}</h4>
        <div class="clip-meta-row">
          <div class="clip-author">
            <span>By</span>
            <a href="#player/${encodeURIComponent(clip.gamertag)}">${sanitizeHTML(clip.gamertag)}</a>
          </div>
          <div class="clip-actions">
            <span style="font-size: 0.75rem; color: var(--text-subtle);">👁️ ${formatNumber(clip.views)}</span>
            <button class="upvote-btn" data-id="${clip.id}">
              ▲ <span class="upvote-count">${clip.upvotes}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  `).join('');

  // Attach card click handlers for video player
  container.querySelectorAll('.clip-thumb-box').forEach(el => {
    el.addEventListener('click', () => {
      const clipId = parseInt(el.getAttribute('data-id'), 10);
      playClip(clipId);
    });
  });

  // Attach upvote handlers
  container.querySelectorAll('.upvote-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const clipId = parseInt(btn.getAttribute('data-id'), 10);
      upvoteClip(clipId, btn);
    });
  });
}

function playClip(clipId) {
  const clip = state.clips.find(c => c.id === clipId);
  if (!clip) return;

  state.activeVideoClip = clip;
  fetch(`/api/clips/${clip.id}/view`, { method: 'POST' }).catch(() => {});

  const modal = document.getElementById('video-modal');
  const title = document.getElementById('video-modal-title');
  const playerContainer = document.getElementById('video-modal-player');
  const meta = document.getElementById('video-modal-meta');

  title.innerText = clip.title;

  // If Medal embed URL is present, or direct video URL fallback
  if (clip.medal_url && clip.medal_url.includes('medal.tv/clip/')) {
    // Medal embed format
    const embedUrl = clip.medal_url.replace('/games/', '/clip/').replace('medal.tv/games/', 'medal.tv/clip/');
    playerContainer.innerHTML = `
      <iframe src="${embedUrl}?autoplay=1&muted=0&loop=1" allow="autoplay" allowfullscreen></iframe>
    `;
  } else {
    // Custom HTML5 video player with theater mode controls
    const vidUrl = clip.video_url || 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4';
    playerContainer.innerHTML = `
      <video id="active-html5-video" controls autoplay playsinline style="width: 100%; height: 100%; border-radius: 8px;">
        <source src="${vidUrl}" type="video/mp4">
        Your browser does not support Bedrock video clips.
      </video>
    `;
  }

  meta.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-top: 1rem;">
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <span class="bundle-item-pill" style="color: var(--accent-cyan);">${sanitizeHTML(clip.game)}</span>
        <span style="font-size: 0.85rem; color: var(--text-muted);">Recorded by <a href="#player/${encodeURIComponent(clip.gamertag)}" style="color: var(--text-main); font-weight: 700;">${sanitizeHTML(clip.gamertag)}</a></span>
      </div>
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <button class="btn btn-outline btn-sm" id="toggle-theater-btn">Toggle Theater Mode</button>
        <button class="btn btn-primary btn-sm" onclick="copyToClipboard('${clip.medal_url || window.location.href}', 'Clip link copied!')">Share Clip</button>
      </div>
    </div>
  `;

  const theaterBtn = document.getElementById('toggle-theater-btn');
  if (theaterBtn) {
    theaterBtn.addEventListener('click', () => {
      const card = modal.querySelector('.modal-card');
      card.classList.toggle('wide');
      theaterBtn.innerText = card.classList.contains('wide') ? 'Standard View' : 'Theater View';
    });
  }

  openModal(modal);
}

async function upvoteClip(clipId, btn) {
  try {
    const res = await fetch(`/api/clips/${clipId}/upvote`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      btn.classList.add('upvoted');
      const countEl = btn.querySelector('.upvote-count');
      if (countEl) countEl.innerText = data.upvotes;
      showToast('Clip upvoted!');
    }
  } catch (err) {
    console.error('Failed to upvote clip:', err);
  }
}

// Clip Filter Listeners
document.querySelectorAll('.clip-game-filter').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.clip-game-filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.clipsFilterGame = btn.getAttribute('data-game');
    loadClips();
  });
});

// Submit Clip Form
const submitClipForm = document.getElementById('submit-clip-form');
if (submitClipForm) {
  submitClipForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      title: document.getElementById('clip-input-title').value.trim(),
      gamertag: document.getElementById('clip-input-gamertag').value.trim(),
      game: document.getElementById('clip-input-game').value,
      medal_url: document.getElementById('clip-input-url').value.trim(),
      duration: document.getElementById('clip-input-duration').value.trim() || '0:30'
    };

    try {
      const res = await fetch('/api/clips', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        showToast('Medal clip submitted successfully!');
        closeAllModals();
        submitClipForm.reset();
        loadClips();
      } else {
        alert(data.error || 'Failed to submit clip');
      }
    } catch (err) {
      console.error('Failed to submit clip:', err);
    }
  });
}

// ==========================================================================
// Player Encounters & Reputation View
// ==========================================================================

async function loadRecentEncounters() {
  const container = document.getElementById('recent-encounters-list');
  if (!container) return;

  try {
    const res = await fetch(`/api/encounters/recent?tag=${encodeURIComponent(state.encounterTagFilter)}`);
    const data = await res.json();
    if (!data.success) return;

    state.recentEncounters = data.encounters;
    renderRecentEncounters();
  } catch (err) {
    console.error('Failed to load recent encounters:', err);
  }
}

function getTagClass(type) {
  if (type.includes('Clutch')) return 'tag-clutch';
  if (type.includes('Teammate') || type.includes('Wholesome')) return 'tag-teammate';
  if (type.includes('Sweat')) return 'tag-sweat';
  if (type.includes('Trapper')) return 'tag-trapper';
  if (type.includes('Suspicious') || type.includes('Cheater')) return 'tag-sus';
  return 'tag-clutch';
}

function renderRecentEncounters() {
  const container = document.getElementById('recent-encounters-list');
  if (!container) return;

  if (state.recentEncounters.length === 0) {
    container.innerHTML = `<div style="text-align: center; padding: 2.5rem; color: var(--text-subtle);">No encounters logged for this category yet. Be the first to share an encounter!</div>`;
    return;
  }

  container.innerHTML = state.recentEncounters.map(enc => `
    <div class="encounter-card" id="encounter-${enc.id}">
      <div class="encounter-top">
        <div class="encounter-player-target">
          <span style="font-size: 0.85rem; color: var(--text-subtle);">Player Encounter:</span>
          <a href="#player/${encodeURIComponent(enc.player_gamertag)}" class="target-link">
            ${sanitizeHTML(enc.player_gamertag)}
          </a>
          <span class="encounter-tag-pill ${getTagClass(enc.encounter_type)}">
            ${sanitizeHTML(enc.encounter_type)}
          </span>
        </div>
        <div style="font-size: 0.82rem; color: #fbbf24;">
          ${'★'.repeat(enc.rating)}${'☆'.repeat(5 - enc.rating)}
        </div>
      </div>
      <p class="encounter-text">"${sanitizeHTML(enc.comment)}"</p>
      <div class="encounter-meta">
        <div>
          <span>In ${sanitizeHTML(enc.game_played)}</span>
          <span style="margin: 0 6px;">•</span>
          <span>Logged by <strong>${sanitizeHTML(enc.reviewer_name)}</strong></span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
          <button class="helpful-btn" onclick="upvoteEncounter(${enc.id})">
            👍 Helpful (${enc.helpful_votes || 0})
          </button>
          <button class="helpful-btn" style="color: var(--text-subtle);" onclick="reportEncounter(${enc.id})">
            Flag
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

async function loadPlayerProfile(gamertag) {
  const profileSection = document.getElementById('player-profile-view');
  if (!profileSection) return;

  profileSection.style.display = 'block';
  profileSection.scrollIntoView({ behavior: 'smooth' });

  try {
    const res = await fetch(`/api/players/${encodeURIComponent(gamertag)}`);
    const data = await res.json();
    if (!data.success) return;

    state.activePlayer = data;
    renderPlayerProfile();
  } catch (err) {
    console.error('Failed to load player profile:', err);
  }
}

function renderPlayerProfile() {
  const p = state.activePlayer.player;
  const s = state.activePlayer.stats;
  const encounters = state.activePlayer.encounters;

  document.getElementById('profile-gamertag').innerText = p.gamertag;
  document.getElementById('profile-rank-title').innerText = p.rank_title || 'Bedrock Player';
  document.getElementById('profile-bio').innerText = p.bio || 'Minecraft Bedrock CubeCraft Player.';
  document.getElementById('profile-score-num').innerText = `${p.reputation_score}%`;
  document.getElementById('profile-avatar').innerText = p.gamertag.charAt(0).toUpperCase();
  document.getElementById('profile-avatar').style.backgroundColor = p.avatar_color || '#00e5ff';

  // Badges
  const badgesContainer = document.getElementById('profile-badges');
  if (badgesContainer) {
    badgesContainer.innerHTML = s.badges.map(b => `
      <span class="bundle-item-pill" style="border-color: ${b.color}; color: ${b.color}; font-weight: 700;">
        ${b.icon} ${b.name}
      </span>
    `).join('');
  }

  // Pre-fill encounter modal button
  const logBtn = document.getElementById('log-encounter-for-player-btn');
  if (logBtn) {
    logBtn.onclick = () => openEncounterModal(p.gamertag);
  }

  // Render player encounters list
  const listContainer = document.getElementById('player-specific-encounters-list');
  if (listContainer) {
    if (encounters.length === 0) {
      listContainer.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-subtle);">No encounters logged yet for ${sanitizeHTML(p.gamertag)}. Be the first!</div>`;
    } else {
      listContainer.innerHTML = encounters.map(enc => `
        <div class="encounter-card" style="margin-bottom: 1rem;">
          <div class="encounter-top">
            <span class="encounter-tag-pill ${getTagClass(enc.encounter_type)}">${sanitizeHTML(enc.encounter_type)}</span>
            <div style="font-size: 0.82rem; color: #fbbf24;">${'★'.repeat(enc.rating)}${'☆'.repeat(5 - enc.rating)}</div>
          </div>
          <p class="encounter-text">"${sanitizeHTML(enc.comment)}"</p>
          <div class="encounter-meta">
            <span>Encountered in <strong>${sanitizeHTML(enc.game_played)}</strong> by <strong>${sanitizeHTML(enc.reviewer_name)}</strong></span>
            <button class="helpful-btn" onclick="upvoteEncounter(${enc.id})">👍 Helpful (${enc.helpful_votes || 0})</button>
          </div>
        </div>
      `).join('');
    }
  }
}

// Encounter Upvoting & Reporting
async function upvoteEncounter(id) {
  try {
    const res = await fetch(`/api/encounters/${id}/helpful`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('Marked encounter as helpful!');
      loadRecentEncounters();
      if (state.activePlayer) {
        loadPlayerProfile(state.activePlayer.player.gamertag);
      }
    }
  } catch (err) {
    console.error('Failed to upvote encounter:', err);
  }
}

async function reportEncounter(id) {
  if (!confirm('Report this comment for violating community guidelines?')) return;
  try {
    const res = await fetch(`/api/encounters/${id}/report`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('Encounter comment reported.');
      loadRecentEncounters();
    }
  } catch (err) {
    console.error('Failed to report encounter:', err);
  }
}

// Encounter Modal Logic
function openEncounterModal(gamertag = '') {
  const modal = document.getElementById('encounter-modal');
  const inputGamertag = document.getElementById('encounter-input-gamertag');
  if (inputGamertag) {
    inputGamertag.value = gamertag;
  }
  openModal(modal);
}

const submitEncounterForm = document.getElementById('submit-encounter-form');
if (submitEncounterForm) {
  submitEncounterForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const gamertag = document.getElementById('encounter-input-gamertag').value.trim();
    if (!gamertag) {
      alert('Please enter a player gamertag');
      return;
    }

    const payload = {
      reviewer_name: document.getElementById('encounter-input-reviewer').value.trim() || 'Anonymous Bedrocker',
      game_played: document.getElementById('encounter-input-game').value,
      encounter_type: document.getElementById('encounter-input-type').value,
      rating: parseInt(document.getElementById('encounter-input-rating').value, 10),
      comment: document.getElementById('encounter-input-comment').value.trim()
    };

    try {
      const res = await fetch(`/api/players/${encodeURIComponent(gamertag)}/encounters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        showToast(data.message);
        closeAllModals();
        submitEncounterForm.reset();
        loadRecentEncounters();
        loadGlobalStats();
        // Load the profile if user is viewing encounters
        loadPlayerProfile(gamertag);
      } else {
        alert(data.error || 'Failed to submit encounter review');
      }
    } catch (err) {
      console.error('Failed to post encounter:', err);
    }
  });
}

// Encounter Tag Filter Buttons
document.querySelectorAll('.enc-tag-filter').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.enc-tag-filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.encounterTagFilter = btn.getAttribute('data-tag');
    loadRecentEncounters();
  });
});

// Search Autocomplete for Gamertags
function initSearchAutocomplete() {
  const searchInput = document.getElementById('global-gamertag-search');
  const resultsDropdown = document.getElementById('search-autocomplete-dropdown');
  if (!searchInput || !resultsDropdown) return;

  let debounceTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const query = searchInput.value.trim();
    if (query.length < 2) {
      resultsDropdown.style.display = 'none';
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/players/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();
        if (data.success && data.players.length > 0) {
          resultsDropdown.innerHTML = data.players.map(p => `
            <div class="search-result-item" style="padding: 0.6rem 0.85rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-subtle);" data-gamertag="${p.gamertag}">
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span class="player-mini-avatar" style="background: ${p.avatar_color || '#00e5ff'}; width: 24px; height: 24px; font-size: 0.7rem;">${p.gamertag.charAt(0)}</span>
                <span style="font-weight: 600; color: #fff;">${sanitizeHTML(p.gamertag)}</span>
              </div>
              <span class="rep-pill positive" style="font-size: 0.65rem;">⭐ ${p.reputation_score}% Rep</span>
            </div>
          `).join('');

          resultsDropdown.style.display = 'block';

          resultsDropdown.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => {
              const tag = item.getAttribute('data-gamertag');
              searchInput.value = '';
              resultsDropdown.style.display = 'none';
              window.location.hash = `player/${encodeURIComponent(tag)}`;
            });
          });
        } else {
          resultsDropdown.innerHTML = `
            <div style="padding: 0.75rem; font-size: 0.82rem; color: var(--text-muted); text-align: center;">
              No records for "${sanitizeHTML(query)}".
              <button class="btn btn-outline btn-sm" style="margin-top: 0.5rem; width: 100%;" onclick="openEncounterModal('${sanitizeHTML(query)}'); document.getElementById('search-autocomplete-dropdown').style.display='none';">
                + Log First Encounter
              </button>
            </div>
          `;
          resultsDropdown.style.display = 'block';
        }
      } catch (err) {
        console.error('Search error:', err);
      }
    }, 200);
  });

  document.addEventListener('click', (e) => {
    if (!searchInput.contains(e.target) && !resultsDropdown.contains(e.target)) {
      resultsDropdown.style.display = 'none';
    }
  });
}

// ==========================================================================
// Modal Helpers
// ==========================================================================

function openModal(modal) {
  if (!modal) return;
  closeAllModals();
  modal.classList.add('active');
  state.activeModal = modal;
}

function closeAllModals() {
  document.querySelectorAll('.modal-overlay').forEach(m => {
    m.classList.remove('active');
    // Stop any playing video
    const vid = m.querySelector('video');
    if (vid) vid.pause();
    const iframe = m.querySelector('iframe');
    if (iframe) iframe.src = '';
  });
  state.activeModal = null;
}

function initModalListeners() {
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeAllModals();
    });
  });

  document.querySelectorAll('.close-btn').forEach(btn => {
    btn.addEventListener('click', closeAllModals);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAllModals();
  });

  // Modal triggers
  const submitClipBtn = document.getElementById('open-submit-clip-modal-btn');
  if (submitClipBtn) {
    submitClipBtn.addEventListener('click', () => {
      openModal(document.getElementById('submit-clip-modal'));
    });
  }

  const logEncounterBtn = document.getElementById('open-log-encounter-modal-btn');
  if (logEncounterBtn) {
    logEncounterBtn.addEventListener('click', () => {
      openEncounterModal();
    });
  }
}
