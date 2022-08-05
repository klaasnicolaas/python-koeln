"""Models for Open Data Platform of Köln."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
    def from_dict(cls, data: dict[str, Any]) -> DisabledParking:
        """Return a DisabledParking object from a dictionary.

        Args:
            data: The data from the API.

        Returns:
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
