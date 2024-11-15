"""Test the models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aresponses import ResponsesMockServer
from syrupy.assertion import SnapshotAssertion

from . import load_fixtures

if TYPE_CHECKING:
    from koeln import DisabledParking, StadtKoeln


async def test_all_disabled_parkings(
    aresponses: ResponsesMockServer,
    snapshot: SnapshotAssertion,
    stadt_koeln_client: StadtKoeln,
) -> None:
    """Test all disabled parkings spaces function."""
    aresponses.add(
        "geoportal.stadt-koeln.de",
        "/arcgis/rest/services/basiskarten/stadtplanthemen/MapServer/0/query",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("disabled_parkings.json"),
        ),
    )
    spaces: list[DisabledParking] = await stadt_koeln_client.disabled_parkings()
    assert spaces == snapshot
