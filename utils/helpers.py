import pandas as pd
from .exceptions import DebugException
from utils.configurations import PROJECT_SPECIFIC_FILTERS

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
    _, end_type = find_word_indexes(label, "GumTreeType")
    start_content, end_content = find_word_indexes(label, "GumTreeContent")
    start_pos, end_pos = find_word_indexes(label, "GumTreeSPos")
    start_end, end_end = find_word_indexes(label, "GumTreeEPos")
    return {
        "type": label[end_type + 2 : start_content].strip(),
        "content": label[end_content + 2 : start_pos].strip(),
        "s_pos": int(label[end_pos + 2 : start_end].strip()),
        "e_pos": int(label[end_end + 2 :].strip()),
    }


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
def file_is_build(file_name, patterns={"inclde": [], "exclude": []}):
    if file_name is None:
        raise DebugException("WEIRD PYDRILLER FILENAME")

    return (file_name.endswith(tuple(patterns["include"]))) and (
        not file_name.endswith(tuple(patterns["exclude"]))
    )


def file_is_filtered(file_path, filtering_patterns=PROJECT_SPECIFIC_FILTERS):
    if file_path is None:
        return True
    if filtering_patterns["include"]["starts_with"]:
        if not file_path.startswith(
            tuple(filtering_patterns["include"]["starts_with"])
        ):
            return True
    if filtering_patterns["include"]["ends_with"]:
        if not file_path.endswith(tuple(filtering_patterns["include"]["ends_with"])):
            return True
    if filtering_patterns["exclude"]["starts_with"]:
        if file_path.startswith(tuple(filtering_patterns["exclude"]["starts_with"])):
            return True
    if filtering_patterns["exclude"]["ends_with"]:
        if file_path.endswith(tuple(filtering_patterns["exclude"]["ends_with"])):
            return True
    return False


def file_is_target(modified_file, patterns):
    if isinstance(modified_file, str):
        return file_is_build(modified_file, patterns) and not file_is_filtered(
            modified_file
        )
    return file_is_build(modified_file.filename, patterns) and not (
        file_is_filtered(modified_file.new_path)
        and file_is_filtered(modified_file.old_path)
    )


def get_file_dir(modified_file):
    if modified_file.new_path is not None:
        return modified_file.new_path.replace(modified_file.filename, "")
    elif modified_file.old_path is not None:
        return modified_file.old_path.replace(modified_file.filename, "")
    elif modified_file.filename is not None:
        return ""
    else:
        return None


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
def create_csv_files(summarization_methods, save_path):
    # Initialize files
    # Save summaries
    summaries_columns = [
        "commit",
        "subject_file",
        "operation",
        "source_node",
        "source_node_summary",
        "source_position",
        "destination_node",
        "destination_node_summary",
        "destination_postion",
    ]
    for sm in summarization_methods:
        summaries_df = pd.DataFrame(columns=summaries_columns)
        summaries_df.to_csv(save_path / f"summaries_{sm.lower()}.csv", index=False)

    # Save metadata on build changes
    modified_build_files_columns = [
        "commit_hash",
        "file_dir",
        "file_name",
        "build_language",
        "file_action",
        "before_path",
        "after_path",
        "saved_as",
        "has_gumtree_error",
        "elapsed_time",
    ]
    modified_build_files_df = pd.DataFrame(columns=modified_build_files_columns)
    modified_build_files_df.to_csv(save_path / "all_build_files.csv", index=False)

    # Save metadata on all changes
    all_commits_columns = [
        "commit_hash",
        "chronological_commit_order",
        "commit_parents",
        "has_build",
        "has_nonbuild",
        "is_missing",
        "elapsed_time",
    ]
    all_commits_df = pd.DataFrame(columns=all_commits_columns)
    all_commits_df.to_csv(save_path / "all_commits.csv", index=False)
