"""Pytest Gherkin plugin implementation

This will be a new type of Gherkin/BDD implementation for Pytest.
It is based on the Gherkin library and Pytest framework.

Created by BigBirdCode
"""

import logging

import pytest
from parse import with_pattern

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


def value_options(*args):
    """Return a special function to represent a given set of values for steps
    Usage:
    >>> operator = value_options("add", "subtract")
    >>> @action("my step with {operator:operator} value", dict(operator=operator))
    >>> def my_step(operator):
    >>>     if operator == "add":
    >>>         ...
    Note: When user add a wrong value,
    it will not match and reported as not implemented step!
    """

    @with_pattern(r"|".join(args))
    def parse_options(text):
        return text

    return parse_options


@pytest.fixture
def context():
    """Context is a dictionary to store inter-step values"""
    # TODO: make it an object instead
    return dict()


# ------------------------------------------------
# Plugin step function decorator
# ------------------------------------------------


def step(step_name, extra_types=None):
    """Step decorator, all Given-When-Then steps use this same decorator"""

    def decorator(func):
        # Register the step, other way return the function unchanged
        step_function = StepFunction(func, step_name, extra_types)
        # Check for similar steps, in both directions
        step_function.search_and_report_similar()
        # Register it
        data.add_step(step_function)
        return func

    return decorator
