"""Pytest Gherkin plugin data containers"""

from collections import namedtuple
import logging

import parse

from .version import __plugin_name__


_AVAILABLE_STEP_FUNCTIONS = list()
_GHERKIN_ERRORS = list()

LOGGER = logging.getLogger(__plugin_name__)


def add_error(msg):
    """Add an error message to the collected Gherkin errors"""
    _GHERKIN_ERRORS.append(msg)


def get_errors():
    """Return the collected Gherkin errors"""
    return _GHERKIN_ERRORS


def add_step(step):
    """Add a step to the available steps"""
    _AVAILABLE_STEP_FUNCTIONS.append(step)


def get_steps():
    """Get all the available steps"""
    return _AVAILABLE_STEP_FUNCTIONS


StepFunction = namedtuple(
    "StepFunction", ["function", "name_parser", "step_name", "name_to_check"]
)


def step(step_name):
    """Step decorator, all Given-When-Then steps use this same decorator"""

    def decorator(func):
        # Register the step, other way return the function unchanged
        LOGGER.debug("Registering step: %s", step_name)
        name_to_check = step_name.replace("{", "").replace("}", "")
        name_parser = parse.compile(step_name)
        for other_step in get_steps():
            # Check for similar steps, in both directions
            if name_parser.parse(
                other_step.name_to_check
            ) or other_step.name_parser.parse(name_to_check):
                add_error(
                    "Similar step name was already declared:\n    {} \n    {}".format(
                        step_name, other_step.step_name
                    )
                )
        add_step(
            StepFunction(
                function=func,
                name_parser=name_parser,
                step_name=step_name,
                name_to_check=name_to_check,
            )
        )
        return func

    return decorator
