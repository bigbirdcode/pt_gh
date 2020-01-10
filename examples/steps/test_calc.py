"""Example for Pytest-Gherkin"""

from pt_gh import step, ValueList


Operator = ValueList("add", "subtract")


@step("I have {num1} and {num2}")
def given_numbers(num1: int, num2: int, context):
    """Example of parameter types converted based on annotation
    and context is a fixture as in Pytest"""
    context["nums"] = []
    context["nums"].append(num1)
    context["nums"].append(num2)
    context["ans"] = ""


@step("I {operator} them")
def i_en_de_crypt(operator: Operator, context):
    """Example of parameter created and checked based on ValueList
    and context is a fixture as in Pytest"""
    if operator.value == "add":
        context["ans"] = context["nums"][0] + context["nums"][1]
    else:
        context["ans"] = context["nums"][0] - context["nums"][1]


@step("I have {result} as result")
def i_get_answer(result: int, context):
    """Example of parameter types converted based on annotation
    and context is a fixture as in Pytest"""
    assert context["ans"] == result


@step("I have a matrix:")
def i_have_a_matrix(data_table, context):
    """data_table is a special parameter, a Python 2D list
    created from Gherkin data table
    and context is a fixture as in Pytest
    Note: data_table contains strings, user has to convert"""
    context["matrix"] = [[int(x) for x in row] for row in data_table]


@step("I sum all rows")
def i_sum_all_rows(context):
    """Just a simple fixture parameter"""
    context["vector"] = [sum(row) for row in context["matrix"]]


@step("I have a vector:")
def i_have_a_vector(data_table, context):
    """data_table is a special parameter, a Python 2D list
    created from Gherkin data table
    and context is a fixture as in Pytest
    Note: data_table contains strings, user has to convert"""
    assert context["vector"] == [int(x[0]) for x in data_table]
