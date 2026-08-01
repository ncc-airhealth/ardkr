"""ardkr.catalog — STAC catalog load and search.

extra: [catalog]  (pip install "ardkr[catalog]")

The public catalog is static STAC on the open bucket. Load/search APIs TBD.
"""

from __future__ import annotations

try:
    import pystac  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.catalog requires pystac: pip install "ardkr[catalog]"'
    ) from exc

# TODO: load/search static STAC from the open bucket.
