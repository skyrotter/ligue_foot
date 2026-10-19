/*
 * Ligue Foot – cartes Lovelace autonomes (aucune dépendance : ni card-mod,
 * ni mushroom, ni button-card). Chargé automatiquement par l'intégration.
 *
 * Cartes :
 *  - custom:ligue-foot-next-match-card  (entité « Prochain match »)
 *  - custom:ligue-foot-form-card        (entité « Dernier résultat »)
 *  - custom:ligue-foot-standings-card   (entité « Classement »)
 *  - custom:ligue-foot-matchday-card    (entité « Journée »)
 */

const LF_VERSION = "0.2.0";

// ---------------------------------------------------------------- Traductions
const LF_TEXT = {
  fr: {
    noMatch: "Aucun match à venir",
    live: "En direct",
    kickoffIn: "Coup d'envoi dans",
    now: "Coup d'envoi imminent",
    day: "jour",
    days: "jours",
    form: "Forme",
    standings: "Classement",
    results: "Derniers résultats",
    upcoming: "Prochaine journée",
    pts: "Pts",
    played: "J",
    won: "G",
    drawn: "N",
    lost: "P",
    diff: "+/-",
    team: "Équipe",
    win: "V",
    draw: "N",
    loss: "D",
    missing: "Entité introuvable : ",
    noData: "Pas de données",
    entity: "Entité",
    rows: "Nombre de lignes (vide = tout)",
    highlight: "Équipes à surligner (séparées par une virgule)",
    design: "Design",
    dNight: "Nuit",
    dHa: "Natif Home Assistant",
    dLight: "Clair",
    dStadium: "Stade",
    nextName: "Match à venir – Ligue Foot",
    nextDesc: "Prochain match d'une équipe favorite.",
    formName: "Forme d'équipe – Ligue Foot",
    formDesc: "Les 5 derniers résultats d'une équipe.",
    standingsName: "Classement – Ligue Foot",
    standingsDesc: "Classement d'un championnat.",
    matchdayName: "Journée – Ligue Foot",
    matchdayDesc: "Derniers résultats et prochaine journée.",
  },
  en: {
    noMatch: "No upcoming match",
    live: "Live",
    kickoffIn: "Kick-off in",
    now: "Kick-off imminent",
    day: "day",
    days: "days",
    form: "Form",
    standings: "Standings",
    results: "Latest results",
    upcoming: "Next matchday",
    pts: "Pts",
    played: "P",
    won: "W",
    drawn: "D",
    lost: "L",
    diff: "GD",
    team: "Team",
    win: "W",
    draw: "D",
    loss: "L",
    missing: "Entity not found: ",
    noData: "No data",
    entity: "Entity",
    rows: "Number of rows (empty = all)",
    highlight: "Teams to highlight (comma separated)",
    design: "Design",
    dNight: "Night",
    dHa: "Home Assistant (native)",
    dLight: "Light",
    dStadium: "Stadium",
    nextName: "Next match – Ligue Foot",
    nextDesc: "Next match of a favourite team.",
    formName: "Team form – Ligue Foot",
    formDesc: "Last 5 results of a team.",
    standingsName: "Standings – Ligue Foot",
    standingsDesc: "League table.",
    matchdayName: "Matchday – Ligue Foot",
    matchdayDesc: "Latest results and next matchday.",
  },
};

function lfLang(hass) {
  const l = (hass && (hass.locale?.language || hass.language)) || "en";
  return l.toLowerCase().startsWith("fr") ? "fr" : "en";
}

