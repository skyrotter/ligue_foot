"""Constantes de l'intégration Ligue Foot."""

DOMAIN = "ligue_foot"

# Ligues supportées
LEAGUE_LIGUE1 = "ligue1"
LEAGUE_LIGUE2 = "ligue2"

LEAGUES = {
    LEAGUE_LIGUE1: {"name": "Ligue 1", "espn_id": "FRA.1"},
    LEAGUE_LIGUE2: {"name": "Ligue 2", "espn_id": "FRA.2"},
}

# Config flow
CONF_LEAGUE = "league"
CONF_TEAM_ID = "team_id"
CONF_TEAM_NAME = "team_name"

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
ESPN_SCOREBOARD = "{base}/{league_id}/scoreboard"
ESPN_STANDINGS = "{base}/{league_id}/standings"
ESPN_TEAMS = "{base}/{league_id}/teams"
ESPN_TEAM_SCHEDULE = "{base}/{league_id}/teams/{team_id}/schedule"

# Événements HA
EVENT_GOAL = "ligue_foot_goal"
EVENT_KICKOFF = "ligue_foot_kickoff"
EVENT_MATCH_FINISHED = "ligue_foot_match_finished"
EVENT_RED_CARD = "ligue_foot_red_card"
