import json
from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent

with open(ROOT_PATH/'config.json', 'r') as f:
    config = json.load(f)

DATA_PATH = Path(config['DATA_PATH'])
PROJECT = config['PROJECT']
REPOSITORY = config['REPOSITORY']
BUILD_SYSTEM = config['BUILD_SYSTEM'].lower()
SUMMARIZATION_METHODS = config['SUMMARIZATION_METHODS']
COMMITS = config['COMMITS']

SAVE_PATH = Path(DATA_PATH/f'{PROJECT}_results')
SAVE_PATH.mkdir(parents=True, exist_ok=True)

PATTERNS = []
if BUILD_SYSTEM == 'cmake':
    PATTERNS = ['CMakeLists.txt', '.cmake']
    LANGUAGE = 'cmake'
if BUILD_SYSTEM == 'bazel':
    PATTERNS = ['BUILD.bazel', '.bzl']
    LANGUAGE = 'python'