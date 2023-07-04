# pylint: disable=W0621
"""Asynchronous Python client providing Open Data information of Köln."""

import asyncio

from koeln import StadtKoeln


async def main() -> None:
    """Fetch disabled parkings using the Köln API client."""
    async with StadtKoeln() as client:
        disabled_parkings = await client.disabled_parkings()

        count: int = len(disabled_parkings)
        for item in disabled_parkings:
            print(item)

        print("__________________________")
        print(f"Total locations found: {count}")


if __name__ == "__main__":
    asyncio.run(main())
