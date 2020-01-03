"""Example for Pytest-Gherkin"""

import codecs

from pt_gh import step


@step('I have a text "{text_in}"')
@step('I have an encrypted text "{text_in}"')
def given_i_have_text(text_in, context):
    """1 parameter and 1 fixture,
    default type is string
    step can have multiple annotations"""
    context["text"] = text_in
    context["ans"] = ""


@step("I encrypt it")
@step("I decrypt it")
def i_en_de_crypt(context):
    """Just a simple fixture parameter
    step can have multiple annotations"""
    context["ans"] = codecs.encode(context["text"], encoding="rot_13").upper()


@step('I get the answer "{text_out}"')
def i_get_answer(text_out, context):
    """1 parameter and 1 fixture
    default type is string"""
    assert context["ans"] == text_out


@step("I have a long text:")
@step("I have a long encrypted text:")
def given_i_have_long_text(multi_line, context):
    """multi_line is a special parameter, a Python list
    created from Gherkin multi line parameter
    and context is a fixture as in Pytest
    Note: multi_line contains strings, user has to convert"""
    context["text"] = multi_line
    context["ans"] = ""


@step("I encrypt all lines")
@step("I decrypt all lines")
def i_en_de_crypt_all_lines(context):
    """Here we process the previous multi_line parameter"""
    result = list()
    for line in context["text"]:
        result.append(codecs.encode(line, encoding="rot_13").upper())
    context["ans"] = result


@step("I get the long answer:")
def i_get_long_answer(multi_line, context):
    """multi_line is a special parameter, a Python list
    created from Gherkin multi line parameter
    and context is a fixture as in Pytest
    Note: multi_line contains strings, user has to convert"""
    assert context["ans"] == multi_line
