"""Software level or feature level tests of the entire sw app"""

# pragma pylint: disable=missing-docstring,redefined-outer-name

import codecs

from pt_gh import action


context = {"text": "", "ans": ""}


@action('I have a text "{text_in}"')
@action('I have an encrypted text "{text_in}"')
def given_context(text_in):
    """Given steps works as fixture, it will return a storage,
    simulating io for my_sw"""
    context["text"] = text_in
    context["ans"] = ""


@action("I encrypt it")
@action("I decrypt it")
def i_en_de_crypt():
    context["ans"] = codecs.encode(context["text"], encoding="rot_13").upper()


@action('I get the answer "{text_out}"')
def i_get_answer(text_out):
    assert context["ans"] == text_out
