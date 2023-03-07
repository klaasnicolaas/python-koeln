"""Test the models."""
from aiohttp import ClientSession
from aresponses import ResponsesMockServer

from koeln import DisabledParking, StadtKoeln

from . import load_fixtures


async def test_all_disabled_parkings(aresponses: ResponsesMockServer) -> None:
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
    async with ClientSession() as session:
        client = StadtKoeln(session=session)
        spaces: list[DisabledParking] = await client.disabled_parkings()
        assert spaces is not None
        for item in spaces:
            assert isinstance(item, DisabledParking)
            assert item.longitude is not None
            assert item.latitude is not None
            assert isinstance(item.longitude, float)
            assert isinstance(item.latitude, float)
