/**
 * CubeCraft Bedrock Community Hub - Client Application
 * Modular ES6 architecture handling 39 Game Mode Leaderboards, 800+ Players,
 * Bundles Showcase, Playable Medal & Community Clips Theatre, and Encounters.
 */

// Application State
const state = {
  currentView: 'leaderboards',
  gamesList: [],
  selectedGame: 'EggWars',
  selectedMode: 'All Modes',
  leaderboardSort: 'points',
  leaderboardSearch: '',
  bundles: [],
  clips: [],
  clipsFilterGame: 'all',
  clipsFilterType: 'all',
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

function extractYouTubeId(url) {
  if (!url) return null;
  const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
  return match ? match[1] : null;
}

// ==========================================================================
// Initialization & Navigation
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initServerPill();
  loadGlobalStats();
  loadGamesList();
  loadBundles();
  loadClips();
  loadRecentEncounters();
  initModalListeners();
  initSearchAutocomplete();
  initCommunityClipSubmissions();
  startBundleCountdownTimer();

  // Live leaderboards sync button
  const syncBtn = document.getElementById('sync-leaderboards-btn');
  if (syncBtn) {
    syncBtn.addEventListener('click', async () => {
      syncBtn.innerText = '⏳ Syncing...';
      syncBtn.disabled = true;
      try {
        const res = await fetch('/api/sync-leaderboards', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'Synced live Bedrock leaderboards!');
        loadGlobalStats();
        loadLeaderboards();
      } catch (err) {
        showToast('Sync error. Try again shortly.');
      } finally {
        syncBtn.innerText = '🔄 Live Refresh';
        syncBtn.disabled = false;
      }
    });
  }

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
      document.getElementById('stat-leaderboard-entries').innerText = formatNumber(s.total_leaderboard_entries);
      document.getElementById('stat-encounters-count').innerText = formatNumber(s.total_encounters);
      document.getElementById('stat-clips-count').innerText = formatNumber(s.total_clips);
    }
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

// ==========================================================================
// Leaderboards View & 39 Sub-Modes
// ==========================================================================

