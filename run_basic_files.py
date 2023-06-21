from pathlib import Path
from pydriller import Repository
from tqdm import tqdm
import pandas as pd
import subprocess
import gc
from datetime import datetime
from utils.helpers import (
    create_csv_files,
    write_source_code,
    file_is_build,
    get_file_dir,
    get_processed_path,
    read_dotdiff,
)
from utils.configurations import (
    ROOT_PATH,
    SAVE_PATH,
    REPOSITORY,
    BRANCH,
    COMMITS,
    LANGUAGES,
    PATTERN_SETS,
    PATTERNS_FLATTENED,
    FILTERING,
    SUMMARIZATION_METHODS,
)
from diff_model import ASTDiff

SAVE_PATH = SAVE_PATH / "run_basic_files"
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
    has_nonbuild = False
    commit_build_files = [].copy()

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

    # Initialize summaries
    summaries = {}.copy()
    for sm in SUMMARIZATION_METHODS:
        summaries[sm] = [].copy()

    # Iterate over the languages and file naming conventions
    # supported by the build system
    for LANGUAGE in LANGUAGES:
        PATTERNS = PATTERN_SETS[LANGUAGE]

        # If the commit is not missing and modified files are available,
        # iterate over the modified files to find modified build files.
        for modified_file in commit.modified_files:
            # Identify if the file is a build specification file and expected to be analyzed
            if file_is_build(modified_file.filename, PATTERNS):
                # Commit-level attribute to show that the commit has affected build files.
                has_build = True

                # Start analysis of the build file
                file_start = datetime.now()
                file_modification_data = {
                    "commit_hash": commit.hash,
                    "file_dir": get_file_dir(modified_file),
                    "file_name": modified_file.filename,
                    "build_language": LANGUAGE,
                    "file_action": str(modified_file.change_type).split(".")[-1],
                    "before_path": modified_file.old_path,
                    "after_path": modified_file.new_path,
                    "saved_as": get_processed_path(modified_file),
                    "has_gumtree_error": False,
                    "elapsed_time": None,
                }
                commit_build_files.append(file_modification_data)

                print(f'Processing modified file {file_modification_data["saved_as"]}')

                # Setup commit directory
                commit_dir = Path(COMMITS_SAVE_PATH / commit.hash)

                # build files before change
                before_dir = commit_dir / "before"
                before_dir.mkdir(parents=True, exist_ok=True)
                write_source_code(
                    before_dir / file_modification_data["saved_as"],
                    modified_file.source_code_before,
                )

                # build files after change
                after_dir = commit_dir / "after"
                after_dir.mkdir(parents=True, exist_ok=True)
                write_source_code(
                    after_dir / file_modification_data["saved_as"],
                    modified_file.source_code,
                )

                # GumTree output setup
                gumtree_output_dir = commit_dir / "gumtree_output"
                gumtree_output_dir.mkdir(parents=True, exist_ok=True)

                # Run GumTree
                command = [
                    str(ROOT_PATH / "process.sh"),
                    str(LANGUAGE),
                    str(commit_dir),
                    str(file_modification_data["saved_as"]),
                    str(gumtree_output_dir),
                ]
                process = subprocess.Popen(command, stdout=subprocess.PIPE)
                output, error = process.communicate()
                with open(f"{gumtree_output_dir}/get_webdiff.txt", "a") as f:
                    f.write(
                        f"gumtree webdiff -g {LANGUAGE}-treesitter "
                        + f'{commit_dir}/before/{file_modification_data["saved_as"]} '
                        + f'{commit_dir}/after/{file_modification_data["saved_as"]}\n'
                    )

                # Summarizer output setup
                summary_dir = commit_dir / "summaries"
                summary_dir.mkdir(parents=True, exist_ok=True)

                # Check if the output of the GumTree is valid.
                try:
                    dotdiff_content = read_dotdiff(
                        f'{gumtree_output_dir}/{file_modification_data["saved_as"]}_dotdiff.dot'
                    )
                except:
                    file_modification_data["has_gumtree_error"] = True
                # Do not apply method if GumTree output throws an error
                if not file_modification_data["has_gumtree_error"]:
                    # Load GumTree output and slice
                    diff = ASTDiff(
                        *dotdiff_content,
                        file_modification_data["file_action"],
                        file_modification_data["saved_as"],
                        commit.hash,
                        LANGUAGE,
                    )
                    diff.source.slice.export_dot(
                        f'{summary_dir}/{file_modification_data["saved_as"]}_slice_source.dot'
                    )
                    diff.destination.slice.export_dot(
                        f'{summary_dir}/{file_modification_data["saved_as"]}_slice_destination.dot'
                    )

                    # Convert slices to svg
                    command = [str(ROOT_PATH / "convert.sh"), str(summary_dir)]
                    process = subprocess.Popen(command, stdout=subprocess.PIPE)
                    output, error = process.communicate()

                    # Summarize and log
                    for sm in SUMMARIZATION_METHODS:
                        summary = diff.summarize(method=sm)
                        summaries[sm] += list(
                            map(
                                lambda entry: {
                                    "commit": commit.hash,
                                    "subject_file": file_modification_data["saved_as"],
                                    **entry,
                                },
                                summary,
                            )
                        )

                # End of file analysis
                file_modification_data["elapsed_time"] = datetime.now() - file_start

            # If at least one file is non-build, log it
            else:
                # Commit-level attribute to show that the commit has affected non-build files.
                has_nonbuild = True

    # Save summaries
    for sm in SUMMARIZATION_METHODS:
        summaries_df = pd.DataFrame(summaries[sm])
        summaries_df.to_csv(
            SAVE_PATH / f"summaries_{sm.lower()}.csv",
            mode="a",
            header=False,
            index=False,
        )

    # Save metadata on build files
    commit_build_files_df = pd.DataFrame(commit_build_files)
    commit_build_files_df.to_csv(
        SAVE_PATH / "all_build_files.csv", mode="a", header=False, index=False
    )

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