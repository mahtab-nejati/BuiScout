import pandas as pd
from pathlib import Path
import shutil
from .exceptions import DebugException

#################################
######## Helpers for AST ########
#################################


# Word locater for parsing labels
def find_word_indexes(text, word):
    # Find the start index of the word in the text
    start_index = text.find(word)
    return (start_index, start_index + len(word) - 1)


# GumTree node label parser
def parse_label(label):
    # Locate properties
    _, end_type = find_word_indexes(label, "GumTreeNodeType")
    start_content, end_content = find_word_indexes(label, "GumTreeNodeContent")
    start_pos, end_pos = find_word_indexes(label, "GumTreeNodeSPos")
    start_end, end_end = find_word_indexes(label, "GumTreeNodeEPos")
    parsed_label = {
        "type": label[end_type + 2 : start_content].strip(),
        "content": label[end_content + 2 : start_pos].strip(),
        "s_pos": int(label[end_pos + 2 : start_end].strip()),
        "e_pos": int(label[end_end + 2 :].strip()),
    }
    if len(parsed_label["type"]) == 0 and len(parsed_label["content"]) == 0:
        parsed_label["type"] = '"'
        parsed_label["content"] = '"'
    return parsed_label


#################################
######## Helpers for run ########
#################################
from networkx.drawing.nx_agraph import from_agraph


# Reading the GumTree dotdiff output from the .dot file
def read_dotdiff(path):
    try:
        import pygraphviz
    except ImportError as err:
        raise ImportError(
            "read_dot() requires pygraphviz " "http://pygraphviz.github.io/"
        ) from err
    A = pygraphviz.AGraph(file=path)

    source = from_agraph(A.get_subgraph("cluster_src\xa0"))
    source.name = "source"

    destination = from_agraph(A.get_subgraph("cluster_dst\xa0"))
    destination.name = "destination"

    matches = dict(
        map(
            lambda e: (e[0], e[1]),
            filter(lambda e: e.attr.get("style") == "dashed", A.edges()),
        )
    )

    A.clear()
    return source, destination, matches


#################################
######## Helpers for run ########
#################################
# Check if the modified file a build specification
def file_is_build(file_name, patterns):
    if file_name is None:
        raise DebugException("WEIRD PYDRILLER FILENAME")

    if patterns["starts_with"]:
        starts = file_name.startswith(tuple(patterns["starts_with"]))
    else:
        starts = False

    if patterns["ends_with"]:
        ends = file_name.endswith(tuple(patterns["ends_with"]))
    else:
        ends = False

    return starts or ends


def file_is_filtered(file_path, filtering_patterns):
    if file_path is None:
        return True
    if filtering_patterns["starts_with"]:
        if file_path.startswith(tuple(filtering_patterns["starts_with"])):
            return True
    if filtering_patterns["ends_with"]:
        if file_path.endswith(tuple(filtering_patterns["ends_with"])):
            return True
    return False


def file_is_target(modified_file, patterns):
    if isinstance(modified_file, str):
        return file_is_build(
            modified_file, patterns["include"]
        ) and not file_is_filtered(modified_file, patterns["exclude"])
    return file_is_build(modified_file.filename, patterns["include"]) and not (
        file_is_filtered(modified_file.new_path, patterns["exclude"])
        or file_is_filtered(modified_file.old_path, patterns["exclude"])
    )


# Prpcess the path to project files
def get_processed_path(modified_file):
    if modified_file.new_path is not None:
        return modified_file.new_path.replace("/", "__")
    elif modified_file.old_path is not None:
        return modified_file.old_path.replace("/", "__")
    elif modified_file.filename is not None:
        return modified_file.filename.replace("/", "__")
    else:
        return None


# Write the source code into the files under the processed path
def write_source_code(file_path, source_code):
    if source_code is None:
        source_code = ""
    with open(file_path, "w") as f:
        f.write(source_code)


# Prepare the report csv files
def create_csv_files(save_path):
    # Save metadata on build changes
    build_files_columns = [
        "commit_hash",
        "file_name",
        "build_language",
        "file_action",
        "before_path",
        "after_path",
        "saved_as",
        "has_gumtree_error",
        "data_flow_source_analysis",
        "data_flow_destination_analysis",
        "data_flow_source_reach",
        "data_flow_destination_reach",
    ]
    build_files_df = pd.DataFrame(columns=build_files_columns)
    build_files_df.to_csv(save_path / "all_build_files.csv", index=False)

    # Save metadata on all changes
    commits_columns = [
        "commit_hash",
        "chronological_commit_order",
        "commit_parents",
        "has_build",
        "has_nonbuild",
        "is_missing",
        "elapsed_time",
    ]
    commits_df = pd.DataFrame(columns=commits_columns)
    commits_df.to_csv(save_path / "all_commits.csv", index=False)


def clear_existing_data(SAVE_PATH):
    # Clear existing code and gumtree outputs
    to_remove = Path(SAVE_PATH / "code")
    if to_remove.exists():
        shutil.rmtree(to_remove)
    to_remove = Path(SAVE_PATH / "gumtree_output")
    if to_remove.exists():
        shutil.rmtree(to_remove)


def setup_init():
    return


def setup_is_completed():
    return
