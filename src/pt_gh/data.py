"""Pytest Gherkin plugin data containers"""


_AVAILABLE_STEP_FUNCTIONS = list()
_MISSING_STEP_FUNCTIONS = list()
_GHERKIN_ERRORS = list()


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


def add_missing_step(step):
    """Add a step to the missing steps, for generation"""
    _MISSING_STEP_FUNCTIONS.append(step)


def get_missing_steps():
    """Get all the missing steps"""
    return _MISSING_STEP_FUNCTIONS
