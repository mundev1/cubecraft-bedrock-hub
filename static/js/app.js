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
  analyticsData: null,
  analyticsTab: 'masters',
  competitivenessSort: 'tightest',
  bundles: [],
  clips: [],
  clipsFilterGame: 'all',
  clipsFilterType: 'all',
  clipsSort: 'recent',
  activePlayer: null,
  recentEncounters: [],
  encounterTagFilter: 'all',
  activeModal: null,
  activeVideoClip: null,
  mapsGuide: {
    maps: [],
    generators: null,
    bridging: null,
    selectedFilter: 'all',
    selectedBridgeFilter: 'all',
    maxBridgeDistance: 45,
    calc: {
      type: 'diamond',
      tier: 3,
      count: 4,
      duration: 5
    }
  }
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
  initAnalytics();
  loadAnalytics();
  initMapsGuide();
  loadMapsGuide();
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

  // Auto-refresh live stats every 30 seconds
  setInterval(loadGlobalStats, 30000);
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
  } else if (['leaderboards', 'analytics', 'maps-guide', 'marketplace', 'clips', 'encounters'].includes(hash)) {
    switchView(hash);
    if (hash === 'analytics') {
      loadAnalytics();
    } else if (hash === 'maps-guide') {
      loadMapsGuide();
    }
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

      const setStat = (id, val) => {
        const el = document.getElementById(id);
        if (el && val !== undefined && val !== null) {
          el.innerText = formatNumber(val);
        }
      };

      setStat('stat-players-count', s.total_players);
      setStat('stat-leaderboard-entries', s.total_leaderboard_entries);
      setStat('stat-encounters-count', s.total_encounters);
      setStat('stat-clips-count', s.total_clips);
      setStat('stat-marketplace-count', s.total_marketplace_items || s.active_bundles);
      setStat('stat-games-count', s.total_games || 39);
      setStat('stat-online-players', s.online_players);

      const pillCount = document.getElementById('server-pill-count');
      if (pillCount && s.online_players) {
        pillCount.innerText = `(${formatNumber(s.online_players)} Online)`;
      }

      const ribbonOnline = document.getElementById('ribbon-online-count');
      if (ribbonOnline && s.online_players) {
        ribbonOnline.innerText = `${formatNumber(s.online_players)} Online`;
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
// Cross-Mode Dominance & Server Analytics Engine (100% Real Aggregated Data)
// ==========================================================================

function initAnalytics() {
  document.querySelectorAll('.analytics-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.analytics-tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.analytics-tab-content').forEach(c => c.style.display = 'none');

      btn.classList.add('active');
      const targetTab = btn.getAttribute('data-tab');
      state.analyticsTab = targetTab;
      const content = document.getElementById(`analytics-tab-${targetTab}`);
      if (content) {
        content.style.display = 'block';
        if (targetTab === 'tracker') {
          renderServerTrackerChart();
        }
      }
    });
  });

  const sortSelect = document.getElementById('competitiveness-sort-select');
  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      state.competitivenessSort = e.target.value;
      if (state.analyticsData && state.analyticsData.competitiveness) {
        renderCompetitiveness();
      }
    });
  }

  const refreshBtn = document.getElementById('refresh-analytics-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
      refreshBtn.innerText = '⏳ Calculating...';
      refreshBtn.disabled = true;
      try {
        await loadAnalytics();
        showToast('Analytics recomputed from live database!');
      } catch (e) {
        showToast('Error refreshing analytics.');
      } finally {
        refreshBtn.innerText = '🔄 Refresh Analytics';
        refreshBtn.disabled = false;
      }
    });
  }
}

async function loadAnalytics() {
  try {
    const res = await fetch('/api/analytics/overview');
    const data = await res.json();
    if (!data.success) return;

    state.analyticsData = data;

    // 1. Update Ribbon
    if (data.masters && data.masters.length > 0) {
      const topMaster = data.masters[0];
      const masterElem = document.getElementById('ribbon-top-master');
      if (masterElem) masterElem.innerText = topMaster.gamertag;
      const modesElem = document.getElementById('ribbon-top-master-modes');
      if (modesElem) modesElem.innerText = `Ranked in ${topMaster.distinct_games} Distinct Games (${formatNumber(topMaster.total_points)} Pts)`;
    }

    if (data.competitiveness && data.competitiveness.length > 0) {
      const tightest = data.competitiveness[0];
      const tightElem = document.getElementById('ribbon-tightest-mode');
      if (tightElem) tightElem.innerText = `${tightest.game} ${tightest.mode}`;
      const spreadElem = document.getElementById('ribbon-tightest-spread');
      if (spreadElem) spreadElem.innerText = `${formatNumber(tightest.point_spread)} Pts Spread (#1 to #25)`;
    }

    if (data.rank_distribution && data.rank_distribution.grouped_tiers) {
      const tiers = data.rank_distribution.grouped_tiers;
      const topTier = tiers[0];
      const rankElem = document.getElementById('ribbon-top-rank');
      if (rankElem) rankElem.innerText = topTier.tier;
      const rankPctElem = document.getElementById('ribbon-top-rank-pct');
      if (rankPctElem) rankPctElem.innerText = `${topTier.percentage}% of Top Competitors (${topTier.count} players)`;
    }

    if (data.server_tracker) {
      const tracker = data.server_tracker;
      const onlineElem = document.getElementById('ribbon-online-count');
      if (onlineElem) onlineElem.innerText = `${formatNumber(tracker.current_online)} Online`;
      const peakElem = document.getElementById('ribbon-peak-window');
      if (peakElem) peakElem.innerText = `Peak: ${tracker.peak_window}`;
    }

    // 2. Render Sub-Modules
    renderAllAroundMasters();
    renderCompetitiveness();
    renderRankDistribution();
    renderServerTrackerChart();
  } catch (err) {
    console.error('Failed to load analytics:', err);
  }
}

