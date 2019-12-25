from setuptools import find_packages
from setuptools import setup

long_description = """
This will be a new type of Gherkin/BDD implementation for Pytest. It is based on the Gherkin library and Pytest framework.
"""

setup(
    name="pytest-gherkin",
    version="0.1",
    url="https://github.com/bigbirdcode",
    license="MIT License",
    author="BigBirdCode",
    author_email="na",
    description="Gherkin/BDD implementation for Pytest",
    long_description=long_description,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Framework :: Pytest",
        "Environment :: Desktop Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Development",
        "Topic :: Testing",
    ],
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.5",
    install_requires=["pytest>=3.5.0", "gherkin-official>=4.1.3"],
    extras_require={"dev": ["flake8", "pylint",],},
    entry_points={"pytest11": ["pytest_gherkin = pt_gh.pt_gh"]},
)
