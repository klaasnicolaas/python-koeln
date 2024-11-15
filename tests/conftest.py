"""Fixture for the Koeln tests."""

from collections.abc import AsyncGenerator

import pytest
from aiohttp import ClientSession

from koeln import ODPKoeln, StadtKoeln


@pytest.fixture(name="odp_koeln_client")
async def odp_client() -> AsyncGenerator[ODPKoeln, None]:
    """Return an ODP Koeln client."""
    async with (
        ClientSession() as session,
        ODPKoeln(session=session) as odp_koeln_client,
    ):
        yield odp_koeln_client


@pytest.fixture(name="stadt_koeln_client")
async def stadt_client() -> AsyncGenerator[StadtKoeln, None]:
    """Return an Stadt Koeln client."""
    async with (
        ClientSession() as session,
        StadtKoeln(session=session) as stadt_koeln_client,
    ):
        yield stadt_koeln_client
