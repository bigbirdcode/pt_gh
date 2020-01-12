"""Example for Pytest-Gherkin"""

import ast

from pytest import approx

from pt_gh import step, value_options


operator = value_options("add", "subtract")


@step("I have {num1:d} and {num2:d}")
def given_numbers_i(num1, num2, context):
    """Example of parameter types converted based on annotation
    and context is a fixture as in Pytest"""
    context["nums"] = []
    context["nums"].append(num1)
    context["nums"].append(num2)
    context["ans"] = 0


@step("I have floats {num1:f} and {num2:f}")
def given_numbers_f(num1, num2, context):
    """Example of parameter types converted based on annotation
    and context is a fixture as in Pytest"""
    context["nums"] = []
    context["nums"].append(num1)
    context["nums"].append(num2)
    context["ans"] = 0.0


@step("I have list of floats {float_list}")
def i_have_list_of_floats(float_list, context):
    """I have list of floats"""
    float_list = ast.literal_eval(float_list)
    context["nums"] = float_list
    context["ans"] = 0.0


@step("I {operator:operator} them", dict(operator=operator))
def i_en_de_crypt(operator, context):
    """Example of parameter created and checked based on ValueList
    and context is a fixture as in Pytest"""
    if operator == "add":
        for num in context["nums"]:
            context["ans"] += num
    else:
        context["ans"] = context["nums"][0]
        for num in context["nums"][1:]:
            context["ans"] -= num


@step("I have {result:d} as result")
def i_get_answer_i(result, context):
    """Example of parameter types converted based on annotation
    and context is a fixture as in Pytest"""
    assert context["ans"] == result


@step("I have float {result:f} as result")
def i_get_answer_f(result, context):
    """Example of parameter types converted based on annotation
    and context is a fixture as in Pytest"""
    assert context["ans"] == approx(result)


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
