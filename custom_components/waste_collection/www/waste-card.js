class WasteCollectionCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._modalOpen = false;
    this._view = 'card'; // 'card' | 'schedule' | 'import'
    this._pickups = [];
    this._importError = '';
  }

  setConfig(config) {
    this.config = config;
  }

  set hass(hass) {
    this._hass = hass;
    const masterState = hass.states['sensor.waste_collection_schedule'];
    if (masterState && masterState.attributes.pickups) {
      this._pickups = masterState.attributes.pickups;
    }
    if (!this.shadowRoot.innerHTML) this._render();
    else if (!this._modalOpen) this._updateCard();
  }

  // ─────────────────────────────────────────────
  //  Data helpers
  // ─────────────────────────────────────────────
  _today() {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  }

  _parseDate(str) {
    if (!str) return null;
    const d = new Date(str + 'T00:00:00');
    return isNaN(d) ? null : d;
  }

  _daysUntil(dateStr) {
    const d = this._parseDate(dateStr);
    if (!d) return null;
    const diff = d - this._today();
    return Math.round(diff / 86400000);
  }

  _nextPickup(type) {
    const today = this._today();
    const future = this._pickups
      .filter(p => p.type === type)
      .map(p => ({ ...p, _d: this._parseDate(p.date) }))
      .filter(p => p._d && p._d >= today)
      .sort((a, b) => a._d - b._d);
    return future[0] || null;
  }

  _formatDate(dateStr) {
    const d = this._parseDate(dateStr);
    if (!d) return '—';
    return d.toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  _daysLabel(days) {
    if (days === null) return 'brak';
    if (days < 0) return 'minęło';
    if (days === 0) return 'DZIŚ';
    if (days === 1) return 'JUTRO';
    return `za ${days} dni`;
  }

  _urgencyClass(days) {
    if (days === null || days < 0) return 'none';
    if (days <= 1) return 'urgent';
    if (days <= 3) return 'soon';
    return 'ok';
  }

  // ─────────────────────────────────────────────
  //  Waste type definitions
  // ─────────────────────────────────────────────
  _wasteTypes() {
    return [
      { id: 'bio',     label: 'Bio',       icon: '🍃', color: '#4caf50', bg: '#e8f5e9' },
      { id: 'mixed',   label: 'Zmieszane', icon: '🗑️',  color: '#607d8b', bg: '#eceff1' },
      { id: 'plastic', label: 'Plastik',   icon: '🧴',  color: '#ff9800', bg: '#fff3e0' },
      { id: 'paper',   label: 'Papier',    icon: '📄', color: '#2196f3', bg: '#e3f2fd' },
      { id: 'glass',   label: 'Szkło',     icon: '🍾',  color: '#9c27b0', bg: '#f3e5f5' },
    ];
  }

  // ─────────────────────────────────────────────
  //  Save to HA
  // ─────────────────────────────────────────────
  _save() {
    this._hass.callService('waste_collection', 'update_schedule', {
      pickups: this._pickups,
    });
  }

  // ─────────────────────────────────────────────
  //  Render
  // ─────────────────────────────────────────────
  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        :host { display: block; }
        
        ha-card {
          font-family: 'Segoe UI', system-ui, sans-serif;
          overflow: hidden;
          position: relative;
        }

        /* ── MAIN CARD VIEW ── */
        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 16px 8px;
        }
        .card-title {
          font-size: 1.1em;
          font-weight: 600;
          color: var(--primary-text-color);
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .header-actions { display: flex; gap: 8px; }
        .btn-icon {
          background: none;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          padding: 6px 10px;
          cursor: pointer;
          font-size: 1em;
          color: var(--primary-text-color);
          transition: background 0.15s;
        }
        .btn-icon:hover { background: var(--secondary-background-color); }

        /* ── WASTE TILES GRID ── */
        .tiles-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 10px;
          padding: 8px 16px 16px;
        }
        @media (max-width: 400px) {
          .tiles-grid { grid-template-columns: repeat(3, 1fr); }
        }

        .tile {
          border-radius: 14px;
          padding: 14px 6px 12px;
          text-align: center;
          background: var(--ha-card-background, var(--card-background-color, #1c1c1e));
          border: 1px solid rgba(255,255,255,0.07);
          box-shadow: 0 2px 8px rgba(0,0,0,0.25);
          transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
          cursor: default;
          position: relative;
          overflow: hidden;
        }
        .tile:hover {
          transform: translateY(-3px);
          box-shadow: 0 6px 18px rgba(0,0,0,0.35);
        }

        .tile-icon {
          font-size: 2em;
          line-height: 1;
          margin-bottom: 8px;
          display: block;
          filter: drop-shadow(0 1px 3px rgba(0,0,0,0.4));
        }
        .tile-label {
          font-size: 0.6em;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.8px;
          color: var(--secondary-text-color);
          margin-bottom: 5px;
        }
        .tile-days {
          font-size: 0.78em;
          font-weight: 800;
          line-height: 1.2;
          color: var(--primary-text-color);
        }
        .tile-date {
          font-size: 0.55em;
          opacity: 0.5;
          margin-top: 4px;
          color: var(--secondary-text-color);
        }

        /* urgency highlight — colored top border like HA button-card active state */
        .tile.urgent {
          border-top: 3px solid var(--tile-color);
          animation: pulse 1.5s infinite;
        }
        .tile.soon {
          border-top: 3px solid var(--tile-color);
          opacity: 0.92;
        }
        .tile.ok {
          border-top: 3px solid transparent;
        }
        .tile.none {
          opacity: 0.5;
        }

        @keyframes pulse {
          0%, 100% { box-shadow: 0 2px 8px rgba(0,0,0,0.25); }
          50% { box-shadow: 0 0 0 4px rgba(var(--tile-color-rgb, 255,152,0), 0.25); }
        }

        /* ── SCHEDULE VIEW ── */
        .panel {
          padding: 16px;
        }
        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 14px;
        }
        .panel-title { font-size: 1em; font-weight: 600; }
        .btn-back {
          background: none; border: none; cursor: pointer;
          font-size: 0.85em; color: var(--primary-color);
          display: flex; align-items: center; gap: 4px; padding: 4px 0;
        }

        .add-row {
          display: grid;
          grid-template-columns: 1fr 1fr auto;
          gap: 8px;
          margin-bottom: 14px;
        }
        .add-row select, .add-row input {
          padding: 8px 10px;
          border-radius: 8px;
          border: 1px solid var(--divider-color);
          background: var(--secondary-background-color);
          color: var(--primary-text-color);
          font-size: 0.9em;
        }
        .btn-add {
          background: var(--primary-color);
          color: white;
          border: none;
          border-radius: 8px;
          padding: 8px 14px;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.9em;
          white-space: nowrap;
        }
        .btn-add:hover { opacity: 0.9; }

        .schedule-list { max-height: 350px; overflow-y: auto; }
        .schedule-group { margin-bottom: 12px; }
        .schedule-group-title {
          font-size: 0.75em;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          padding: 4px 0;
          border-bottom: 1px solid var(--divider-color);
          margin-bottom: 6px;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .pickup-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 6px 0;
          border-bottom: 1px solid var(--divider-color);
          font-size: 0.88em;
        }
        .pickup-row:last-child { border-bottom: none; }
        .pickup-date { color: var(--primary-text-color); }
        .pickup-days { color: var(--secondary-text-color); font-size: 0.85em; }
        .btn-del-pickup {
          background: none; border: none; cursor: pointer;
          color: var(--error-color); font-size: 1em; padding: 2px 6px;
          border-radius: 4px;
        }
        .btn-del-pickup:hover { background: var(--error-color); color: white; }
        .past { opacity: 0.45; }

        /* ── IMPORT VIEW ── */
        .import-area {
          border: 2px dashed var(--divider-color);
          border-radius: 12px;
          padding: 24px;
          text-align: center;
          margin-bottom: 14px;
          cursor: pointer;
          transition: border-color 0.2s, background 0.2s;
        }
        .import-area:hover, .import-area.drag-over {
          border-color: var(--primary-color);
          background: var(--secondary-background-color);
        }
        .import-area p { font-size: 0.85em; color: var(--secondary-text-color); margin-top: 8px; }
        .import-icon { font-size: 2.5em; }
        #file-input { display: none; }

        .import-type-selector {
          display: flex;
          gap: 8px;
          margin-bottom: 14px;
        }
        .type-chip {
          flex: 1;
          padding: 8px;
          border: 1px solid var(--divider-color);
          border-radius: 8px;
          text-align: center;
          cursor: pointer;
          font-size: 0.85em;
          transition: all 0.15s;
        }
        .type-chip.active {
          border-color: var(--primary-color);
          background: var(--primary-color);
          color: white;
          font-weight: 600;
        }

        .import-hint {
          font-size: 0.78em;
          color: var(--secondary-text-color);
          line-height: 1.5;
          margin-bottom: 12px;
          background: var(--secondary-background-color);
          border-radius: 8px;
          padding: 10px 12px;
        }
        .import-hint code {
          font-family: monospace;
          background: var(--divider-color);
          padding: 1px 4px;
          border-radius: 3px;
          font-size: 0.95em;
        }

        .error-msg {
          color: var(--error-color);
          font-size: 0.82em;
          margin-top: 6px;
          padding: 8px 10px;
          background: rgba(var(--rgb-error-color, 244,67,54), 0.08);
          border-radius: 6px;
        }
        .success-msg {
          color: var(--success-color, #4caf50);
          font-size: 0.82em;
          padding: 8px 10px;
          background: rgba(76,175,80,0.08);
          border-radius: 6px;
          margin-top: 6px;
        }

        .btn-row { display: flex; gap: 8px; margin-top: 14px; }
        .btn-secondary {
          flex: 1; padding: 10px; border-radius: 8px;
          border: 1px solid var(--divider-color);
          background: none; color: var(--primary-text-color);
          cursor: pointer; font-size: 0.9em;
        }
        .btn-primary {
          flex: 2; padding: 10px; border-radius: 8px;
          background: var(--primary-color); color: white;
          border: none; cursor: pointer; font-size: 0.9em; font-weight: 600;
        }

        .hidden { display: none !important; }
      </style>

      <ha-card>
        <!-- MAIN CARD VIEW -->
        <div id="view-card">
          <div class="card-header">
            <div class="card-title">🚛 Wywóz śmieci</div>
            <div class="header-actions">
              <button class="btn-icon" id="btn-import" title="Importuj harmonogram">📥</button>
              <button class="btn-icon" id="btn-schedule" title="Zarządzaj harmonogramem">📅</button>
            </div>
          </div>
          <div class="tiles-grid" id="tiles-grid"></div>
        </div>

        <!-- SCHEDULE VIEW -->
        <div id="view-schedule" class="hidden panel">
          <div class="panel-header">
            <div class="panel-title">📅 Harmonogram</div>
            <button class="btn-back" id="btn-back-schedule">← Wróć</button>
          </div>
          <div class="add-row">
            <select id="add-type">
              <option value="bio">🍃 Bio</option>
              <option value="mixed">🗑️ Zmieszane</option>
              <option value="plastic">♻️ Plastik</option>
              <option value="paper">📰 Papier</option>
              <option value="glass">🫙 Szkło</option>
            </select>
            <input type="date" id="add-date">
            <button class="btn-add" id="btn-add-pickup">+ Dodaj</button>
          </div>
          <div class="schedule-list" id="schedule-list"></div>
        </div>

        <!-- IMPORT VIEW -->
        <div id="view-import" class="hidden panel">
          <div class="panel-header">
            <div class="panel-title">📥 Importuj harmonogram</div>
            <button class="btn-back" id="btn-back-import">← Wróć</button>
          </div>

          <div class="import-type-selector">
            <div class="type-chip active" data-fmt="ics">📆 ICS (iCal)</div>
            <div class="type-chip" data-fmt="json">{ } JSON</div>
          </div>

          <div id="hint-ics" class="import-hint">
            <strong>Format ICS (iCal)</strong> — eksportuj kalendarz z aplikacji urzędu lub gminy.<br>
            Nazwa zdarzenia powinna zawierać słowo: <code>bio</code>, <code>plastik</code>, <code>papier</code>, <code>szkło</code> lub <code>zmieszane</code>.
          </div>
          <div id="hint-json" class="import-hint hidden">
            <strong>Format JSON</strong> — tablica obiektów lub obiekt z kluczem <code>pickups</code>:<br>
            <code>[{"type":"bio","date":"2025-03-14"},...]</code><br>
            Dozwolone typy: <code>bio</code>, <code>mixed</code>, <code>plastic</code>, <code>paper</code>, <code>glass</code>
          </div>

          <div class="import-area" id="drop-zone">
            <div class="import-icon">📂</div>
            <strong>Przeciągnij plik lub kliknij, aby wybrać</strong>
            <p>Obsługiwane formaty: .ics, .json</p>
            <input type="file" id="file-input" accept=".ics,.json,.txt">
          </div>
          <div id="import-msg"></div>

          <div class="btn-row">
            <button class="btn-secondary" id="btn-import-cancel">Anuluj</button>
            <button class="btn-primary" id="btn-import-apply" disabled>Zastosuj import</button>
          </div>
        </div>
      </ha-card>
    `;

    this._setupListeners();
    this._updateCard();
  }

  // ─────────────────────────────────────────────
  //  Update dynamic card content
  // ─────────────────────────────────────────────
  _updateCard() {
    this._renderTiles();
    if (this._view === 'schedule') this._renderScheduleList();
  }

  _renderTiles() {
    const grid = this.shadowRoot.getElementById('tiles-grid');
    if (!grid) return;

    grid.innerHTML = this._wasteTypes().map(wt => {
      const next = this._nextPickup(wt.id);
      const days = next ? this._daysUntil(next.date) : null;
      const urgency = this._urgencyClass(days);
      const daysText = this._daysLabel(days);
      const dateText = next ? this._formatDate(next.date) : '—';
      const daysColor = (urgency === 'urgent' || urgency === 'soon') ? wt.color : 'var(--primary-text-color)';

      return `
        <div class="tile ${urgency}" style="--tile-color:${wt.color}; border-top-color:${(urgency === 'urgent' || urgency === 'soon') ? wt.color : 'transparent'};">
          <span class="tile-icon">${wt.icon}</span>
          <div class="tile-label">${wt.label}</div>
          <div class="tile-days" style="color:${daysColor}">${daysText}</div>
          <div class="tile-date">${dateText}</div>
        </div>
      `;
    }).join('');
  }

  _renderScheduleList() {
    const list = this.shadowRoot.getElementById('schedule-list');
    if (!list) return;

    const types = this._wasteTypes();
    const sorted = [...this._pickups].sort((a, b) => {
      const da = this._parseDate(a.date), db = this._parseDate(b.date);
      if (!da || !db) return 0;
      return da - db;
    });

    // Group by type
    const groups = {};
    for (const wt of types) groups[wt.id] = [];
    for (const p of sorted) {
      if (groups[p.type] !== undefined) groups[p.type].push(p);
    }

    const today = this._today();

    list.innerHTML = types.map(wt => {
      const items = groups[wt.id];
      if (items.length === 0) return `
        <div class="schedule-group">
          <div class="schedule-group-title">${wt.icon} ${wt.label}</div>
          <div style="font-size:0.8em;color:var(--secondary-text-color);padding:4px 0;">Brak wpisów</div>
        </div>
      `;
      return `
        <div class="schedule-group">
          <div class="schedule-group-title" style="color:${wt.color}">${wt.icon} ${wt.label}</div>
          ${items.map(p => {
            const d = this._parseDate(p.date);
            const past = d && d < today;
            const days = this._daysUntil(p.date);
            return `
              <div class="pickup-row ${past ? 'past' : ''}">
                <span class="pickup-date">${this._formatDate(p.date)}</span>
                <span class="pickup-days">${this._daysLabel(days)}</span>
                <button class="btn-del-pickup" 
                  onclick="this.getRootNode().host._deletePickup('${wt.id}','${p.date}')">✕</button>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }).join('');
  }

  // ─────────────────────────────────────────────
  //  View switching
  // ─────────────────────────────────────────────
  _showView(view) {
    this._view = view;
    const views = ['card', 'schedule', 'import'];
    for (const v of views) {
      const el = this.shadowRoot.getElementById(`view-${v}`);
      if (el) el.classList.toggle('hidden', v !== view);
    }
    if (view === 'schedule') this._renderScheduleList();
    if (view === 'card') this._updateCard();
  }

  // ─────────────────────────────────────────────
  //  Event listeners
  // ─────────────────────────────────────────────
  _setupListeners() {
    const root = this.shadowRoot;

    // Navigation
    root.getElementById('btn-schedule').onclick = () => this._showView('schedule');
    root.getElementById('btn-import').onclick = () => { this._showView('import'); this._resetImport(); };
    root.getElementById('btn-back-schedule').onclick = () => this._showView('card');
    root.getElementById('btn-back-import').onclick = () => this._showView('card');
    root.getElementById('btn-import-cancel').onclick = () => this._showView('card');

    // Add pickup
    root.getElementById('btn-add-pickup').onclick = () => {
      const type = root.getElementById('add-type').value;
      const date = root.getElementById('add-date').value;
      if (!date) return;
      // Avoid duplicates
      if (!this._pickups.find(p => p.type === type && p.date === date)) {
        this._pickups.push({ type, date });
        this._save();
      }
      root.getElementById('add-date').value = '';
      this._renderScheduleList();
    };

    // Import format chips
    root.querySelectorAll('.type-chip').forEach(chip => {
      chip.onclick = () => {
        root.querySelectorAll('.type-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const fmt = chip.dataset.fmt;
        root.getElementById('hint-ics').classList.toggle('hidden', fmt !== 'ics');
        root.getElementById('hint-json').classList.toggle('hidden', fmt !== 'json');
        this._resetImport();
      };
    });

    // File drop zone
    const dropZone = root.getElementById('drop-zone');
    const fileInput = root.getElementById('file-input');

    dropZone.onclick = () => fileInput.click();
    dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); };
    dropZone.ondragleave = () => dropZone.classList.remove('drag-over');
    dropZone.ondrop = (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) this._handleFile(file);
    };
    fileInput.onchange = () => {
      if (fileInput.files[0]) this._handleFile(fileInput.files[0]);
    };

    // Apply import
    root.getElementById('btn-import-apply').onclick = () => {
      if (this._pendingImport) {
        // Merge, avoiding duplicates
        let added = 0;
        for (const p of this._pendingImport) {
          if (!this._pickups.find(x => x.type === p.type && x.date === p.date)) {
            this._pickups.push(p);
            added++;
          }
        }
        this._save();
        this._showView('card');
      }
    };
  }

  // ─────────────────────────────────────────────
  //  File handling
  // ─────────────────────────────────────────────
  _resetImport() {
    this._pendingImport = null;
    const root = this.shadowRoot;
    root.getElementById('import-msg').innerHTML = '';
    root.getElementById('btn-import-apply').disabled = true;
    root.getElementById('file-input').value = '';
  }

  _handleFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      try {
        let pickups = [];
        const fmt = this.shadowRoot.querySelector('.type-chip.active')?.dataset.fmt || 'ics';

        if (fmt === 'ics' || file.name.endsWith('.ics')) {
          const events = this._parseICS(text);
          for (const ev of events) {
            if (!ev.date) continue;
            const type = this._detectType(ev.summary || '');
            if (type) pickups.push({ type, date: ev.date });
          }
        } else {
          pickups = this._parseJSON(text);
        }

        if (pickups.length === 0) throw new Error('Nie znaleziono żadnych wpisów wywozu śmieci');

        this._pendingImport = pickups;
        this.shadowRoot.getElementById('import-msg').innerHTML =
          `<div class="success-msg">✅ Znaleziono <strong>${pickups.length}</strong> wpisów. Kliknij „Zastosuj import".</div>`;
        this.shadowRoot.getElementById('btn-import-apply').disabled = false;
      } catch (err) {
        this._pendingImport = null;
        this.shadowRoot.getElementById('import-msg').innerHTML =
          `<div class="error-msg">❌ Błąd: ${err.message}</div>`;
        this.shadowRoot.getElementById('btn-import-apply').disabled = true;
      }
    };
    reader.readAsText(file);
  }

  _parseICS(text) {
    const events = [];
    const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
    let current = null;
    for (const line of lines) {
      if (line === 'BEGIN:VEVENT') { current = {}; }
      else if (line === 'END:VEVENT' && current) { events.push(current); current = null; }
      else if (current) {
        if (line.startsWith('DTSTART')) {
          const val = line.split(':').slice(1).join(':').trim().replace(/T.*$/, '');
          if (val.length === 8) {
            current.date = `${val.substring(0,4)}-${val.substring(4,6)}-${val.substring(6,8)}`;
          }
        } else if (line.startsWith('SUMMARY')) {
          current.summary = line.split(':').slice(1).join(':').trim();
        }
      }
    }
    return events;
  }

  _detectType(summary) {
    const s = summary.toLowerCase();
    if (s.includes('bio') || s.includes('organic') || s.includes('zielony')) return 'bio';
    if (s.includes('plastik') || s.includes('plastic') || s.includes('żółt') || s.includes('yellow') || s.includes('pet')) return 'plastic';
    if (s.includes('papier') || s.includes('paper') || s.includes('niebieski') || s.includes('blue')) return 'paper';
    if (s.includes('szkło') || s.includes('glass') || s.includes('szklany')) return 'glass';
    if (s.includes('zmieszan') || s.includes('mixed') || s.includes('szary') || s.includes('grey') || s.includes('gray') || s.includes('ogólny')) return 'mixed';
    return null;
  }

  _parseJSON(text) {
    const data = JSON.parse(text);
    const arr = Array.isArray(data) ? data : data.pickups;
    if (!Array.isArray(arr)) throw new Error('Oczekiwano tablicy lub obiektu z kluczem "pickups"');
    return arr.filter(p => p.type && p.date);
  }

  _deletePickup(type, date) {
    this._pickups = this._pickups.filter(p => !(p.type === type && p.date === date));
    this._save();
    this._renderScheduleList();
  }

  getCardSize() { return 3; }

  static getConfigElement() {
    return document.createElement('div'); // no config needed
  }

  static getStubConfig() {
    return {};
  }
}

customElements.define('waste-collection-card', WasteCollectionCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'waste-collection-card',
  name: 'Waste Collection Card',
  description: 'Track waste collection schedule with countdown timers.',
  preview: false,
});