"""Constantes de l'intégration Ligue Foot."""

DOMAIN = "ligue_foot"

# Ligues et compétitions supportées
# Ligues nationales françaises
LEAGUE_LIGUE1 = "ligue1"
LEAGUE_LIGUE2 = "ligue2"

# Autres ligues nationales
LEAGUE_PREMIER_LEAGUE = "premier_league"
LEAGUE_LALIGA = "laliga"
LEAGUE_BUNDESLIGA = "bundesliga"
LEAGUE_SERIE_A = "serie_a"
LEAGUE_LIGA_PORTUGAL = "liga_portugal"
LEAGUE_JUPILER_PRO = "jupiler_pro"

# Compétitions européennes
LEAGUE_UEFA_CL = "uefa_cl"  # Champions League
LEAGUE_UEFA_EL = "uefa_el"  # Europa League
LEAGUE_UEFA_CONF = "uefa_conf"  # Conference League

# Les identifiants ESPN (espn_id) sont en minuscules, comme dans l'API ESPN.
LEAGUES = {
    # Ligues nationales
    LEAGUE_LIGUE1: {"name": "Ligue 1", "espn_id": "fra.1", "country": "FRA"},
    LEAGUE_LIGUE2: {"name": "Ligue 2", "espn_id": "fra.2", "country": "FRA"},
    # Autres ligues nationales
    LEAGUE_PREMIER_LEAGUE: {"name": "Premier League", "espn_id": "eng.1", "country": "ENG"},
    LEAGUE_LALIGA: {"name": "LaLiga", "espn_id": "esp.1", "country": "ESP"},
    LEAGUE_BUNDESLIGA: {"name": "Bundesliga", "espn_id": "ger.1", "country": "GER"},
    LEAGUE_SERIE_A: {"name": "Serie A", "espn_id": "ita.1", "country": "ITA"},
    LEAGUE_LIGA_PORTUGAL: {"name": "Liga Portugal", "espn_id": "por.1", "country": "POR"},
    LEAGUE_JUPILER_PRO: {"name": "Jupiler Pro League", "espn_id": "bel.1", "country": "BEL"},
    # Compétitions européennes
    LEAGUE_UEFA_CL: {"name": "UEFA Champions League", "espn_id": "uefa.champions", "country": "UEFA"},
    LEAGUE_UEFA_EL: {"name": "UEFA Europa League", "espn_id": "uefa.europa", "country": "UEFA"},
    LEAGUE_UEFA_CONF: {"name": "UEFA Conference League", "espn_id": "uefa.europa.conf", "country": "UEFA"},
}

# Config flow
CONF_LEAGUE = "league"
CONF_LEAGUES = "leagues"  # Multiple leagues selection
CONF_TEAM_ID = "team_id"
CONF_TEAM_NAME = "team_name"

# Light configuration
CONF_LIGHTS = "lights"
CONF_LIGHT_GOAL = "light_goal"
CONF_LIGHT_KICKOFF = "light_kickoff"
CONF_LIGHT_PREMATCH = "light_prematch"
CONF_LIGHT_RESTORE = "light_restore"

# Update intervals
UPDATE_INTERVAL_MINUTES = 5

# Intervalles de polling (secondes)
SCAN_INTERVAL_DEFAULT = 180       # 3 min au repos
SCAN_INTERVAL_LIVE = 60           # 1 min pendant un match
SCAN_INTERVAL_MATCHDAY = 300      # 5 min le jour d'un match (avant coup d'envoi)

# Cache
CACHE_TTL_DAYS = 7                # Durée de conservation des dernières données connues

# États de synchronisation
SYNC_STATUS_READY = "ready"
SYNC_STATUS_INITIALIZING = "initializing"
SYNC_STATUS_FETCHING = "fetching"
SYNC_STATUS_RATE_LIMITED = "rate_limited"
SYNC_STATUS_PROVIDER_UNAVAILABLE = "provider_unavailable"

# URL de base ESPN
ESPN_API_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
ESPN_API_BASE_V2 = "https://site.api.espn.com/apis/v2/sports/soccer"  # utilisé pour les standings
ESPN_SCOREBOARD = "{base}/{league_id}/scoreboard"
ESPN_STANDINGS = "{base}/{league_id}/standings"
ESPN_TEAMS = "{base}/{league_id}/teams"
ESPN_TEAM_SCHEDULE = "{base}/{league_id}/teams/{team_id}/schedule"

# Événements HA
EVENT_GOAL = "ligue_foot_goal"
EVENT_KICKOFF = "ligue_foot_kickoff"
EVENT_MATCH_FINISHED = "ligue_foot_match_finished"
EVENT_RED_CARD = "ligue_foot_red_card"