async function loadGamesList() {
  try {
    const res = await fetch('/api/games');
    const data = await res.json();
    if (!data.success) return;

    state.gamesList = data.games;
    const container = document.getElementById('game-selector-grid');
    if (!container) return;

    container.innerHTML = state.gamesList.map(game => `
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
        renderSubmodesPills(state.selectedGame);
        loadLeaderboards();
      });
    });

    renderSubmodesPills(state.selectedGame);
    loadLeaderboards();
  } catch (err) {
    console.error('Failed to load games:', err);
  }
}

function renderSubmodesPills(gameName) {
  const container = document.getElementById('submodes-pills-list');
  if (!container) return;

  const game = state.gamesList.find(g => g.name === gameName);
  const modes = game ? game.modes : ['All Modes'];

  container.innerHTML = modes.map(m => `
    <button class="submode-pill ${m === state.selectedMode ? 'active' : ''}" data-mode="${m}">
      ${m}
    </button>
  `).join('');

  container.querySelectorAll('.submode-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      container.querySelectorAll('.submode-pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.selectedMode = pill.getAttribute('data-mode');
      loadLeaderboards();
    });
  });
}

async function loadLeaderboards() {
  const tableBody = document.getElementById('leaderboard-table-body');
  const podiumContainer = document.getElementById('podium-container');
  if (!tableBody || !podiumContainer) return;

  tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-subtle);">Fetching Bedrock leaderboards...</td></tr>`;

  try {
    const url = `/api/leaderboards?game=${encodeURIComponent(state.selectedGame)}&mode=${encodeURIComponent(state.selectedMode)}&sort_by=${state.leaderboardSort}&search=${encodeURIComponent(state.leaderboardSearch)}`;
    const res = await fetch(url);
    const data = await res.json();

    if (!data.success || data.leaderboard.length === 0) {
      podiumContainer.innerHTML = '';
      tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-subtle);">No players found for ${sanitizeHTML(state.selectedGame)} (${sanitizeHTML(state.selectedMode)}).</td></tr>`;
      return;
    }

    renderPodium(data.podium);
    renderLeaderboardTable(data.leaderboard);
  } catch (err) {
    console.error('Failed to load leaderboards:', err);
    tableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 2rem; color: #f43f5e;">Error loading leaderboards.</td></tr>`;
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
    const avatarHtml = p.player_avatar_icon ? `
      <div class="player-avatar-box">
        <img src="${p.player_avatar_icon}" alt="${sanitizeHTML(p.player_gamertag)}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
        <div class="player-avatar-fallback" style="display: none; background: ${p.avatar_color || '#00e5ff'};">${initial}</div>
      </div>
    ` : `
      <div class="player-avatar-box">
        <div class="player-avatar-fallback" style="background: ${p.avatar_color || '#00e5ff'};">${initial}</div>
      </div>
    `;

    return `
      <div class="podium-card rank-${rank}">
        <div class="podium-rank-badge">#${rank}</div>
        ${avatarHtml}
        <a href="#player/${encodeURIComponent(p.player_gamertag)}" class="podium-name">
          ${sanitizeHTML(p.player_gamertag)}
        </a>
        <div>
          <span class="podium-rank-title" style="color: ${p.avatar_color || '#fff'};">${sanitizeHTML(p.rank_title || 'Bedrock Player')}</span>
        </div>
        <div style="font-size: 0.74rem; color: var(--text-subtle); margin-bottom: 0.5rem;">
          ${sanitizeHTML(p.mode)}
        </div>
        <div class="podium-stats">
          <div class="stat-item">
            <span class="stat-val">${formatNumber(p.points || p.wins)}</span>
            <span class="stat-lbl">Points</span>
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
    const avatarHtml = r.player_avatar_icon ? `
      <div class="player-mini-avatar">
        <img src="${r.player_avatar_icon}" alt="${sanitizeHTML(r.player_gamertag)}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
        <div class="player-avatar-fallback" style="display: none; background: ${r.avatar_color || '#00e5ff'}; font-size: 0.9rem;">${initial}</div>
      </div>
    ` : `
      <div class="player-mini-avatar">
        <div class="player-avatar-fallback" style="background: ${r.avatar_color || '#00e5ff'}; font-size: 0.9rem;">${initial}</div>
      </div>
    `;

    return `
      <tr>
        <td class="td-rank">#${r.dynamic_rank}</td>
        <td>
          <div class="td-player">
            ${avatarHtml}
            <div class="player-info-meta">
              <a href="#player/${encodeURIComponent(r.player_gamertag)}" class="player-link">
                ${sanitizeHTML(r.player_gamertag)}
              </a>
              <div>
                <span class="rep-pill positive">⭐ ${r.reputation_score || 100}% Rep (${r.encounter_count || 0} reviews)</span>
              </div>
            </div>
          </div>
        </td>
        <td style="color: var(--text-muted); font-size: 0.82rem;">${sanitizeHTML(r.mode)}</td>
        <td><span class="podium-rank-title" style="color: ${r.avatar_color || '#fff'};">${sanitizeHTML(r.rank_title || 'Player')}</span></td>
        <td style="font-weight: 700; color: #fff;">${formatNumber(r.points || r.wins)}</td>
        <td>${formatNumber(r.kills)}</td>
        <td>${r.streak ? `${r.streak} 🔥` : '-'}</td>
        <td style="color: var(--accent-cyan); font-weight: 600; font-size: 0.82rem;">${sanitizeHTML(r.favorite_kit || 'Standard')}</td>
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
      inspectBundle(btn.getAttribute('data-id'));
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
// Playable Medal & Community Clips View
// ==========================================================================

async function loadClips() {
  const container = document.getElementById('clips-grid');
  if (!container) return;

  try {
    const url = `/api/clips?game=${encodeURIComponent(state.clipsFilterGame)}&type=${encodeURIComponent(state.clipsFilterType)}&sort=${state.clipsSort}`;
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
    container.innerHTML = `<div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-subtle);">No Bedrock clips found for this filter. Use the form above to submit the first clip!</div>`;
    return;
  }

  container.innerHTML = state.clips.map(clip => `
    <div class="clip-card" data-id="${clip.id}">
      <div class="clip-thumb-box" style="background-image: url('${clip.thumbnail_url}');" data-id="${clip.id}">
        <span class="clip-game-badge">${sanitizeHTML(clip.game)}</span>
        ${clip.is_community ? '<span class="clip-community-badge">Community</span>' : ''}
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

  container.querySelectorAll('.clip-thumb-box').forEach(el => {
    el.addEventListener('click', () => {
      const clipId = parseInt(el.getAttribute('data-id'), 10);
      playClip(clipId);
    });
  });

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

  const ytId = extractYouTubeId(clip.video_url || clip.medal_url);

  if (ytId) {
    // Responsive YouTube embed (100% reliable in all browsers)
    playerContainer.innerHTML = `
      <iframe src="https://www.youtube-nocookie.com/embed/${ytId}?autoplay=1&rel=0" allow="autoplay; encrypted-media; fullscreen" allowfullscreen style="width:100%; height:100%; border:none;"></iframe>
    `;
  } else {
    // Bulletproof HTML5 video player with verified video stream & controls
    const vidSrc = clip.video_url || "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4";
    playerContainer.innerHTML = `
      <video id="active-html5-video" controls autoplay playsinline preload="metadata" style="width: 100%; height: 100%; object-fit: contain;">
        <source src="${vidSrc}" type="video/mp4">
        Your browser does not support Bedrock video clips.
      </video>
    `;
  }

  // Metadata & Action bar
  const medalLinkBtn = clip.medal_url && clip.medal_url.includes('medal.tv') ? `
    <a href="${clip.medal_url}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm" style="border-color: #ff3366; color: #ff6699;">
      Open on Medal.tv ↗
    </a>
  ` : '';

  meta.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-top: 1rem;">
      <div style="display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap;">
        <span class="bundle-item-pill" style="color: var(--accent-cyan); font-weight: 700;">${sanitizeHTML(clip.game)}</span>
        <span style="font-size: 0.88rem; color: var(--text-muted);">
          Recorded by <a href="#player/${encodeURIComponent(clip.gamertag)}" style="color: #fff; font-weight: 700;">${sanitizeHTML(clip.gamertag)}</a>
        </span>
        ${clip.is_community ? '<span class="clip-community-badge" style="position:static;">Community Verified</span>' : ''}
      </div>
      <div style="display: flex; align-items: center; gap: 0.6rem;">
        ${medalLinkBtn}
        <button class="btn btn-outline btn-sm" id="toggle-theater-btn">Theater Mode</button>
        <button class="btn btn-primary btn-sm" onclick="copyToClipboard('${clip.medal_url || window.location.href}', 'Clip link copied!')">Share Clip</button>
      </div>
    </div>
    ${clip.description ? `<p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.75rem; line-height: 1.5;">${sanitizeHTML(clip.description)}</p>` : ''}
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

// Community Clip Submission Initializer
function initCommunityClipSubmissions() {
  const toggleBtn = document.getElementById('toggle-submit-clip-panel-btn');
  const form = document.getElementById('inline-submit-clip-form');
  const cancelBtn = document.getElementById('cancel-inline-clip-btn');

  if (toggleBtn && form) {
    toggleBtn.addEventListener('click', () => {
      const isHidden = form.style.display === 'none';
      form.style.display = isHidden ? 'block' : 'none';
      toggleBtn.innerText = isHidden ? 'Close Form' : '+ Post Your Clip';
      if (isHidden) form.scrollIntoView({ behavior: 'smooth' });
    });
  }

  if (cancelBtn && form && toggleBtn) {
    cancelBtn.addEventListener('click', () => {
      form.style.display = 'none';
      toggleBtn.innerText = '+ Post Your Clip';
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        title: document.getElementById('inline-clip-title').value.trim(),
        gamertag: document.getElementById('inline-clip-gamertag').value.trim(),
        game: document.getElementById('inline-clip-game').value,
        clip_url: document.getElementById('inline-clip-url').value.trim(),
        description: document.getElementById('inline-clip-desc').value.trim(),
        duration: '0:35'
      };

      try {
        const res = await fetch('/api/clips', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message);
          form.reset();
          form.style.display = 'none';
          if (toggleBtn) toggleBtn.innerText = '+ Post Your Clip';
          loadClips();
          loadGlobalStats();
        } else {
          alert(data.error || 'Failed to submit clip');
        }
      } catch (err) {
        console.error('Submission error:', err);
      }
    });
  }

  // Clip Filter Listeners
  document.querySelectorAll('.clip-type-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.clip-type-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.clipsFilterType = btn.getAttribute('data-type');
      loadClips();
    });
  });

  document.querySelectorAll('.clip-game-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.clip-game-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.clipsFilterGame = btn.getAttribute('data-game');
      loadClips();
    });
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
  document.getElementById('profile-bio').innerText = p.bio || 'CubeCraft Bedrock Ranked Player.';
  document.getElementById('profile-score-num').innerText = `${p.reputation_score}%`;

  const avatarBox = document.getElementById('profile-avatar');
  const initial = p.gamertag.charAt(0).toUpperCase();
  if (p.avatar_icon) {
    avatarBox.innerHTML = `
      <img src="${p.avatar_icon}" alt="${sanitizeHTML(p.gamertag)}" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';" />
      <div class="player-avatar-fallback" style="display:none; background:${p.avatar_color || '#00e5ff'};">${initial}</div>
    `;
  } else {
    avatarBox.innerHTML = `
      <div class="player-avatar-fallback" style="background:${p.avatar_color || '#00e5ff'};">${initial}</div>
    `;
  }

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
      listContainer.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-subtle);">No encounters logged yet for ${sanitizeHTML(p.gamertag)}. Be the first to share an encounter!</div>`;
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
  if (!confirm('Report this comment for community moderation?')) return;
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
        loadPlayerProfile(gamertag);
      } else {
        alert(data.error || 'Failed to submit encounter review');
      }
    } catch (err) {
      console.error('Failed to post encounter:', err);
    }
  });
}

