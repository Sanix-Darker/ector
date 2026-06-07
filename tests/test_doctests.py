"""Run module doctests as part of the suite (BUG-007/BUG-011: examples must be valid)."""

import doctest

import pytest

import ector.money
import ector.products
import ector.text_utils

_MODULES = [ector.money, ector.text_utils, ector.products]


@pytest.mark.parametrize("module", _MODULES, ids=lambda m: m.__name__)
def test_module_doctests(module):
    results = doctest.testmod(module, verbose=False)
    assert results.failed == 0, f"{module.__name__}: {results.failed} doctest failures"
