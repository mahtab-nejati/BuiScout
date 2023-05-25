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

SAVE_PATH = Path(DATA_PATH/f'{PROJECT}_{BUILD_SYSTEM}_results')
SAVE_PATH.mkdir(parents=True, exist_ok=True)

PATTERN_SETS = [[]]
if BUILD_SYSTEM == 'cmake':
    PATTERN_SETS = [['CMakeLists.txt', '.cmake']]
    LANGUAGES = ['cmake']
if BUILD_SYSTEM == 'bazel':
    PATTERN_SETS = [['BUILD.bazel', '.bzl']]
    LANGUAGES = ['python']
if BUILD_SYSTEM == 'gradle':
    PATTERN_SETS = [['.gradle.kts'], # Kotlin file name patterns
                    ['.gradle']] # Groovy file name patterns
    LANGUAGES = ['kotlin',
                'groovy']