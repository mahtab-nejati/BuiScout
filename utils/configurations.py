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
GUMTREE_OUTPUT_AVAILABLE = config["USE_EXISTING_DATA"] == "YES"
PROJECT = config["PROJECT"]

REPOSITORY = config["REPOSITORY"].rstrip("/")
if config["BRANCH"].upper() == "ALL":
    BRANCH = None
else:
    BRANCH = config["BRANCH"]
if isinstance(config["COMMITS"], str) and config["COMMITS"].upper() == "ALL":
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
    PATTERN_SETS = {
        "cmake": {"include": ["CMakeLists.txt", ".cmake"], "exclude": [".h.cmake"]}
    }  # cmake file name patterns
elif BUILD_SYSTEM == "bazel":
    LANGUAGES = ["python"]
    PATTERN_SETS = {
        "python": {"include": ["BUILD.bazel", ".bzl"], "exclude": []}
    }  # python file name patterns
elif BUILD_SYSTEM == "gradle":
    LANGUAGES = ["kotlin", "groovy"]
    PATTERN_SETS = {
        "kotlin": {  # kotlin file name patterns
            "include": [".gradle.kts"],
            "exclude": [],
        },
        "groovy": {"include": [".gradle"], "exclude": []},  # groovy file name patterns
    }
else:
    raise ValueError(f'Selected build system "{BUILD_SYSTEM}" not supported.')

ROOT_FILE = config["ROOT_FILE"]

PATTERNS_FLATTENED = {
    "include": reduce(
        lambda a, b: a + b, map(lambda sets: sets["include"], PATTERN_SETS.values())
    ),
    "exclude": reduce(
        lambda a, b: a + b, map(lambda sets: sets["exclude"], PATTERN_SETS.values())
    ),
}

if config["FILTER_BUILDY_COMMITS_AT_INITIALIZATION"].upper() == "YES":
    FILTERING = True
else:
    FILTERING = False

PROJECT_SPECIFIC_FILTERS = config["PROJECT_SPECIFIC_FILTERS"]
