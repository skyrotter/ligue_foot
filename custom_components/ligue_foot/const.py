"""Constantes de l'intégration Ligue Foot."""

DOMAIN = "ligue_foot"

# Ligues gérées (code ESPN -> nom affiché)
LEAGUES = {
    "fra.1": "Ligue 1",
    "fra.2": "Ligue 2",
}

CONF_LEAGUES = "leagues"
CONF_TEAMS = "teams"
CONF_REMINDER_MINUTES = "reminder_minutes"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_MESSAGE = "message"

DEFAULT_REMINDER_MINUTES = 30
DEFAULT_MESSAGE = "⚽ {home} - {away} à {time} ({minutes} min) – {venue}"

# Fenêtre de matchs récupérée autour d'aujourd'hui (en jours)
DAYS_BEHIND = 30
DAYS_AHEAD = 45

UPDATE_INTERVAL_MINUTES = 15
