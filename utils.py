# Helpers
def file_is_build(file_name, patterns=[]):
    if file_name is None:
        print("WEIRD")
    return file_name.endswith(tuple(patterns))

def get_processed_path(modified_file):
    if modified_file.new_path is not None:
        return modified_file.new_path.replace("/", "__")
    elif modified_file.old_path is not None:
        return modified_file.old_path.replace("/", "__")
    elif modified_file.filename is not None:
        return modified_file.filename.replace("/", "__")
    else:
        return None

def write_source_code(file_path, source_code):
    if source_code is None:
        source_code = ""
    with open(file_path, 'w') as f:
        f.write(source_code)

# helper to find start and end index of a word
def find_word_indexes(string, word):
    # Find the index of the word in the string
    index = string.find(word)

    # Compute the start and end indexes of the word in the string
    start_index = index
    end_index = index + len(word) - 1

    return (start_index, end_index)

# helper to clean the label of nodes
def parse_label(label):
    # init the dictionary
    content = {}

    # find start and end indexes
    _ , end_type = find_word_indexes(label, "GumTreeType")
    start_content, end_content = find_word_indexes(label, "GumTreeContent")
    start_pos, end_pos = find_word_indexes(label, "GumTreeSPos")
    start_end, end_end = find_word_indexes(label, "GumTreeEPos")

    content["type"] = label[end_type+2:start_content].strip()
    content["content"] = label[end_content+2:start_pos].strip()
    content["s_pos"] = label[end_pos+2:start_end].strip()
    content["e_pos"] = label[end_end+2:].strip()
    
    return content