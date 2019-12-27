==============================
Pytest_Gherkin, in short pt_gh
==============================

This will be a new type of Gherkin/BDD implementation for Pytest. It is based on the Gherkin library and Pytest framework.

BigBirdCode

Pytest based Gherkin, BDD goals
-------------------------------

Test codes are larger than tested codes. Therefore they must be simple and manageable.

# Test description and test implementation are separated

- Test description: feature files with Scenarios
- Test implementation: Python files with step definitions

# Test descriptions: clear explanation what to test

- Scenarios are the bases of the tests, they must contain everything to understand the tests
- Scenarios are to be located and loaded automatically
- Scenarios can be organized to folders and feature files
- Starting with clean Gherkin syntax, additional features can be added later
- No special syntax for parameters, just plain English text
- Scenario Outlines use <substitute> syntax and handled automatically

# Test implementation: Reusable steps

- Step definition must be simple, same for Scenario and Scenario Outlines
- Steps can be organized in folders and files, detected and loaded automatically (name start with test_, later it can be step_)
- In step definition no GWT, just step name
- No hidden data in steps, data must come in as parameters
- Parameter marks must be consistent, always {name}
- Parameter value can be given by type mark (name: List[int])
- Multi line parameters are converted to List[str] automatically, name: multi_line
- Tables are converted to Python tables (2d lists, List[List[str]]) automatically, name: data_table, further conversion must be handled by the code

# Use Pytest

- Fixtures can be used as in Pytest
- Step parameters are first checked from step definition (i.e. {name}) then from fixtures
- Special parameter names: data_table and multi_line to mark these features
- Special fixture: context to help inter-step data storage
- Special fixture: logger

# Reporting

- As Pytest, basic run do not output anything, but still logs are created
- With verbose (-v), Scenario names shall be displayed
- With extra verbose (-vv), all step names names shall be displayed
- Step names shall be displayed before their starts, and result after they finish
- Failed steps to be marked as failed clearly
- Logs shall contain scenario names, step names, parameter values and step logs
- Different logging types will be added later
