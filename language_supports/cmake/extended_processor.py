from utils.visitors import NodeVisitor


class ExtendedProcessor(NodeVisitor):
    """
    To skip, uncomment the generic_visit method definition below.
    """

    BUILT_IN_COMMANDS = [
        "BREAK",
        "CMAKE_HOST_SYSTEM_INFORMATION",
        "CMAKE_LANGUAGE",
        "CMAKE_MINIMUM_REQUIRED",
        "CMAKE_PARSE_ARGUMENTS",
        "CMAKE_PATH",
        "CMAKE_POLICY",
        "CONFIGURE_FILE",
        "CONTINUE",
        "EXECUTE_PROCESS",
        "FILE",
        "FIND_FILE",
        "FIND_LIBRARY",
        "FIND_PACKAGE",
        "FIND_PATH",
        "FIND_PROGRAM",
        "GET_CMAKE_PROPERTY",
        "GET_DIRECTORY_PROPERTY",
        "GET_FILENAME_COMPONENT",
        "GET_PROPERTY",
        "INCLUDE",
        "INCLUDE_GUARD",
        "LIST",
        "MARK_AS_ADVANCED",
        "MATH",
        "MESSAGE",
        "OPTION",
        "RETURN",
        "SEPARATE_ARGUMENTS",
        "SET",
        "SET_DIRECTORY_PROPERTIES",
        "SET_PROPERTY",
        "SITE_NAME",
        "STRING",
        "UNSET",
        "VARIABLE_WATCH",
        "ADD_COMPILE_DEFINITIONS",
        "ADD_COMPILE_OPTIONS",
        "ADD_CUSTOM_COMMAND",
        "ADD_CUSTOM_TARGET",
        "ADD_DEFINITIONS",
        "ADD_DEPENDENCIES",
        "ADD_EXECUTABLE",
        "ADD_LIBRARY",
        "ADD_LINK_OPTIONS",
        "ADD_SUBDIRECTORY",
        "ADD_TEST",
        "AUX_SOURCE_DIRECTORY",
        "BUILD_COMMAND",
        "CMAKE_FILE_API",
        "CREATE_TEST_SOURCELIST",
        "DEFINE_PROPERTY",
        "ENABLE_LANGUAGE",
        "ENABLE_TESTING",
        "EXPORT",
        "FLTK_WRAP_UI",
        "GET_SOURCE_FILE_PROPERTY",
        "GET_TARGET_PROPERTY",
        "GET_TEST_PROPERTY",
        "INCLUDE_DIRECTORIES",
        "INCLUDE_EXTERNAL_MSPROJECT",
        "INCLUDE_REGULAR_EXPRESSION",
        "INSTALL",
        "LINK_DIRECTORIES",
        "LINK_LIBRARIES",
        "LOAD_CACHE",
        "PROJECT",
        "REMOVE_DEFINITIONS",
        "SET_SOURCE_FILES_PROPERTIES",
        "SET_TARGET_PROPERTIES",
        "SET_TESTS_PROPERTIES",
        "SOURCE_GROUP",
        "TARGET_COMPILE_DEFINITIONS",
        "TARGET_COMPILE_FEATURES",
        "TARGET_COMPILE_OPTIONS",
        "TARGET_INCLUDE_DIRECTORIES",
        "TARGET_LINK_DIRECTORIES",
        "TARGET_LINK_LIBRARIES",
        "TARGET_LINK_OPTIONS",
        "TARGET_PRECOMPILE_HEADERS",
        "TARGET_SOURCES",
        "TRY_COMPILE",
        "TRY_RUN",
        "CTEST_BUILD",
        "CTEST_CONFIGURE",
        "CTEST_COVERAGE",
        "CTEST_EMPTY_BINARY_DIRECTORY",
        "CTEST_MEMCHECK",
        "CTEST_READ_CUSTOM_FILES",
        "CTEST_RUN_SCRIPT",
        "CTEST_SLEEP",
        "CTEST_START",
        "CTEST_SUBMIT",
        "CTEST_TEST",
        "CTEST_UPDATE",
        "CTEST_UPLOAD",
        "SUBDIRS",
    ]

    # def generic_visit(self, node_data):
    #     return

    def check_and_update_node_operation(self, node_data):
        if node_data["operation"] != "no-op":
            return self.generic_visit(node_data)

        subtree_nodes = self.ast.get_subtree_nodes(node_data)
        affected_nodes = filter(
            lambda subtree_node_data: (
                (subtree_node_data["operation"] != "no-op")
                and (
                    subtree_node_data["type"] not in self.ast.IGNORED_TYPES
                )
            ),
            subtree_nodes.values(),
        )
        for _ in affected_nodes:
            self.ast.update_node_operation(node_data, "updated")
            break

        return self.generic_visit(node_data)

    def visit_function_definition(self, node_data):
        return self.check_and_update_node_operation(node_data)

    def visit_macro_definition(self, node_data):
        return self.check_and_update_node_operation(node_data)

    def visit_normal_command(self, node_data):
        command_identifier = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "identifier")
        )["content"].upper()
        if command_identifier in self.BUILT_IN_COMMANDS:
            return self.check_and_update_node_operation(node_data)

    def visit_condition(self, node_data):
        parent_data = self.ast.get_data(self.ast.get_parent(node_data))
        if parent_data["operation"] != "no-op":
            return self.generic_visit(node_data)

        subtree_nodes = self.ast.get_subtree_nodes(node_data)
        affected_nodes = filter(
            lambda subtree_node_data: subtree_node_data["operation"] != "no-op",
            subtree_nodes.values(),
        )
        for _ in affected_nodes:
            self.ast.update_node_operation(parent_data, "updated")
            break

        return self.generic_visit(node_data)

    def visit_bracket_argument(self, node_data):
        self.visit_argument(node_data)

    def visit_quoted_argument(self, node_data):
        self.visit_argument(node_data)

    def visit_unquoted_argument(self, node_data):
        self.visit_argument(node_data)

    def visit_argument(self, node_data):
        self.check_and_update_node_operation(node_data)
        children = self.ast.get_children(node_data).values()
        for child in children:
            self.visit_argument(child)
        return
