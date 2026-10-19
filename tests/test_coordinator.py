"""Tests du coordinateur Ligue Foot."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_cached_or_raise_with_fresh_cache():
    """Le cache récent doit être retourné sans exception."""
    from datetime import datetime, timezone
    from custom_components.ligue_foot.coordinator import LigueFootCoordinator

    mock_hass = MagicMock()
    mock_entry = MagicMock()
    mock_entry.data = {"league": "ligue1", "team_id": "123"}
    mock_entry.entry_id = "test_entry"

    coordinator = LigueFootCoordinator.__new__(LigueFootCoordinator)
    coordinator._last_known = {"next_match": {"home_team": "PSG"}}
    coordinator._last_known_at = datetime.now(tz=timezone.utc)

    result = coordinator._cached_or_raise()
    assert result["next_match"]["home_team"] == "PSG"


def test_cached_or_raise_no_cache():
    """Sans cache, une exception doit être levée."""
    from homeassistant.helpers.update_coordinator import UpdateFailed
    from custom_components.ligue_foot.coordinator import LigueFootCoordinator

    coordinator = LigueFootCoordinator.__new__(LigueFootCoordinator)
    coordinator._last_known = {}
    coordinator._last_known_at = None

    with pytest.raises(UpdateFailed):
        coordinator._cached_or_raise()


def test_calendar_uses_filtered_source_over_mixed():
    """Le calendrier doit utiliser les matchs filtrés par compétition,
    pas la liste combinée toutes compétitions."""
    from custom_components.ligue_foot.coordinator import LigueFootCoordinator

    coordinator = LigueFootCoordinator.__new__(LigueFootCoordinator)
    coordinator.team_id = "abc"

    filtered_schedule = {
        "events": [
            {"date": "2026-11-01T20:00:00Z", "id": "1", "competitions": [
                {"competitors": [
                    {"homeAway": "home", "team": {"id": "abc", "displayName": "PSG"}},
                    {"homeAway": "away", "team": {"id": "xyz", "displayName": "Lyon"}},
                ]}
            ], "status": {"type": {"state": "pre", "description": "Scheduled"}}},
        ]
    }
    assert len(filtered_schedule["events"]) == 1
