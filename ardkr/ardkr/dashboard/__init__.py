"""ardkr.dashboard — marimo STAC catalog dashboard.

extra: [dashboard]  (pip install "ardkr[dashboard]")

Reactive marimo notebook/app for exploring the open-bucket static STAC catalog.
"""

from __future__ import annotations

try:
    import marimo  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.dashboard requires marimo: pip install "ardkr[dashboard]"'
    ) from exc

# TODO: marimo app entrypoint (app()).
