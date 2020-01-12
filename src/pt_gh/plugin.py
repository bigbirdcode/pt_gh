"""Pytest Gherkin plugin implementation

This will be a new type of Gherkin/BDD implementation for Pytest.
It is based on the Gherkin library and Pytest framework.

Created by BigBirdCode
"""

import logging

import pytest

from .version import __version__, __plugin_name__
from .nodes import GherkinException, FeatureFile, StepFunction
from . import data
from . import generate


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
    and process them with parameters and fixtures.
    Verify and process rely on not just the scenarios but also the step functions
    that were collected by Pytest."""
    for item in items:
        if hasattr(item, "verify_and_process_scenario"):
            # item is a scenario, verify it
            item.verify_and_process_scenario()
    collected_errors = data.get_errors()
    for error in collected_errors:
        LOGGER.error(error)
    missing_steps = data.get_missing_steps()
    if missing_steps:
        LOGGER.error(
            "Following steps were missing, see steps_proposal.py for example implementation:"
        )
        for miss_step in missing_steps:
            LOGGER.error(miss_step)
        generate.generate(missing_steps)
    if collected_errors or missing_steps:
        raise GherkinException("There was errors in collection, exiting")


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
    >>> @action("my step with {operator} value")
    >>> def my_step(operator: Operator):
    >>>     if operator.value == "add":
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
    # TODO: make it an object instead
    return dict()


# ------------------------------------------------
# Plugin step function decorator
# ------------------------------------------------


def step(step_name):
    """Step decorator, all Given-When-Then steps use this same decorator"""

    def decorator(func):
        # Register the step, other way return the function unchanged
        step_function = StepFunction(func, step_name)
        # Check for similar steps, in both directions
        step_function.search_and_report_similar()
        # Register it
        data.add_step(step_function)
        return func

    return decorator
