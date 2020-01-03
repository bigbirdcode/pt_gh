"""Pytest Gherkin plugin nodes"""

import inspect
import logging

import parse
import pytest
from _pytest.fixtures import FixtureRequest, FixtureLookupError
from gherkin.parser import Parser
from gherkin.pickles import compiler

from .version import __plugin_name__
from . import data


LOGGER = logging.getLogger(__plugin_name__)


DATA_TABLE = "data_table"
MULTI_LINE = "multi_line"
RESERVED_NAMES = (DATA_TABLE, MULTI_LINE)


class GherkinException(Exception):
    """Basic exception to represent Gherkin problems"""


class StepFunction:

    """Step functions with step name, parse and check"""

    def __init__(self, function, step_name):
        LOGGER.debug("Registering step: %s", step_name)
        self.function = function
        self.step_name = step_name
        self.name_to_check = step_name.replace("{", "").replace("}", "")
        self.name_parser = parse.compile(step_name)

    def parse(self, text):
        """Shortcut to parse a text with name parser"""
        return self.name_parser.parse(text)

    def parse_parameters(self, text):
        """Shortcut to parse a text and return the found parameters
        Assumption: text match"""
        return self.parse(text).named

    def match_similar(self, other):
        """Check for similar step name definition, in both directions
        similarity result ambiguity, therefore an error"""
        return self.name_parser.parse(other.name_to_check) or other.name_parser.parse(
            self.name_to_check
        )

    def search_and_report_similar(self):
        """Compare the step name with already collected step names
        if similarity found then report as error"""
        for other in data.get_steps():
            if self.match_similar(other):
                data.add_error(
                    "Similar step name was already declared:\n    {} \n    {}".format(
                        self.step_name, other.step_name
                    )
                )


def search_step_function(step_text):
    """Find the matching step from the available steps"""
    for step_function in data.get_steps():
        match = step_function.parse(step_text)
        if match:
            return step_function
    # At collection time report errors
    # Assumption: this will not happen at execution time
    data.add_error("Step not found: {}".format(step_text))
    return None


class FeatureFile(pytest.File):

    """Feature file implementation"""

    def collect(self):
        """Collect and return scenarios from a feature file
        Gherkin pickles are used, so scenario outlines are already processed"""
        LOGGER.info("Collecting file: %s", self.fspath)
        parser = Parser()
        # Read the file, parse and compile
        # keep all this, so later we can check if needed
        # Gherkin pickles compile Scenario Outlines,
        # so far we use this implementation
        with self.fspath.open() as handle:
            self.gherkin_text = handle.read()
        self.gherkin_document = parser.parse(self.gherkin_text)
        self.gherkin_pickles = compiler.compile(self.gherkin_document)
        for scenario in self.gherkin_pickles:
            yield ScenarioItem(scenario=scenario, parent=self)


class ScenarioItem(pytest.Item):

    """Scenario item, as a test for Pytest"""

    def __init__(self, *, scenario, parent):
        # note: self.name will store scenario_name
        scenario_name = scenario["name"].replace(" ", "_")
        LOGGER.debug("Processing scenario: %s", scenario_name)
        super().__init__(scenario_name, parent)
        # Hacking self, to enable build FixtureRequest object
        fixture_mgr = self.session._fixturemanager
        self._fixtureinfo = fixture_mgr.getfixtureinfo(
            node=self, func=None, cls=None, funcargs=False
        )

        # Keep references of compiled scenario pickle and feature
        self.scenario = scenario  # Gherkin pickled scenario
        self.feature = parent  # Shortcut to the FeatureFile

        # Fixtures are needed for scenario level, initialize containers
        self.fixture_names = set()  # Names of the needed fixtures
        self.fixture_parameters = dict()  # Actual fixtures, filled at setup

        # Steps, filled with verify and process call
        self.steps = []

        # Apply tags as pytest marks
        for tag in scenario["tags"]:
            tag_name = tag["name"].lstrip("@")
            self.config.hook.pytest_gherkin_apply_tag(tag=tag_name, scenario=self)

    def verify_and_process_scenario(self):
        """Process all steps, by locating step functions and creating scenario steps.
        Locating and creating actions verify that all steps exists and have good parameters.
        Meanwhile collecting problems to data gherkin errors.
        Processing is also creating a set of needed fixtures (not checked here)."""
        LOGGER.debug("Verify and process scenario: %s", self.name)
        for gherkin_step in self.scenario["steps"]:
            step_function = search_step_function(gherkin_step["text"])
            if step_function:
                scenario_step = ScenaroStep(gherkin_step, step_function, self)
                self.steps.append(scenario_step)
                self.fixture_names |= scenario_step.fixture_needs

    def setup(self):
        """Pytest setup, here we prepare the fixtures to use"""
        fixture_request = FixtureRequest(self)
        # Now get all the needed fixtures for the scenario
        # steps will later collect their needs
        self.fixture_parameters.clear()
        for fixture_name in self.fixture_names:
            try:
                self.fixture_parameters[fixture_name] = fixture_request.getfixturevalue(
                    fixture_name
                )
            except FixtureLookupError:
                raise GherkinException("Fixture not found: " + fixture_name)

    def runtest(self):
        """Pytest calls it to run the actual test
        We need to find the steps and execute them one-by-one"""
        self.config.hook.pytest_gherkin_before_scenario(scenario=self)
        for step in self.steps:
            step.run_step(self.fixture_parameters)
        self.config.hook.pytest_gherkin_after_scenario(scenario=self)

    # def repr_failure(self, excinfo):
    #     """ called when self.runtest() raises an exception. """
    #     if isinstance(excinfo.value, GherkinException):
    #         return str(excinfo)
    #     else:
    #         super().repr_failure(excinfo)

    # def reportinfo(self):
    #     return self.fspath, 0, "usecase: %s" % self.name


