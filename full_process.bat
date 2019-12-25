call clean.bat
call build.bat
call create_test_env.bat
call install.bat
flake8 src tests
pytest
call testenv\Scripts\deactivate
