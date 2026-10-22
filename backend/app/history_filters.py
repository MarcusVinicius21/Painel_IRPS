"""Additive history scope. Provider is the exact fact provenance, not a text search."""
from pydantic import Field
from .schemas import Strict

class HistoryFilters(Strict):
    provider: str | None = Field(default=None,min_length=1,max_length=80,pattern=r'^[A-Z][A-Z0-9_]*$')
    only_comparable: bool = False
