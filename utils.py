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