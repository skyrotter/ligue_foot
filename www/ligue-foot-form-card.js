/**
 * Ligue Foot – Carte "Forme récente"
 * Aucune dépendance tierce.
 */
class LigueFootFormCard extends HTMLElement {
  set hass(hass) {
    if (!this._config) return;
    const entity = hass.states[this._config.entity];
    if (!entity) return;

    const attrs = entity.attributes || {};
    const results = attrs.results || (entity.state ? entity.state.split(' ') : []);

    const COLORS = { W: '#43a047', D: '#fb8c00', L: '#e53935' };
    const LABELS = { W: 'V', D: 'N', L: 'D' };

    const bubblesHtml = results.map(r => `
      <div class="bubble" style="background:${COLORS[r] || '#888'}" title="${r === 'W' ? 'Victoire' : r === 'D' ? 'Nul' : 'Défaite'}">
        ${LABELS[r] || r}
      </div>
    `).join('');

    // Calcul mini stats
    const w = results.filter(r => r === 'W').length;
    const d = results.filter(r === 'D').length;
    const l = results.filter(r === 'L').length;

    this.shadowRoot.querySelector('#content').innerHTML = `
      <style>
        :host { display: block; }
        .card { background: var(--card-background-color); border-radius: 12px; padding: 16px; font-family: var(--primary-font-family, sans-serif); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .title { font-size: 0.75rem; color: var(--secondary-text-color); text-transform: uppercase; letter-spacing: .05em; }
        .mini-stats { font-size: 0.78rem; color: var(--secondary-text-color); display: flex; gap: 10px; }
        .mini-stats span { display: flex; align-items: center; gap: 3px; }
        .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
        .bubbles { display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; }
        .bubble { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 1rem; color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,.2); }
        .empty { color: var(--secondary-text-color); font-size: 0.85rem; text-align: center; padding: 10px 0; }
      </style>
      <div class="card">
        <div class="header">
          <span class="title">${this._config.title || 'Forme récente'}</span>
          ${results.length ? `
          <div class="mini-stats">
            <span><span class="dot" style="background:#43a047"></span>${w}V</span>
            <span><span class="dot" style="background:#fb8c00"></span>${d}N</span>
            <span><span class="dot" style="background:#e53935"></span>${l}D</span>
          </div>` : ''}
        </div>
        ${results.length
          ? `<div class="bubbles">${bubblesHtml}</div>`
          : '<div class="empty">Aucun résultat disponible</div>'
        }
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

  getCardSize() { return 2; }

  static getStubConfig() {
    return { entity: 'sensor.mon_equipe_forme' };
  }
}

customElements.define('ligue-foot-form-card', LigueFootFormCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'ligue-foot-form-card',
  name: 'Ligue Foot – Forme récente',
  description: 'Affiche les 5 derniers résultats sous forme de bulles colorées (V/N/D).',
});