function renderAllAroundMasters() {
  const container = document.getElementById('analytics-masters-grid');
  if (!container || !state.analyticsData || !state.analyticsData.masters) return;

  const gameIcons = {
    'EggWars': '🥚',
    'SkyWars': '☁️',
    'BlockWars': '🧱',
    'BedWars': '🛏️',
    'Lucky Islands': '🍀',
    'Duels (Battle Arena)': '🏆',
    'Survival Games': '⚔️',
    'MinerWare': '⛏️',
    'Parkour': '🏃',
    'Pillars of Fortune': '🏛️',
    'Disasters': '🌋',
    'Mob Hunt': '🏹'
  };

  container.innerHTML = state.analyticsData.masters.map((master, idx) => {
    const medalClass = idx === 0 ? 'top-1' : (idx === 1 ? 'top-2' : (idx === 2 ? 'top-3' : ''));
    const medalSymbol = idx === 0 ? '🥇' : (idx === 1 ? '🥈' : (idx === 2 ? '🥉' : `#${idx + 1}`));
    const avatarUrl = master.avatar_icon || `https://mc-heads.net/avatar/${encodeURIComponent(master.gamertag)}/100`;

    return `
      <div class="analytics-master-card" onclick="window.location.hash='player/${encodeURIComponent(master.gamertag)}'">
        <div style="display: flex; align-items: center; gap: 1rem;">
          <div class="master-medal-box ${medalClass}">${medalSymbol}</div>
          <div class="master-avatar-wrap">
            <img 
              src="${avatarUrl}" 
              alt="${sanitizeHTML(master.gamertag)}"
              loading="lazy"
              onerror="this.onerror=null; this.src='https://mc-heads.net/avatar/${encodeURIComponent(master.gamertag)}/100';"
            />
          </div>
        </div>

        <div class="master-details">
          <div class="master-title-row">
            <span class="master-gamertag">${sanitizeHTML(master.gamertag)}</span>
            <span class="podium-rank-title" style="font-size: 0.72rem; padding: 2px 7px;">${sanitizeHTML(master.rank_title || 'Bedrock Player')}</span>
            <span class="bundle-item-pill" style="color: var(--accent-cyan); font-weight: 700; font-size: 0.74rem;">
              ⭐ ${master.distinct_games} Distinct Games (${master.distinct_modes} Sub-Modes)
            </span>
          </div>

          <div class="master-badges-row">
            ${(master.leaderboards || []).map(lb => `
              <span class="analytics-mode-chip">
                <span>${gameIcons[lb.game] || '🎮'} ${sanitizeHTML(lb.game)}:</span>
                <strong>#${lb.rank}</strong>
                <span style="font-size: 0.68rem; color: var(--text-subtle);">(${formatNumber(lb.points)} pts)</span>
              </span>
            `).join('')}
          </div>
        </div>

        <div class="master-score-box">
          <span style="font-size: 0.72rem; color: var(--text-subtle); text-transform: uppercase; font-weight: 700;">Cross-Mode Points</span>
          <span class="master-total-points">${formatNumber(master.total_points)}</span>
          <span style="font-size: 0.75rem; color: var(--accent-cyan);">Inspect Profile →</span>
        </div>
      </div>
    `;
  }).join('');
}

function renderCompetitiveness() {
  const tbody = document.getElementById('competitiveness-table-body');
  if (!tbody || !state.analyticsData || !state.analyticsData.competitiveness) return;

  let scores = [...state.analyticsData.competitiveness];
  const sort = state.competitivenessSort || 'tightest';

  if (sort === 'widest') {
    scores.sort((a, b) => b.point_spread - a.point_spread);
  } else if (sort === 'highest_threshold') {
    scores.sort((a, b) => b.min_points - a.min_points);
  } else if (sort === 'highest_leader') {
    scores.sort((a, b) => b.max_points - a.max_points);
  } else if (sort === 'alphabetical') {
    scores.sort((a, b) => a.game.localeCompare(b.game) || a.mode.localeCompare(b.mode));
  } else {
    scores.sort((a, b) => a.point_spread - b.point_spread);
  }

  const maxSpreadFound = Math.max(...scores.map(s => s.point_spread), 1);

  tbody.innerHTML = scores.map(s => {
    const tightPct = Math.max(5, Math.min(100, Math.round((1 - (s.point_spread / maxSpreadFound)) * 100)));

    return `
      <tr>
        <td>
          <div style="font-weight: 700; color: #fff;">${sanitizeHTML(s.game)}</div>
          <div style="font-size: 0.76rem; color: var(--text-subtle);">${sanitizeHTML(s.mode)}</div>
        </td>
        <td>
          <span class="badge" style="background: rgba(255, 255, 255, 0.05); color: ${s.tier_color}; border: 1px solid ${s.tier_color}40; font-weight: 700; font-size: 0.74rem;">
            ${s.tier_badge}
          </span>
          <div style="font-size: 0.72rem; color: var(--text-subtle); margin-top: 2px;">${s.tier}</div>
        </td>
        <td>
          <div style="font-weight: 700; color: #fbbf24;">${sanitizeHTML(s.rank1_player || 'Leader')}</div>
          <div style="font-size: 0.76rem; color: var(--text-muted);">${formatNumber(s.max_points)} points</div>
        </td>
        <td>
          <div style="font-weight: 600; color: var(--text-main);">${sanitizeHTML(s.rank25_player || 'Gatekeeper')}</div>
          <div style="font-size: 0.76rem; color: var(--text-subtle);">${formatNumber(s.min_points)} pts cutoff</div>
        </td>
        <td>
          <div class="spread-meter-container">
            <div style="display: flex; justify-content: space-between; font-size: 0.78rem;">
              <strong style="color: ${s.tier_color};">${formatNumber(s.point_spread)} pts</strong>
              <span style="color: var(--text-subtle); font-size: 0.72rem;">gap</span>
            </div>
            <div class="spread-meter-bg">
              <div class="spread-meter-fill" style="width: ${tightPct}%; background: ${s.tier_color};"></div>
            </div>
          </div>
        </td>
        <td>
          <span style="font-family: var(--font-mono); font-weight: 700; color: ${s.ratio > 5 ? '#a855f7' : 'var(--text-main)'};">
            ${s.ratio}x
          </span>
          <div style="font-size: 0.7rem; color: var(--text-subtle);">lead multiple</div>
        </td>
      </tr>
    `;
  }).join('');
}

