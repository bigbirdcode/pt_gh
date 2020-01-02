"""Pytest-Gherkin plugin hooks"""

import pytest

#@pytest.hookspec(firstresult=True)
@pytest.mark.firstresult
def pytest_gherkin_apply_tag(tag, scenario):
    """Apply a tag (from a ``.feature`` file) to the given scenario.

    The default implementation does the equivalent of
    ``scenario.add_marker(tag)``, but you can override this hook and
    return ``True`` to do more sophisticated handling of tags.
    """

