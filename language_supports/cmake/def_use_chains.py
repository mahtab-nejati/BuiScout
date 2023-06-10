import data_flow_analysis as cm


class DefUseChains(cm.DefUseChains):
    def visit_function_definition(self, node_data):
        self.register_new_definition(node_data)

        header_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "function_header")
        )

        body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))

        return self.generic_visit(node_data)

    def visit_function_header(self, node_data):
        return self.generic_visit(node_data)

    def visit_macro_definition(self, node_data):
        definition = self.register_new_definition(node_data)

        header_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "macro_header")
        )
        body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))
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

        list_operation = self.ast.unparse_subtree(
            self.ast.get_data(self.ast.get_child_by_order(arguments_node_data, 0))
        ).upper()
        modifier_oprations = [
            "APPEND",
            "INSERT",
            "REMOVE_ITEM",
            "REMOVE_AT",
            # # TODO (Decision): The following three operations modify the list
            # # but do not change the content (only reordering and cleaning).
            # # Do we need to consider them?
            # "REMOVE_DUPLICATES",
            # "REVERSE",
            # "SORT",
        ]
        if list_operation in modifier_oprations:
            def_node = self.ast.get_data(
                self.ast.get_child_by_order(arguments_node_data, 1)
            )
            self.register_new_definition(def_node)
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