function renderRankDistribution() {
  const container = document.getElementById('rank-bars-container');
  if (!container || !state.analyticsData || !state.analyticsData.rank_distribution) return;

  const data = state.analyticsData.rank_distribution;
  const tiers = data.grouped_tiers || [];

  container.innerHTML = `
    <!-- Top Stacked Overview Bar -->
    <div style="margin-bottom: 1.75rem;">
      <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.6rem;">
        <span style="font-size: 0.82rem; color: var(--text-subtle); font-weight: 700; text-transform: uppercase;">Stacked Share (826 Players)</span>
        <span style="font-size: 0.82rem; color: var(--accent-cyan); font-weight: 700;">100% Top-25 Leaderboard Base</span>
      </div>
      <div style="display: flex; width: 100%; height: 22px; border-radius: 6px; overflow: hidden; border: 1px solid var(--border-subtle);">
        ${tiers.map(t => `
          <div 
            style="width: ${t.percentage}%; background: ${t.color}; height: 100%;" 
            title="${t.tier}: ${t.percentage}% (${t.count} players)"
          ></div>
        `).join('')}
      </div>
      <div style="display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 0.75rem; font-size: 0.75rem;">
        ${tiers.map(t => `
          <div style="display: flex; align-items: center; gap: 5px;">
            <span style="width: 10px; height: 10px; border-radius: 2px; background: ${t.color}; display: inline-block;"></span>
            <span style="color: var(--text-muted);">${t.tier} (${t.percentage}%)</span>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Detailed Individual Progress Bars -->
    <div class="rank-dist-list">
      ${tiers.map(t => `
        <div class="rank-dist-item">
          <div class="rank-dist-header">
            <span style="font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px;">
              <span style="width: 8px; height: 8px; border-radius: 50%; background: ${t.color};"></span>
              ${t.tier}
            </span>
            <span style="font-family: var(--font-mono); font-weight: 800; color: ${t.color};">
              ${t.percentage}% <span style="font-size: 0.75rem; color: var(--text-subtle); font-weight: 400;">(${t.count} players)</span>
            </span>
          </div>
          <div class="rank-dist-progress-bg">
            <div class="rank-dist-progress-bar" style="width: ${t.percentage}%; background: ${t.color};"></div>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}

function renderServerTrackerChart() {
  const container = document.getElementById('server-tracker-chart-container');
  if (!container || !state.analyticsData || !state.analyticsData.server_tracker) return;

  const tracker = state.analyticsData.server_tracker;
  const points = tracker.hourly_timeline || [];
  if (points.length === 0) return;

  const width = container.clientWidth || 800;
  const height = 240;
  const padLeft = 45;
  const padRight = 20;
  const padTop = 25;
  const padBottom = 35;

  const plotW = width - padLeft - padRight;
  const plotH = height - padTop - padBottom;

  const minVal = Math.min(...points.map(p => p.online_count), 2500);
  const maxVal = Math.max(...points.map(p => p.online_count), 9500);

  const getX = (idx) => padLeft + (idx / (points.length - 1)) * plotW;
  const getY = (val) => padTop + plotH - ((val - minVal) / (maxVal - minVal)) * plotH;

  let pathD = `M ${getX(0)} ${getY(points[0].online_count)}`;
  for (let i = 1; i < points.length; i++) {
    const x0 = getX(i - 1);
    const y0 = getY(points[i - 1].online_count);
    const x1 = getX(i);
    const y1 = getY(points[i].online_count);
    const mx = (x0 + x1) / 2;
    pathD += ` C ${mx} ${y0}, ${mx} ${y1}, ${x1} ${y1}`;
  }

  const areaD = `${pathD} L ${getX(points.length - 1)} ${padTop + plotH} L ${getX(0)} ${padTop + plotH} Z`;

  const gridVals = [
    Math.round(minVal),
    Math.round(minVal + (maxVal - minVal) * 0.33),
    Math.round(minVal + (maxVal - minVal) * 0.66),
    Math.round(maxVal)
  ];

  let svgHtml = `
    <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: 100%; overflow: visible;" id="tracker-svg">
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.35"/>
          <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.0"/>
        </linearGradient>
      </defs>

      <!-- Horizontal Grid Lines -->
      ${gridVals.map(val => `
        <line 
          x1="${padLeft}" y1="${getY(val)}" 
          x2="${width - padRight}" y2="${getY(val)}" 
          stroke="rgba(255, 255, 255, 0.08)" 
          stroke-dasharray="4,4"
        />
        <text 
          x="${padLeft - 8}" y="${getY(val) + 4}" 
          fill="var(--text-subtle)" font-size="10" 
          text-anchor="end" font-family="monospace"
        >${formatNumber(val)}</text>
      `).join('')}

      <!-- Bottom baseline -->
      <line 
        x1="${padLeft}" y1="${padTop + plotH}" 
        x2="${width - padRight}" y2="${padTop + plotH}" 
        stroke="var(--border-subtle)"
      />

      <!-- Area fill -->
      <path d="${areaD}" fill="url(#areaGrad)" />

      <!-- Curve Line -->
      <path d="${pathD}" fill="none" stroke="var(--accent-cyan)" stroke-width="2.5" stroke-linecap="round"/>

      <!-- Data Points & Labels -->
      ${points.map((p, idx) => {
        const x = getX(idx);
        const y = getY(p.online_count);
        const color = p.is_peak ? '#ef4444' : (p.is_offpeak ? '#10b981' : 'var(--accent-cyan)');
        const showLabel = idx % 3 === 0 || idx === points.length - 1;

        return `
          <g class="chart-point-group" data-hour="${p.label}" data-count="${p.online_count}">
            <circle cx="${x}" cy="${y}" r="3.5" fill="${color}" stroke="#06080d" stroke-width="1.5" />
            ${showLabel ? `
              <text 
                x="${x}" y="${padTop + plotH + 18}" 
                fill="var(--text-subtle)" font-size="10" 
                text-anchor="middle" font-family="monospace"
              >${p.hour}:00</text>
            ` : ''}
          </g>
        `;
      }).join('')}
    </svg>
    <div id="chart-tooltip" class="server-chart-tooltip"></div>
  `;

  container.innerHTML = svgHtml;

  const tooltip = container.querySelector('#chart-tooltip');
  container.querySelectorAll('.chart-point-group').forEach(grp => {
    grp.addEventListener('mouseenter', (e) => {
      const hour = grp.getAttribute('data-hour');
      const count = grp.getAttribute('data-count');
      if (tooltip) {
        tooltip.innerHTML = `<strong>${hour}</strong>: ${formatNumber(parseInt(count))} players`;
        tooltip.style.display = 'block';
      }
    });

    grp.addEventListener('mousemove', (e) => {
      if (tooltip) {
        const rect = container.getBoundingClientRect();
        tooltip.style.left = `${e.clientX - rect.left + 10}px`;
        tooltip.style.top = `${e.clientY - rect.top - 30}px`;
      }
    });

    grp.addEventListener('mouseleave', () => {
      if (tooltip) tooltip.style.display = 'none';
    });
  });

  const peakTimeElem = document.getElementById('tracker-peak-time');
  if (peakTimeElem) peakTimeElem.innerText = tracker.peak_window;
  const offpeakTimeElem = document.getElementById('tracker-offpeak-time');
  if (offpeakTimeElem) offpeakTimeElem.innerText = tracker.offpeak_window;
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

// ==========================================================================
// Official Bedrock Mode & Maps Strategy Guide
// ==========================================================================

function initMapsGuide() {
  // Guide Subtabs (Blueprints, Generators, Bridging)
  const tabBtns = document.querySelectorAll('.guide-tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const targetTab = btn.getAttribute('data-guide-tab');
      document.querySelectorAll('.guide-tab-panel').forEach(p => {
        p.style.display = 'none';
        p.classList.remove('active');
      });

      const activePanel = document.getElementById(`guide-panel-${targetTab}`);
      if (activePanel) {
        activePanel.style.display = 'block';
        activePanel.classList.add('active');
      }
    });
  });

  // Map Filter Buttons (All, EggWars, SkyWars)
  const mapFilterBtns = document.querySelectorAll('.map-filter-btn');
  mapFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      mapFilterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.mapsGuide.selectedFilter = btn.getAttribute('data-filter');
      renderMapsGrid();
    });
  });

  // Void Bridging Filter Buttons
  const bridgeFilterBtns = document.querySelectorAll('.bridge-filter-btn');
  bridgeFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      bridgeFilterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.mapsGuide.selectedBridgeFilter = btn.getAttribute('data-filter');
      renderBridgingBenchmarks();
    });
  });

  // Bridging Distance Slider
  const distSlider = document.getElementById('bridge-max-distance');
  const distLabel = document.getElementById('bridge-max-distance-label');
  if (distSlider && distLabel) {
    distSlider.addEventListener('input', (e) => {
      const val = parseInt(e.target.value);
      distLabel.innerText = `≤ ${val} blk`;
      state.mapsGuide.maxBridgeDistance = val;
      renderBridgingBenchmarks();
    });
  }

  // Refresh button
  const refreshBtn = document.getElementById('refresh-maps-guide-btn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadMapsGuide(true);
      showToast('Refreshing strategy blueprints & generator data...');
    });
  }

  initGeneratorCalculator();
}

async function loadMapsGuide(force = false) {
  if (state.mapsGuide.maps.length > 0 && !force) {
    renderMapsGrid();
    renderGeneratorReference();
    updateGeneratorCalculator();
    renderBridgingBenchmarks();
    return;
  }

  try {
    const res = await fetch('/api/strategy/overview');
    const data = await res.json();
    if (data.success) {
      state.mapsGuide.maps = data.maps || [];
      state.mapsGuide.generators = data.generators || null;
      state.mapsGuide.bridging = data.bridging || null;

      renderMapsGrid();
      renderGeneratorReference();
      updateGeneratorCalculator();
      renderBridgingBenchmarks();
    }
  } catch (err) {
    console.error('Failed to load strategy guide overview:', err);
    const grid = document.getElementById('maps-blueprint-grid');
    if (grid) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: #f43f5e;">
          Failed to load map blueprints. Please click 'Refresh Data'.
        </div>
      `;
    }
  }
}

