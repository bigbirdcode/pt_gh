Feature: ROT13
    As a user I want rot-13 encryption

@basic
Scenario: Encrypt a text
    Given I have a text "DO NOT LOOK"
    When I encrypt it
    Then I get the answer "QB ABG YBBX"

@basic
Scenario: Decrypt a text
    Given I have an encrypted text "GBB ZNAL FRPERGF"
    When I decrypt it
    Then I get the answer "TOO MANY SECRETS"

@basic
Scenario: Encrypt a long text
    Given I have a long text:
        """
        DO
        NOT
        LOOK
        """
    When I encrypt all lines
    Then I get the long answer:
        """
        QB
        ABG
        YBBX
        """

@basic
Scenario: Decrypt a long text
    Given I have a long encrypted text:
        """
        GBB
        ZNAL
        FRPERGF
        """
    When I decrypt all lines
    Then I get the long answer:
        """
        TOO
        MANY
        SECRETS
        """

@detailed
Scenario Outline: Encrypt more texts: <text_in> --> <text_out>
    Given I have a text "<text_in>"
    When I encrypt it
    Then I get the answer "<text_out>"

    Examples:
    | text_in      | text_out     |
    | TDD!         | GQQ!         |
    | BDD!!!       | OQQ!!!       |
    | something... | FBZRGUVAT... |
    | EveryThing?  | RIRELGUVAT?  |

@detailed
Scenario Outline: Decrypt more texts: <text_in> --> <text_out>
    Given I have an encrypted text "<text_in>"
    When I decrypt it
    Then I get the answer "<text_out>"

    Examples:
    | text_in      | text_out     |
    | GQQ!         | TDD!         |
    | OQQ!!!       | BDD!!!       |
    | fbzrguvat... | SOMETHING... |
    | RirelGuvat?  | EVERYTHING?  |
