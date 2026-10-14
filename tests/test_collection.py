"""Prove complete collection and rejection of inconsistent source responses."""

from copy import deepcopy
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from koeln import ODPKoelnError, StadtKoeln


def page(*identities: int) -> dict[str, Any]:
    """Build a small real-shaped ArcGIS response."""
    return {
        "spatialReference": {"wkid": 4326},
        "geometryType": "esriGeometryPoint",
        "features": [
            {
                "attributes": {
                    "id": identity,
                    "anzahl": None,
                    "bemerkung": "2 Stunden",
                },
                "geometry": {"x": 6.95, "y": 50.94},
            }
            for identity in identities
        ],
    }


async def test_complete_collection() -> None:
    """Retain claims and use the current endpoint with an ordered full read."""
    response = page(1, 2)
    request = AsyncMock(side_effect=[{"count": 2}, response, response, {"count": 2}])
    with patch.object(StadtKoeln, "_request", request):
        result = await StadtKoeln().parking_collection()
    assert (
        result.total_count,
        result.pages_fetched,
        result.source_version,
        result.complete,
    ) == (2, 1, None, True)
    assert result.records[0].source_attributes == response["features"][0]["attributes"]
    assert result.records[0].geometry == {"type": "Point", "coordinates": [6.95, 50.94]}
    assert request.call_args_list[1].kwargs["params"]["orderByFields"] == "id ASC"
    assert request.call_args_list[0].args == (
        "verkehr/behindertenparkplaetze/MapServer/0/query",
    )


async def test_multiple_pages_and_empty() -> None:
    """Fetch beyond one page, and explicitly prove an empty selection."""
    first, last = page(*range(1, 501)), page(501)
    first["exceededTransferLimit"] = True
    for responses, total, pages in [
        ([{"count": 501}, first, last, first, last, {"count": 501}], 501, 2),
        ([{"count": 0}, page(), page(), {"count": 0}], 0, 1),
    ]:
        with patch.object(StadtKoeln, "_request", AsyncMock(side_effect=responses)):
            result = await StadtKoeln().parking_collection()
        assert (len(result.records), result.pages_fetched) == (total, pages)


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, "2"])
async def test_invalid_limit(value: object) -> None:
    """A ceiling must never silently truncate records."""
    with pytest.raises(ValueError, match="positive integer"):
        await StadtKoeln().parking_collection(max_records=value)  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize("count", [None, True, -1, 10001, "2"])
async def test_invalid_count(count: object) -> None:
    """Reject missing, malformed or excessive counts before fetching pages."""
    with (
        patch.object(StadtKoeln, "_request", AsyncMock(return_value={"count": count})),
        pytest.raises(ODPKoelnError),
    ):
        await StadtKoeln().parking_collection()


@pytest.mark.parametrize(
    "response",
    [
        page(1),
        page(1, 1),
        page(2, 1),
        {"error": {"code": 500}},
        {**page(1, 2), "exceededTransferLimit": True},
        {**page(1, 2), "spatialReference": {"wkid": 25832}},
        {**page(1, 2), "geometryType": "esriGeometryPolygon"},
    ],
)
async def test_incomplete_page(response: dict[str, Any]) -> None:
    """Partial results, duplicate IDs, transfer limits and wrong CRS fail closed."""
    with (
        patch.object(
            StadtKoeln, "_request", AsyncMock(side_effect=[{"count": 2}, response])
        ),
        pytest.raises(ODPKoelnError),
    ):
        await StadtKoeln().parking_collection()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("id", None),
        ("id", True),
        ("id", 0),
        ("x", True),
        ("x", float("nan")),
        ("y", 91),
    ],
)
async def test_invalid_record(field: str, value: object) -> None:
    """Reject invalid original IDs and WGS84 positions."""
    response = page(1)
    feature = response["features"][0]
    feature["attributes" if field == "id" else "geometry"][field] = value
    with (
        patch.object(
            StadtKoeln, "_request", AsyncMock(side_effect=[{"count": 1}, response])
        ),
        pytest.raises(ODPKoelnError),
    ):
        await StadtKoeln().parking_collection()


async def test_changed_source_and_connection_failure() -> None:
    """Same count with changed claims is not a successful collection."""
    changed = deepcopy(page(1))
    changed["features"][0]["attributes"]["anzahl"] = 2
    for responses in [
        [{"count": 1}, page(1), changed, {"count": 1}],
        [{"count": 1}, page(1), page(1), {"count": 2}],
    ]:
        with (
            patch.object(StadtKoeln, "_request", AsyncMock(side_effect=responses)),
            pytest.raises(ODPKoelnError, match="changed"),
        ):
            await StadtKoeln().parking_collection()


@pytest.mark.parametrize(
    "feature", [{}, {"attributes": None}, {"attributes": {"id": 1}, "geometry": None}]
)
async def test_missing_record_fields(feature: dict[str, Any]) -> None:
    """Malformed features use the public package error contract."""
    response = page(1)
    response["features"] = [feature]
    with (
        patch.object(
            StadtKoeln, "_request", AsyncMock(side_effect=[{"count": 1}, response])
        ),
        pytest.raises(ODPKoelnError),
    ):
        await StadtKoeln().parking_collection()
