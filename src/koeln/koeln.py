"""Asynchronous Python client providing Open Data information of Köln."""

from __future__ import annotations

import asyncio
import socket
from dataclasses import dataclass
from datetime import datetime
from importlib import metadata
from typing import Any, Self

from aiohttp import ClientError, ClientSession
from aiohttp.hdrs import METH_GET
from yarl import URL

from .exceptions import ODPKoelnConnectionError, ODPKoelnError
from .models import DisabledParking, ParkingCollection, ParkingRecord

VERSION = metadata.version("koeln")
NRW_PARKING_URL = "https://www.mobilitaetsdaten.nrw/api/systemadapter-mobilithek-exporter/behindertenparkplaetze-koeln.json"


class _UnexpectedContentTypeError(ODPKoelnError):
    """An unavailable service returned a web page instead of source JSON."""


@dataclass
class ODPKoeln:
    """Main class for handling data fetching from Open Data Platform of Köln."""

    request_timeout: float = 10.0
    session: ClientSession | None = None

    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        method: str = METH_GET,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Handle a request to the Open Data Platform API of Köln.

        Args:
        ----
            uri: Request URI, without '/', for example, 'status'
            method: HTTP method to use, for example, 'GET'
            params: Extra options to improve or limit the response.

        Returns:
        -------
            A Python dictionary (text) with the response from
            the Open Data Platform API of Köln.

        Raises:
        ------
            ODPKoelnConnectionError: Timeout occurred while
                connecting to the Open Data Platform API.
            ODPKoelnError: If the data is not valid.

        """
        url = URL.build(
            scheme="https",
            host="offenedaten-koeln.de",
            path="/api/action/datastore/",
        ).join(URL(uri))

        headers = {
            "Accept": "application/json",
            "User-Agent": f"PythonODPKoeln/{VERSION}",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    params=params,
                    headers=headers,
                    ssl=True,
                )
                response.raise_for_status()
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the Open Data Platform API."
            raise ODPKoelnConnectionError(
                msg,
            ) from exception
        except (ClientError, socket.gaierror) as exception:
            msg = "Error occurred while communicating with Open Data Platform API."
            raise ODPKoelnConnectionError(
                msg,
            ) from exception

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected content type response from the Open Data Platform API"
            raise ODPKoelnError(
                msg,
                {"Content-Type": content_type, "Response": text},
            )

        return await response.json()

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The Open Data Platform Koeln object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()


@dataclass
class StadtKoeln:
    """Main class for handling data fetching from Stadt of Köln."""

    request_timeout: float = 10.0
    session: ClientSession | None = None

    _close_session: bool = False

    async def _request(
        self,
        uri: str,
        *,
        method: str = METH_GET,
        params: dict[str, Any] | None = None,
        content_types: tuple[str, ...] = ("application/json",),
    ) -> Any:
        """Handle a request to the Stadt of Köln API.

        Args:
        ----
            uri: Request URI, without '/', for example, 'status'
            method: HTTP method to use, for example, 'GET'
            params: Extra options to improve or limit the response.

        Returns:
        -------
            A Python dictionary (text) with the response from
            the Open Data Platform API of Koeln.

        Raises:
        ------
            ODPKoelnConnectionError: Timeout occurred while
                connecting to the Open Data Platform API.
            ODPKoelnError: If the data is not valid.

        """
        version = metadata.version("koeln")
        url = URL.build(
            scheme="https",
            host="geoportal.stadt-koeln.de",
            path="/arcgis/rest/services/",
        ).join(URL(uri))

        headers = {
            "Accept": "application/json",
            "User-Agent": f"PythonStadtKoeln/{version}",
        }

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with asyncio.timeout(self.request_timeout):
                async with self.session.request(
                    method, url, params=params, headers=headers, ssl=True
                ) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("Content-Type", "")
                    if (
                        content_type.split(";", 1)[0].strip().lower()
                        not in content_types
                    ):
                        text = await response.text()
                        msg = "Expected source JSON instead of a web page"
                        raise _UnexpectedContentTypeError(
                            msg, {"Content-Type": content_type, "Response": text}
                        )
                    try:
                        return await response.json(content_type=None)
                    except ValueError as error:
                        msg = "Invalid source JSON"
                        raise ODPKoelnError(msg) from error
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the Open Data Platform API."
            raise ODPKoelnConnectionError(msg) from exception
        except (ClientError, socket.gaierror) as exception:
            msg = "Error occurred while communicating with Open Data Platform API."
            raise ODPKoelnConnectionError(msg) from exception

    async def parking_collection(
        self, *, max_records: int = 10000
    ) -> ParkingCollection:
        """Read the current entire layer twice; reject incomplete or changing data.

        Keep integer IDs across the official NRW fallback on transport failure.
        A mirror publication marker is not a record observation date.
        """
        if (
            isinstance(max_records, bool)
            or not isinstance(max_records, int)
            or max_records < 1
        ):
            msg = "max_records must be a positive integer"
            raise ValueError(msg)
        try:
            return await self._arcgis_collection(max_records)
        except (ODPKoelnConnectionError, _UnexpectedContentTypeError):
            return await self._nrw_collection(max_records)

    async def _arcgis_collection(self, max_records: int) -> ParkingCollection:
        """Keep primary validation failures distinct from transport availability."""
        uri = "verkehr/behindertenparkplaetze/MapServer/0/query"
        count = await self._request(
            uri, params={"where": "1=1", "returnCountOnly": "true", "f": "json"}
        )
        total = count.get("count") if isinstance(count, dict) else None
        if (
            isinstance(total, bool)
            or not isinstance(total, int)
            or not 0 <= total <= max_records
        ):
            msg = "Invalid or excessive source count"
            raise ODPKoelnError(msg)
        first, pages = await self._parking_pages(uri, total)
        second, _ = await self._parking_pages(uri, total)
        final = await self._request(
            uri, params={"where": "1=1", "returnCountOnly": "true", "f": "json"}
        )
        if final != count or first != second:
            msg = "Source changed during collection"
            raise ODPKoelnError(msg)
        return ParkingCollection(first, total, pages, None)

    async def _nrw_collection(self, max_records: int) -> ParkingCollection:
        """Read the official complete NRW document twice without mixing sources."""
        first = await self._request(
            NRW_PARKING_URL,
            content_types=("application/json", "application/octet-stream"),
        )
        records, version = self._nrw_records(first, max_records)
        second = await self._request(
            NRW_PARKING_URL,
            content_types=("application/json", "application/octet-stream"),
        )
        repeated, repeated_version = self._nrw_records(second, max_records)
        if records != repeated or version != repeated_version:
            msg = "NRW source changed during collection"
            raise ODPKoelnError(msg)
        return ParkingCollection(
            records, len(records), 1, version, source_url=NRW_PARKING_URL
        )

    @staticmethod
    def _nrw_records(payload: Any, max_records: int) -> tuple[list[ParkingRecord], str]:
        """Validate the full document, original ID namespace and publication marker."""
        message = "Invalid or incomplete NRW source document"
        try:
            if (
                not isinstance(payload, dict)
                or set(payload) != {"modelBaseVersion", "parkingPublicationLight"}
                or payload["modelBaseVersion"] != "3"
            ):
                raise ODPKoelnError(message)
            publication = payload["parkingPublicationLight"]
            if not isinstance(publication, dict) or set(publication) != {
                "publicationTime",
                "parkingSite",
            }:
                raise ODPKoelnError(message)
            version = publication["publicationTime"]
            if (
                not isinstance(version, str)
                or datetime.fromisoformat(version).tzinfo is None
            ):
                raise ODPKoelnError(message)
            sites = publication["parkingSite"]
            if not isinstance(sites, list) or not 0 < len(sites) <= max_records:
                raise ODPKoelnError(message)
            records = sorted(
                (ParkingRecord.from_nrw_dict(item) for item in sites),
                key=lambda record: record.id,
            )
            if len({record.id for record in records}) != len(records):
                raise ODPKoelnError(message)
        except (KeyError, TypeError, ValueError) as error:
            msg = "Invalid or incomplete NRW source document"
            raise ODPKoelnError(msg) from error
        return records, version

    async def _parking_pages(
        self, uri: str, total: int
    ) -> tuple[list[ParkingRecord], int]:
        """Fetch ordered pages, validating IDs, CRS and exact page lengths."""
        records: list[ParkingRecord] = []
        pages = 0
        for offset in range(0, max(total, 1), 500):
            payload = await self._request(
                uri,
                params={
                    "where": "1=1",
                    "outFields": "*",
                    "outSR": "4326",
                    "f": "json",
                    "orderByFields": "id ASC",
                    "resultOffset": offset,
                    "resultRecordCount": 500,
                },
            )
            features = payload.get("features") if isinstance(payload, dict) else None
            if (
                not isinstance(payload, dict)
                or payload.get("error")
                or not isinstance(payload.get("spatialReference"), dict)
                or payload["spatialReference"].get("wkid") != 4326
                or payload.get("geometryType") != "esriGeometryPoint"
                or not isinstance(features, list)
                or len(features) != min(500, total - offset)
                or (
                    offset + len(features) >= total
                    and payload.get("exceededTransferLimit", False)
                )
            ):
                msg = "Incomplete or invalid source page"
                raise ODPKoelnError(msg)
            for feature in features:
                record = ParkingRecord.from_dict(feature)
                if records and record.id <= records[-1].id:
                    msg = "Duplicate or unordered source identity"
                    raise ODPKoelnError(msg)
                records.append(record)
            pages += 1
        return records, pages

    async def disabled_parkings(self) -> list[DisabledParking]:
        """Get list of disabled parking spaces.

        Returns
        -------
            A list of DisabledParking objects.

        """
        locations = await self._request(
            "basiskarten/stadtplanthemen/MapServer/0/query",
            params={
                "where": "objectid is not null",
                "outFields": "*",
                "outSR": "4326",
                "f": "json",
            },
        )
        return [DisabledParking.from_dict(item) for item in locations["features"]]

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        """Async enter.

        Returns
        -------
            The Stadt Koeln object.

        """
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        """Async exit.

        Args:
        ----
            _exc_info: Exec type.

        """
        await self.close()
