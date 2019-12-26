"""Example for Pytest-Gherkin"""

# pragma pylint: disable=missing-docstring,redefined-outer-name

from pt_gh import action, ValueList


class Operator(ValueList):
    keys = ["add", "subtract"]


context = {"nums": [], "ans": ""}


@action("I have {num1} and {num2}")
def given_numbers(num1: int, num2: int):
    context["nums"] = []
    context["nums"].append(num1)
    context["nums"].append(num2)
    context["ans"] = ""


@action("I {operator} them")
def i_en_de_crypt(operator: Operator):
    if operator.value == "add":
        context["ans"] = context["nums"][0] + context["nums"][1]
    else:
        context["ans"] = context["nums"][0] - context["nums"][1]


@action("I have {result} as result")
def i_get_answer(result: int):
    assert context["ans"] == result
