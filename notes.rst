=====
Notes
=====

Some random thoughts to remember.

Selection a test by the "pytest tests/features/rot13.feature::Decrypt_a_long_text" notation is not working, because Pytest stops the collection when it finds the desired test. Use "pytest -k" or "pytest -m" instead.

Do not use pytest parametrization. It is against the BDD concept, to hide values into code.

Originally I wanted to use type hints for parameter type definition, but this would be too difficult for me. Instead parse types are perfect and simple, so I changed to that.


TODO
----

None

Hooks
-----

pytest_runtest_logreport
