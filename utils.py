from networkx.drawing.nx_agraph import write_dot

#################################
##### Helpers for ast_model #####
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
    
    source = from_agraph(A.get_subgraph('cluster_src\xa0'))
    source.name = "source"

    destination = from_agraph(A.get_subgraph('cluster_dst\xa0'))
    destination.name = "destination"

    matches = dict(map(lambda e: (e[0], e[1]), filter(lambda e: e.attr.get('style')=='dashed', A.edges())))

    A.clear()
    return source, destination, matches

# Word locater for parsing labels
def find_word_indexes(text, word):
    # Find the start index of the word in the text
    start_index = text.find(word)
    return (start_index, start_index + len(word) - 1)

# GumTree node label parser
def parse_label(label):
    # Locate properties
    _ , end_type = find_word_indexes(label, "GumTreeType")
    start_content, end_content = find_word_indexes(label, "GumTreeContent")
    start_pos, end_pos = find_word_indexes(label, "GumTreeSPos")
    start_end, end_end = find_word_indexes(label, "GumTreeEPos")

    return {"type": label[end_type+2:start_content].strip(),
            "content":label[end_content+2:start_pos].strip(),
            "s_pos": label[end_pos+2:start_end].strip(),
            "e_pos": label[end_end+2:].strip()}

#################################
######## Helpers for run ########
#################################
# Check if the modified file a build specification
def file_is_build(file_name, patterns=[]):
    if file_name is None:
        print("WEIRD PYDRILLER FILENAME")
    return file_name.endswith(tuple(patterns))

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
    with open(file_path, 'w') as f:
        f.write(source_code)
