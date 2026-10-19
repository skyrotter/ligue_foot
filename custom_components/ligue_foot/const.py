"""Constantes de l'intégration Ligue Foot."""


DOMAIN = "ligue_foot"


# Ligues gérées (code ESPN -> nom affiché)
LEAGUES = {
    "fra.1": "Ligue 1",
    "fra.2": "Ligue 2",
    "eng.1": "Premier League",
    "esp.1": "LaLiga",
    "ger.1": "Bundesliga",
    "ita.1": "Serie A",
    "por.1": "Liga Portugal",
    "bel.1": "Jupiler Pro League",
}


CONF_LEAGUES = "leagues"
CONF_TEAMS = "teams"
CONF_REMINDER_MINUTES = "reminder_minutes"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_MESSAGE = "message"


DEFAULT_REMINDER_MINUTES = 30
DEFAULT_MESSAGE = "⚽ {home} - {away} à {time} ({minutes} min) – {venue}"


# Fenêtre de matchs récupérée autour d'aujourd'hui (en jours)
DAYS_BEHIND = 70
DAYS_AHEAD = 45


UPDATE_INTERVAL_MINUTES = 15

# Cartes Lovelace fournies avec l'intégration
CARDS_URL = "/ligue_foot_static/ligue-foot-cards.js"
CARDS_VERSION = "0.4.0"

# Lumières (Philips Hue, Ambilight, toute entité light)
CONF_LIGHTS = "lights"
CONF_LIGHT_KICKOFF = "light_kickoff"
CONF_LIGHT_GOAL = "light_goal"
CONF_LIGHT_PREMATCH = "light_prematch"
CONF_LIGHT_RESTORE = "light_restore"
