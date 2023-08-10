from pydriller import Repository
from pydriller.git import Git
from tqdm import tqdm
import pandas as pd
import subprocess, gc
from datetime import datetime
from utils.helpers import (
    create_csv_files,
    file_is_target,
)
from utils.configurations import (
    GUMTREE_OUTPUT_AVAILABLE,
    ROOT_PATH,
    SAVE_PATH,
    REPOSITORY,
    BRANCH,
    COMMITS,
    LANGUAGES,
    ROOT_FILE,
    PATTERN_SETS,
    PATTERNS_FLATTENED,
    FILTERING,
    SUMMARIZATION_METHODS,
)
from system_commit_model import SystemDiff, SystemDiffShortcut

SAVE_PATH = SAVE_PATH / "run_data_flow_system"
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

# Run tool on commits
chronological_commit_order = 0
for commit in tqdm(repo.traverse_commits()):
    gc.collect()
    print(f"Commit in process: {commit.hash}")
    chronological_commit_order += 1
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
    except ValueError:
        # Log missing commits and move to then next
        commit_data_df = pd.DataFrame(
            {
                "commit_hash": [commit.hash],
                "chronological_commit_order": [chronological_commit_order],
                "commit_parents": [commit.parents],
                "has_build": [None],
                "has_nonbuild": [None],
                "is_missing": [True],
                "elapsed_time": [datetime.now() - commit_start],
            }
        )
        commit_data_df.to_csv(
            SAVE_PATH / "all_commits.csv", mode="a", header=False, index=False
        )
        continue

    # Iterate over the languages and file naming conventions
    # supported by the build system
    for LANGUAGE in LANGUAGES:
        PATTERNS = PATTERN_SETS[LANGUAGE]

        # Identify if the commit has build modifications
        if any(map(lambda mf: file_is_target(mf, PATTERNS), commit.modified_files)):
            has_build = True

            # Initialize summaries
            summary_dir = COMMITS_SAVE_PATH / commit.hash / "summaries"
            summary_dir.mkdir(parents=True, exist_ok=True)
            summaries = {}.copy()
            for sm in SUMMARIZATION_METHODS:
                summaries[sm] = [].copy()

            if not GUMTREE_OUTPUT_AVAILABLE:
                diff = SystemDiff(
                    REPOSITORY,
                    repo,
                    git_repo,
                    BRANCH,
                    commit,
                    ROOT_FILE,
                    LANGUAGE,
                    PATTERNS,
                    ROOT_PATH,
                    SAVE_PATH,
                )
            else:
                diff = SystemDiffShortcut(
                    REPOSITORY,
                    repo,
                    git_repo,
                    BRANCH,
                    commit,
                    ROOT_FILE,
                    LANGUAGE,
                    PATTERNS,
                    ROOT_PATH,
                    SAVE_PATH,
                )

            for build_file in diff.file_data.values():
                # Skip files with GumTree error
                if build_file["diff"] is None:
                    continue
                # Skip if no change to file
                if build_file["file_action"] is None:
                    continue
                # Summarize and log
                for sm in SUMMARIZATION_METHODS:
                    summary = build_file["diff"].summarize(method=sm)
                    summaries[sm] += list(
                        map(
                            lambda entry: {
                                "commit": commit.hash,
                                "subject_file": build_file["saved_as"],
                                **entry,
                            },
                            summary,
                        )
                    )
                build_file["diff"].source.slice.export_dot(
                    f'{summary_dir}/{build_file["saved_as"]}_slice_source.dot'
                )
                build_file["diff"].destination.slice.export_dot(
                    f'{summary_dir}/{build_file["saved_as"]}_slice_destination.dot'
                )

            # Convert slices to svg
            command = [str(ROOT_PATH / "convert.sh"), str(summary_dir)]
            process = subprocess.Popen(command, stdout=subprocess.PIPE)
            output, error = process.communicate()

            for sm in SUMMARIZATION_METHODS:
                summaries_df = pd.DataFrame(summaries[sm])
                summaries_df.to_csv(
                    SAVE_PATH / f"summaries_{sm.lower()}.csv",
                    mode="a",
                    header=False,
                    index=False,
                )

            commit_build_files_df = pd.DataFrame(list(diff.file_data.values()))
            commit_build_files_df.drop(labels=["diff"], axis=1, inplace=True)
            commit_build_files_df.to_csv(
                SAVE_PATH / "all_build_files.csv", mode="a", header=False, index=False
            )

            diff.perform_data_flow_analysis()
            diff.export_csv()

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

print(f"Finished processing in {datetime.now()-all_commits_start}")
