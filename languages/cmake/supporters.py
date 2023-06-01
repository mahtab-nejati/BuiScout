from utils.visitors import NodeVisitor
from utils.exceptions import MissingArgumentsException
import data_flow_analysis.chain_model as cm

# TODO (VVV_High): logical target name such as those created by the add_executable(), add_library(), or add_custom_target() commands

ROOT_TYPE = "source_file"
# Nodes of type listed in IGNORED_TYPES
# and their entire subtree are ignored
IGNORED_TYPES = [
    "bracket_comment",
    "line_comment",
    "(",
    ")",
    "{",
    "}",
    "<",
    ">",
    "\\n",
    "\\t",
    "$",
    ";",
    ":",
    "quotation",
]
BASIC_TYPES = [ROOT_TYPE]


class NameGetter(NodeVisitor):
    def generic_visit(self, node_data):
        return self.ast.unparse_subtree(node_data)

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
        method = f"visit_{command_identifier}"
        visitor = getattr(self, method, self.visit_user_defined_normal_command)
        return visitor(node_data)

    def visit_user_defined_normal_command(self, node_data):
        return (
            "<CMD>"
            + self.ast.get_data(self.ast.get_children_by_type(node_data, "identifier"))[
                "content"
            ].upper()
        )

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