// ------------------------------------------------------------------- Style
const LF_STYLE = `
  :host { display: block; }
  ha-card {
    display: block;
    background: var(--lf-bg);
    color: var(--lf-fg);
    border-radius: 18px;
    border: 1px solid var(--lf-border);
    border-bottom: 3px solid var(--lf-accent);
    padding: 16px;
    box-sizing: border-box;
    overflow: hidden;
    /* Design « Nuit » (par défaut) */
    --lf-bg: linear-gradient(160deg, #101a33 0%, #0b1226 100%);
    --lf-fg: #e8edf7; --lf-muted: #8d99b3; --lf-soft: #c4cde0;
    --lf-title: #d9a441; --lf-accent: #2aa5e0;
    --lf-border: rgba(255, 255, 255, 0.06); --lf-line: rgba(255, 255, 255, 0.08);
    --lf-hl: rgba(42, 165, 224, 0.16); --lf-rank: #3a4565; --lf-rank-fg: #fff;
    --lf-win: #2e9e5b; --lf-draw: #8d99b3; --lf-loss: #d64545;
  }
  /* Design « Natif Home Assistant » : suit le thème clair/sombre de l'utilisateur */
  ha-card.ha {
    --lf-bg: var(--ha-card-background, var(--card-background-color, #fff));
    --lf-fg: var(--primary-text-color); --lf-muted: var(--secondary-text-color);
    --lf-soft: var(--primary-text-color); --lf-title: var(--primary-color);
    --lf-accent: var(--primary-color); --lf-border: var(--divider-color);
    --lf-line: var(--divider-color);
    --lf-hl: color-mix(in srgb, var(--primary-color) 14%, transparent);
    --lf-rank: var(--secondary-background-color, #ddd); --lf-rank-fg: var(--primary-text-color);
  }
  /* Design « Clair » */
  ha-card.light {
    --lf-bg: #ffffff; --lf-fg: #14213d; --lf-muted: #6b7a90; --lf-soft: #3d4a63;
    --lf-title: #0a7d4b; --lf-accent: #0a7d4b;
    --lf-border: #e3e8ef; --lf-line: #e3e8ef; --lf-hl: rgba(10, 125, 75, 0.1);
    --lf-rank: #e3e8ef; --lf-rank-fg: #14213d;
  }
  /* Design « Stade » */
  ha-card.stadium {
    --lf-bg: repeating-linear-gradient(90deg, #14532d 0 48px, #166534 48px 96px);
    --lf-fg: #f4fff6; --lf-muted: #b7e4c7; --lf-soft: #dcfce7;
    --lf-title: #fde68a; --lf-accent: #ffffff;
    --lf-border: rgba(255, 255, 255, 0.25); --lf-line: rgba(255, 255, 255, 0.22);
    --lf-hl: rgba(255, 255, 255, 0.18); --lf-rank: rgba(0, 0, 0, 0.35); --lf-rank-fg: #fff;
  }
  .title {
    color: var(--lf-title);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 0 0 12px;
    display: flex; align-items: center; gap: 8px;
  }
  .title ha-icon { --mdc-icon-size: 18px; }
  .muted { color: var(--lf-muted); font-size: 13px; }
  .empty { text-align: center; padding: 18px 0; color: var(--lf-muted); }
  img.logo { object-fit: contain; flex: none; }
  .err { color: #ff8a80; padding: 8px 0; }

  /* --- Prochain match --- */
  .match { display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); align-items: center; gap: 8px; }
  .match .team { display: flex; flex-direction: column; align-items: center; gap: 8px; text-align: center; }
  .match .team img { width: 64px; height: 64px; max-width: 100%; }
  .match .team span { font-weight: 700; font-size: 14px; overflow-wrap: anywhere; }
  .match .mid { text-align: center; min-width: 0; }
  .match .time { font-size: 22px; font-weight: 800; }
  .match .score { font-size: 30px; font-weight: 800; letter-spacing: 2px; }
  .badge-live {
    display: inline-block; margin-top: 4px; padding: 2px 10px; border-radius: 10px;
    background: #e53935; color: #fff; font-size: 11px; font-weight: 700;
    animation: lf-pulse 1.4s infinite;
  }
  @keyframes lf-pulse { 50% { opacity: 0.55; } }
  .info { text-align: center; margin-top: 12px; display: grid; gap: 2px; }
  .info .when { font-size: 14px; text-transform: capitalize; }
  .info .count { font-weight: 700; font-size: 15px; margin-top: 8px;
    padding-top: 10px; border-top: 1px solid var(--lf-line); }

  /* --- Forme --- */
  .form { display: flex; justify-content: space-around; gap: 6px; }
  .form .f { display: flex; flex-direction: column; align-items: center; gap: 6px; }
  .form .f img { width: 36px; height: 36px; }
  .form .f small { color: var(--lf-muted); font-size: 11px; }
  .pill {
    width: 26px; height: 26px; border-radius: 50%; display: grid; place-items: center;
    font-weight: 800; font-size: 13px; color: #fff;
  }
  .pill.V { background: var(--lf-win); }
  .pill.N { background: var(--lf-draw); }
  .pill.D { background: var(--lf-loss); }
  .pill.q { background: var(--lf-rank); color: var(--lf-rank-fg); }

  /* --- Classement --- */
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { color: var(--lf-muted); font-weight: 600; padding: 4px 4px; text-align: center; }
  td { padding: 5px 4px; text-align: center; border-top: 1px solid var(--lf-line); }
  th.t, td.t { text-align: left; }
  td.t { font-weight: 600; }
  .tn { display: flex; align-items: center; gap: 8px; }
  .tn img { width: 20px; height: 20px; }
  td.pts { font-weight: 800; }
  .rank {
    display: inline-grid; place-items: center; width: 24px; height: 24px; border-radius: 50%;
    background: var(--lf-rank); color: var(--lf-rank-fg); font-weight: 700; font-size: 12px;
  }
  .rank[style] { color: #fff; }
  tr.hl td { background: var(--lf-hl); }

  /* --- Journée --- */
  .sec { margin-bottom: 14px; }
  .sec:last-child { margin-bottom: 0; }
  .day { text-align: center; font-weight: 700; font-size: 13px; padding: 6px 0 4px;
    color: var(--lf-soft); border-top: 1px solid var(--lf-line); }
  .day:first-of-type { border-top: 0; }
  .row { display: grid; grid-template-columns: 1fr 64px 1fr; align-items: center; gap: 6px;
    padding: 4px 0; font-size: 13px; }
  .row .h { display: flex; justify-content: flex-end; align-items: center; gap: 6px; text-align: right; }
  .row .a { display: flex; justify-content: flex-start; align-items: center; gap: 6px; }
  .row img { width: 20px; height: 20px; }
  .row .sc { text-align: center; font-weight: 800; }
  .row .sc.t { font-weight: 600; color: var(--lf-soft); }
`;