class ScenaroStep:

    """Step class represent the functions behind the Gherkin steps"""

    def __init__(self, gherkin_step, step_function, scenario):
        self.scenario = scenario
        self.gherkin_step = gherkin_step
        self.step_text = gherkin_step["text"]
        self.step_function = step_function
        self.step_parameters = step_function.parse_parameters(self.step_text)
        self.function_sig = inspect.signature(self.step_function.function)
        self.call_parameters = dict()
        self.argument = None
        self.fixture_needs = set()
        # Check everything at once, but "and" is lazy
        success1 = self.verify_parameters()
        success2 = self.verify_and_build_argument()
        if success1 and success2:
            self.build_parameters()

    def verify_parameters(self):
        """Verify the received/parsed parameter names"""
        # Check whether the right parameters were given for the step
        for parameter in self.step_parameters.keys():
            if parameter not in self.function_sig.parameters:
                data.add_error(
                    "For step {} wrong parameters found: {}".format(
                        self.step_text, parameter
                    )
                )
                return False
        for name in RESERVED_NAMES:
            if name in self.step_parameters:
                data.add_error(
                    "For step {} reserved parameter name {} found".format(
                        self.step_text, name
                    )
                )
                return False
        return True

    def verify_and_build_argument(self):
        """Create and check arguments (multi_line or data_table) if there is any"""
        argument = parse_arguments(self.gherkin_step["arguments"])
        if argument and argument[0] not in self.function_sig.parameters:
            data.add_error(
                "For step {} argument found, but not parameter: {}".format(
                    self.step_text, argument[0]
                )
            )
            return False
        for name in RESERVED_NAMES:
            if name in self.function_sig.parameters and not argument:
                data.add_error(
                    "For step {0} {1} parameter found, but not the {1}".format(
                        self.step_text, name
                    )
                )
                return False
        self.argument = argument
        return True

    def build_parameters(self):
        """Create properly converted parameters for a step function and collect fixture needs"""
        # Now build the right call parameters
        # we have checked that available values are all listed,
        # so no further check needed. Remaining ones are fixtures.
        for param_name, param in self.function_sig.parameters.items():
            if param_name in self.step_parameters:
                converter = (
                    param.annotation
                    if param.annotation != inspect.Parameter.empty
                    else str
                )
                self.call_parameters[param_name] = converter(
                    self.step_parameters[param_name]
                )
            elif self.argument and param_name == self.argument[0]:
                self.call_parameters[param_name] = self.argument[1]
            else:
                # this will be a fixture
                self.fixture_needs.add(param_name)

    def run_step(self, fixtures):
        """Run the step, with the actual fixtures"""
        call_fixtures = dict()
        LOGGER.info(self.step_text)
        LOGGER.debug("    Calling function: %s", self.step_function.function.__name__)
        if self.call_parameters:
            LOGGER.debug("    Parameters:")
            for k, v in self.call_parameters.items():
                LOGGER.debug("        %s: %s", k, v)
        if self.fixture_needs:
            # Build the actual and needed fixtures
            LOGGER.debug("    Fixtures:")
            for k in self.fixture_needs:
                v = fixtures[k]
                call_fixtures[k] = v
                LOGGER.debug("        %s: %s", k, v)
        self.scenario.config.hook.pytest_gherkin_before_step(
            step=self, scenario=self.scenario
        )
        self.step_function.function(**self.call_parameters, **call_fixtures)
        self.scenario.config.hook.pytest_gherkin_after_step(
            step=self, scenario=self.scenario
        )


def parse_arguments(arguments):
    """Parse the Gherkin pre-processed arguments and return type and content"""
    if not arguments:
        return ()
    if len(arguments) != 1:
        data.add_error("Cannot handle multiple arguments")
        return ()
    if "content" in arguments[0]:
        return _parse_arguments_multi_line(arguments[0])
    if "rows" in arguments[0]:
        return _parse_arguments_data_table(arguments[0])
    data.add_error("Unknown arguments format, gherkin version error: " + arguments[0])
    return ()


def _parse_arguments_multi_line(arguments):
    """Build a Python list from multi line argument"""
    lines = arguments["content"].split("\n")
    return (MULTI_LINE, lines)


def _parse_arguments_data_table(arguments):
    """Build a Python 2D list from data tables"""
    table = list()
    for row in arguments["rows"]:
        row_data = list()
        for cell in row["cells"]:
            row_data.append(cell["value"])
        table.append(row_data)
    return (DATA_TABLE, table)