document.querySelectorAll('.enc-tag-filter').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.enc-tag-filter').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.encounterTagFilter = btn.getAttribute('data-tag');
    loadRecentEncounters();
  });
});

// Search Autocomplete for 800+ Gamertags
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
          resultsDropdown.innerHTML = data.players.map(p => {
            const avatarHtml = p.avatar_icon ? `
              <img src="${p.avatar_icon}" style="width: 24px; height: 24px; object-fit: contain;" alt="${sanitizeHTML(p.gamertag)}" />
            ` : `
              <span class="player-mini-avatar" style="background: ${p.avatar_color || '#00e5ff'}; width: 24px; height: 24px; font-size: 0.7rem;">${p.gamertag.charAt(0)}</span>
            `;

            return `
              <div class="search-result-item" style="padding: 0.6rem 0.85rem; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-subtle);" data-gamertag="${p.gamertag}">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                  ${avatarHtml}
                  <span style="font-weight: 600; color: #fff;">${sanitizeHTML(p.gamertag)}</span>
                  <span style="font-size: 0.7rem; color: var(--text-subtle);">(${sanitizeHTML(p.rank_title || 'Player')})</span>
                </div>
                <span class="rep-pill positive" style="font-size: 0.65rem;">⭐ ${p.reputation_score}% Rep</span>
              </div>
            `;
          }).join('');

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
              No local record for "${sanitizeHTML(query)}".
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
    }, 180);
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

  const logEncounterBtn = document.getElementById('open-log-encounter-modal-btn');
  if (logEncounterBtn) {
    logEncounterBtn.addEventListener('click', () => {
      openEncounterModal();
    });
  }
}