// ----------------------------------------------------------------- Utilitaires
const lfEsc = (v) =>
  String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const lfLogo = (url, size) =>
  url
    ? `<img class="logo" src="${lfEsc(url)}" ${size ? `width="${size}" height="${size}"` : ""} loading="lazy" onerror="this.style.visibility='hidden'">`
    : "";

function lfLocale(hass) {
  return hass?.locale?.language || hass?.language || "fr";
}

// ------------------------------------------------------------------ Base
class LigueFootBase extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._st = null;
  }

  setConfig(config) {
    if (!config || !config.entity) throw new Error("entity est obligatoire");
    this._config = config;
    this._st = null;
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    const st = hass.states[this._config?.entity];
    if (st !== this._st) {
      this._st = st;
      this._render();
    }
  }

  connectedCallback() {
    // Rafraîchit le compte à rebours chaque minute
    this._timer = setInterval(() => this._render(), 60000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
  }

  getCardSize() {
    return 4;
  }

  get _t() {
    return LF_TEXT[lfLang(this._hass)];
  }

  // Design choisi : night (défaut), ha, light, stadium
  _design() {
    const d = this._config && this._config.design;
    return ["ha", "light", "stadium"].includes(d) ? d : "night";
  }

  _frame(inner) {
    this.shadowRoot.innerHTML = `<style>${LF_STYLE}</style><ha-card class="${this._design()}">${inner}</ha-card>`;
  }

  _render() {
    if (!this._config) return;
    const t = this._t;
    if (!this._hass) return;
    if (!this._st) {
      this._frame(`<div class="err">${t.missing}${lfEsc(this._config.entity)}</div>`);
      return;
    }
    this._frame(this._body(this._st, t));
  }

  _fmtDate(iso, opts) {
    return new Date(iso).toLocaleString(lfLocale(this._hass), opts);
  }
}

