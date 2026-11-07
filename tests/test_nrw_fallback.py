"""Exercise the official fallback without changing the existing source IDs."""

import json
from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from aresponses import ResponsesMockServer

from koeln import ODPKoelnError, StadtKoeln
from koeln.exceptions import ODPKoelnConnectionError

NRW_URL = "https://www.mobilitaetsdaten.nrw/api/systemadapter-mobilithek-exporter/behindertenparkplaetze-koeln.json"


def publication() -> dict[str, Any]:
    """Represent the complete, non-paginated NRW download."""
    return {
        "modelBaseVersion": "3",
        "parkingPublicationLight": {
            "publicationTime": "2026-01-01T09:00:00Z",
            "parkingSite": [
                {
                    "id": "parking-disabled-koeln-137",
                    "type": "other",
                    "description": "Behindertenparkplätze",
                    "name": "Sülzgürtel 42",
                    "numberOfSpaces": 1,
                    "locationAndDimension": {
                        "coordinatesForDisplay": {
                            "latitude": 50.915243,
                            "longitude": 6.91971,
                        }
                    },
                }
            ],
        },
    }


async def test_html_redirect_uses_official_nrw_download(
    aresponses: ResponsesMockServer,
) -> None:
    """Reproduce the real redirect and keep original numeric IDs and claims."""
    aresponses.add(
        "geoportal.stadt-koeln.de",
        "/arcgis/rest/services/verkehr/behindertenparkplaetze/MapServer/0/query",
        "GET",
        aresponses.Response(
            status=301, headers={"Location": "https://www.stadt-koeln.de/"}
        ),
    )
    aresponses.add(
        "www.stadt-koeln.de",
        "/",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "text/html"},
            text="<html>Homepage</html>",
        ),
    )
    for _ in range(2):
        aresponses.add(
            "www.mobilitaetsdaten.nrw",
            "/api/systemadapter-mobilithek-exporter/behindertenparkplaetze-koeln.json",
            "GET",
            aresponses.Response(
                status=200,
                headers={"Content-Type": "application/octet-stream"},
                body=json.dumps(publication()).encode(),
            ),
        )
    async with StadtKoeln() as client:
        result = await client.parking_collection()
    assert result.records[0].id == 137
    assert (
        result.records[0].source_attributes
        == publication()["parkingPublicationLight"]["parkingSite"][0]
    )
    assert result.records[0].geometry == {
        "type": "Point",
        "coordinates": [6.91971, 50.915243],
    }
    assert result.source_url == NRW_URL
    assert result.source_version == "2026-01-01T09:00:00Z"
    assert (result.total_count, result.pages_fetched, result.complete) == (1, 1, True)
    aresponses.assert_plan_strictly_followed()


@pytest.mark.parametrize(
    "error", [ODPKoelnConnectionError("timeout"), ODPKoelnConnectionError("HTTP 503")]
)
async def test_connection_failure_uses_fallback(error: Exception) -> None:
    """Unavailable primary transport can recover through the mirror."""
    with patch.object(
        StadtKoeln,
        "_request",
        AsyncMock(side_effect=[error, publication(), publication()]),
    ):
        result = await StadtKoeln().parking_collection()
    assert result.records[0].id == 137


async def test_invalid_primary_is_not_replaced_by_fallback() -> None:
    """Do not hide incomplete, corrupt or changing primary data."""
    request = AsyncMock(return_value={"count": "invalid"})
    with patch.object(StadtKoeln, "_request", request), pytest.raises(ODPKoelnError):
        await StadtKoeln().parking_collection()
    assert request.await_count == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", "137"),
        ("id", "parking-disabled-koeln-0137"),
        ("id", "parking-disabled-bonn-137"),
        ("id", True),
        ("numberOfSpaces", -1),
        ("numberOfSpaces", True),
        ("numberOfSpaces", 1.5),
        ("locationAndDimension", {}),
        (
            "locationAndDimension",
            {"coordinatesForDisplay": {"latitude": 91, "longitude": 6.9}},
        ),
    ],
)
async def test_invalid_nrw_record_fails_closed(field: str, value: object) -> None:
    """Reject invented identities, lossy capacity and invalid positions."""
    data = publication()
    data["parkingPublicationLight"]["parkingSite"][0][field] = value
    with (
        patch.object(
            StadtKoeln,
            "_request",
            AsyncMock(side_effect=[ODPKoelnConnectionError(), data, data]),
        ),
        pytest.raises(ODPKoelnError),
    ):
        await StadtKoeln().parking_collection()


@pytest.mark.parametrize(
    "case",
    [
        "empty",
        "duplicate",
        "excessive",
        "version",
        "timestamp",
        "changed",
        "missing",
        "paginated",
    ],
)
async def test_invalid_or_changed_nrw_snapshot(case: str) -> None:
    """Only accept a bounded complete document read consistently twice."""
    data = publication()
    second = deepcopy(data)
    if case == "empty":
        data["parkingPublicationLight"]["parkingSite"] = []
    elif case in {"duplicate", "excessive"}:
        data["parkingPublicationLight"]["parkingSite"] *= 2
    elif case == "version":
        data["modelBaseVersion"] = "unknown"
    elif case == "timestamp":
        data["parkingPublicationLight"]["publicationTime"] = "not a timestamp"
    elif case == "changed":
        second["parkingPublicationLight"]["parkingSite"][0]["numberOfSpaces"] = 2
    elif case == "missing":
        del data["parkingPublicationLight"]["parkingSite"]
    else:
        data["next"] = "next-page"
    with (
        patch.object(
            StadtKoeln,
            "_request",
            AsyncMock(side_effect=[ODPKoelnConnectionError(), data, second]),
        ),
        pytest.raises(ODPKoelnError),
    ):
        await StadtKoeln().parking_collection(
            max_records=1 if case == "excessive" else 10000
        )


async def test_both_sources_unavailable() -> None:
    """Do not return success when neither transport can supply records."""
    with (
        patch.object(
            StadtKoeln,
            "_request",
            AsyncMock(side_effect=ODPKoelnConnectionError("unavailable")),
        ),
        pytest.raises(ODPKoelnConnectionError),
    ):
        await StadtKoeln().parking_collection()


async def test_invalid_json_is_not_an_availability_fallback(
    aresponses: ResponsesMockServer,
) -> None:
    """Malformed JSON from the primary remains an error, not a source switch."""
    aresponses.add(
        "geoportal.stadt-koeln.de",
        "/arcgis/rest/services/verkehr/behindertenparkplaetze/MapServer/0/query",
        "GET",
        aresponses.Response(
            status=200, headers={"Content-Type": "application/json"}, body=b"not-json"
        ),
    )
    async with StadtKoeln() as client:
        with pytest.raises(ODPKoelnError, match="Invalid source JSON"):
            await client.parking_collection()
    aresponses.assert_plan_strictly_followed()
