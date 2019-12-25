from collections import namedtuple

from gherkin.parser import Parser
from gherkin.pickles import compiler
import parse
import pytest


_AVAILABLE_ACTIONS = list()

Action = namedtuple("Action", ["function", "parser"])


def pytest_collect_file(parent, path):
    if path.ext == ".feature":
        return FeatureFile(path, parent)


class FeatureFile(pytest.File):
    def collect(self):
        parser = Parser()
        with self.fspath.open() as handle:
            gherkin_text = handle.read()
        gherkin_document = parser.parse(gherkin_text)
        gherkin_pickles = compiler.compile(gherkin_document)
        for scenario in gherkin_pickles:
            yield ScenarioItem(scenario=scenario, parent=self)


class ScenarioItem(pytest.Item):
    def __init__(self, *, scenario, parent):
        super().__init__(scenario["name"], parent)
        self.scenario = scenario

    def runtest(self):
        for step in self.scenario["steps"]:
            step_text = step["text"]
            for act in _AVAILABLE_ACTIONS:
                match = act.parser.parse(step_text)
                if match:
                    act.function(**match.named)
                    break


def action(name):
    def decorator(fn):
        _AVAILABLE_ACTIONS.append(Action(function=fn, parser=parse.compile(name)))
        return fn

    return decorator