// ------------------------------------------------------------ Prochain match
class LigueFootNextMatchCard extends LigueFootBase {
  _countdown(iso, t) {
    const diff = new Date(iso).getTime() - Date.now();
    if (diff <= 60000) return t.now;
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${t.kickoffIn} ${mins} min`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${t.kickoffIn} ${hours} h ${String(mins % 60).padStart(2, "0")}`;
    const d = Math.floor(hours / 24);
    return `${t.kickoffIn} ${d} ${d > 1 ? t.days : t.day}`;
  }

  _body(st, t) {
    const a = st.attributes;
    if (!a.kickoff) {
      return `<div class="title">${lfEsc(this._config.name || a.team || "")}</div><div class="empty">${t.noMatch}</div>`;
    }
    const started = a.match_state === "in" || a.match_state === "post";
    const mid = started
      ? `<div class="score">${a.home_score ?? 0} - ${a.away_score ?? 0}</div>${a.match_state === "in" ? `<span class="badge-live">${t.live}</span>` : ""}`
      : `<div class="time">${this._fmtDate(a.kickoff, { hour: "2-digit", minute: "2-digit" })}</div>`;
    const when = this._fmtDate(a.kickoff, { weekday: "long", day: "numeric", month: "long" });
    return `
      <div class="title"><ha-icon icon="mdi:soccer"></ha-icon>${lfEsc(a.league || "")}</div>
      <div class="match">
        <div class="team">${lfLogo(a.home_logo)}<span>${lfEsc(a.home_team)}</span></div>
        <div class="mid">${mid}</div>
        <div class="team">${lfLogo(a.away_logo)}<span>${lfEsc(a.away_team)}</span></div>
      </div>
      <div class="info">
        <div class="when">${lfEsc(when)}</div>
        ${a.venue ? `<div class="muted">${lfEsc(a.venue)}</div>` : ""}
        ${started ? "" : `<div class="count">${this._countdown(a.kickoff, t)}</div>`}
      </div>`;
  }

  static getConfigElement() {
    return lfEditor("next");
  }
  static getStubConfig(hass) {
    return { entity: lfFindEntity(hass, /(prochain_match|next_match)$/) };
  }
}

// -------------------------------------------------------------------- Forme
class LigueFootFormCard extends LigueFootBase {
  _body(st, t) {
    const a = st.attributes;
    const list = a.last_matches || [];
    const title = `${t.form} – ${this._config.name || a.team || ""}`;
    if (!list.length) return `<div class="title">${lfEsc(title)}</div><div class="empty">${t.noData}</div>`;
    const label = { V: t.win, N: t.draw, D: t.loss };
    const cls = { V: "V", N: "N", D: "D loss" };
    const items = list
      .map((m) => {
        const mine = m.at_home ? m.home_score : m.away_score;
        const theirs = m.at_home ? m.away_score : m.home_score;
        return `<div class="f">
          ${lfLogo(m.opponent_logo)}
          <span class="pill ${cls[m.result] || "q"}">${label[m.result] || "?"}</span>
          <small>${mine ?? "-"}-${theirs ?? "-"}</small>
        </div>`;
      })
      .join("");
    return `<div class="title"><ha-icon icon="mdi:chart-line"></ha-icon>${lfEsc(title)}</div><div class="form">${items}</div>`;
  }

