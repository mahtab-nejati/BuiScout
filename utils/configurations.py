import json5
from pathlib import Path
from functools import reduce
import sys

ROOT_PATH = Path(__file__).parent.parent
# Appending root path to sys.path
# to import from utils and ast_model
sys.path.append(str(ROOT_PATH))

with open(ROOT_PATH / "config.json", "r") as f:
    config = json5.load(f)

USE_MULTIPROCESSING = config["USE_MULTIPROCESSING"].upper() == "YES"

PROCESS_AS_A_COMMIT_SERIES = config["PROCESS_AS_A_COMMIT_SERIES"].upper() == "YES"

if PROCESS_AS_A_COMMIT_SERIES:
    USE_EXISTING_AST_DIFFS = False
else:
    USE_EXISTING_AST_DIFFS = config["USE_EXISTING_AST_DIFFS"].upper() == "YES"

CLEAR_PROGRESS = config["CLEAR_PROGRESS"].upper() == "YES"

VERBOSE = config["VERBOSE"].upper() == "YES"

DATA_FLOW_ANALYSIS_MODE = config["DATA_FLOW_ANALYSIS_MODE"].upper()
if DATA_FLOW_ANALYSIS_MODE != "GLOBAL":
    DATA_FLOW_ANALYSIS_MODE = "CHANGE_LOCATION"

SNAPSHOT_MODE = config["SNAPSHOT_MODE"].upper() == "YES"

EXECUTE_CALLABLE_TYPES = config["EXECUTE_CALLABLE_TYPES"].upper() == "YES"

USE_PROJECT_SPECIFIC_MODELS = not (
    config["USE_PROJECT_SPECIFIC_MODELS"].upper() == "NO"
)

FILTERING = config["FILTER_BUILDY_COMMITS_AT_INITIALIZATION"].upper() == "YES"

DATA_PATH = Path(config["DATA_PATH"])
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
EXCLUDED_COMMITS = config["EXCLUDED_COMMITS"]

BUILD_SYSTEM = config["BUILD_SYSTEM"].lower()
ENTRY_FILES = config["ENTRY_FILES"]

PROJECT_SPECIFIC_INCLUDES = config["PROJECT_SPECIFIC_INCLUDES"]
PROJECT_SPECIFIC_EXCLUDES = config["PROJECT_SPECIFIC_EXCLUDES"]

PROJECT_SPECIFIC_MANUAL_PATH_RESOLUTION = config[
    "PROJECT_SPECIFIC_MANUAL_PATH_RESOLUTION"
]

# EXTENDED CONFIGURATIONS

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
        "cmake": {
            "include": {"starts_with": [], "ends_with": ["CMakeLists.txt", ".cmake"]},
            "exclude": {"starts_with": [], "ends_with": [".h.cmake"]},
        }
    }  # cmake file name patterns
elif BUILD_SYSTEM == "bazel":
    LANGUAGES = ["python"]
    PATTERN_SETS = {
        "python": {
            "include": {"starts_with": [], "ends_with": ["BUILD.bazel", ".bzl"]},
            "exclude": {"starts_with": [], "ends_with": []},
        }
    }  # python file name patterns
elif BUILD_SYSTEM == "gradle":
    LANGUAGES = ["kotlin", "groovy"]
    PATTERN_SETS = {
        "kotlin": {  # kotlin file name patterns
            "include": {"starts_with": [], "ends_with": [".gradle.kts"]},
            "exclude": {"starts_with": [], "ends_with": []},
        },
        "groovy": {  # groovy file name patterns
            "include": {"starts_with": [], "ends_with": [".gradle.kts"]},
            "exclude": {"starts_with": [], "ends_with": []},
        },
    }
else:
    raise ValueError(f'Selected build system "{BUILD_SYSTEM}" not supported.')

for l in LANGUAGES:
    if l in PROJECT_SPECIFIC_INCLUDES:
        includes = PROJECT_SPECIFIC_INCLUDES[l]
        if "starts_with" in includes:
            PATTERN_SETS[l]["include"]["starts_with"] = list(
                set(PATTERN_SETS[l]["include"]["starts_with"] + includes["starts_with"])
            )
        if "ends_with" in includes:
            PATTERN_SETS[l]["include"]["ends_with"] = list(
                set(PATTERN_SETS[l]["include"]["ends_with"] + includes["ends_with"])
            )
    if l in PROJECT_SPECIFIC_EXCLUDES:
        excludes = PROJECT_SPECIFIC_EXCLUDES[l]
        if "starts_with" in excludes:
            PATTERN_SETS[l]["exclude"]["starts_with"] = list(
                set(PATTERN_SETS[l]["exclude"]["starts_with"] + excludes["starts_with"])
            )
        if "ends_with" in excludes:
            PATTERN_SETS[l]["exclude"]["ends_with"] = list(
                set(PATTERN_SETS[l]["exclude"]["ends_with"] + excludes["ends_with"])
            )

PATTERNS_FLATTENED = {
    "include": {
        "starts_with": reduce(
            lambda a, b: a + b,
            map(lambda sets: sets["include"]["starts_with"], PATTERN_SETS.values()),
        ),
        "ends_with": reduce(
            lambda a, b: a + b,
            map(lambda sets: sets["include"]["ends_with"], PATTERN_SETS.values()),
        ),
    },
    "exclude": {
        "starts_with": reduce(
            lambda a, b: a + b,
            map(lambda sets: sets["exclude"]["starts_with"], PATTERN_SETS.values()),
        ),
        "ends_with": reduce(
            lambda a, b: a + b,
            map(lambda sets: sets["exclude"]["ends_with"], PATTERN_SETS.values()),
        ),
    },
}
