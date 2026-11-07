# Complete disabled-parking collection

[Back to the README](../README.md)

`await StadtKoeln().parking_collection(max_records=10000)` returns `ParkingCollection(records, total_count, pages_fetched, source_version, complete=True)` from the current `verkehr/behindertenparkplaetze/MapServer/0` layer. Each `ParkingRecord` retains the original integer `id` (source `id`), WGS84 Point `geometry` and unmodified `source_attributes`. `ParkingCollection.source_url` is `None` for this primary route. Count, ordered pagination, unique IDs and two complete reads must agree. The limit is a rejection ceiling, never truncation. Malformed, incomplete or changing responses raise `ODPKoelnError`; connection failures raise `ODPKoelnConnectionError`. A proven empty selection returns an empty collection.

No dataset-wide version is exposed (`source_version=None`), and source IDs are not guaranteed to persist across rebuilds. Counts establish complete retrieval of the published selection, not geographic coverage, current observations or individual bay positions. The legacy `disabled_parkings()` inspection API retains its existing endpoint and model; use the complete API for deliveries.

## Official NRW fallback

When the primary service is unreachable or returns non-JSON (including its current redirect to the municipal homepage), the complete collection API reads the [official Mobidrom/NRW download](https://www.mobilitaetsdaten.nrw/api/ckan/en/dataset/behindertenparkplaetze-koeln). Invalid primary counts, geometry, IDs, incomplete pages or changing data still fail closed; they do not trigger a fallback. The legacy inspection API remains unchanged.

The fallback reads the complete `parkingPublicationLight` document twice, validates version 3, its timezone-aware publication marker, bounded non-empty records, unique IDs, WGS84 points and nullable non-negative integer capacities, and requires the two reads to agree. It has no independent ArcGIS count: completeness refers to the official full-document distribution, not proof of geographic coverage. Unknown document/pagination shapes are rejected rather than silently truncated.

Only IDs matching `parking-disabled-koeln-<positive integer>` map to their original integer suffix: `parking-disabled-koeln-137` remains `ParkingRecord.id=137`. Leading zeros, another municipality, missing or duplicate IDs fail. `source_attributes` preserves the original NRW record, including its prefixed ID and `numberOfSpaces`; it does not pretend these are ArcGIS fields.

`source_url` identifies the actual NRW download; `source_version` carries its `publicationTime`. This is a distribution-generation marker, not an individual parking-space observation date or proof of current conditions. Consumers should retain both provenance and original claims. NRW display coordinates are rounded and may require the consumer's existing geometry/identity review; the client does not invent the primary's more precise geometry.

Both routes use the caller's session and request timeout, including body reading. A failed fallback raises the normal package exception and never returns an empty success for an unavailable source.
