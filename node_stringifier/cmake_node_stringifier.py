
ROOT_TYPE = "source_file"
# Nodes of type listed in IGNORED_TYPES
# and their entire subtree are ignored
IGNORED_TYPES = ['bracket_comment',
                 'line_comment',
                 '(', ')',
                 '{', '}',
                 '<', '>',
                 '/n', '/t',
                 '$', ';',
                 'quotation']
BASIC_TYPES = [ROOT_TYPE]


def stringify(ast, node_data, verbose=False, *args, **kwargs):
    if verbose:
        return stringify_verbose(ast, node_data)
        
    node_type = node_data['type']

    if node_type in BASIC_TYPES:
        return node_type
    
    if node_type == "normal_command":
        identifier = ast.get_data(ast.get_typed_children(node_data, 'identifier'))['content']
        return node_type + ' "' + identifier + '"'
    
    if node_type == "if_statement":
        conditional_branch_count = len(ast.get_typed_children(node_data, 'elseif_clause'))+1 # +1 becuase of if_clause
        default_branch = 'a' if ast.get_typed_children(node_data, 'else_clause') else 'no' # is there is an else_clause
        return node_type + ' with ' + str(conditional_branch_count) + \
                    ' conditional branche(s) and ' + \
                        default_branch +' default branch'
    
    if node_type == "foreach_statement": 
        foreach_clause_data = ast.get_data(ast.get_typed_children(node_data, 'foreach_clause'))
        body_data = ast.get_data(ast.get_typed_children(foreach_clause_data, 'body'))
        if body_data: # body is an optional node ased on the grammar
            return node_type + ' with ' + str(len(list(ast.get_children(body_data)))) + ' statement(s) in its body'
        else:
            return node_type + ' with empty body'
    
    if node_type == "while_statement":
        while_clause_data = ast.get_data(ast.get_typed_children(node_data, 'while_clause'))
        body_data = ast.get_data(ast.get_typed_children(while_clause_data, 'body'))
        if body_data: # body is an optional node ased on the grammar
            return node_type + ' with ' + str(len(list(ast.get_children(body_data)))) + ' statement(s) in its body'
        else:
            return node_type + ' with empty body'
    
    if node_type == "function_definition":
        function_header_data = ast.get_data(ast.get_typed_children(node_data, 'function_header'))
        identifier = ast.get_data(ast.get_typed_children(function_header_data, 'identifier'))['content']
        body_data = ast.get_data(ast.get_typed_children(node_data, 'body'))
        if body_data: # body is an optional node ased on the grammar
            return node_type + ' ' + identifier + ' with ' + str(len(list(ast.get_children(body_data)))) + ' statement(s) in its body'
        else:
            return node_type + ' with empty body'

    if node_type == "macro_definition":
        macro_header_data = ast.get_data(ast.get_typed_children(node_data, 'macro_header'))
        identifier = ast.get_data(ast.get_typed_children(macro_header_data, 'identifier'))['content']
        body_data = ast.get_data(ast.get_typed_children(node_data, 'body'))
        if body_data: # body is an optional node ased on the grammar
            return node_type + ' ' + identifier + ' with ' + str(len(list(ast.get_children(body_data)))) + ' statement(s) in its body'
        else:
            return node_type + ' with empty body'

    if node_type == "block_definition":
        body_data = ast.get_data(ast.get_typed_children(node_data, 'body')) # does not have and identifier
        if body_data: # body is an optional node ased on the grammar
            return node_type + ' ' + identifier + ' with ' + str(len(list(ast.get_children(body_data)))) + ' statement(s) in its body'
        else:
            return node_type + ' with empty body'

    if node_type == "arguments":
        parent_data = ast.get_data(ast.get_parent(node_data)) # can be function/macro_header or normal_command
        if "header" in parent_data['type']: # parent is function/macro_header 
            parent_data = ast.get_data(ast.get_parent(parent_data))
            return node_type + f' of ' + parent_data['type']
        else: # parent is normal_command
            identifier = ast.get_data(ast.get_typed_children(parent_data, 'identifier'))['content']
            return node_type + ' of ' + parent_data['type'] + ' "' + identifier + '"'
    
    if node_type == "identifier":
        parent_data = ast.get_data(ast.get_parent(node_data)) # can be function/macro_header or normal_command
        if "header" in parent_data['type']: # parent is function/macro_header
            parent_data = ast.get_data(ast.get_parent(parent_data)) # grab grandparent instead of parent for clarity
        return node_type + f' "{node_data["content"]}" of ' + parent_data['type']

    if node_type == "elseif_clause":
        body_data = ast.get_data(ast.get_typed_children(node_data, 'body'))
        if body_data: # body is an optional node ased on the grammar
            return node_type + ' conditional branch with ' + \
                str(len(list(ast.get_children(body_data)))) + ' statement(s) in its body'
        else:
            return node_type + ' conditional branch with empty body'
    
    if node_type == "else_clause":
        body_data = ast.get_data(ast.get_typed_children(node_data, 'body'))
        if body_data: # body is an optional node ased on the grammar
            return node_type + ' default branch with ' + \
                str(len(list(ast.get_children(body_data)))) + ' statement(s) in its body'
        else:
            return node_type + ' conditional branch with empty body'

    if node_type == "condition":
        parent_data = ast.get_data(ast.get_parent(node_data)) # can be if/elseif/else/while/foreach_clause (and their end equivalent)
        return node_type + ' of ' + parent_data['type']

    if node_type == "body":
        # parent can be if/elseif/else/while/foreach_clasue or function/macro/block_definition
        parent_data = ast.get_data(ast.get_parent(node_data))
        if parent_data['type'] in ['function_definition', 'macro_definition']: # function/macro_definition have identifiers
            parent_header_data = ast.get_data(ast.get_typed_children(parent_data, 
                                                                     'function_header' if parent_data['type']=='function_definition' else 'macro_header'))
            parent_identifier = ast.get_data(ast.get_typed_children(parent_header_data, 'identifier'))['content']
            return node_type + ' of ' + parent_data['type'] + f' "{parent_identifier}"'
        else:
            return node_type + ' of ' + parent_data['type']

    arguments = ["bracket_argument", "quoted_argument", "unquoted_argument"]
    if node_type in arguments: # RECURSIVE for parent node
        parsed_argument =  ast.parse_subtree(node_data)
        parent_data = node_data
        while parent_data['type'] not in ["arguments", "condition"]: # must be condition or arguments
            parent_data = ast.get_data(ast.get_parent(parent_data))
        return node_type + f' {parsed_argument} in ' + stringify(ast, parent_data)

    variables = ["variable_ref", "variable", "normal_var", "env_var", "cache_var", "quoted_element", "gen_exp", "escape_sequence"]
    if node_type in variables:
        parsed_node = ast.parse_subtree(node_data)
        parent_data = node_data
        while parent_data['type'] not in ["arguments", "condition"]: # must be condition or arguments
            parent_data = ast.get_data(ast.get_parent(parent_data))
        return node_type + f' {parsed_node} in ' + stringify(ast, parent_data)
    
    return f'****{node_type}****'

def stringify_verbose(ast, node_data, *args, **kwargs):
    pass
