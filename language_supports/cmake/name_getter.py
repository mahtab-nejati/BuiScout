from utils.visitors import NodeVisitor
from utils.exceptions import MissingArgumentsException


class NameGetter(NodeVisitor):
    def generic_visit(self, node_data):
        return self.ast.unparse(node_data)

    def visit_if_statement(self, node_data):
        return "<IF_STMNT>"
        # return "<IF_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_if_clause(self, node_data):
        return "<IF_STMNT>IF"
        # return "<IF_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_elseif_clause(self, node_data):
        return "<IF_STMNT>ELSEIF"
        # return "<IF_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_else_clause(self, node_data):
        return "<IF_STMNT>ELSE"
        # return "<IF_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_while_statement(self, node_data):
        return "<WHILE_STMNT>"
        # return "<WHILE_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_while_clause(self, node_data):
        return "<WHILE_STMNT>WHILE"
        # return "<WHILE_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_foreach_statement(self, node_data):
        return "<FOREACH_STMNT>"
        # return "<FOREACH_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_foreach_clause(self, node_data):
        return "<FOREACH_STMNT>FOREACH"
        # return "<FOREACH_STMNT>" + self.visit_conditional_statement(node_data)

    def visit_conditional_statement(self, node_data):
        return self.ast.unparse(node_data, masked_types=["body"])

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
        visitor = getattr(self, f"visit_{command_identifier}", None)
        if visitor is None:
            return f"<CMD>{command_identifier}"
        return visitor(node_data)

    def visit_bracket_argument(self, node_data):
        """
        Documentations: https://cmake.org/cmake/help/latest/manual/cmake-language.7.html#bracket-argument
            No \-escape sequences or ${variable} references are evaluated.
            This is always one argument even though it contains a ; character.
        """
        return self.generic_visit(node_data)

    def visit_quoted_argument(self, node_data):
        """
        Documentations: https://cmake.org/cmake/help/latest/manual/cmake-language.7.html#quoted-argument
            This is always one argument even though it contains a ; character.
            Both \\-escape sequences and ${variable} references are evaluated.
        """
        return self.generic_visit(node_data)

    def visit_unquoted_argument(self, node_data):
        """
        Documentations: https://cmake.org/cmake/help/latest/manual/cmake-language.7.html#unquoted-argument
            This is always one argument even though it contains a ; character.
            Both \\-escape sequences and ${variable} references are evaluated.
        """
        return self.generic_visit(node_data)

    def visit_variable_ref(self, node_data):
        """
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
        # TODO (Medium): Do we want this?
        # return "<ENV>" + self.generic_visit(variable_node_data)
        return self.generic_visit(variable_node_data)

    def visit_cache_var(self, node_data):
        variable_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "variable")
        )
        # TODO (Medium): Do we want this?
        # return "<CACHE>" + self.generic_visit(variable_node_data)
        return self.generic_visit(variable_node_data)

    ##### Special commands

    # Helpers
    def get_keyword_argument(self, command_node_data, command_id, position=0):
        arguments_node_data = self.ast.get_data(
            self.ast.get_children_by_type(command_node_data, "arguments")
        )
        if not arguments_node_data:
            raise MissingArgumentsException(
                command_id, self.ast.get_location(command_node_data)
            )
        return (
            self.ast.unparse(
                self.ast.get_data(self.ast.get_child_by_order(arguments_node_data, 0))
            )
            .upper()
            .strip()
        )

    def find_keyword_argument(self, command_node_data, command_id, keywords=[]):
        if not keywords:
            return "UNKNOWN"
        arguments_node_data = self.ast.get_data(
            self.ast.get_children_by_type(command_node_data, "arguments")
        )
        if not arguments_node_data:
            raise MissingArgumentsException(
                command_id, self.ast.get_location(command_node_data)
            )

        arguments = sorted(
            self.ast.get_children(arguments_node_data).values(),
            key=lambda argument_node_data: argument_node_data["s_pos"],
        )

        for argument in arguments:
            keyword = self.ast.unparse(argument).upper().strip()
            if keyword in keywords:
                return keyword

        return "UNKNOWN"

    # Commands
    def visit_CMAKE_LANGUAGE(self, node_data):
        operation = self.get_keyword_argument(node_data, "CMAKE_LANGUAGE")
        return f"<CMD>CMAKE_LANGUAGE/{operation}"

    def visit_CMAKE_PATH(self, node_data):
        operation = self.get_keyword_argument(node_data, "CMAKE_PATH", 0)
        if operation in ["GET", "CONVERT"]:
            sub_operation = self.get_keyword_argument(node_data, "CMAKE_PATH", 2)
            return f"<CMD>CMAKE_PATH/{operation}/{sub_operation}"

        return f"<CMD>CMAKE_PATH/{operation}"

    def visit_CMAKE_POLICY(self, node_data):
        operation = self.get_keyword_argument(node_data, "CMAKE_POLICY", 0)
        return f"<CMD>CMAKE_POLICY/{operation}"

    def visit_FILE(self, node_data):
        operation = self.get_keyword_argument(node_data, "FILE", 0)
        return f"<CMD>FILE/{operation}"

    def visit_LIST(self, node_data):
        operation = self.get_keyword_argument(node_data, "LIST", 0)
        return f"<CMD>LIST/{operation}"

    def visit_STRING(self, node_data):
        operation = self.get_keyword_argument(node_data, "STRING", 0)
        if operation == "REGEX":
            sub_operation = self.get_keyword_argument(node_data, "STRING", 2)
            return f"<CMD>STRING/{operation}/{sub_operation}"
        if operation == "JSON":
            sub_operation = self.find_keyword_argument(
                node_data,
                "STRING",
                ["GET", "TYPE", "LENGTH", "REMOVE", "MEMBER", "SET", "EQUAL"],
            )
            return f"<CMD>STRING/{operation}/{sub_operation}"
        return f"<CMD>STRING/{operation}"

    def visit_EXPORT(self, node_data):
        operation = self.get_keyword_argument(node_data, "EXPORT", 0)
        return f"<CMD>EXPORT/{operation}"

    def visit_INSTALL(self, node_data):
        operation = self.get_keyword_argument(node_data, "INSTALL", 0)
        return f"<CMD>INSTALL/{operation}"
