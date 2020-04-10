"""Pytest Gherkin plugin utilities"""


TREP = None
REPORT = False
DEBUG = False
FIRST = True


def set_config(config):
    """Set the global value for later use"""
    global TREP, REPORT, DEBUG
    TREP = config.pluginmanager.getplugin("terminalreporter")
    REPORT = config.getoption("bdd_report")
    DEBUG = config.getoption("bdd_debug")


def _write_msg(msg, **markup):
    """Low level writer wrapper"""
    global FIRST
    if FIRST:
        msg = "\n" + msg
        FIRST = False
    if not msg.endswith("\n"):
        msg += "\n"
    TREP.write(msg, **markup)


def write_msg(level, msg):
    """Write a terminal message"""
    if level == "ERROR":
        _write_msg(msg, red=True)
    elif level == "OK":
        _write_msg(msg, green=True)
    else:
        _write_msg(msg)


def write_debug(msg):
    """Write a debug message"""
    if not DEBUG:
        return
    _write_msg(msg)


def write_report(msg):
    """Write a test report message"""
    if not REPORT:
        return
    _write_msg(msg)
