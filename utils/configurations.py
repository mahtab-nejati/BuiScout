import json
from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent

with open(ROOT_PATH / "config.json", "r") as f:
    config = json.load(f)

DATA_PATH = Path(config["DATA_PATH"])
PROJECT = config["PROJECT"]
REPOSITORY = config["REPOSITORY"]
BUILD_SYSTEM = config["BUILD_SYSTEM"].lower()
SUMMARIZATION_METHODS = config["SUMMARIZATION_METHODS"]
COMMITS = config["COMMITS"]

SAVE_PATH = Path(DATA_PATH / f"{PROJECT}_{BUILD_SYSTEM}_results")
SAVE_PATH.mkdir(parents=True, exist_ok=True)

PATTERN_SETS = [[]]
if BUILD_SYSTEM == "cmake":
    LANGUAGES = ["cmake"]
    PATTERN_SETS = {"cmake": ["CMakeLists.txt", ".cmake"]}  # cmake file name patterns
if BUILD_SYSTEM == "bazel":
    LANGUAGES = ["python"]
    PATTERN_SETS = {"python": ["BUILD.bazel", ".bzl"]}  # python file name patterns
if BUILD_SYSTEM == "gradle":
    LANGUAGES = ["kotlin", "groovy"]
    PATTERN_SETS = {
        "kotlin": [".gradle.kts"],  # kotlin file name patterns
        "groovy": [".gradle"],  # groovy file name patterns
    }
