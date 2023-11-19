from pydriller import Repository
from pydriller.git import Git
from tqdm import tqdm
import pandas as pd
from pathlib import Path
import subprocess, gc, shutil, importlib
from datetime import datetime
from utils.exceptions import DebugException
from utils.helpers import (
    create_csv_files,
    file_is_target,
)
from utils.configurations import (
    ROOT_PATH,
    SAVE_PATH,
    REPOSITORY,
    PROJECT,
    BRANCH,
    COMMITS,
    EXCLUDED_COMMITS,
    LANGUAGES,
    ENTRY_FILES,
    PATTERN_SETS,
    PATTERNS_FLATTENED,
    FILTERING,
    SUMMARIZATION_METHODS,
    USE_PROJECT_SPECIFIC_MODELS,
    DATA_FLOW_ANALYSIS_MODE,
)

from system_commit_model import SystemDiffSeries as SystemDiffModel

if USE_PROJECT_SPECIFIC_MODELS:
    project_specific_support_path = ROOT_PATH / "project_specific_support" / PROJECT
    if project_specific_support_path.exists():
        SystemDiffModel = importlib.import_module(
            f"project_specific_support.{PROJECT}"
        ).SystemDiffSeries


SAVE_PATH = SAVE_PATH / f"system_series_{DATA_FLOW_ANALYSIS_MODE.lower()}"
COMMITS_SAVE_PATH = SAVE_PATH / "commits"
COMMITS_SAVE_PATH.mkdir(parents=True, exist_ok=True)

repo = Repository(
    REPOSITORY,
    only_modifications_with_file_types=PATTERNS_FLATTENED["include"]
    if FILTERING
    else None,  # See EXCEPTION_HANDLING_GitPython in comments within code
    only_commits=COMMITS,
    only_in_branch=BRANCH,
    # order="reverse",  # Orders commits from newest to oldest, default behaviour is desired (oldest to newest)
)
git_repo = Git(REPOSITORY)

create_csv_files(SUMMARIZATION_METHODS, SAVE_PATH)

all_commits_start = datetime.now()


def clear_existing_data():
    # Clear existing code and gumtree outputs
    to_remove = Path(SAVE_PATH / "code")
    if to_remove.exists():
        shutil.rmtree(to_remove)
    to_remove = Path(SAVE_PATH / "gumtree_output")
    if to_remove.exists():
        shutil.rmtree(to_remove)


# Clear existing code and gumtree outputs
clear_existing_data()


# Run tool on commits
chronological_commit_order = 0
for commit in tqdm(repo.traverse_commits()):
    gc.collect()
    print(f"Commit in process: {commit.hash}")
    # Commit-level attributes that show whether the commit
    # has affected build/non-build files
    has_build = False
    has_nonbuild = None  # TODO: Disabled to keep script simple

    # Start analysis of the commit
    commit_start = datetime.now()

    # EXCEPTION_HANDLING_GitPython
    # Error handling for missing commits
    # GitPython, and consequently PyDriller,
    # do not handle this well.
    # Although PyDriller offers the
    # only_modifications_with_file_types option,
    # using such filtering throws an error if the
    # commit is missing as GitPython attempts an access
    # to the commit when iterating over the commits.
    # In practice, this does not provide any
    # performance improvements either, as the
    # traversal takes place by iterating over
    # all the commits and just skipping the ones
    # filtered based on user's specifications.
    # This is why use of
    # "FILTER_BUILDY_COMMITS_AT_INITIALIZATION": "NO" is recommended
    # in the configurations.
    try:
        # This will throw an error if the commit is missing
        commit.modified_files
    except AttributeError:
        # Clear existing code and gumtree outputs
        clear_existing_data()
        if not (commit.hash in EXCLUDED_COMMITS):
            raise DebugException(
                f"Submodule commit {commit.hash} must be excluded from analysis."
            )
        continue
    except ValueError:
        # Clear existing code and gumtree outputs
        clear_existing_data()
        if not (commit.hash in EXCLUDED_COMMITS):
            raise DebugException(
                f"Missing commit {commit.hash} must be excluded from analysis."
            )
        continue

    # Iterate over the languages and file naming conventions
    # supported by the build system
    for LANGUAGE in LANGUAGES:
        PATTERNS = PATTERN_SETS[LANGUAGE]

        # Identify if the commit has build modifications
        if any(map(lambda mf: file_is_target(mf, PATTERNS), commit.modified_files)):
            has_build = True

            diff = SystemDiffModel(
                REPOSITORY,
                repo,
                git_repo,
                BRANCH,
                commit,
                ENTRY_FILES,
                LANGUAGE,
                PATTERNS,
                ROOT_PATH,
                SAVE_PATH,
            )

            # Save time by skipping
            if commit.hash in EXCLUDED_COMMITS:
                to_remove = diff.commit_dir
                if to_remove.exists():
                    shutil.rmtree(to_remove)
                continue

            diff.export_csv(propagation_slice_mode=True)

            commit_build_files_df = pd.DataFrame(list(diff.file_data.values()))
            commit_build_files_df.drop(
                labels=["diff", "language_specific_info"],
                axis=1,
                inplace=True,
            )
            commit_build_files_df.to_csv(
                SAVE_PATH / "all_build_files.csv", mode="a", header=False, index=False
            )

    # Don't log if excluded
    if commit.hash in EXCLUDED_COMMITS:
        continue

    chronological_commit_order += 1
    # Log all changes
    commit_data_df = pd.DataFrame(
        {
            "commit_hash": [commit.hash],
            "chronological_commit_order": [chronological_commit_order],
            "commit_parents": [commit.parents],
            "has_build": [has_build],
            "has_nonbuild": [has_nonbuild],
            "is_missing": [False],
            "elapsed_time": [datetime.now() - commit_start],
        }
    )
    commit_data_df.to_csv(
        SAVE_PATH / "all_commits.csv", mode="a", header=False, index=False
    )

# Checkout to head once done.
# This is currently disabled in
# system_commit_mode/sustem_diff_mode.py/SystemDiff()
# for performance improvement.
git_repo.checkout(BRANCH)

# Clear existing code and gumtree outputs
clear_existing_data()

print(f"Finished processing in {datetime.now()-all_commits_start}")
