/**
 * Ligue Foot – Carte "Prochain match"
 * Aucune dépendance tierce, vanilla JS + Lit HTML natif HA.
 */
class LigueFootNextMatchCard extends HTMLElement {
  set hass(hass) {
    if (!this._config) return;
    const entity = hass.states[this._config.entity];
    if (!entity) return;

    const attrs = entity.attributes || {};
    const date = entity.state ? new Date(entity.state) : null;
    const home = attrs.home_team || '—';
    const away = attrs.away_team || '—';
    const homeLogo = attrs.home_team_logo || '';
    const awayLogo = attrs.away_team_logo || '';
    const venue = attrs.venue || '';
    const matchday = attrs.matchday ? `J${attrs.matchday}` : '';
    const status = attrs.status || '';

    const dateStr = date
      ? date.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
      : '—';

    const isLive = status.toLowerCase().includes('progress') || status.toLowerCase().includes('cours');
    const liveTag = isLive ? '<span class="live">LIVE</span>' : '';

    this.shadowRoot.querySelector('#content').innerHTML = `
      <style>
        :host { display: block; }
        .card { background: var(--card-background-color); border-radius: 12px; padding: 16px; font-family: var(--primary-font-family, sans-serif); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-size: 0.75rem; color: var(--secondary-text-color); text-transform: uppercase; letter-spacing: .05em; }
        .live { background: #e53935; color: #fff; padding: 2px 6px; border-radius: 4px; font-weight: 700; animation: blink 1.2s step-end infinite; }
        @keyframes blink { 50% { opacity: 0; } }
        .teams { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
        .team { display: flex; flex-direction: column; align-items: center; flex: 1; gap: 6px; }
        .team img { width: 48px; height: 48px; object-fit: contain; }
        .team .name { font-size: 0.85rem; font-weight: 600; text-align: center; color: var(--primary-text-color); }
        .vs { font-size: 1.4rem; font-weight: 700; color: var(--secondary-text-color); padding: 0 4px; }
        .meta { margin-top: 12px; font-size: 0.78rem; color: var(--secondary-text-color); text-align: center; }
      </style>
      <div class="card">
        <div class="header">
          <span>${this._config.title || 'Prochain match'}</span>
          <span>${matchday} ${liveTag}</span>
        </div>
        <div class="teams">
          <div class="team">
            ${homeLogo ? `<img src="${homeLogo}" alt="${home}" onerror="this.style.display='none'">` : ''}
            <span class="name">${home}</span>
          </div>
          <span class="vs">vs</span>
          <div class="team">
            ${awayLogo ? `<img src="${awayLogo}" alt="${away}" onerror="this.style.display='none'">` : ''}
            <span class="name">${away}</span>
          </div>
        </div>
        <div class="meta">${dateStr}${venue ? ' · ' + venue : ''}</div>
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

  getCardSize() { return 3; }

  static getConfigElement() {
    return document.createElement('ligue-foot-next-match-card-editor');
  }

  static getStubConfig() {
    return { entity: 'sensor.mon_equipe_prochain_match' };
  }
}

customElements.define('ligue-foot-next-match-card', LigueFootNextMatchCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'ligue-foot-next-match-card',
  name: 'Ligue Foot – Prochain match',
  description: 'Affiche le prochain match de l\'équipe configurée.',
});
