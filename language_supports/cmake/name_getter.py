from utils.visitors import NodeVisitor


class NameGetter(NodeVisitor):
    types_with_body_child = [
        "if_clause",
        "elseif_clause",
        "else_clause",
        "while_clause",
        "foreach_clause",
    ]

    def generic_visit(self, node_data):
        return self.ast.unparse_subtree(node_data)

    def visit_if_statement(self, node_data):
        return "<IF_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_if_clause(self, node_data):
        return "<IF_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_elseif_clause(self, node_data):
        return "<IF_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_else_clause(self, node_data):
        return "<IF_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_while_statement(self, node_data):
        return "<WHILE_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_while_clause(self, node_data):
        return "<WHILE_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_foreach_statement(self, node_data):
        return "<FOREACH_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_conditional_statement(self, node_data):
        return self.ast.unparse_subtree(node_data, masked_types=["body"])

    def visit_function_definition(self, node_data):
        header = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "function_header")
        )
        return (
            "<CMD>"
            + self.ast.get_data(self.ast.get_children_by_type(header, "identifier"))[
                "content"
            ].upper()
        )

    def visit_macro_definition(self, node_data):
        header = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "macro_header")
        )
        return (
            "<CMD>"
            + self.ast.get_data(self.ast.get_children_by_type(header, "identifier"))[
                "content"
            ].upper()
        )

    def visit_normal_command(self, node_data):
        command_identifier = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "identifier")
        )["content"].upper()
        return f"<CMD>{command_identifier}"

    def visit_bracket_argument(self, node_data):
        """
        Documentations: https://cmake.org/cmake/help/latest/manual/cmake-language.7.html#bracket-argument
            No \-escape sequences or ${variable} references are evaluated.
            This is always one argument even though it contains a ; character.
        """
        return self.generic_visit(node_data)

    def visit_quoted_argument(self, node_data):
        """
        TODO (High): quoted_argument.quoted_element: ($) => repeat1(choice($.variable_ref, $.gen_exp, $._quoted_text, $.escape_sequence))
        Documentations: https://cmake.org/cmake/help/latest/manual/cmake-language.7.html#quoted-argument
            This is always one argument even though it contains a ; character.
            Both \\-escape sequences and ${variable} references are evaluated.
        """
        return self.generic_visit(node_data)

    def visit_unquoted_argument(self, node_data):
        """
        TODO (High): unquoted_argument: ($) => prec.right(repeat1(choice($.variable_ref, $.gen_exp, $._unquoted_text, $.escape_sequence)))
        Documentations: https://cmake.org/cmake/help/latest/manual/cmake-language.7.html#unquoted-argument
            This is always one argument even though it contains a ; character.
            Both \\-escape sequences and ${variable} references are evaluated.
        """
        return self.generic_visit(node_data)

    def visit_variable_ref(self, node_data):
        """
        TODO (High): variable_ref: ($) => choice($.normal_var, $.env_var, $.cache_var)
        Documentations: https://cmake.org/cmake/help/latest/manual/cmake-language.7.html#variable-references
            Variable names are case-sensitive and may consist of almost any text
            Is evaluated inside a Quoted Argument or an Unquoted Argument.
            Variable references can nest and are evaluated from the inside out, e.g. ${outer_${inner_variable}_variable}
            An environment variable reference has the form $ENV{<variable>}.
            A cache variable reference has the form $CACHE{<variable>}.
            The if() command has a special condition syntax that allows for variable references in the short form <variable> instead of ${<variable>}.
            However, environment variables always need to be referenced as $ENV{<variable>}.
        """
        return self.visit(self.ast.get_data(self.ast.get_children(node_data)))

    def visit_normal_var(self, node_data):
        variable_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "variable")
        )
        return self.generic_visit(variable_node_data)

    def visit_env_var(self, node_data):
        variable_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "variable")
        )
        # TODO (Medium): Figure out after the scoping implementation is done
        # return "<ENV>" + self.generic_visit(variable_node_data)
        return self.generic_visit(variable_node_data)

    def visit_cache_var(self, node_data):
        variable_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "variable")
        )
        # TODO (Medium): Figure out after the scoping implementation is done
        # return "<CACHE>" + self.generic_visit(variable_node_data)
        return self.generic_visit(variable_node_data)