function renderMapsGrid() {
  const grid = document.getElementById('maps-blueprint-grid');
  if (!grid) return;

  const filter = state.mapsGuide.selectedFilter;
  const filtered = state.mapsGuide.maps.filter(m => {
    if (filter === 'all') return true;
    return m.game.toLowerCase() === filter.toLowerCase();
  });

  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-muted);">
        No map blueprints found for this filter.
      </div>
    `;
    return;
  }

  grid.innerHTML = filtered.map(m => {
    const isEgg = m.game === 'EggWars';
    const gameBadgeColor = isEgg ? 'var(--accent-cyan)' : 'var(--accent-emerald)';
    const gameIcon = isEgg ? '🥚' : '☁️';

    // Format bridging quick pills
    let bridgePills = '';
    if (Array.isArray(m.bridging_distances)) {
      bridgePills = m.bridging_distances.slice(0, 2).map(b => `
        <span class="map-distance-pill">
          ${sanitizeHTML(b.target.split(' ')[0])}: <strong>${b.distance_blocks} blk</strong> (${b.jump_bridge_sec}s)
        </span>
      `).join('');
    }

    // Format generator summary
    let genSummary = '';
    if (isEgg && m.generator_breakdown) {
      const gb = m.generator_breakdown;
      const starter = gb.starter_island || [];
      const mid = gb.middle_island ? gb.middle_island[0] : null;
      const starterText = starter.map(s => `${s.count} ${s.type}`).join(', ');
      const midText = mid && mid.generators ? `${mid.generators[0].count} Dia Mid` : '';
      genSummary = `<span style="font-size: 0.76rem; color: #fbbf24;">⚡ ${starterText} • ${midText}</span>`;
    } else {
      genSummary = `<span style="font-size: 0.76rem; color: #10b981;">📦 Fast Chest Loot Rush • ${m.teams_count} Spawns</span>`;
    }

    return `
      <div class="map-card" data-map-id="${sanitizeHTML(m.map_id)}">
        <div class="map-card-thumb-wrap">
          <img src="${sanitizeHTML(m.thumbnail_url)}" alt="${sanitizeHTML(m.name)}" class="map-card-thumb" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600&auto=format&fit=crop&q=80'">
          <div class="map-card-gradient"></div>
          <div class="map-card-badge-row">
            <span class="badge" style="background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); color: ${gameBadgeColor}; border: 1px solid ${gameBadgeColor};">
              ${gameIcon} ${sanitizeHTML(m.game)}
            </span>
            <span class="badge" style="background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); color: #fff;">
              ${sanitizeHTML(m.difficulty)}
            </span>
          </div>
          <div class="map-card-title-row">
            <div class="map-card-theme">${sanitizeHTML(m.theme)}</div>
            <h3>${sanitizeHTML(m.name)}</h3>
          </div>
        </div>

        <div class="map-card-body">
          <p class="map-card-desc">${sanitizeHTML(m.description)}</p>

          <div class="map-quick-benchmarks">
            <div class="map-quick-benchmarks-title">
              <span>📏 Key Void Rush Gaps</span>
            </div>
            <div>${bridgePills}</div>
          </div>

          <div style="margin-bottom: 1rem;">
            ${genSummary}
          </div>

          <div class="map-card-footer">
            <span style="font-size: 0.8rem; color: var(--text-muted);">
              👥 ${sanitizeHTML(m.mode_variant)}
            </span>
            <button class="btn btn-outline btn-sm inspect-map-btn" data-map-id="${sanitizeHTML(m.map_id)}" style="border-color: var(--accent-cyan); color: var(--accent-cyan);">
              Blueprint & Tactics ➔
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  // Attach button clicks
  grid.querySelectorAll('.inspect-map-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const mapId = btn.getAttribute('data-map-id');
      openMapModal(mapId);
    });
  });

  // Also allow clicking the entire card
  grid.querySelectorAll('.map-card').forEach(card => {
    card.addEventListener('click', () => {
      const mapId = card.getAttribute('data-map-id');
      openMapModal(mapId);
    });
  });
}

