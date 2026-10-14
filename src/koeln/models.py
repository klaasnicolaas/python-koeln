"""Models for Open Data Platform of Köln."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Self

from .exceptions import ODPKoelnError


@dataclass
class DisabledParking:
    """Object representing a disabled parking space."""

    entry_id: int
    number: int
    district: str
    district_nr: int
    note: str

    longitude: float
    latitude: float

    @classmethod
    def from_dict(cls: type[DisabledParking], data: dict[str, Any]) -> DisabledParking:
        """Return a DisabledParking object from a dictionary.

        Args:
        ----
            data: The data from the API.

        Returns:
        -------
            A DisabledParking object.

        """
        attr = data["attributes"]
        geo = data["geometry"]
        return cls(
            entry_id=attr.get("objectid"),
            number=attr.get("anzahl"),
            district=attr.get("stadtteil"),
            district_nr=int(attr.get("nr_stadtbezirk")),
            note=attr.get("bemerkung"),
            longitude=geo["x"],
            latitude=geo["y"],
        )


@dataclass
class ParkingRecord:
    """Original identity, WGS84 position and unmodified municipal claims."""

    entry_id: int
    geometry: dict[str, Any]
    source_attributes: dict[str, Any]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Parse original source values and reject unusable identity or position."""
        try:
            attributes = data["attributes"]
            identity = attributes["id"]
            geometry = data["geometry"]
            coordinates = [geometry["x"], geometry["y"]]
        except (KeyError, TypeError) as error:
            msg = "Missing source identity or geometry"
            raise ODPKoelnError(msg) from error
        if isinstance(identity, bool) or not isinstance(identity, int) or identity < 1:
            msg = "Invalid source identity"
            raise ODPKoelnError(msg)
        for value, bound in zip(coordinates, (180, 90), strict=True):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not -bound <= value <= bound
            ):
                msg = "Invalid WGS84 source position"
                raise ODPKoelnError(msg)
        return cls(
            identity, {"type": "Point", "coordinates": coordinates}, attributes.copy()
        )


@dataclass
class ParkingCollection:
    """A complete selection, with source count and retrieval evidence."""

    records: list[ParkingRecord]
    total_count: int
    pages_fetched: int
    source_version: str | None
    complete: bool = True
