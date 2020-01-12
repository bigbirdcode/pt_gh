Feature: simple calculations

@basic
Scenario: Adding integers
    Given I have 4 and 5
    When I add them
    Then I have 9 as result

@basic
Scenario: Subtracting integers
    Given I have 7 and 3
    When I subtract them
    Then I have 4 as result

@detailed
Scenario: Adding a matrix
    Given I have a matrix:
        | 1 | 2 | 3 |
        | 4 | 5 | 6 |
        | 7 | 8 | 9 |
    When I sum all rows
    Then I have a vector:
        |  6 |
        | 15 |
        | 24 |

@basic
Scenario: Adding floats
    Given I have floats 4.1 and 5.2
    When I add them
    Then I have float 9.3 as result

@basic
Scenario: Adding floats
    Given I have list of floats [4.1, 5.2, 6.3]
    When I add them
    Then I have float 15.6 as result

