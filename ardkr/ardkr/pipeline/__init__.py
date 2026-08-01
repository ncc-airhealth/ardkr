"""Public entry point for the :mod:`ardkr.pipeline` framework.

Keep this module small because agents read it frequently. Implementation
details live in private modules.
"""

from .collection_builder import CollectionBuilder

__all__ = ["CollectionBuilder"]
