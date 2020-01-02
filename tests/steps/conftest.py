"""pytest root config file"""

import pytest


def pytest_gherkin_apply_tag(tag, scenario):
    """Hook for pytest-gherkin tag handling.
    All tests and trace identifier numbers are given as Gherkin tags
    as well as the normal tags.
    Here, in this example we convert id tags to user properties instead,
    and leaving the rest to the default hook implementation"""
    if tag.startswith("trace_id_"):
        scenario.user_properties.append(("trace_id", tag))
        return True
    if tag.startswith("test_id_"):
        scenario.user_properties.append(("test_id", tag))
        return True
    # Fall back to pytest-bdd's default behavior
    return None
