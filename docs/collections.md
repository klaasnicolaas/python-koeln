# Complete disabled-parking collection

[Back to the README](../README.md)

`await StadtKoeln().parking_collection(max_records=10000)` returns `ParkingCollection(records, total_count, pages_fetched, source_version, complete=True)` from the current `verkehr/behindertenparkplaetze/MapServer/0` layer. Each `ParkingRecord` retains the original integer `id` (source `id`), WGS84 Point `geometry` and unmodified `source_attributes`. Count, ordered pagination, unique IDs and two complete reads must agree. The limit is a rejection ceiling, never truncation. Malformed, incomplete or changing responses raise `ODPKoelnError`; connection failures raise `ODPKoelnConnectionError`. A proven empty selection returns an empty collection.

No dataset-wide version is exposed (`source_version=None`), and source IDs are not guaranteed to persist across rebuilds. Counts establish complete retrieval of the published selection, not geographic coverage, current observations or individual bay positions. The legacy `disabled_parkings()` inspection API retains its existing endpoint and model; use the complete API for deliveries.
