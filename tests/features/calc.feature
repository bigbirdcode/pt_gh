Feature: simple calculations

Scenario: Adding integers
    Given I have 4 and 5
    When I add them
    Then I have 9 as result

Scenario: Subtracting integers
    Given I have 7 and 3
    When I subtract them
    Then I have 4 as result