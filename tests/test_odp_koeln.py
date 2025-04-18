"""Basic tests for the Open Data Platform API of Köln."""

# pylint: disable=protected-access
import asyncio
from unittest.mock import patch

import pytest
from aiohttp import ClientError, ClientResponse, ClientSession
from aresponses import Response, ResponsesMockServer

from koeln import ODPKoeln
from koeln.exceptions import ODPKoelnConnectionError, ODPKoelnError

from . import load_fixtures


async def test_json_request(
    aresponses: ResponsesMockServer, odp_koeln_client: ODPKoeln
) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        "offenedaten-koeln.de",
        "/api/action/datastore/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("disabled_parkings.json"),
        ),
    )
    await odp_koeln_client._request("test")
    await odp_koeln_client.close()


async def test_internal_session(aresponses: ResponsesMockServer) -> None:
    """Test internal session is handled correctly."""
    aresponses.add(
        "offenedaten-koeln.de",
        "/api/action/datastore/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=load_fixtures("disabled_parkings.json"),
        ),
    )
    async with ODPKoeln() as client:
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
        "offenedaten-koeln.de",
        "/api/action/datastore/test",
        "GET",
        response_handler,
    )

    async with ClientSession() as session:
        client = ODPKoeln(
            session=session,
            request_timeout=0.1,
        )
        with pytest.raises(ODPKoelnConnectionError):
            assert await client._request("test")


async def test_content_type(
    aresponses: ResponsesMockServer, odp_koeln_client: ODPKoeln
) -> None:
    """Test request content type error from Open Data Platform API of Köln."""
    aresponses.add(
        "offenedaten-koeln.de",
        "/api/action/datastore/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "blabla/blabla"},
        ),
    )
    with pytest.raises(ODPKoelnError):
        assert await odp_koeln_client._request("test")


async def test_client_error() -> None:
    """Test request client error from the Open Data Platform API of Köln."""
    async with ClientSession() as session:
        client = ODPKoeln(session=session)
        with (
            patch.object(
                session,
                "request",
                side_effect=ClientError,
            ),
            pytest.raises(ODPKoelnConnectionError),
        ):
            assert await client._request("test")
