import json
from pathlib import Path
from functools import reduce
import sys

ROOT_PATH = Path(__file__).parent.parent
# Appending root path to sys.path
# to import from utils and ast_model
sys.path.append(str(ROOT_PATH))

with open(ROOT_PATH / "config.json", "r") as f:
    config = json.load(f)

DATA_PATH = Path(config["DATA_PATH"])
PROJECT = config["PROJECT"]

REPOSITORY = config["REPOSITORY"]
if config["BRANCH"].upper() == "ALL":
    BRANCH = None
else:
    BRANCH = config["BRANCH"]
if config["COMMITS"].upper() == "ALL":
    COMMITS = None
else:
    COMMITS = config["COMMITS"]

BUILD_SYSTEM = config["BUILD_SYSTEM"].lower()
SUMMARIZATION_METHODS = list(
    map(lambda method: method.upper(), config["SUMMARIZATION_METHODS"])
)

SAVE_PATH = Path(DATA_PATH / f"{PROJECT}_{BUILD_SYSTEM}_results")
SAVE_PATH.mkdir(parents=True, exist_ok=True)

# PATTERN_SETS is a dictionary with
# Keys: each and every one of the listed BUILD_LANGUAGES,
# Values: a list of naming and extention conventions for
# build specification files in the Key language.
# Note that the patterns are matched using the
# str.ends_with() method.
# To add support for a new build system, add and elif clause
# before the else clause and specify languages and file patterns.
if BUILD_SYSTEM == "cmake":
    LANGUAGES = ["cmake"]
    PATTERN_SETS = {"cmake": ["CMakeLists.txt", ".cmake"]}  # cmake file name patterns
elif BUILD_SYSTEM == "bazel":
    LANGUAGES = ["python"]
    PATTERN_SETS = {"python": ["BUILD.bazel", ".bzl"]}  # python file name patterns
elif BUILD_SYSTEM == "gradle":
    LANGUAGES = ["kotlin", "groovy"]
    PATTERN_SETS = {
        "kotlin": [".gradle.kts"],  # kotlin file name patterns
        "groovy": [".gradle"],  # groovy file name patterns
    }
else:
    raise ValueError(f'Selected build system "{BUILD_SYSTEM}" not supported.')


if config["FILTER_BUILDY_COMMITS_AT_INITIALIZATION"].upper() == "YES":
    PATTERNS_FLATTENED = reduce(lambda a, b: a + b, PATTERN_SETS.values())
else:
    PATTERNS_FLATTENED = None
