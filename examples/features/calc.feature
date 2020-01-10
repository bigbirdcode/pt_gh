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
