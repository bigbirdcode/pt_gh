"""Pytest Gherkin plugin implementation"""

from collections import namedtuple
import logging
import inspect

from gherkin.parser import Parser
from gherkin.pickles import compiler
import parse
import pytest
from _pytest.fixtures import FixtureRequest


__version__ = "0.1"
__plugin_name__ = "pt_gh"

_AVAILABLE_ACTIONS = list()

Action = namedtuple("Action", ["function", "parser"])

LOGGER = logging.getLogger(__plugin_name__)
LOGGER.setLevel(logging.DEBUG)


class GherkinException(Exception):
    """Basic exception to represent Gherkin problems"""


def pytest_collect_file(parent, path):
    """Pytest will call it for all files, we are looking for features to process"""
    if path.ext == ".feature":
        return FeatureFile(path, parent)
    return None


def pytest_collection_modifyitems(session, config, items):
    """Pytest will call it after the collection, we use to verify steps are ok and process fixtures"""
    for item in items:
        if hasattr(item, "verify_and_process_steps"):
            # item is a scenario, verify it
            item.verify_and_process_steps()


class FeatureFile(pytest.File):

    """Feature file implementation"""

    def collect(self):
        """Collect and return scenarios from a feature file
        Gherkin pickles are used, so scenario outlines are already processed"""
        LOGGER.debug("Collecting file: %s", self.fspath)
        parser = Parser()
        with self.fspath.open() as handle:
            gherkin_text = handle.read()
        gherkin_document = parser.parse(gherkin_text)
        gherkin_pickles = compiler.compile(gherkin_document)
        for scenario in gherkin_pickles:
            yield ScenarioItem(scenario=scenario, parent=self)


class ScenarioItem(pytest.Item):

    """Scenario item, as a test for Pytest"""

    def __init__(self, *, scenario, parent):
        scenario_name = scenario["name"]
        LOGGER.debug("Processing scenario: %s", scenario_name)
        super().__init__(scenario_name, parent)
        self.scenario = scenario
        self.fixturenames = set()  # Pytest use this to store fixture names
        self.funcargs = {}  # Pytest use this to store fixtures
        # Apply tags as pytest marks
        for tag in scenario["tags"]:
            tag_name = tag["name"].lstrip("@")
            self.add_marker(tag_name)

    def verify_and_process_steps(self):
        """Verify that all steps exists and have good parameters
        Return exception in case of any problem
        Processing is creating a set of needed fixtures."""
        LOGGER.debug("Verify scenario: %s", self.name)
        for step_function, step_arguments in self.iterate_on_steps():
            call_arguments, fixture_arguments = self.build_arguments(
                step_function, step_arguments
            )
            self.fixturenames |= fixture_arguments

    def setup(self):
        """Pytest setup, here we prepare the fixtures to use"""

        def func():
            """Dummy function to hack pytest and process an empty one"""
            pass

        fixture_mgr = self.session._fixturemanager
        self._fixtureinfo = fixture_mgr.getfixtureinfo(
            node=self, func=func, cls=None, funcargs=False
        )
        fixture_request = FixtureRequest(self)
        # Now get the fixtures from self.fixturenames to self.funcargs
        fixture_request._fillfixtures()

    def runtest(self):
        """Pytest calls it to run the actual test
        We need to find the steps and execute them one-by-one"""
        for step_function, step_arguments in self.iterate_on_steps(with_log=True):
            LOGGER.debug("    Calling function: %s", step_function.__name__)
            call_arguments, fixture_arguments = self.build_arguments(
                step_function, step_arguments
            )
            if call_arguments:
                LOGGER.debug("    Arguments:")
                for k, v in call_arguments.items():
                    LOGGER.debug("        %s: %s", k, v)
            if self.funcargs:
                LOGGER.debug("    Fixtures:")
                for k, v in self.funcargs.items():
                    LOGGER.debug("        %s: %s", k, v)
            step_function(**call_arguments, **self.funcargs)

    def iterate_on_steps(self, with_log=False):
        """Iterate on steps and find the appropriate functions"""
        for step in self.scenario["steps"]:
            step_text = step["text"]
            if with_log:
                LOGGER.info("Step: %s", step_text)
            for act in _AVAILABLE_ACTIONS:
                match = act.parser.parse(step_text)
                if match:
                    yield (act.function, match.named)
                    break
            else:
                raise GherkinException("Step not found: " + step_text)

    def build_arguments(self, step_function, step_arguments):
        """Create properly converted parameters for a step function and collect fixture needs"""
        call_arguments = dict()
        fixture_arguments = set()
        sig = inspect.signature(step_function)
        # Check whether the right parameters were given for the step
        if not set(step_arguments) <= set(sig.parameters):
            raise GherkinException("Wrong step arguments found: " + str(step_arguments))
        # Now build the right call parameters
        for param_name, param in sig.parameters.items():
            if param_name in step_arguments:
                converter = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else str
                )
                call_arguments[param_name] = converter(step_arguments[param_name])
            else:
                # this will be a fixture
                fixture_arguments.add(param_name)
        return call_arguments, fixture_arguments

    # def repr_failure(self, excinfo):
    #     """ called when self.runtest() raises an exception. """
    #     if isinstance(excinfo.value, GherkinException):
    #         return str(excinfo)
    #     else:
    #         super().repr_failure(excinfo)

    # def reportinfo(self):
    #     return self.fspath, 0, "usecase: %s" % self.name


def action(name):
    """Step decorator, all Given-When-Then steps use this same decorator"""

    def decorator(func):
        # Register the step, other way return the function unchanged
        name_to_check = name.replace("{", "").replace("}", "")
        for act in _AVAILABLE_ACTIONS:
            if act.parser.parse(name_to_check):
                raise GherkinException(
                    "Similar step name was already declared:\n" + name
                )
        _AVAILABLE_ACTIONS.append(Action(function=func, parser=parse.compile(name)))
        return func

    return decorator


def ValueList(*args):
    """Return a special class to represent a given set of values for steps
    Usage:
    >>> Operator = ValueList("add", "subtract")
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
