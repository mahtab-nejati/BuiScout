import json5
from pathlib import Path
from functools import reduce
import sys
from .helpers import get_mountpoint, is_url, clone_repo

ROOT_PATH = Path(__file__).parent.parent
# Appending root path to sys.path
# to import from utils and ast_model
sys.path.append(str(ROOT_PATH))

mountpoint = get_mountpoint()

if "test" in sys.argv:
    with open(ROOT_PATH / "test/config.json", "r") as f:
        config = json5.load(f)
else:
    with open(mountpoint / "config.json", "r") as f:
        config = json5.load(f)

options = config["OPTIONS"]

RESOURCE_CONTROL = options["RESOURCE_CONTROL"]

COMMIT_SERIES = options["COMMIT_SERIES"]

if COMMIT_SERIES:
    AST_DIFFS_REUSE = False
else:
    AST_DIFFS_REUSE = options["AST_DIFFS_REUSE"]

PROGRESS_RESET = options["PROGRESS_RESET"]

VERBOSE = options["VERBOSE"]

if options["CHANGE_LOCATION_ONLY"]:
    DATA_FLOW_ANALYSIS_MODE = "CHANGE_LOCATION"
else:
    DATA_FLOW_ANALYSIS_MODE = "GLOBAL"

SNAPSHOT_MODE = options["SNAPSHOT_MODE"]

EXECUTE_CALLABLES = options["EXECUTE_CALLABLES"]

PROJECT_MODEL = options["PROJECT_MODEL"]

FILTERING = options["INITIALIZE_WITH_BUILD_COMMITS"]

DATA_PATH = mountpoint / f'{config["RELATIVE_RESULT_PATH"]}'
PROJECT = config["PROJECT"]

REPOSITORY = str(config["REPOSITORY"])
if is_url(REPOSITORY):
    CLEAN_TRACES = True
    clone_repo(REPOSITORY, mountpoint / f"{PROJECT}")
    REPOSITORY = str(mountpoint / f"{PROJECT}")
else:
    CLEAN_TRACES = False
    REPOSITORY = str(mountpoint / f"{REPOSITORY}")


if config["BRANCH"].upper() == "ALL":
    BRANCH = None
else:
    BRANCH = config["BRANCH"]

if isinstance(config["COMMITS"], str) and config["COMMITS"].upper() == "ALL":
    COMMITS = None
else:
    COMMITS = config["COMMITS"]
EXCLUDED_COMMITS = config["EXCLUDED_COMMITS"]

BUILD_TECHNOLOGY = config["BUILD_TECHNOLOGY"].lower()
ENTRY_FILES = config["ENTRY_FILES"]

PROJECT_SPECIFIC_INCLUDES = config["PROJECT_SPECIFIC_INCLUDES"]
PROJECT_SPECIFIC_EXCLUDES = config["PROJECT_SPECIFIC_EXCLUDES"]

PROJECT_SPECIFIC_PATH_RESOLUTION = config["PROJECT_SPECIFIC_PATH_RESOLUTION"]

# EXTENDED CONFIGURATIONS

SAVE_PATH = Path(DATA_PATH / f"{PROJECT}_{BUILD_TECHNOLOGY}_results")
SAVE_PATH.mkdir(parents=True, exist_ok=True)

# PATTERN_SETS is a dictionary with
# Keys: each and every one of the listed BUILD_LANGUAGES,
# Values: a list of naming and extention conventions for
# build specification files in the Key language.
# Note that the patterns are matched using the
# str.ends_with() method.
# To add support for a new build system, add and elif clause
# before the else clause and specify languages and file patterns.
if BUILD_TECHNOLOGY == "cmake":
    LANGUAGES = ["cmake"]
    PATTERN_SETS = {
        "cmake": {
            "include": {
                "starts_with": [],
                "ends_with": ["CMakeLists.txt", ".cmake"],
            },
            "exclude": {"starts_with": [], "ends_with": [".h.cmake"]},
        }
    }  # cmake file name patterns
else:
    raise ValueError(f'Selected build system "{BUILD_TECHNOLOGY}" not supported.')

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
