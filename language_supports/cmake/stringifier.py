from utils.visitors import NodeVisitor


class Stringifier(NodeVisitor):
    def generic_visit(self, node_data):
        return f'***{node_data["type"]}***'

    def visit_source_file(self, node_data):
        return node_data["type"]

    def visit_normal_command(self, node_data):
        identifier = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "identifier")
        )["content"].upper()
        return node_data["type"] + ' "' + identifier + '"'

    def visit_if_statement(self, node_data):
        conditional_branch_count = (
            len(self.ast.get_children_by_type(node_data, "elseif_clause")) + 1
        )  # +1 becuase of if_clause
        default_branch = (
            "a" if self.ast.get_children_by_type(node_data, "else_clause") else "no"
        )  # is there is an else_clause
        return (
            node_data["type"]
            + " with "
            + str(conditional_branch_count)
            + " conditional branche(s) and "
            + default_branch
            + " default branch"
        )

    def visit_foreach_statement(self, node_data):
        foreach_clause_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "foreach_clause")
        )
        body_data = self.ast.get_data(
            self.ast.get_children_by_type(foreach_clause_data, "body")
        )
        if body_data:  # body is an optional node ased on the grammar
            return (
                node_data["type"]
                + " with "
                + str(len(list(self.ast.get_children(body_data))))
                + " statement(s) in its body"
            )
        else:
            return node_data["type"] + " with empty body"

    def visit_while_statement(self, node_data):
        while_clause_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "while_clause")
        )
        body_data = self.ast.get_data(
            self.ast.get_children_by_type(while_clause_data, "body")
        )
        if body_data:  # body is an optional node ased on the grammar
            return (
                node_data["type"]
                + " with "
                + str(len(list(self.ast.get_children(body_data))))
                + " statement(s) in its body"
            )
        else:
            return node_data["type"] + " with empty body"

    def visit_function_definition(self, node_data):
        function_header_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "function_header")
        )
        identifier = self.ast.get_data(
            self.ast.get_children_by_type(function_header_data, "identifier")
        )["content"].upper()
        body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))
        if body_data:  # body is an optional node ased on the grammar
            return (
                node_data["type"]
                + " "
                + identifier
                + " with "
                + str(len(list(self.ast.get_children(body_data))))
                + " statement(s) in its body"
            )
        else:
            return node_data["type"] + " with empty body"

    def visit_macro_definition(self, node_data):
        macro_header_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "macro_header")
        )
        identifier = self.ast.get_data(
            self.ast.get_children_by_type(macro_header_data, "identifier")
        )["content"].upper()
        body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))
        if body_data:  # body is an optional node ased on the grammar
            return (
                node_data["type"]
                + " "
                + identifier
                + " with "
                + str(len(list(self.ast.get_children(body_data))))
                + " statement(s) in its body"
            )
        else:
            return node_data["type"] + " with empty body"

    def visit_block_definition(self, node_data):
        body_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "body")
        )  # does not have and identifier
        if body_data:  # body is an optional node ased on the grammar
            return (
                node_data["type"]
                + " with "
                + str(len(list(self.ast.get_children(body_data))))
                + " statement(s) in its body"
            )
        else:
            return node_data["type"] + " with empty body"

    def visit_arguments(self, node_data):
        parent_data = self.ast.get_data(
            self.ast.get_parent(node_data)
        )  # can be function/macro_header or normal_command
        identifier = self.ast.get_data(
            self.ast.get_children_by_type(parent_data, "identifier")
        )["content"].upper()
        if "header" in parent_data["type"]:  # parent is function/macro_header
            parent_data = self.ast.get_data(self.ast.get_parent(parent_data))
        else:  # parent is normal_command
            pass
        return (
            node_data["type"] + " of " + parent_data["type"] + ' "' + identifier + '"'
        )

    def visit_identifier(self, node_data):
        parent_data = self.ast.get_data(
            self.ast.get_parent(node_data)
        )  # can be function/macro_header or normal_command
        if "header" in parent_data["type"]:  # parent is function/macro_header
            parent_data = self.ast.get_data(
                self.ast.get_parent(parent_data)
            )  # grab grandparent instead of parent for clarity
        return (
            node_data["type"]
            + f' "{node_data["content"].upper()}" of '
            + parent_data["type"]
        )

    def visit_elseif_clause(self, node_data):
        body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))
        if body_data:  # body is an optional node ased on the grammar
            return (
                node_data["type"]
                + " conditional branch with "
                + str(len(list(self.ast.get_children(body_data))))
                + " statement(s) in its body"
            )
        else:
            return node_data["type"] + " conditional branch with empty body"

    def visit_else_clause(self, node_data):
        body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))
        if body_data:  # body is an optional node ased on the grammar
            return (
                node_data["type"]
                + " default branch with "
                + str(len(list(self.ast.get_children(body_data))))
                + " statement(s) in its body"
            )
        else:
            return node_data["type"] + " conditional branch with empty body"

    def visit_condition(self, node_data):
        parent_data = self.ast.get_data(
            self.ast.get_parent(node_data)
        )  # can be if/elseif/else/while/foreach_clause (and their end equivalent)
        return node_data["type"] + " of " + parent_data["type"]

    def visit_body(self, node_data):
        # parent can be if/elseif/else/while/foreach_clasue or function/macro/block_definition
        parent_data = self.ast.get_data(self.ast.get_parent(node_data))
        if parent_data["type"] in [
            "function_definition",
            "macro_definition",
        ]:  # function/macro_definition have identifiers
            parent_header_data = self.ast.get_data(
                self.ast.get_children_by_type(
                    parent_data,
                    "function_header"
                    if parent_data["type"] == "function_definition"
                    else "macro_header",
                )
            )
            parent_identifier = self.ast.get_data(
                self.ast.get_children_by_type(parent_header_data, "identifier")
            )["content"].upper()
            return (
                node_data["type"]
                + " of "
                + parent_data["type"]
                + f' "{parent_identifier}"'
            )
        else:
            return node_data["type"] + " of " + parent_data["type"]

    def visit_bracket_argument(self, node_data):
        return self.visit_argument_types(node_data)

    def visit_quoted_argument(self, node_data):
        return self.visit_argument_types(node_data)

    def visit_unquoted_argument(self, node_data):
        return self.visit_argument_types(node_data)

    def visit_argument_types(self, node_data):  # RECURSIVE for parent node
        parsed_argument = self.ast.unparse(node_data)
        parent_data = node_data
        while parent_data["type"] not in [
            "arguments",
            "condition",
        ]:  # must be condition or arguments
            parent_data = self.ast.get_data(self.ast.get_parent(parent_data))
        return node_data["type"] + f" {parsed_argument} in " + self.visit(parent_data)

    def visit_variable_ref(self, node_data):
        return self.visit_variables(node_data)

    def visit_variable(self, node_data):
        return self.visit_variables(node_data)

    def visit_normal_var(self, node_data):
        return self.visit_variables(node_data)

    def visit_env_var(self, node_data):
        return self.visit_variables(node_data)

    def visit_cache_var(self, node_data):
        return self.visit_variables(node_data)

    def visit_quoted_element(self, node_data):
        return self.visit_variables(node_data)

    def visit_gen_exp(self, node_data):
        return self.visit_variables(node_data)

    def visit_escape_sequence(self, node_data):
        return self.visit_variables(node_data)

    def visit_variables(self, node_data):
        parsed_node = self.ast.unparse(node_data)
        parent_data = node_data
        while parent_data["type"] not in [
            "arguments",
            "condition",
        ]:  # must be condition or arguments
            parent_data = self.ast.get_data(self.ast.get_parent(parent_data))
        return node_data["type"] + f" {parsed_node} in " + self.visit(parent_data)
