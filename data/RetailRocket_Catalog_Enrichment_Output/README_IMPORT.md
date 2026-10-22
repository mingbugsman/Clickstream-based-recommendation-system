# RetailRocket Catalog — Import Guide

## Data provenance
- `product_snapshot.parquet`: derived from RetailRocket IDs + event counts + property snapshot.
- `product_presentation.parquet`: SYNTHETIC product and category labels for UI only.
- `product_catalog.parquet` / `.csv`: joined read model for Product API.
- `category_mapping.csv`: ORIGINAL category IDs and parent IDs, SYNTHETIC Vietnamese labels.
- `demo_candidates.csv`: products with historical interactions, sorted by event count.
- `placeholders/*.svg`: copy to `frontend/public/placeholders/`.

**Not actual products:** category names, product names, product types, brands, and images are demonstration metadata, NOT reconstructed original semantics. Price is NULL.

## Example backend read/query
Use DuckDB to inspect or import files:

```python
import duckdb
con = duckdb.connect()
rows = con.execute("SELECT item_id, display_name, category_display_name, image_url FROM read_parquet('product_catalog.parquet') ORDER BY item_id LIMIT 24").fetchall()
```

Build a DB index/primary key on `item_id`, and paginate on the SERVER. Recommendation results should join by **original `item_id`**. Historical evaluation must not use SYNTHETIC display labels.

## Important snapshot caveat
In default `LATEST_OBSERVED` mode the catalog reflects the final/latest attribute values in the input files; this is suitable for a static storefront demo, NOT time-correct historical replay. For historical replay regenerate with `SNAPSHOT_AT_MS` at the target moment (or query property change logs as-of the event time).

The raw input files are never overwritten. More details in generator_config.json and enrichment_quality_report.json.
