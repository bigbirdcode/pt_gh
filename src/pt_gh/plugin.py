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
_GHERKIN_WARNINGS = list()

LOGGER = logging.getLogger(__plugin_name__)
LOGGER.setLevel(logging.DEBUG)


class GherkinException(Exception):
    """Basic exception to represent Gherkin problems"""


def pytest_addhooks(pluginmanager):
    """ This example assumes the hooks are grouped in the 'hooks' module. """
    from . import hooks

    pluginmanager.add_hookspecs(hooks)


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
    if _GHERKIN_WARNINGS:
        raise GherkinException("\n".join(_GHERKIN_WARNINGS))


class FeatureFile(pytest.File):

    """Feature file implementation"""

    def collect(self):
        """Collect and return scenarios from a feature file
        Gherkin pickles are used, so scenario outlines are already processed"""
        LOGGER.info("Collecting file: %s", self.fspath)
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
        scenario_name = scenario["name"].replace(" ", "_")
        LOGGER.debug("Processing scenario: %s", scenario_name)
        super().__init__(scenario_name, parent)
        self.scenario = scenario  # Scenario contains the Gherkin pickled scenario
        self.feature = parent  # The parent is the FeatureFile object, this is a shortcut
        self.fixturenames = set()  # Pytest use this to store fixture names
        self.funcargs = {}  # Pytest use this to store fixtures
        # Apply tags as pytest marks
        for tag in scenario["tags"]:
            tag_name = tag["name"].lstrip("@")
            #self.add_marker(tag_name)
            self.config.hook.pytest_gherkin_apply_tag(tag=tag_name, scenario=self)

    def verify_and_process_steps(self):
        """Verify that all steps exists and have good parameters
        Return exception in case of any problem
        Processing is creating a set of needed fixtures."""
        LOGGER.debug("Verify scenario: %s", self.name)
        for step, step_function, step_arguments in self.iterate_on_steps():
            call_arguments, fixture_arguments = build_arguments(
                step, step_function, step_arguments
            )
            self.fixturenames |= fixture_arguments

    def setup(self):
        """Pytest setup, here we prepare the fixtures to use"""

        def func():
            # Dummy function to hack pytest and process an empty one
            pass

        fixture_mgr = self.session._fixturemanager
        self._fixtureinfo = fixture_mgr.getfixtureinfo(
            node=self, func=func, cls=None, funcargs=False
        )
        fixture_request = FixtureRequest(self)
        # Now get the fixtures from self.fixturenames to self.funcargs
        # TODO: Here need to check that we have all the needed fixtures
        fixture_request._fillfixtures()
        if len(self.funcargs) != len(self.fixturenames):
            # not working...
            raise GherkinException("Not all fixtures were found!")

    def runtest(self):
        """Pytest calls it to run the actual test
        We need to find the steps and execute them one-by-one"""
        for step, step_function, step_arguments in self.iterate_on_steps(with_log=True):
            LOGGER.debug("    Calling function: %s", step_function.__name__)
            call_arguments, fixture_arguments = build_arguments(
                step, step_function, step_arguments
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
        """Iterate on steps and find the appropriate functions
        return the function and the parsed parameters from the step name
        Note: function parameters not checked here"""
        for step in self.scenario["steps"]:
            step_text = step["text"]
            if with_log:
                LOGGER.info("Step: %s", step_text)
            for act in _AVAILABLE_ACTIONS:
                match = act.name_parser.parse(step_text)
                if match:
                    yield (step, act.function, match.named)
                    break
            else:
                msg = "Step not found: {}".format(step_text)
                if with_log:
                    LOGGER.warning(msg)
                _GHERKIN_WARNINGS.append(msg)

    # def repr_failure(self, excinfo):
    #     """ called when self.runtest() raises an exception. """
    #     if isinstance(excinfo.value, GherkinException):
    #         return str(excinfo)
    #     else:
    #         super().repr_failure(excinfo)

    # def reportinfo(self):
    #     return self.fspath, 0, "usecase: %s" % self.name


def build_arguments(step, step_function, step_arguments):
    """Create properly converted parameters for a step function and collect fixture needs"""
    call_arguments = dict()
    fixture_arguments = set()
    sig = inspect.signature(step_function)
    # Check whether the right parameters were given for the step
    if not set(step_arguments) <= set(sig.parameters):
        raise GherkinException("Wrong step arguments found: " + str(step_arguments))
    # Create arguments (multi_line or data_table) if there is any
    argument = parse_arguments(step["arguments"])
    if argument and argument[0] not in sig.parameters:
        raise GherkinException(
            "Found step argument but not function parameter: " + argument[0]
        )
    # Now build the right call parameters
    for param_name, param in sig.parameters.items():
        if param_name in step_arguments:
            converter = (
                param.annotation if param.annotation != inspect.Parameter.empty else str
            )
            call_arguments[param_name] = converter(step_arguments[param_name])
        elif argument and param_name == argument[0]:
            call_arguments[param_name] = argument[1]
        else:
            # this will be a fixture
            fixture_arguments.add(param_name)
    return call_arguments, fixture_arguments


def parse_arguments(arguments):
    """Parse the Gherkin pre-processed arguments and return type and content"""
    if not arguments:
        return ()
    if len(arguments) != 1:
        raise GherkinException("Cannot handle multiple arguments")
    if "content" in arguments[0]:
        return _parse_arguments_multi_line(arguments[0])
    if "rows" in arguments[0]:
        return _parse_arguments_data_table(arguments[0])
    raise GherkinException("Unknown arguments format")


def _parse_arguments_multi_line(arguments):
    """Build a Python list from multi line argument"""
    lines = arguments["content"].split("\n")
    return ("multi_line", lines)


def _parse_arguments_data_table(arguments):
    """Build a Python 2D list from data tables"""
    table = list()
    for row in arguments["rows"]:
        row_data = list()
        for cell in row["cells"]:
            row_data.append(cell["value"])
        table.append(row_data)
    return ("data_table", table)


def pytest_gherkin_apply_tag(tag, scenario):
    """Default hook implementation"""
    scenario.add_marker(tag)


Action = namedtuple("Action", ["function", "name_parser", "step_name", "name_to_check"])


def action(step_name):
    """Step decorator, all Given-When-Then steps use this same decorator"""

    def decorator(func):
        # Register the step, other way return the function unchanged
        name_to_check = step_name.replace("{", "").replace("}", "")
        LOGGER.debug("Registering step: %s", step_name)
        name_parser = parse.compile(step_name)
        for act in _AVAILABLE_ACTIONS:
            # Check for similar steps, in both directions
            if name_parser.parse(act.name_to_check) or act.name_parser.parse(
                name_to_check
            ):
                _GHERKIN_WARNINGS.append(
                    "Similar step name was already declared:\n    {} \n    {}".format(
                        step_name, act.step_name
                    )
                )
        _AVAILABLE_ACTIONS.append(
            Action(
                function=func,
                name_parser=name_parser,
                step_name=step_name,
                name_to_check=name_to_check,
            )
        )
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
