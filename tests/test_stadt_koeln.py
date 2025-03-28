"""Basic tests for the Open Data Platform API of Köln."""

# pylint: disable=protected-access
import asyncio
from unittest.mock import patch

import pytest
from aiohttp import ClientError, ClientResponse, ClientSession
from aresponses import Response, ResponsesMockServer

from koeln import StadtKoeln
from koeln.exceptions import ODPKoelnConnectionError, ODPKoelnError

from . import load_fixtures


async def test_json_request(
    aresponses: ResponsesMockServer, stadt_koeln_client: StadtKoeln
) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        "geoportal.stadt-koeln.de",
        "/arcgis/rest/services/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("disabled_parkings.json"),
        ),
    )
    await stadt_koeln_client._request("test")
    await stadt_koeln_client.close()


async def test_internal_session(aresponses: ResponsesMockServer) -> None:
    """Test internal session is handled correctly."""
    aresponses.add(
        "geoportal.stadt-koeln.de",
        "/arcgis/rest/services/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("disabled_parkings.json"),
        ),
    )
    async with StadtKoeln() as client:
        await client._request("test")


async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout from the Open Data Platform API of Köln."""

    # Faking a timeout by sleeping
    async def response_handler(_: ClientResponse) -> Response:
        await asyncio.sleep(0.2)
        return aresponses.Response(
            body="Goodmorning!",
            text=load_fixtures("disabled_parkings.json"),
        )

    aresponses.add(
        "geoportal.stadt-koeln.de",
        "/arcgis/rest/services/test",
        "GET",
        response_handler,
    )

    async with ClientSession() as session:
        client = StadtKoeln(
            session=session,
            request_timeout=0.1,
        )
        with pytest.raises(ODPKoelnConnectionError):
            assert await client._request("test")


async def test_content_type(
    aresponses: ResponsesMockServer, stadt_koeln_client: StadtKoeln
) -> None:
    """Test request content type error from Open Data Platform API of Köln."""
    aresponses.add(
        "geoportal.stadt-koeln.de",
        "/arcgis/rest/services/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "blabla/blabla"},
        ),
    )
    with pytest.raises(ODPKoelnError):
        await stadt_koeln_client._request("test")


async def test_client_error() -> None:
    """Test request client error from the Open Data Platform API of Köln."""
    async with ClientSession() as session:
        client = StadtKoeln(session=session)
        with (
            patch.object(
                session,
                "request",
                side_effect=ClientError,
            ),
            pytest.raises(ODPKoelnConnectionError),
        ):
            assert await client._request("test")
