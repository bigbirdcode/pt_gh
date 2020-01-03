"""Pytest Gherkin plugin implementation

This will be a new type of Gherkin/BDD implementation for Pytest.
It is based on the Gherkin library and Pytest framework.

Created by BigBirdCode
"""

import logging

import pytest

from .version import __version__, __plugin_name__
from .nodes import GherkinException, FeatureFile
from . import data


LOGGER = logging.getLogger(__plugin_name__)
LOGGER.setLevel(logging.DEBUG)
LOGGER.debug("Pytest plugin %s version %s starting", __plugin_name__, __version__)


# ------------------------------------------------
# Pytest hooks for the plugin
# ------------------------------------------------


def pytest_addhooks(pluginmanager):
    """Define Plugin hooks from the hooks module"""
    from . import hooks

    pluginmanager.add_hookspecs(hooks)


def pytest_collect_file(parent, path):
    """Pytest will call it for all files, we are looking for features to process"""
    if path.ext == ".feature":
        return FeatureFile(path, parent)
    return None


def pytest_collection_modifyitems(session, config, items):
    """Pytest will call it after the collection, we use to verify steps are ok,
    and process them with parameters and fixtures"""
    for item in items:
        if hasattr(item, "verify_and_process_scenario"):
            # item is a scenario, verify it
            item.verify_and_process_scenario()
    collected_errors = data.get_errors()
    if collected_errors:
        raise GherkinException("\n".join(collected_errors))


# ------------------------------------------------
# Plugin hooks, default implementations
# ------------------------------------------------


def pytest_gherkin_apply_tag(tag, scenario):
    """Adding scenario tags as Pytest marks,
    default hook implementation"""
    scenario.add_marker(tag)


# ------------------------------------------------
# Plugin helpers and fixtures
# ------------------------------------------------


def ValueList(*args):
    """Return a special class to represent a given set of values for steps
    Usage:
    >>> Operator = ValueList("add", "subtract")
    >>> @action("my step with {oper} value")
    >>> def my_step(oper: Operator):
    >>>     if oper.value == "add":
    >>>         ...
    """

    class SubValueList:
        """Value List subclass with customized keys"""

        def __init__(self, value):
            self.keys = args
            if value not in self.keys:
                raise GherkinException("Unknown value: " + value)
            self.value = value

        def __str__(self):
            return self.value

    return SubValueList


@pytest.fixture
def context():
    """Context is a dictionary to store inter-step values"""
    return dict()