function openMapModal(mapId) {
  const map = state.mapsGuide.maps.find(m => m.map_id === mapId);
  const modal = document.getElementById('map-modal');
  const titleEl = document.getElementById('map-modal-title');
  const bodyEl = document.getElementById('map-modal-body');

  if (!map || !modal || !bodyEl) return;

  const isEgg = map.game === 'EggWars';
  const gameIcon = isEgg ? '🥚' : '☁️';
  titleEl.innerHTML = `${gameIcon} ${sanitizeHTML(map.name)} — Tactical Blueprint & Strategy`;

  // Bridging rows
  let bridgingTableRows = '';
  if (Array.isArray(map.bridging_distances)) {
    bridgingTableRows = map.bridging_distances.map(b => {
      const dangerClass = `danger-${b.danger_level.toLowerCase()}`;
      return `
        <tr>
          <td style="font-weight: 700; color: #fff;">${sanitizeHTML(b.target)}</td>
          <td><strong style="color: var(--accent-cyan);">${b.distance_blocks}</strong> blk</td>
          <td style="color: #10b981; font-weight: 700;">${b.jump_bridge_sec}s</td>
          <td style="color: var(--text-muted);">${b.sneak_bridge_sec}s</td>
          <td>${b.blocks_needed} (${(b.blocks_needed / 64).toFixed(2)} stack)</td>
          <td><span class="danger-badge ${dangerClass}">${sanitizeHTML(b.danger_level)}</span></td>
          <td style="font-size: 0.8rem; color: var(--text-muted);">${sanitizeHTML(b.tactical_note)}</td>
        </tr>
      `;
    }).join('');
  }

  // Generator breakdown display
  let genBreakdownHTML = '';
  if (isEgg && map.generator_breakdown) {
    const gb = map.generator_breakdown;
    const starter = gb.starter_island || [];
    const sub = gb.sub_islands || [];
    const mid = gb.middle_island || [];

    genBreakdownHTML = `
      <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1.25rem; margin-bottom: 1.5rem;">
        <h4 style="font-size: 1rem; font-weight: 800; color: #fff; margin-bottom: 0.8rem; display: flex; align-items: center; gap: 0.5rem;">
          <span>⚙️ Generator Node Placements</span>
        </h4>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem;">
          <div style="background: var(--bg-surface); padding: 0.85rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.76rem; text-transform: uppercase; color: var(--accent-cyan); font-weight: 700;">Starter Island</div>
            <ul style="margin: 0.4rem 0 0 1rem; padding: 0; font-size: 0.82rem; color: var(--text-muted); line-height: 1.6;">
              ${starter.map(s => `<li><strong>${s.count}x ${s.type}</strong> (${s.location})</li>`).join('')}
            </ul>
          </div>
          <div style="background: var(--bg-surface); padding: 0.85rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.76rem; text-transform: uppercase; color: #10b981; font-weight: 700;">Sub-Islands</div>
            <ul style="margin: 0.4rem 0 0 1rem; padding: 0; font-size: 0.82rem; color: var(--text-muted); line-height: 1.6;">
              ${sub.map(s => `<li><strong>${s.count}x ${s.name}</strong> (${s.generators.map(g => `${g.count}x ${g.type} Lv${g.tier}`).join(', ')})</li>`).join('')}
            </ul>
          </div>
          <div style="background: var(--bg-surface); padding: 0.85rem; border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">
            <div style="font-size: 0.76rem; text-transform: uppercase; color: #fbbf24; font-weight: 700;">Central Mid Island</div>
            <ul style="margin: 0.4rem 0 0 1rem; padding: 0; font-size: 0.82rem; color: var(--text-muted); line-height: 1.6;">
              ${mid.map(m => `<li><strong>${m.name}</strong> (${m.generators.map(g => `${g.count}x ${g.type} Lv${g.tier}`).join(', ')})</li>`).join('')}
            </ul>
          </div>
        </div>
      </div>
    `;
  }

  bodyEl.innerHTML = `
    <!-- Top Map Banner -->
    <div style="position: relative; height: 180px; border-radius: var(--radius-md); overflow: hidden; margin-bottom: 1.5rem; background: #000;">
      <img src="${sanitizeHTML(map.thumbnail_url)}" alt="${sanitizeHTML(map.name)}" style="width: 100%; height: 100%; object-fit: cover; opacity: 0.75;">
      <div style="position: absolute; inset: 0; background: linear-gradient(0deg, rgba(6,8,13,0.95) 0%, rgba(6,8,13,0.3) 100%);"></div>
      <div style="position: absolute; bottom: 16px; left: 20px; right: 20px; z-index: 2;">
        <div style="display: flex; gap: 0.5rem; margin-bottom: 0.3rem;">
          <span class="badge" style="background: rgba(0,229,255,0.2); color: var(--accent-cyan);">${sanitizeHTML(map.game)}</span>
          <span class="badge" style="background: rgba(255,255,255,0.15); color: #fff;">${sanitizeHTML(map.difficulty)}</span>
          <span class="badge" style="background: rgba(16,185,129,0.2); color: #10b981;">${map.teams_count} Teams • Size ${map.team_size}</span>
        </div>
        <h2 style="font-size: 1.6rem; font-weight: 900; color: #fff; margin: 0;">${sanitizeHTML(map.name)}</h2>
        <p style="font-size: 0.84rem; color: var(--accent-cyan); margin-top: 0.2rem;">${sanitizeHTML(map.theme)}</p>
      </div>
    </div>

    <!-- Layout Schematic Box -->
    <div style="background: var(--bg-surface-elevated); border-left: 4px solid var(--accent-cyan); border-radius: 0 var(--radius-md) var(--radius-md) 0; padding: 1.25rem; margin-bottom: 1.5rem;">
      <h4 style="font-size: 0.96rem; font-weight: 800; color: #fff; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.5rem;">
        <span>📐 Architecture & Layout Schematic</span>
      </h4>
      <p style="font-size: 0.88rem; color: var(--text-main); line-height: 1.6; margin: 0;">
        ${sanitizeHTML(map.layout_schematic)}
      </p>
    </div>

    <!-- 3-Column Tactical Playbook -->
    <div class="tactics-grid">
      <div class="tactics-card">
        <h4 style="color: var(--accent-cyan);">
          <span>🚀 Opening Void Rush</span>
        </h4>
        <p>${sanitizeHTML(map.tactics_rush)}</p>
      </div>

      <div class="tactics-card">
        <h4 style="color: #10b981;">
          <span>🛡️ Base & Defense Meta</span>
        </h4>
        <p>${sanitizeHTML(map.tactics_defense)}</p>
      </div>

      <div class="tactics-card">
        <h4 style="color: #fbbf24;">
          <span>👑 Mid Control & Dominance</span>
        </h4>
        <p>${sanitizeHTML(map.tactics_mid_control)}</p>
      </div>
    </div>

    <!-- Generator Placements (EggWars) -->
    ${genBreakdownHTML}

    <!-- Void Bridging Matrix -->
    <div style="background: var(--bg-surface-elevated); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); overflow: hidden; margin-bottom: 1.5rem;">
      <div style="padding: 1rem 1.25rem; border-bottom: 1px solid var(--border-subtle); background: var(--bg-surface);">
        <h4 style="font-size: 1rem; font-weight: 800; color: #fff; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
          <span>📏 Void Bridging Distance Matrix</span>
          <span style="font-size: 0.75rem; color: var(--accent-cyan); font-weight: 600;">5.6 bps Bedrock Sprint vs 1.6 bps Sneak</span>
        </h4>
      </div>
      <div style="overflow-x: auto;">
        <table class="table" style="margin-bottom: 0;">
          <thead>
            <tr>
              <th>Target Island</th>
              <th>Distance</th>
              <th>Sprint Jump-Bridge</th>
              <th>Sneak-Bridge</th>
              <th>Blocks (Stacks)</th>
              <th>Danger</th>
              <th>Tactical Recommendation</th>
            </tr>
          </thead>
          <tbody>
            ${bridgingTableRows}
          </tbody>
        </table>
      </div>
    </div>
  `;

  openModal(modal);
}

