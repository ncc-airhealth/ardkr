"""ardkr — spatial-data pipeline and STAC catalog package.

The core includes STAC support through pystac. Heavier integrations load via
optional extras and are imported lazily from here.

- ardkr.common    : (core) Secrets and shared helpers
- ardkr.storage   : [storage]  S3 connection (get_client)
- ardkr.pipeline  : [pipeline] collection lifecycle framework
- ardkr.catalog   : (core) STAC catalog load/search
- ardkr.dashboard : [dashboard] marimo STAC dashboard
- ardkr.modeling  : [modeling] team geovariable / modeling
"""

from __future__ import annotations

__version__ = "0.0.0"

# Lazy import gate keeps optional modules out of a plain ``import ardkr``.
_FEATURE_MODULES = ("pipeline", "storage", "catalog", "dashboard", "modeling")
_CORE_MODULES = {"catalog"}


def __getattr__(name: str):
    if name in _FEATURE_MODULES:
        import importlib

        try:
            return importlib.import_module(f"{__name__}.{name}")
        except ImportError as exc:
            if name in _CORE_MODULES:
                raise
            raise ImportError(
                f'ardkr.{name} requires its extra: pip install "ardkr[{name}]"'
            ) from exc
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "__version__",
    "catalog",
    "dashboard",
    "modeling",
    "pipeline",
    "storage",
]