  getCardSize() {
    return 2;
  }
  static getConfigElement() {
    return lfEditor("form");
  }
  static getStubConfig(hass) {
    return { entity: lfFindEntity(hass, /(dernier_resultat|last_result)$/) };
  }
}

// --------------------------------------------------------------- Classement
class LigueFootStandingsCard extends LigueFootBase {
  _body(st, t) {
    const a = st.attributes;
    let rows = a.table || [];
    if (!rows.length) return `<div class="title">${t.standings}</div><div class="empty">${t.noData}</div>`;
    const max = parseInt(this._config.max_rows, 10);
    if (max > 0) rows = rows.slice(0, max);
    const hl = (Array.isArray(this._config.highlight)
      ? this._config.highlight
      : String(this._config.highlight || "").split(",")
    )
      .map((s) => s.trim().toLowerCase())
      .filter(Boolean);
    const body = rows
      .map((r) => {
        const on = hl.some((h) => r.team.toLowerCase().includes(h));
        const bg = r.zone ? `style="background:${lfEsc(r.zone)}"` : "";
        return `<tr class="${on ? "hl" : ""}" title="${lfEsc(r.zone_desc || "")}">
          <td><span class="rank" ${bg}>${r.rank}</span></td>
          <td class="t"><div class="tn">${lfLogo(r.logo)}<span>${lfEsc(r.team)}</span></div></td>
          <td class="pts">${r.points}</td><td>${r.played}</td><td>${r.wins}</td>
          <td>${r.draws}</td><td>${r.losses}</td><td>${r.goal_diff > 0 ? "+" : ""}${r.goal_diff}</td>
        </tr>`;
      })
      .join("");
    const title = this._config.name || `${t.standings} ${a.league || ""}`.trim();
    return `<div class="title"><ha-icon icon="mdi:trophy"></ha-icon>${lfEsc(title)}</div>
      <table>
        <tr><th>#</th><th class="t">${t.team}</th><th>${t.pts}</th><th>${t.played}</th>
        <th>${t.won}</th><th>${t.drawn}</th><th>${t.lost}</th><th>${t.diff}</th></tr>
        ${body}
      </table>`;
  }

  getCardSize() {
    return 8;
  }
  static getConfigElement() {
    return lfEditor("standings");
  }
  static getStubConfig(hass) {
    return { entity: lfFindEntity(hass, /(classement|standings)$/) };
  }
}

// ------------------------------------------------------------------ Journée
class LigueFootMatchdayCard extends LigueFootBase {
  _group(matches, withScore, t) {
    const locale = lfLocale(this._hass);
    let lastDay = "";
    let html = "";
    for (const m of matches) {
      const d = new Date(m.kickoff);
      const day = d.toLocaleDateString(locale, { weekday: "long", day: "numeric", month: "numeric" });
      if (day !== lastDay) {
        html += `<div class="day">${lfEsc(day.charAt(0).toUpperCase() + day.slice(1))}</div>`;
        lastDay = day;
      }
      const started = m.state !== "pre";
      const center = started
        ? `<div class="sc">${m.home_score ?? 0} - ${m.away_score ?? 0}</div>`
        : `<div class="sc t">${d.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" })}</div>`;
      html += `<div class="row">
        <div class="h"><span>${lfEsc(m.home)}</span>${lfLogo(m.home_logo)}</div>
        ${center}
        <div class="a">${lfLogo(m.away_logo)}<span>${lfEsc(m.away)}</span></div>
      </div>`;
    }
    return html;
  }

