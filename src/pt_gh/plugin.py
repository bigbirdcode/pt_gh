"""Pytest Gherkin plugin implementation

This will be a new type of Gherkin/BDD implementation for Pytest.
It is based on the Gherkin library and Pytest framework.

Created by BigBirdCode
"""

import pytest
from parse import with_pattern

from .nodes import FeatureFile, StepFunction
from . import data
from . import generate
from . import hooks
from . import utils


# ------------------------------------------------
# Pytest hooks for the plugin
# ------------------------------------------------


def pytest_addoption(parser):
    """Adding BDD related options"""
    group = parser.getgroup("bdd")
    group.addoption(
        "--bdd",
        action="store_true",
        dest="bdd_execution",
        default=False,
        help="Enable BDD test execution. Note, with this Pytest will ONLY execute BDD tests.",
    )
    group.addoption(
        "--bdd_report",
        action="store_true",
        dest="bdd_report",
        default=False,
        help="Enable BDD test report on the terminal",
    )
    group.addoption(
        "--bdd_debug",
        action="store_true",
        dest="bdd_debug",
        default=False,
        help="Enable BDD test debug messages on the terminal",
    )


@pytest.mark.trylast
def pytest_configure(config):
    """Configure plugin"""
    utils.set_config(config)


def pytest_addhooks(pluginmanager):
    """Define Plugin hooks from the hooks module"""
    pluginmanager.add_hookspecs(hooks)


def pytest_collect_file(parent, path):
    """Pytest will call it for all files, we are looking for features to process"""
    if not parent.config.getoption("bdd_execution"):
        return None
    # BDD execution, processing feature files
    if path.ext == ".feature":
        return FeatureFile(path, parent)
    return None


def pytest_collection_modifyitems(session, config, items):  # pylint: disable=unused-argument
    """Pytest will call it after the collection, we use to verify steps are ok,
    and process them with parameters and fixtures.
    Verify and process rely on not just the scenarios but also the step functions
    that were collected by Pytest."""
    if not config.getoption("bdd_execution"):
        return
    # BDD execution
    # Remove all non-BDD tests
    items[:] = [item for item in items if hasattr(item, "verify_and_process_scenario")]
    # Process the BDD tests, i.e. scenario items
    for item in items:
        item.verify_and_process_scenario()
    # Check errors
    if data.get_errors() or data.get_missing_steps():
        # TODO: I don't know a better way to exit, but deselect all tests
        items.clear()


def pytest_collection_finish(session):  # pylint: disable=unused-argument
    """ called after collection has been performed and modified.
    BDD errors will be reported here
    """
    collected_errors = data.get_errors()
    missing_steps = data.get_missing_steps()
    if not collected_errors and not missing_steps:
        return
    # We had errors or missing steps
    for error in collected_errors:
        utils.write_msg("ERROR", error)
    if missing_steps:
        utils.write_msg(
            "ERROR",
            "Following steps were missing, see steps_proposal.py for example implementation:",
        )
        for miss_step in missing_steps:
            utils.write_msg("INFO", miss_step)
        generate.generate(missing_steps)
    utils.write_msg("ERROR", "!!!!! Exit because of BDD problems !!!!!")


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