function initGeneratorCalculator() {
  const typeSelect = document.getElementById('calc-gen-type');
  const tierSelect = document.getElementById('calc-gen-tier');
  const countSelect = document.getElementById('calc-gen-count');
  const durationSlider = document.getElementById('calc-gen-duration');

  const triggers = [typeSelect, tierSelect, countSelect, durationSlider];
  triggers.forEach(el => {
    if (el) {
      el.addEventListener('input', () => updateGeneratorCalculator());
      el.addEventListener('change', () => updateGeneratorCalculator());
    }
  });
}

function updateGeneratorCalculator() {
  if (!state.mapsGuide.generators) return;

  const typeEl = document.getElementById('calc-gen-type');
  const tierEl = document.getElementById('calc-gen-tier');
  const countEl = document.getElementById('calc-gen-count');
  const durationEl = document.getElementById('calc-gen-duration');

  if (!typeEl || !tierEl || !countEl || !durationEl) return;

  const type = typeEl.value; // 'diamond', 'iron', 'gold'
  const tier = parseInt(tierEl.value); // 1, 2, 3, 4
  const count = parseInt(countEl.value); // 1, 2, 4
  const duration = parseInt(durationEl.value); // 1 to 15 mins

  // Update duration badge
  const durationBadge = document.getElementById('calc-duration-badge');
  if (durationBadge) {
    durationBadge.innerText = `${duration} Minute${duration > 1 ? 's' : ''}`;
  }

  const durationSub = document.getElementById('calc-kpi-duration-sub');
  if (durationSub) {
    durationSub.innerText = `Over ${duration} minute duration`;
  }

  const genConfig = state.mapsGuide.generators[type];
  if (!genConfig || !genConfig.tiers[tier - 1]) return;

  const tierData = genConfig.tiers[tier - 1];
  const ratePerMinPerGen = tierData.rate_per_min;
  const combinedRate = ratePerMinPerGen * count;
  const totalYield = Math.floor(combinedRate * duration);
  const intervalSec = tierData.interval_sec;

  // Update Rate KPI
  const rateKpi = document.getElementById('calc-kpi-rate');
  if (rateKpi) {
    rateKpi.innerText = `${combinedRate.toFixed(1)} / min`;
  }

  // Update Interval KPI
  const intervalKpi = document.getElementById('calc-kpi-interval');
  if (intervalKpi) {
    intervalKpi.innerText = `1 item every ${intervalSec}s (per gen)`;
  }

  // Update Total Yield KPI
  const totalKpi = document.getElementById('calc-kpi-total');
  if (totalKpi) {
    totalKpi.innerText = `${formatNumber(totalYield)} ${genConfig.material}s`;
  }

  // Update Upgrade Cost KPI
  const costKpi = document.getElementById('calc-kpi-cost');
  const costTypeEl = document.getElementById('calc-kpi-cost-type');
  if (costKpi) {
    costKpi.innerText = tierData.upgrade_cost;
  }
  if (costTypeEl) {
    costTypeEl.innerText = `To upgrade to Tier ${tier}`;
  }

  // Calculate Breakeven ROI
  const roiKpi = document.getElementById('calc-kpi-roi');
  const roiSub = document.getElementById('calc-kpi-roi-sub');
  if (roiKpi && roiSub) {
    if (tierData.cost_amount === 0) {
      roiKpi.innerText = '0.0 Min';
      roiSub.innerText = 'Free / default base spawn';
    } else {
      // Calculate minutes to generate the invested resource
      if (tierData.cost_type === 'Diamond' && type === 'diamond') {
        const paybackMinutes = tierData.cost_amount / combinedRate;
        const mins = paybackMinutes.toFixed(1);
        roiKpi.innerText = `${mins} Min`;
        roiSub.innerText = `Payback time for ${tierData.cost_amount} diamonds`;
      } else {
        roiKpi.innerText = 'Fast ROI';
        roiSub.innerText = `Invest ${tierData.cost_amount} ${tierData.cost_type}`;
      }
    }
  }

  // Dynamic Strategy Tip
  const tipEl = document.getElementById('calc-tactical-tip');
  if (tipEl) {
    let tipText = '';
    if (type === 'diamond') {
      if (tier === 4 && count === 4) {
        tipText = `Controlling 4 mid Diamond generators at Tier 4 produces a staggering 64 diamonds per minute! In just 45 seconds, your team can purchase full Obsidian cages, full enchanted diamond gear, and multiple ender pearls for an unstoppable endgame push.`;
      } else if (tier >= 3) {
        tipText = `Controlling ${count} Diamond gen(s) at Tier ${tier} yields ${combinedRate.toFixed(0)} diamonds per minute. At this rate, an Obsidian egg shell (20 diamonds) is fully funded in just ${(20 / combinedRate).toFixed(1)} minutes!`;
      } else {
        tipText = `Even a single Tier 2 Diamond generator doubles resource velocity from 2 to 4 diamonds/min. Upgrade early on sub-islands before contesting mid.`;
      }
    } else if (type === 'iron') {
      tipText = `Iron Tier ${tier} produces ${combinedRate.toFixed(0)} iron per minute. Upgrade to Tier 2 (20 iron) on your very first spawn tick to double block generation speed for your void bridger.`;
    } else {
      tipText = `Gold Generator Tier ${tier} delivers ${combinedRate.toFixed(0)} gold/min. Crucial for purchasing Golden Apples (2 gold each) and chainmail armor in the first 3 minutes of combat.`;
    }

    tipEl.innerHTML = `💡 <strong>Bedrock Strategy Tip:</strong> ${tipText}`;
  }
}

