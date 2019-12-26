"""Example for Pytest-Gherkin"""

# pragma pylint: disable=missing-docstring,redefined-outer-name

import codecs

from pt_gh import action


context = {"text": "", "ans": ""}


@action('I have a text "{text_in}"')
@action('I have an encrypted text "{text_in}"')
def given_i_have_text(text_in):
    context["text"] = text_in
    context["ans"] = ""


@action("I encrypt it")
@action("I decrypt it")
def i_en_de_crypt():
    context["ans"] = codecs.encode(context["text"], encoding="rot_13").upper()


@action('I get the answer "{text_out}"')
def i_get_answer(text_out):
    assert context["ans"] == text_out
