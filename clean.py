"""Delete Python cache and Pytest cache folders completely"""

import pathlib
import shutil

dirs_to_remove = [
    "**/__pycache__",
    "**/*.egg-info",
    ".pytest_cache",
    "build",
    "dist",
    "testenv",
]

for dir_to_remove in dirs_to_remove:
    for p in pathlib.Path(".").glob(dir_to_remove):
        shutil.rmtree(p)
