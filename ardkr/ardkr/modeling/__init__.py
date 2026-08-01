"""ardkr.modeling — team geovariable and modeling workflows.

extra: [modeling]  (pip install "ardkr[modeling]")

Build team variables and models from catalog collections.
"""

from __future__ import annotations

try:
    import numpy  # noqa: F401
    import pandas  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        'ardkr.modeling requires numpy and pandas: '
        'pip install "ardkr[modeling]"'
    ) from exc

# TODO: geovariable / modeling pipeline.
