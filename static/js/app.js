/**
 * CubeCraft Bedrock Community Hub - Client Application
 * Modular ES6 architecture handling 39 Game Mode Leaderboards, 826+ Players,
 * Bundles Showcase, Playable Community Clips Theatre, and Player Encounters.
 * Displays ONLY authentic data from the CubeCraft Bedrock API.
 */

// Application State
const state = {
  currentView: 'leaderboards',
  gamesList: [],
  selectedGame: 'EggWars',
  selectedMode: 'All Modes',
  leaderboardSearch: '',
  marketplace: [],
  marketplacePage: 1,
  marketplaceLimit: 24,
  marketplaceFilter: 'all',
  marketplaceSort: 'rating',
  marketplaceSearch: '',
  marketplaceTotalPages: 1,
  marketplaceTotalItems: 0,
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
  loadMarketplace();
  initMarketplaceControls();
  loadClips();
  loadRecentEncounters();
  initModalListeners();
  initSearchAutocomplete();
  initCommunityClipSubmissions();

  // Live leaderboards sync button
  const syncBtn = document.getElementById('sync-leaderboards-btn');
  if (syncBtn) {
    syncBtn.addEventListener('click', async () => {
      syncBtn.innerText = '⏳ Syncing...';
      syncBtn.disabled = true;
      try {
        const res = await fetch('/api/sync-leaderboards', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'Synced official Bedrock leaderboards!');
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
  } else if (hash === 'bundles') {
    switchView('marketplace');
  } else if (['leaderboards', 'marketplace', 'clips', 'encounters'].includes(hash)) {
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

      const mpElem = document.getElementById('stat-marketplace-count');
      if (mpElem && (s.total_marketplace_items !== undefined || s.active_bundles !== undefined)) {
        mpElem.innerText = formatNumber(s.total_marketplace_items || s.active_bundles);
      }

      const gamesElem = document.getElementById('stat-games-count');
      if (gamesElem) {
        gamesElem.innerText = formatNumber(s.total_games || 39);
      }

      const onlinePlayersElem = document.getElementById('stat-online-players');
      if (onlinePlayersElem && s.online_players !== undefined) {
        onlinePlayersElem.innerText = formatNumber(s.online_players);
      }
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

  tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-subtle);">Fetching official CubeCraft Bedrock leaderboards...</td></tr>`;

  try {
    const url = `/api/leaderboards?game=${encodeURIComponent(state.selectedGame)}&mode=${encodeURIComponent(state.selectedMode)}&search=${encodeURIComponent(state.leaderboardSearch)}`;
    const res = await fetch(url);
    const data = await res.json();

    if (!data.success || data.leaderboard.length === 0) {
      podiumContainer.innerHTML = '';
      tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-subtle);">No players found for ${sanitizeHTML(state.selectedGame)} (${sanitizeHTML(state.selectedMode)}).</td></tr>`;
      return;
    }

    renderPodium(data.podium);
    renderLeaderboardTable(data.leaderboard);
  } catch (err) {
    console.error('Failed to load leaderboards:', err);
    tableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; padding: 2rem; color: #f43f5e;">Error loading leaderboards.</td></tr>`;
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
            <span class="stat-val">${formatNumber(p.points)}</span>
            <span class="stat-lbl">Official Points</span>
          </div>
          <div class="stat-item">
            <span class="stat-val">#${p.rank || rank}</span>
            <span class="stat-lbl">Leaderboard Rank</span>
          </div>
          <div class="stat-item">
            <span class="stat-val">${p.encounter_count || 0}</span>
            <span class="stat-lbl">Reviews</span>
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
            </div>
          </div>
        </td>
        <td style="color: var(--text-muted); font-size: 0.82rem;">${sanitizeHTML(r.mode)}</td>
        <td><span class="podium-rank-title" style="color: ${r.avatar_color || '#fff'};">${sanitizeHTML(r.rank_title || 'Bedrock Player')}</span></td>
        <td style="font-weight: 700; color: #fff; font-size: 0.95rem;">${formatNumber(r.points)}</td>
        <td>
          <a href="#player/${encodeURIComponent(r.player_gamertag)}" class="rep-pill positive" style="text-decoration: none; font-size: 0.75rem;">
            💬 ${r.encounter_count || 0} Reviews
          </a>
        </td>
      </tr>
    `;
  }).join('');
}

const lbSearchInput = document.getElementById('lb-search-input');
if (lbSearchInput) {
  lbSearchInput.addEventListener('input', (e) => {
    state.leaderboardSearch = e.target.value;
    loadLeaderboards();
  });
}

// ==========================================================================
// Marketplace Showcase View (900+ Official Items)
// ==========================================================================

let marketplaceSearchTimeout = null;

function initMarketplaceControls() {
  const searchInput = document.getElementById('marketplace-search-input');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(marketplaceSearchTimeout);
      marketplaceSearchTimeout = setTimeout(() => {
        state.marketplaceSearch = e.target.value.trim();
        state.marketplacePage = 1;
        loadMarketplace();
      }, 250);
    });
  }

  const sortSelect = document.getElementById('marketplace-sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      state.marketplaceSort = e.target.value;
      state.marketplacePage = 1;
      loadMarketplace();
    });
  }

  document.querySelectorAll('.mp-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.mp-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.marketplaceFilter = btn.getAttribute('data-filter') || 'all';
      state.marketplacePage = 1;
      loadMarketplace();
    });
  });

  const syncBtn = document.getElementById('sync-marketplace-btn');
  if (syncBtn) {
    syncBtn.addEventListener('click', async () => {
      syncBtn.innerText = '⏳ Refreshing...';
      syncBtn.disabled = true;
      try {
        const res = await fetch('/api/sync-marketplace', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'Marketplace refreshed successfully!');
        loadGlobalStats();
        loadMarketplace();
      } catch (err) {
        showToast('Error syncing marketplace.');
      } finally {
        syncBtn.innerText = '🔄 Refresh Catalog';
        syncBtn.disabled = false;
      }
    });
  }
}

async function loadMarketplace() {
  const grid = document.getElementById('marketplace-grid');
  if (!grid) return;

  grid.innerHTML = `
    <div style="grid-column: 1/-1; text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
      <div style="font-size: 1.5rem; margin-bottom: 0.5rem; animation: pulse 1.5s infinite;">⏳</div>
      <div>Loading official Bedrock Marketplace items...</div>
    </div>
  `;

  try {
    const url = `/api/marketplace?page=${state.marketplacePage}&limit=${state.marketplaceLimit}&filter=${state.marketplaceFilter}&sort=${state.marketplaceSort}&search=${encodeURIComponent(state.marketplaceSearch)}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) {
      grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--accent-rose); padding: 2rem;">Failed to load marketplace items.</div>`;
      return;
    }

    state.marketplace = data.items;
    state.marketplaceTotalPages = data.total_pages;
    state.marketplaceTotalItems = data.total;

    const totalPill = document.getElementById('marketplace-total-pill');
    if (totalPill) {
      totalPill.innerText = `${formatNumber(data.total)} Official Items`;
    }

    renderMarketplace();
    renderMarketplacePagination();
  } catch (err) {
    console.error('Failed to load marketplace:', err);
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--accent-rose); padding: 2rem;">Network error loading marketplace.</div>`;
  }
}