function renderGeneratorReference() {
  const container = document.getElementById('generator-reference-cards');
  if (!container || !state.mapsGuide.generators) return;

  const gens = state.mapsGuide.generators;
  const keys = ['iron', 'gold', 'diamond'];

  container.innerHTML = keys.map(k => {
    const g = gens[k];
    const rows = g.tiers.map(t => `
      <tr>
        <td style="font-weight: 700; color: #fff;">Tier ${t.tier}</td>
        <td style="color: var(--accent-cyan); font-weight: 700;">${t.interval_sec}s</td>
        <td style="color: #10b981; font-weight: 700;">${t.rate_per_min.toFixed(1)} /min</td>
        <td style="color: #fbbf24;">${sanitizeHTML(t.upgrade_cost)}</td>
      </tr>
    `).join('');

    return `
      <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <div style="padding: 1rem 1.25rem; border-bottom: 1px solid var(--border-subtle); background: var(--bg-surface-elevated); display: flex; align-items: center; justify-content: space-between;">
          <h4 style="font-size: 1.05rem; font-weight: 800; color: #fff; margin: 0; display: flex; align-items: center; gap: 0.5rem;">
            <span>${g.icon} ${sanitizeHTML(g.name)}</span>
          </h4>
          <span class="badge" style="background: rgba(255,255,255,0.08); color: ${g.badge_color};">
            ${sanitizeHTML(g.material)}
          </span>
        </div>
        <div style="padding: 0.5rem 0;">
          <table class="gen-spec-table">
            <thead>
              <tr>
                <th>Tier</th>
                <th>Interval</th>
                <th>Spawn Rate</th>
                <th>Upgrade Cost</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }).join('');
}

function renderBridgingBenchmarks() {
  const tbody = document.getElementById('bridging-benchmarks-tbody');
  if (!tbody || !state.mapsGuide.bridging) return;

  const filter = state.mapsGuide.selectedBridgeFilter;
  const maxDist = state.mapsGuide.maxBridgeDistance;

  const benchmarks = state.mapsGuide.bridging.benchmarks.filter(b => {
    if (filter !== 'all' && b.game.toLowerCase() !== filter.toLowerCase()) return false;
    if (b.distance_blocks > maxDist) return false;
    return true;
  });

  if (benchmarks.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">
          No void bridging benchmarks match this distance threshold (${maxDist} blocks).
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = benchmarks.map(b => {
    const dangerClass = `danger-${b.danger_level.toLowerCase()}`;
    const isEgg = b.game === 'EggWars';
    const gameColor = isEgg ? 'var(--accent-cyan)' : 'var(--accent-emerald)';

    return `
      <tr>
        <td>
          <strong style="color: #fff;">${sanitizeHTML(b.map_name)}</strong>
          <span style="font-size: 0.72rem; color: ${gameColor}; margin-left: 6px; font-weight: 700;">${sanitizeHTML(b.game)}</span>
        </td>
        <td style="font-weight: 600; color: #cbd5e1;">${sanitizeHTML(b.target)}</td>
        <td>
          <span style="font-size: 1.05rem; font-weight: 900; color: var(--accent-cyan);">${b.distance_blocks}</span>
          <span style="font-size: 0.75rem; color: var(--text-subtle);"> blk</span>
        </td>
        <td style="color: #10b981; font-weight: 800; font-size: 0.95rem;">
          ⚡ ${b.jump_bridge_sec}s
        </td>
        <td style="color: var(--text-muted); font-size: 0.82rem;">
          🚶 ${b.sneak_bridge_sec}s
        </td>
        <td style="font-size: 0.82rem; color: #cbd5e1;">
          ${b.blocks_needed} <span style="color: var(--text-subtle);">(${(b.blocks_needed / 64).toFixed(2)} stk)</span>
        </td>
        <td>
          <span class="danger-badge ${dangerClass}">${sanitizeHTML(b.danger_level)}</span>
        </td>
        <td style="font-size: 0.8rem; color: var(--text-muted); line-height: 1.4; max-width: 260px;">
          ${sanitizeHTML(b.tactical_note)}
        </td>
      </tr>
    `;
  }).join('');
}
