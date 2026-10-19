/**
 * Ligue Foot – Carte "Résultats de la journée"
 * Lit le scoreboard depuis sensor.*_sync (attribut scoreboard) ou sensor.*_prochain_match.
 * Aucune dépendance tierce.
 */
class LigueFootMatchdayCard extends HTMLElement {
  set hass(hass) {
    if (!this._config) return;
    const entity = hass.states[this._config.entity];
    if (!entity) return;

    const attrs = entity.attributes || {};
    // Cherche les events dans scoreboard.events (via sensor de sync) ou events direct
    const events = (attrs.scoreboard && attrs.scoreboard.events)
      ? attrs.scoreboard.events
      : (attrs.events || []);

    const matchesHtml = events.length
      ? events.map(ev => this._renderEvent(ev)).join('')
      : '<div class="empty">Aucun match disponible</div>';

    this.shadowRoot.querySelector('#content').innerHTML = `
      <style>
        :host { display: block; }
        .card { background: var(--card-background-color); border-radius: 12px; padding: 16px; font-family: var(--primary-font-family, sans-serif); }
        .title { font-size: 0.75rem; color: var(--secondary-text-color); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 12px; }
        .match { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 4px; padding: 8px 0; }
        .match:not(:last-child) { border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.08)); }
        .team { display: flex; align-items: center; gap: 6px; font-size: 0.85rem; font-weight: 500; color: var(--primary-text-color); }
        .team.away { flex-direction: row-reverse; text-align: right; }
        .team img { width: 24px; height: 24px; object-fit: contain; flex-shrink: 0; }
        .score { font-size: 1rem; font-weight: 700; text-align: center; min-width: 48px; color: var(--primary-text-color); }
        .score .time { font-size: 0.72rem; font-weight: 400; color: var(--secondary-text-color); display: block; }
        .live-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #e53935; margin-right: 3px; animation: blink 1.2s step-end infinite; vertical-align: middle; }
        @keyframes blink { 50% { opacity: 0; } }
        .empty { color: var(--secondary-text-color); font-size: 0.85rem; text-align: center; padding: 10px 0; }
      </style>
      <div class="card">
        <div class="title">${this._config.title || 'Journée en cours'}</div>
        ${matchesHtml}
      </div>
    `;
  }

  _renderEvent(ev) {
    try {
      const comps = (ev.competitions || [{}])[0];
      const competitors = comps.competitors || [];
      const home = competitors.find(c => c.homeAway === 'home') || competitors[0] || {};
      const away = competitors.find(c => c.homeAway === 'away') || competitors[competitors.length - 1] || {};
      const state = (ev.status || {}).type || {};
      const isLive = state.state === 'in';
      const isPost = state.state === 'post';
      const homeScore = home.score ?? '';
      const awayScore = away.score ?? '';
      const homeName = (home.team || {}).displayName || '—';
      const awayName = (away.team || {}).displayName || '—';
      const homeLogo = (home.team || {}).logo || '';
      const awayLogo = (away.team || {}).logo || '';
      let timeStr = '';
      if (isLive) {
        const clock = ((ev.status || {}).displayClock) || state.shortDetail || '';
        timeStr = `<span class="time"><span class="live-dot"></span>${clock}</span>`;
      } else if (isPost) {
        timeStr = '<span class="time">Terminé</span>';
      } else {
        const d = ev.date ? new Date(ev.date) : null;
        timeStr = d ? `<span class="time">${d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</span>` : '';
      }
      const scoreHtml = (isLive || isPost)
        ? `<div class="score">${homeScore} – ${awayScore}${timeStr}</div>`
        : `<div class="score">vs${timeStr}</div>`;
      return `
        <div class="match">
          <div class="team home">
            ${homeLogo ? `<img src="${homeLogo}" alt="" onerror="this.style.display='none'">` : ''}
            <span>${homeName}</span>
          </div>
          ${scoreHtml}
          <div class="team away">
            ${awayLogo ? `<img src="${awayLogo}" alt="" onerror="this.style.display='none'">` : ''}
            <span>${awayName}</span>
          </div>
        </div>`;
    } catch (e) {
      return '';
    }
  }

  setConfig(config) {
    if (!config.entity) throw new Error('entity requis');
    this._config = config;
    if (!this.shadowRoot) {
      this.attachShadow({ mode: 'open' });
      this.shadowRoot.innerHTML = '<div id="content"></div>';
    }
  }

  getCardSize() { return 4; }

  static getStubConfig() {
    return { entity: 'sensor.mon_equipe_sync' };
  }
}

customElements.define('ligue-foot-matchday-card', LigueFootMatchdayCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'ligue-foot-matchday-card',
  name: 'Ligue Foot – Résultats journée',
  description: 'Affiche tous les matchs de la journée en cours avec scores live.',
});