function renderMarketplace() {
  const grid = document.getElementById('marketplace-grid');
  if (!grid) return;

  if (state.marketplace.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 4rem 1rem; color: var(--text-muted);">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
        <h3 style="color: #fff; font-size: 1.1rem; margin-bottom: 0.3rem;">No marketplace items found</h3>
        <p style="font-size: 0.85rem;">Try adjusting your search query or filter settings.</p>
      </div>
    `;
    return;
  }

  grid.innerHTML = state.marketplace.map(item => {
    const isAvailable = Boolean(item.available);
    const ratingStr = item.rating !== null && item.rating !== undefined ? item.rating.toFixed(1) : 'New';
    const priceStr = item.price === 0 ? 'Free' : `${formatNumber(item.price)} Minecoins`;
    const priceClass = item.price === 0 ? 'free' : '';

    return `
      <div class="marketplace-card" data-id="${item.id}">
        <div class="marketplace-thumb-wrap">
          <img 
            class="marketplace-thumb" 
            src="${item.thumbnail}" 
            alt="${sanitizeHTML(item.name)}"
            loading="lazy"
            onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\\'marketplace-thumb-fallback\\\'>🎮</div>';"
          />
          <span class="marketplace-rating-tag">★ ${ratingStr}</span>
          <span class="marketplace-badge-available ${isAvailable ? 'in-store' : 'vaulted'}">
            ${isAvailable ? 'In Store' : 'Vaulted'}
          </span>
        </div>
        <div class="marketplace-content">
          <h3 class="marketplace-title" title="${sanitizeHTML(item.name)}">${sanitizeHTML(item.name)}</h3>
          <p class="marketplace-desc">${sanitizeHTML(item.description || 'Official CubeCraft Bedrock Marketplace item.')}</p>
          <div class="marketplace-footer">
            <span class="marketplace-price ${priceClass}">
              ${item.price > 0 ? '🪙 ' : ''}${priceStr}
            </span>
            <button class="btn btn-outline btn-sm inspect-mp-btn" data-id="${item.id}" style="padding: 0.35rem 0.75rem; font-size: 0.78rem;">
              Inspect
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  grid.querySelectorAll('.marketplace-card').forEach(card => {
    card.addEventListener('click', () => {
      const id = card.getAttribute('data-id');
      inspectMarketplaceItem(id);
    });
  });
}

function renderMarketplacePagination() {
  const container = document.getElementById('marketplace-pagination');
  if (!container) return;

  const current = state.marketplacePage;
  const total = state.marketplaceTotalPages;

  if (total <= 1) {
    container.innerHTML = '';
    return;
  }

  let html = `
    <button class="mp-page-btn" id="mp-page-prev" ${current <= 1 ? 'disabled' : ''}>‹ Prev</button>
  `;

  // Determine page numbers to show
  const range = [];
  const delta = 2;
  for (let i = Math.max(2, current - delta); i <= Math.min(total - 1, current + delta); i++) {
    range.push(i);
  }

  // First page
  html += `<button class="mp-page-btn ${current === 1 ? 'active' : ''}" data-page="1">1</button>`;

  if (current - delta > 2) {
    html += `<span class="mp-page-info">...</span>`;
  }

  range.forEach(p => {
    html += `<button class="mp-page-btn ${current === p ? 'active' : ''}" data-page="${p}">${p}</button>`;
  });

  if (current + delta < total - 1) {
    html += `<span class="mp-page-info">...</span>`;
  }

  // Last page
  if (total > 1) {
    html += `<button class="mp-page-btn ${current === total ? 'active' : ''}" data-page="${total}">${total}</button>`;
  }

  html += `
    <button class="mp-page-btn" id="mp-page-next" ${current >= total ? 'disabled' : ''}>Next ›</button>
    <span class="mp-page-info" style="font-size: 0.78rem;">Page ${current} of ${total} (${formatNumber(state.marketplaceTotalItems)} items)</span>
  `;

  container.innerHTML = html;

  container.querySelectorAll('.mp-page-btn[data-page]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const p = parseInt(btn.getAttribute('data-page'));
      if (p && p !== state.marketplacePage) {
        state.marketplacePage = p;
        loadMarketplace();
        const view = document.getElementById('view-marketplace');
        if (view) view.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  const prevBtn = document.getElementById('mp-page-prev');
  if (prevBtn) {
    prevBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (state.marketplacePage > 1) {
        state.marketplacePage--;
        loadMarketplace();
        const view = document.getElementById('view-marketplace');
        if (view) view.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }

  const nextBtn = document.getElementById('mp-page-next');
  if (nextBtn) {
    nextBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (state.marketplacePage < state.marketplaceTotalPages) {
        state.marketplacePage++;
        loadMarketplace();
        const view = document.getElementById('view-marketplace');
        if (view) view.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  }
}

async function inspectMarketplaceItem(itemId) {
  const modal = document.getElementById('marketplace-modal');
  const title = document.getElementById('marketplace-modal-title');
  const body = document.getElementById('marketplace-modal-body');
  if (!modal || !title || !body) return;

  let item = state.marketplace.find(i => i.id === itemId);
  if (!item) {
    try {
      const res = await fetch(`/api/marketplace/${itemId}`);
      const data = await res.json();
      if (data.success) item = data.item;
    } catch (e) {
      console.error(e);
    }
  }

  if (!item) return;

  title.innerText = item.name;

  const isAvailable = Boolean(item.available);
  const ratingStr = item.rating !== null && item.rating !== undefined ? item.rating.toFixed(1) : 'Not Rated';
  const priceDisplay = item.price === 0 ? 'FREE' : `${formatNumber(item.price)} Minecoins`;
  const dateStr = item.creation_date ? new Date(item.creation_date).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : 'Official CubeCraft Release';

  body.innerHTML = `
    <div style="display: grid; grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr); gap: 1.5rem; align-items: start;">
      <div style="position: relative; border-radius: var(--radius-md); overflow: hidden; background: #080d18; border: 1px solid var(--border-subtle); aspect-ratio: 16/9;">
        <img 
          src="${item.thumbnail}" 
          alt="${sanitizeHTML(item.name)}" 
          style="width: 100%; height: 100%; object-fit: cover;"
          onerror="this.onerror=null; this.parentElement.innerHTML='<div class=\\\'marketplace-thumb-fallback\\\'>🎮</div>';"
        />
        <span class="marketplace-rating-tag" style="top: 0.75rem; left: 0.75rem; font-size: 0.8rem; padding: 4px 10px;">★ ${ratingStr}</span>
        <span class="marketplace-badge-available ${isAvailable ? 'in-store' : 'vaulted'}" style="top: 0.75rem; right: 0.75rem; font-size: 0.75rem; padding: 4px 10px;">
          ${isAvailable ? '🟢 In Store Now' : '🔒 Legacy / Vaulted'}
        </span>
      </div>

      <div style="display: flex; flex-direction: column; gap: 1rem;">
        <div>
          <span style="font-size: 0.75rem; color: var(--accent-cyan); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Official Bedrock Item</span>
          <h2 style="font-size: 1.35rem; font-weight: 800; color: #fff; margin-top: 0.2rem;">${sanitizeHTML(item.name)}</h2>
          <div style="font-size: 0.78rem; color: var(--text-subtle); margin-top: 0.2rem;">Released: ${dateStr}</div>
        </div>

        <div style="background: var(--bg-surface); padding: 0.85rem 1rem; border-radius: var(--radius-md); border: 1px solid var(--border-subtle); display: flex; align-items: center; justify-content: space-between;">
          <span style="font-size: 0.85rem; color: var(--text-subtle);">Store Price:</span>
          <span style="font-size: 1.2rem; font-weight: 800; color: #fbbf24; font-family: var(--font-mono);">
            ${item.price > 0 ? '🪙 ' : ''}${priceDisplay}
          </span>
        </div>

        <div>
          <h4 style="font-size: 0.85rem; font-weight: 700; color: var(--text-subtle); text-transform: uppercase; margin-bottom: 0.4rem;">Description</h4>
          <div style="font-size: 0.88rem; color: var(--text-muted); line-height: 1.6; white-space: pre-line; max-height: 160px; overflow-y: auto; padding-right: 0.5rem;">
            ${sanitizeHTML(item.description || 'No description provided for this item.')}
          </div>
        </div>

        <div style="border-top: 1px solid var(--border-subtle); padding-top: 0.75rem; display: flex; flex-direction: column; gap: 0.4rem;">
          <div style="font-size: 0.74rem; color: var(--text-subtle);">Xbox Marketplace ID:</div>
          <div style="display: flex; gap: 0.5rem; align-items: center;">
            <code style="font-size: 0.75rem; background: var(--bg-surface-elevated); padding: 3px 6px; border-radius: 4px; color: var(--accent-cyan); word-break: break-all;">${item.id}</code>
            <button class="btn btn-outline btn-sm copy-mp-id-btn" data-id="${item.id}" style="padding: 2px 6px; font-size: 0.72rem;">Copy</button>
          </div>
        </div>
      </div>
    </div>
  `;

  body.querySelectorAll('.copy-mp-id-btn').forEach(b => {
    b.addEventListener('click', (e) => {
      e.stopPropagation();
      copyToClipboard(b.getAttribute('data-id'), 'Copied Marketplace UUID!');
    });
  });

  openModal(modal);
}

// ==========================================================================
// Playable Community & Medal Clips View
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
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-subtle);">No clips found for this game category. Be the first to submit a clutch!</div>`;
    return;
  }

  container.innerHTML = state.clips.map(clip => `
    <div class="clip-card" data-id="${clip.id}">
      <div class="clip-thumb-container" onclick="playClip(${clip.id})">
        <img src="${clip.thumbnail_url || 'https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=600&q=80'}" alt="${sanitizeHTML(clip.title)}" class="clip-thumb" onerror="this.src='https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=600&q=80';" />
        <div class="play-overlay-icon">▶</div>
        <span class="clip-duration-badge">${clip.duration || '0:30'}</span>
        ${clip.is_community ? '<span class="community-clip-badge">👥 Community</span>' : '<span class="community-clip-badge" style="background:#f59e0b; color:#06080d;">⭐ Featured</span>'}
      </div>
      <div class="clip-meta-content">
        <h3 class="clip-title" onclick="playClip(${clip.id})">${sanitizeHTML(clip.title)}</h3>
        <div class="clip-author-row">
          <a href="#player/${encodeURIComponent(clip.gamertag)}" class="clip-author">
            👤 ${sanitizeHTML(clip.gamertag)}
          </a>
          <span class="clip-game-pill">${sanitizeHTML(clip.game)}</span>
        </div>
        <div class="clip-actions-row">
          <span style="font-size: 0.78rem; color: var(--text-subtle);">👁️ ${formatNumber(clip.views)} views</span>
          <button class="upvote-btn" onclick="upvoteClip(${clip.id}, event)">
            ❤️ ${formatNumber(clip.upvotes)}
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

function playClip(clipId) {
  const clip = state.clips.find(c => c.id === clipId);
  if (!clip) return;

  state.activeVideoClip = clip;
  const modal = document.getElementById('video-modal');
  const title = document.getElementById('video-modal-title');
  const playerBox = document.getElementById('video-modal-player');
  const metaBox = document.getElementById('video-modal-meta');

  title.innerText = clip.title;

  const ytId = extractYouTubeId(clip.video_url || clip.medal_url);
  if (ytId) {
    playerBox.innerHTML = `
      <iframe src="https://www.youtube.com/embed/${ytId}?autoplay=1" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="width:100%; height:100%; border:none;"></iframe>
    `;
  } else {
    playerBox.innerHTML = `
      <video src="${clip.video_url}" controls autoplay playsinline style="width:100%; height:100%; background:#000; border-radius: var(--radius-md);"></video>
    `;
  }

  metaBox.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 1rem; flex-wrap: wrap; gap: 0.75rem;">
      <div>
        <a href="#player/${encodeURIComponent(clip.gamertag)}" style="color: var(--accent-cyan); font-weight: 700; text-decoration: none; font-size: 0.95rem;">
          👤 ${sanitizeHTML(clip.gamertag)}
        </a>
        <span style="margin: 0 6px; color: var(--text-subtle);">•</span>
        <span class="bundle-item-pill">${sanitizeHTML(clip.game)}</span>
      </div>
      <div style="display: flex; gap: 0.75rem; align-items: center;">
        ${clip.medal_url ? `<a href="${clip.medal_url}" target="_blank" rel="noopener" class="btn btn-outline btn-sm">Open on Medal.tv ↗</a>` : ''}
        <button class="btn btn-primary btn-sm" onclick="upvoteClip(${clip.id})">❤️ Upvote (${clip.upvotes})</button>
      </div>
    </div>
    ${clip.description ? `<p style="font-size: 0.88rem; color: var(--text-muted); margin-top: 0.75rem; line-height: 1.5;">${sanitizeHTML(clip.description)}</p>` : ''}
  `;

  // Register view count
  fetch(`/api/clips/${clip.id}/view`, { method: 'POST' }).catch(() => {});
  clip.views = (clip.views || 0) + 1;

  openModal(modal);
}

async function upvoteClip(clipId, event) {
  if (event) event.stopPropagation();
  try {
    const res = await fetch(`/api/clips/${clipId}/upvote`, { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      showToast('Liked clip!');
      const c = state.clips.find(clip => clip.id === clipId);
      if (c) c.upvotes = data.upvotes;
      renderClips();
    }
  } catch (err) {
    console.error('Failed to upvote clip:', err);
  }
}

function initCommunityClipSubmissions() {
  const toggleBtn = document.getElementById('toggle-submit-clip-panel-btn');
  const form = document.getElementById('inline-submit-clip-form');
  const cancelBtn = document.getElementById('cancel-inline-clip-btn');

  if (toggleBtn && form) {
    toggleBtn.addEventListener('click', () => {
      form.style.display = form.style.display === 'none' ? 'block' : 'none';
      if (form.style.display === 'block') {
        form.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }

  if (cancelBtn && form) {
    cancelBtn.addEventListener('click', () => {
      form.style.display = 'none';
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        title: document.getElementById('inline-clip-title').value.strip ? document.getElementById('inline-clip-title').value.trim() : document.getElementById('inline-clip-title').value,
        gamertag: document.getElementById('inline-clip-gamertag').value.trim(),
        game: document.getElementById('inline-clip-game').value,
        clip_url: document.getElementById('inline-clip-url').value.trim(),
        description: document.getElementById('inline-clip-desc').value.trim()
      };

      try {
        const res = await fetch('/api/clips', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
          showToast(data.message || 'Clip posted to community hub!');
          form.reset();
          form.style.display = 'none';
          loadClips();
        } else {
          showToast(data.error || 'Failed to submit clip.');
        }
      } catch (err) {
        showToast('Error publishing clip. Please check connection.');
      }
    });
  }

  // Filter Listeners for Clips
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
  const leaderboards = state.activePlayer.leaderboards || [];

  document.getElementById('profile-gamertag').innerText = p.gamertag;
  document.getElementById('profile-rank-title').innerText = p.rank_title || 'Bedrock Player';
  document.getElementById('profile-bio').innerText = p.bio || 'CubeCraft Bedrock Ranked Player.';
  document.getElementById('profile-score-num').innerText = `${s.positive_rate || 100}%`;

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

  // Render player game modes breakdown table
  const modesTbody = document.getElementById('profile-modes-table-body');
  if (modesTbody) {
    if (leaderboards.length === 0) {
      modesTbody.innerHTML = `<tr><td colspan="4" style="text-align: center; padding: 1.5rem; color: var(--text-subtle);">No ranked leaderboards registered yet on CubeCraft Bedrock for ${sanitizeHTML(p.gamertag)}.</td></tr>`;
    } else {
      modesTbody.innerHTML = leaderboards.map(lb => `
        <tr>
          <td><strong style="color: #fff;">${sanitizeHTML(lb.game)}</strong></td>
          <td style="color: var(--text-muted);">${sanitizeHTML(lb.mode)}</td>
          <td style="font-weight: 700; color: #fff;">${formatNumber(lb.points)}</td>
          <td><span class="podium-rank-badge" style="width: 26px; height: 26px; font-size: 0.75rem;">#${lb.rank || 1}</span></td>
        </tr>
      `).join('');
    }
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
    const payload = {
      reviewer_name: document.getElementById('encounter-input-reviewer').value.trim() || 'Anonymous Bedrocker',
      game_played: document.getElementById('encounter-input-game').value,
      encounter_type: document.getElementById('encounter-input-type').value,
      rating: parseInt(document.getElementById('encounter-input-rating').value, 10),
      comment: document.getElementById('encounter-input-comment').value.trim()
    };
    const targetGamertag = document.getElementById('encounter-input-gamertag').value.trim();

    if (!targetGamertag) {
      showToast('Please specify a target player gamertag.');
      return;
    }

    try {
      const res = await fetch(`/api/players/${encodeURIComponent(targetGamertag)}/encounters`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        showToast(data.message || 'Encounter logged successfully!');
        closeModal(document.getElementById('encounter-modal'));
        submitEncounterForm.reset();
        loadRecentEncounters();
        if (state.activePlayer && state.activePlayer.player.gamertag.toLowerCase() === targetGamertag.toLowerCase()) {
          loadPlayerProfile(targetGamertag);
        }
      } else {
        showToast(data.error || 'Failed to post encounter.');
      }
    } catch (err) {
      showToast('Error posting review. Try again.');
    }
  });
}

// Search Autocomplete
function initSearchAutocomplete() {
  const input = document.getElementById('global-gamertag-search');
  const dropdown = document.getElementById('search-autocomplete-dropdown');
  if (!input || !dropdown) return;

  let debounceTimer;
  input.addEventListener('input', (e) => {
    clearTimeout(debounceTimer);
    const q = e.target.value.trim();
    if (!q) {
      dropdown.style.display = 'none';
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/players/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        if (!data.success || !data.players || data.players.length === 0) {
          dropdown.innerHTML = `<div style="padding: 0.85rem; font-size: 0.85rem; color: var(--text-subtle); text-align: center;">No ranked player found for "${sanitizeHTML(q)}". <br><a href="#player/${encodeURIComponent(q)}" style="color: var(--accent-cyan); text-decoration: none; font-weight: 600; display: inline-block; margin-top: 4px;">Search live profile ➔</a></div>`;
          dropdown.style.display = 'block';
          return;
        }

        dropdown.innerHTML = data.players.map(p => `
          <div class="search-result-item" onclick="navigateToPlayer('${p.gamertag}')" style="display: flex; align-items: center; justify-content: space-between; padding: 0.65rem 0.85rem; border-bottom: 1px solid var(--border-subtle); cursor: pointer; transition: background 0.15s ease;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
              <img src="${p.avatar_icon || `https://mc-heads.net/avatar/${encodeURIComponent(p.gamertag)}/30`}" alt="${sanitizeHTML(p.gamertag)}" style="width: 24px; height: 24px; border-radius: 4px;" onerror="this.src='https://mc-heads.net/avatar/${encodeURIComponent(p.gamertag)}/30';" />
              <div>
                <strong style="font-size: 0.85rem; color: #fff;">${sanitizeHTML(p.gamertag)}</strong>
                <span class="podium-rank-title" style="color: ${p.avatar_color || '#fff'}; font-size: 0.72rem; margin-left: 4px;">${sanitizeHTML(p.rank_title || 'Bedrock Player')}</span>
              </div>
            </div>
            <span style="font-size: 0.75rem; color: var(--accent-cyan);">View ➔</span>
          </div>
        `).join('');
        dropdown.style.display = 'block';
      } catch (err) {
        console.error('Search error:', err);
      }
    }, 200);
  });

  document.addEventListener('click', (e) => {
    if (!input.contains(e.target) && !dropdown.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });
}

function navigateToPlayer(gamertag) {
  window.location.hash = `player/${encodeURIComponent(gamertag)}`;
  const dropdown = document.getElementById('search-autocomplete-dropdown');
  if (dropdown) dropdown.style.display = 'none';
}

// Modal Listeners
function initModalListeners() {
  document.querySelectorAll('.close-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-overlay');
      if (modal) closeModal(modal);
    });
  });

  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal(modal);
    });
  });

  const openLogBtn = document.getElementById('open-log-encounter-modal-btn');
  if (openLogBtn) {
    openLogBtn.addEventListener('click', () => openEncounterModal());
  }
}

function openModal(modal) {
  if (!modal) return;
  modal.classList.add('active');
  state.activeModal = modal;
}

function closeModal(modal) {
  if (!modal) return;
  modal.classList.remove('active');
  state.activeModal = null;
  if (modal.id === 'video-modal') {
    const playerBox = document.getElementById('video-modal-player');
    if (playerBox) playerBox.innerHTML = '';
    state.activeVideoClip = null;
  }
}
