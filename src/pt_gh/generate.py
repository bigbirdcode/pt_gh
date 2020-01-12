"""Pytest Gherkin plugin generate missing steps"""

import re


TEMPLATE = '''@step("{0}")
def {1}(context):
    """{0}"""
    raise RuntimeError("Not implemented")

'''


def generate(missing_steps):
    """Generate a basic implementation for the missing steps"""
    with open("steps_proposal.py", "w") as f:
        for step in missing_steps:
            step_str = step.replace('"', "'")
            step_fn = re.sub(r"\W", "_", step).lower()
            step_def = TEMPLATE.format(step_str, step_fn)
            f.write(step_def)
