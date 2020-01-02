=====
Notes
=====

Selection a text by the "pytest tests/features/rot13.feature::Decrypt_a_long_text" notation is not working, because Pytest stops the collection when it finds the desired test. Use "pytest -k" or "pytest -m" instead.

Do not use pytest parametrization. It is against the BDD concept, to hide values into code.