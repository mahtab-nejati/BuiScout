import data_flow_analysis as cm
from utils.exceptions import MissingArgumentsException


class DefUseChains(cm.DefUseChains):
    def visit_function_definition(self, node_data):
        self.register_new_definition(node_data)

        # header_data = self.ast.get_data(
        #     self.ast.get_children_by_type(node_data, "function_header")
        # )

        # body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))

        return self.generic_visit(node_data)

    def visit_function_header(self, node_data):
        return self.generic_visit(node_data)

    def visit_macro_definition(self, node_data):
        self.register_new_definition(node_data)

        # header_data = self.ast.get_data(
        #     self.ast.get_children_by_type(node_data, "macro_header")
        # )
        # body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))

        return self.generic_visit(node_data)

    def visit_macro_header(self, node_data):
        return self.generic_visit(node_data)

    def visit_if_clause(self, node_data):
        return self.visit_conditional_expression(node_data)

    def visit_elseif_clause(self, node_data):
        return self.visit_conditional_expression(node_data)

    def visit_else_clause(self, node_data):
        return self.visit_conditional_expression(node_data)

    def visit_endif_clause(self, node_data):
        return self.visit_conditional_expression(node_data)

    def visit_while_clause(self, node_data):
        return self.visit_conditional_expression(node_data)

    def visit_endwhile_clause(self, node_data):
        return self.visit_conditional_expression(node_data)

    def visit_conditional_expression(self, node_data):
        # TODO (High): Update this and all users of this
        # after updating the grammar.js in tree-sitter-cmake
        condition_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "condition")
        )
        operators = [
            "NOT",
            "AND",
            "OR",
            "COMMAND",
            "POLICY",
            "TARGET",
            "EXISTS",
            "IS_NEWER_THAN",
            "IS_DIRECTORY",
            "IS_SYMLINK",
            "IS_ABSOLUTE",
            "MATCHES",
            "LESS",
            "GREATER",
            "EQUAL",
            "STRLESS",
            "STRGREATER",
            "STREQUAL",
            "VERSION_LESS",
            "VERSION_GREATER",
            "VERSION_EQUAL",
            "DEFINED",
            "(",
            ")",
        ]
        arguments = sorted(
            self.ast.get_children(condition_node_data).values(),
            key=lambda data: data["s_pos"],
        )
        for argument in arguments:
            if argument["content"].upper() not in operators:
                self.add_user(argument)
        return self.generic_visit(node_data)

    def visit_normal_command(self, node_data):
        command_identifier = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "identifier")
        )["content"].upper()
        method = f"visit_{command_identifier}"
        visitor = getattr(self, method, self.visit_user_defined_normal_command)
        return visitor(node_data)

    def visit_user_defined_normal_command(self, node_data):
        self.add_user(node_data)
        return self.generic_visit(node_data)

    ############################
    ###### CMake Commands ######
    ############################

    def visit_LIST(self, node_data):
        # TODO (Low): Create a new method that checks for missing arguments.
        # This is used in other parts of the code (see visit_SET).
        # Check for MissingArgumentsException
        arguments_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "arguments")
        )
        if not arguments_node_data:
            raise MissingArgumentsException("LIST", self.ast.get_location(node_data))

        list_operation_node = self.ast.get_data(
            self.ast.get_child_by_order(arguments_node_data, 0)
        )
        list_operation = self.ast.unparse_subtree(list_operation_node).upper()

        # The following operations defined a variable as the last argument
        output_var_definer = ["LENGTH", "GET", "JOIN", "SUBLIST", "FIND"]
        if list_operation in output_var_definer:
            def_node = self.ast.get_data(
                self.ast.get_child_by_order(arguments_node_data, -1)
            )
            self.register_new_definition(def_node)
            return self.generic_visit(node_data)

        # The following operations affect the list and define zero or more variables as the ast arguments
        multi_output_var_definer = [
            "POP_BACK",  # Affect the list and generate multiple output vars
            "POP_FRONT",  # Affect the list and generate multiple output vars
        ]
        if list_operation in multi_output_var_definer:
            def_nodes = filter(
                lambda def_node_data: def_node_data["id"] == list_operation_node["id"],
                self.ast.get_children(arguments_node_data).values(),
            )
            for def_node in def_nodes:
                self.register_new_definition(def_node)
            return self.generic_visit(node_data)

        # # TODO (Decision): The following commented operations modify the list
        # # but do not change the content (only reordering and cleaning).
        # # Do we need to consider them?
        # The following operations only affect the list itself
        modifier_oprator = [
            "APPEND",
            "FILTER",
            "INSERT",
            "PREPEND",
            "REMOVE_ITEM",
            "REMOVE_AT",
            # "REMOVE_DUPLICATES",
            "TRANSFORM",
            # "REVERSE",
            # "SORT",
        ]
        if list_operation in modifier_oprator:
            def_node = self.ast.get_data(
                self.ast.get_child_by_order(arguments_node_data, 1)
            )
            self.register_new_definition(def_node)
            return self.generic_visit(node_data)

        return self.generic_visit(node_data)

    def visit_OPTION(self, node_data):
        # TODO (Low): Create a new method that checks for missing arguments.
        # This is used in other parts of the code (see visit_LIST).
        # Check for MissingArgumentsException
        arguments_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "arguments")
        )
        if not arguments_node_data:
            raise MissingArgumentsException("OPTION", self.ast.get_location(node_data))

        def_node = self.ast.get_data(
            self.ast.get_child_by_order(arguments_node_data, 0)
        )
        self.register_new_definition(def_node)
        # TODO (Medium): Identify impact!
        return self.generic_visit(node_data)

    def visit_SET(self, node_data):
        # TODO (Low): Create a new method that checks for missing arguments.
        # This is used in other parts of the code (see visit_LIST).
        # Check for MissingArgumentsException
        arguments_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "arguments")
        )
        if not arguments_node_data:
            raise MissingArgumentsException("SET", self.ast.get_location(node_data))

        def_node = self.ast.get_data(
            self.ast.get_child_by_order(arguments_node_data, 0)
        )
        self.register_new_definition(def_node)
        # TODO (Medium): Identify impact!
        return self.generic_visit(node_data)

    def visit_INCLUDE(self, node_data):
        # For file-level analysis
        if self.sysdiff is None:
            return self.generic_visit(node_data)

        # The included path
        included_file_path = self.ast.get_data(
            self.ast.get_child_by_order(
                self.ast.get_data(
                    self.ast.get_children_by_type(node_data, "arguments")
                ),
                0,
            )
        )["content"]

        # For files that do not exist in the project
        # or files that are refered to using a variable (CAVEAT)
        if included_file_path not in self.sysdiff.file_data:
            return self.generic_visit(node_data)

        # For files with GumTree error
        if self.sysdiff.file_data[included_file_path]["diff"] is None:
            return self.generic_visit(node_data)

        self.ast_stack.append(self.ast)
        self.ast = getattr(
            self.sysdiff.file_data[included_file_path]["diff"], self.ast.name
        )

        # Working on included file
        self.generic_visit(self.ast.get_data(self.ast.root))
        # Finished working on included file

        self.ast = self.ast_stack.pop()
        return self.generic_visit(node_data)

    ############################
    #### CMake Commands End ####
    ############################

    def visit_bracket_argument(self, node_data):
        # TODO
        # when it's def point
        #  when it's use point
        # # NOTE: No generic_visit required
        # # as the inner scape sequnces, regex,
        # # and variable refs are not evaluated.
        # self.generic_visit(node_data)
        return

    def visit_quoted_argument(self, node_data):
        # TODO
        # when it's def point
        #  when it's use point
        return self.generic_visit(node_data)

    def visit_unquoted_argument(self, node_data):
        # TODO
        # when it's def point
        #  when it's use point
        return self.generic_visit(node_data)

    def visit_variable_ref(self, node_data):
        # TODO (High)
        self.add_user(node_data)
        return
