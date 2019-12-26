"""Pytest Gherkin plugin implementation"""

from collections import namedtuple
import inspect

from gherkin.parser import Parser
from gherkin.pickles import compiler
import parse
import pytest


_AVAILABLE_ACTIONS = list()

Action = namedtuple("Action", ["function", "parser"])


class GherkinException(Exception):
    """Basic exception to represent Gherkin problems"""


def pytest_collect_file(parent, path):
    """Pytest will call it for all files, we are looking for features to process"""
    if path.ext == ".feature":
        return FeatureFile(path, parent)
    return None


class FeatureFile(pytest.File):

    """Feature file implementation"""

    def collect(self):
        """Collect and return scenarios from a feature file
        Gherkin pickles are used, so scenario outlines are already processed"""
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
        super().__init__(scenario["name"], parent)
        self.scenario = scenario

    def runtest(self):
        """Pytest calls it to run the actual test
        We need to find the steps and execute them one-by-one"""
        for step in self.scenario["steps"]:
            step_text = step["text"]
            for act in _AVAILABLE_ACTIONS:
                match = act.parser.parse(step_text)
                if match:
                    call_step_function(act.function, match.named)
                    break
            else:
                raise GherkinException("Step not found: " + step_text)

    # def repr_failure(self, excinfo):
    #     """ called when self.runtest() raises an exception. """
    #     if isinstance(excinfo.value, GherkinException):
    #         return str(excinfo)
    #     else:
    #         super().repr_failure(excinfo)

    # def reportinfo(self):
    #     return self.fspath, 0, "usecase: %s" % self.name


def call_step_function(step_function, step_arguments):
    """Call a step function with properly converted parameters"""
    call_arguments = {}
    sig = inspect.signature(step_function)
    # Check whether the right parameters were given for the step
    if not set(step_arguments) <= set(sig.parameters):
        raise GherkinException("Wrong step arguments found: " + str(step_arguments))
    # Now build the right call parameters
    for param_name, param in sig.parameters.items():
        if param_name in step_arguments:
            converter = (
                param.annotation if param.annotation != inspect.Parameter.empty else str
            )
            call_arguments[param_name] = converter(step_arguments[param_name])
        else:
            # this will be a fixture
            pass
    step_function(**call_arguments)


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
                raise RuntimeError("Unknown value: " + value)
            self.value = value

    return SubValueList