  _body(st, t) {
    const a = st.attributes;
    const results = a.results || [];
    const upcoming = a.upcoming || [];
    if (!results.length && !upcoming.length) {
      return `<div class="title">${t.results}</div><div class="empty">${t.noData}</div>`;
    }
    const league = this._config.name || a.league || "";
    return `
      ${results.length ? `<div class="sec"><div class="title"><ha-icon icon="mdi:calendar-check"></ha-icon>${lfEsc(league)} · ${t.results}</div>${this._group(results, true, t)}</div>` : ""}
      ${upcoming.length ? `<div class="sec"><div class="title"><ha-icon icon="mdi:calendar-clock"></ha-icon>${t.upcoming}</div>${this._group(upcoming, false, t)}</div>` : ""}`;
  }

  getCardSize() {
    return 8;
  }
  static getConfigElement() {
    return lfEditor("matchday");
  }
  static getStubConfig(hass) {
    return { entity: lfFindEntity(hass, /(journee|matchday)$/) };
  }
}

// ------------------------------------------------------------ Éditeur visuel
class LigueFootEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._build();
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) this._form.hass = hass;
  }

  _schema() {
    const t = LF_TEXT[lfLang(this._hass)];
    const schema = [
      {
        name: "entity",
        required: true,
        selector: { entity: { domain: "sensor", integration: "ligue_foot" } },
      },
      { name: "name", selector: { text: {} } },
      {
        name: "design",
        selector: {
          select: {
            mode: "dropdown",
            options: [
              { value: "night", label: t.dNight },
              { value: "ha", label: t.dHa },
              { value: "light", label: t.dLight },
              { value: "stadium", label: t.dStadium },
            ],
          },
        },
      },
    ];
    if (this.kind === "standings") {
      schema.push({ name: "max_rows", selector: { number: { min: 1, max: 20, mode: "box" } } });
      schema.push({ name: "highlight", selector: { text: {} } });
    }
    return schema;
  }

  _build() {
    if (!this._form) {
      this._form = document.createElement("ha-form");
      this._form.addEventListener("value-changed", (ev) => {
        this._config = ev.detail.value;
        this.dispatchEvent(
          new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true })
        );
      });
      this.appendChild(this._form);
    }
    const t = LF_TEXT[lfLang(this._hass)];
    const labels = { entity: t.entity, design: t.design, name: "Nom", max_rows: t.rows, highlight: t.highlight };
    this._form.hass = this._hass;
    this._form.data = this._config;
    this._form.schema = this._schema();
    this._form.computeLabel = (s) => labels[s.name] || s.name;
  }
}

function lfEditor(kind) {
  const el = document.createElement("ligue-foot-editor");
  el.kind = kind;
  return el;
}

function lfFindEntity(hass, re) {
  const ids = Object.keys(hass?.states || {}).filter(
    (id) => id.startsWith("sensor.") && re.test(id) && hass.entities?.[id]?.platform === "ligue_foot"
  );
  return ids[0] || "";
}

// -------------------------------------------------------------- Enregistrement
const LF_CARDS = [
  ["ligue-foot-next-match-card", LigueFootNextMatchCard, "nextName", "nextDesc"],
  ["ligue-foot-form-card", LigueFootFormCard, "formName", "formDesc"],
  ["ligue-foot-standings-card", LigueFootStandingsCard, "standingsName", "standingsDesc"],
  ["ligue-foot-matchday-card", LigueFootMatchdayCard, "matchdayName", "matchdayDesc"],
];

if (!customElements.get("ligue-foot-editor")) {
  customElements.define("ligue-foot-editor", LigueFootEditor);
}

window.customCards = window.customCards || [];
for (const [tag, klass, nameKey, descKey] of LF_CARDS) {
  if (!customElements.get(tag)) customElements.define(tag, klass);
  const t = LF_TEXT[(navigator.language || "en").toLowerCase().startsWith("fr") ? "fr" : "en"];
  window.customCards.push({ type: tag, name: t[nameKey], description: t[descKey], preview: false });
}

console.info(`%c LIGUE-FOOT %c v${LF_VERSION} `, "background:#2aa5e0;color:#fff", "background:#101a33;color:#fff");
