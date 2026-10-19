/**
 * Ligue Foot – Carte "Classement"
 * Aucune dépendance tierce.
 */
class LigueFootStandingsCard extends HTMLElement {
  set hass(hass) {
    if (!this._config) return;
    const entity = hass.states[this._config.entity];
    if (!entity) return;

    const attrs = entity.attributes || {};
    const table = attrs.table || [];
    const myPos = parseInt(entity.state, 10) || null;
    const maxRows = this._config.max_rows || 20;
    const rows = table.slice(0, maxRows);

    const rowsHtml = rows.map(r => {
      const isMe = r.position === myPos;
      return `
        <tr class="${isMe ? 'highlight' : ''}">
          <td class="pos">${r.position}</td>
          <td class="logo">${r.logo ? `<img src="${r.logo}" alt="" onerror="this.style.display='none'">` : ''}</td>
          <td class="name">${r.team || '—'}</td>
          <td>${r.played ?? '—'}</td>
          <td>${r.wins ?? '—'}</td>
          <td>${r.draws ?? '—'}</td>
          <td>${r.losses ?? '—'}</td>
          <td class="gd">${r.gd != null ? (r.gd > 0 ? '+' + r.gd : r.gd) : '—'}</td>
          <td class="pts"><strong>${r.points ?? '—'}</strong></td>
        </tr>`;
    }).join('');

    this.shadowRoot.querySelector('#content').innerHTML = `
      <style>
        :host { display: block; }
        .card { background: var(--card-background-color); border-radius: 12px; padding: 16px; font-family: var(--primary-font-family, sans-serif); }
        .title { font-size: 0.75rem; color: var(--secondary-text-color); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
        th { color: var(--secondary-text-color); font-weight: 500; padding: 4px 4px; text-align: center; }
        td { padding: 5px 4px; text-align: center; color: var(--primary-text-color); }
        td.name { text-align: left; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        td.pos { width: 24px; font-weight: 600; }
        td.pts { color: var(--primary-color, #03a9f4); }
        td.gd { color: var(--secondary-text-color); font-size: 0.78rem; }
        td.logo img { width: 20px; height: 20px; object-fit: contain; vertical-align: middle; }
        tr.highlight td { background: color-mix(in srgb, var(--primary-color, #03a9f4) 12%, transparent); border-radius: 4px; }
        tr:not(:last-child) td { border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.08)); }
      </style>
      <div class="card">
        <div class="title">${this._config.title || 'Classement'}</div>
        <table>
          <thead>
            <tr>
              <th>#</th><th></th><th style="text-align:left">Équipe</th>
              <th title="Matchs joués">MJ</th><th title="Victoires">V</th>
              <th title="Nuls">N</th><th title="Défaites">D</th>
              <th title="Diff. buts">DB</th><th title="Points">Pts</th>
            </tr>
          </thead>
          <tbody>${rowsHtml || '<tr><td colspan="9" style="text-align:center;padding:12px;color:var(--secondary-text-color)">Données indisponibles</td></tr>'}</tbody>
        </table>
      </div>
    `;
  }

  setConfig(config) {
    if (!config.entity) throw new Error('entity requis');
    this._config = config;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = '<div id="content"></div>';
    }
  }

  getCardSize() { return Math.min((this._config?.max_rows || 20) + 2, 12); }

  static getStubConfig() {
    return { entity: 'sensor.ligue_1_classement', max_rows: 20 };
  }
}

customElements.define('ligue-foot-standings-card', LigueFootStandingsCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'ligue-foot-standings-card',
  name: 'Ligue Foot – Classement',
  description: 'Affiche le classement complet de la ligue avec mise en évidence de l\'équipe.',
});
