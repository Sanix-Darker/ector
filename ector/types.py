"""Typed result structures for ECTOR.

These ``TypedDict`` definitions describe the runtime shape of the values
returned by :func:`ector.extract`. At runtime the values remain plain ``dict``
objects; the types exist purely for editor support and static analysis.

See ``docs/features/06-public-api.md`` for the normative schema.
"""

from __future__ import annotations

from typing import TypedDict

# Simple aliases used across modules (PEP 604 unions, valid on Python >= 3.10).
Price = float | None
Currency = str | None


class Product(TypedDict, total=False):
    """A single extracted product request.

    - ``product``: the cleaned product name (always present in practice).
    - ``price``: a positive amount, present only when tied to the product.
    - ``currency``: lowercase currency code, present only when known.
    - ``quantity``: integer quantity, present only when a quantity is detected.
    - ``brand``: a recognised brand within the product phrase.
    - ``attributes``: recognised descriptors (colors, sizes, materials, ...).
    - ``condition``: one of ``new`` | ``used`` | ``refurbished``.
    """

    product: str
    price: float
    currency: str
    quantity: int
    brand: str
    attributes: list[str]
    condition: str


class Budget(TypedDict, total=False):
    """An inferred overall spending limit."""

    price: float
    currency: str


class PriceConstraint(TypedDict, total=False):
    """A parsed price constraint expressed in the request.

    ``type`` is one of ``max`` | ``min`` | ``around`` | ``between``. For
    ``between`` both ``min`` and ``max`` are set; otherwise ``value`` is set.
    """

    type: str
    value: float
    min: float
    max: float
    currency: str


class ExtractResult(TypedDict, total=False):
    """The top-level result returned by :func:`ector.extract`.

    ``products`` is always present (possibly empty). Other keys appear only when
    detected, keeping the output minimal and backward compatible.
    """

    products: list[Product]
    budget: Budget
    price_constraint: PriceConstraint
    intent: str
