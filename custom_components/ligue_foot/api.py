"""Client pour l'API non officielle d'ESPN (football)."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

import aiohttp

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
BASE_V2 = "https://site.api.espn.com/apis/v2/sports/soccer"


class EspnApiError(Exception):
    """Erreur lors de l'appel à ESPN."""


def _score(raw: Any) -> int | None:
    """Le score peut être une chaîne, un nombre ou un dict selon l'endpoint."""
    if isinstance(raw, dict):
        raw = raw.get("displayValue", raw.get("value"))
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return None


def _logo(team: dict) -> str:
    """URL du logo : champ « logo » (scoreboard), sinon logos[0], sinon URL ESPN."""
    if team.get("logo"):
        return team["logo"]
    logos = team.get("logos") or []
    if logos and logos[0].get("href"):
        return logos[0]["href"]
    return f"https://a.espncdn.com/i/teamlogos/soccer/500/{team['id']}.png"


def _parse_event(event: dict, league: str) -> dict | None:
    """Transforme un événement ESPN en dict simple."""
    try:
        comp = event["competitions"][0]
        competitors = {c["homeAway"]: c for c in comp["competitors"]}
        home, away = competitors["home"], competitors["away"]
        kickoff = datetime.fromisoformat(event["date"].replace("Z", "+00:00"))

        # Détermine le gagnant
        winner = None
        home_score = _score(home.get("score"))
        away_score = _score(away.get("score"))
        if home_score is not None and away_score is not None:
            if home_score > away_score:
                winner = "home"
            elif away_score > home_score:
                winner = "away"
            else:
                winner = "draw"

        # Extrait les événements du match (buts, cartons, etc.)
        match_events = []
        for event_item in comp.get("videos", []):
            # Les vidéos/événements ESPN contiennent buts et cartons
            match_events.append({
                "type": event_item.get("type"),
                "description": event_item.get("description"),
            })

        # Extrait les statistiques pour les cartons jaunes et expulsions
        yellow_cards = {"home": 0, "away": 0}
        red_cards = {"home": 0, "away": 0}

        for comp_team in comp.get("competitors", []):
            side = comp_team["homeAway"]
            stats = comp_team.get("statistics", [])
            for stat in stats:
                if stat.get("name") == "yellowCards":
                    yellow_cards[side] = int(stat.get("value", 0) or 0)
                elif stat.get("name") == "redCards":
                    red_cards[side] = int(stat.get("value", 0) or 0)

        return {
            "id": str(event["id"]),
            "league": league,
            "kickoff": kickoff,
            "state": comp["status"]["type"]["state"],  # pre / in / post
            "venue": (comp.get("venue") or {}).get("fullName"),
            "winner": winner,  # "home", "away", "draw", or None
            "home": {
                "id": str(home["team"]["id"]),
                "name": home["team"]["displayName"],
                "score": home_score,
                "logo": _logo(home["team"]),
                "yellow_cards": yellow_cards["home"],
                "red_cards": red_cards["home"],
            },
            "away": {
                "id": str(away["team"]["id"]),
                "name": away["team"]["displayName"],
                "score": away_score,
                "logo": _logo(away["team"]),
                "yellow_cards": yellow_cards["away"],
                "red_cards": red_cards["away"],
            },
            "match_events": match_events,
        }
    except (KeyError, IndexError, ValueError, TypeError):
        return None


class EspnApi:
    """Petit client async."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _get(self, url: str, params: dict | None = None) -> dict:
        try:
            async with self._session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise EspnApiError(str(err)) from err

    async def teams(self, league: str) -> list[dict]:
        """Liste des équipes d'une ligue : [{id, name}]."""
        data = await self._get(f"{BASE}/{league}/teams")
        try:
            raw = data["sports"][0]["leagues"][0]["teams"]
            return sorted(
                (
                    {
                        "id": str(t["team"]["id"]),
                        "name": t["team"]["displayName"],
                        "color": t["team"].get("color"),
                        "alternate_color": t["team"].get("alternateColor"),
                    }
                    for t in raw
                ),
                key=lambda t: t["name"],
            )
        except (KeyError, IndexError) as err:
            raise EspnApiError("Réponse équipes inattendue") from err

    async def matches(self, league: str, start: date, end: date) -> list[dict]:
        """Matchs d'une ligue entre deux dates.

        ESPN refuse les plages de dates pour le foot (erreur 400) : on demande
        l'année civile entière (dates=AAAA), une requête par année couverte.
        """
        lo = datetime.combine(start, time.min, tzinfo=timezone.utc)
        hi = datetime.combine(end, time.max, tzinfo=timezone.utc)
        found: dict[str, dict] = {}
        for year in range(start.year, end.year + 1):
            data = await self._get(
                f"{BASE}/{league}/scoreboard", params={"dates": year, "limit": 500}
            )
            for event in data.get("events", []):
                match = _parse_event(event, league)
                if match and lo <= match["kickoff"] <= hi:
                    found[match["id"]] = match
        return sorted(found.values(), key=lambda m: m["kickoff"])

    async def standings(self, league: str) -> list[dict]:
        """Classement d'une ligue."""
        data = await self._get(f"{BASE_V2}/{league}/standings")
        try:
            entries = data["children"][0]["standings"]["entries"]
        except (KeyError, IndexError) as err:
            raise EspnApiError("Réponse classement inattendue") from err
        rows = []
        for entry in entries:
            stats = {s["name"]: s.get("value") for s in entry.get("stats", [])}
            rows.append(
                {
                    "rank": int(stats.get("rank") or 0),
                    "team": entry["team"]["displayName"],
                    "logo": _logo(entry["team"]),
                    # Zone (Ligue des champions, relégation...) fournie par ESPN
                    "zone": (entry.get("note") or {}).get("color"),
                    "zone_desc": (entry.get("note") or {}).get("description"),
                    "points": int(stats.get("points") or 0),
                    "played": int(stats.get("gamesPlayed") or 0),
                    "wins": int(stats.get("wins") or 0),
                    "draws": int(stats.get("ties") or 0),
                    "losses": int(stats.get("losses") or 0),
                    "goal_diff": int(stats.get("pointDifferential") or 0),
                }
            )
        return sorted(rows, key=lambda r: r["rank"])
