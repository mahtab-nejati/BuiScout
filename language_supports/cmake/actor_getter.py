from utils.visitors import NodeVisitor


class ActorGetter(NodeVisitor):

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
    reach_impacting_types = [
        "block_definition",
        "foreach_clause",
        "if_clause",
        "elseif_clause",
        "else_clause",
        "while_clause",
    ]
    callable_definer_types = [
        "function_definition",
        "macro_definition",
    ]
    code_block_types = [
        "block_definition",
        "foreach_clause",
        "endforeach_clause",
    ]
    conditional_types = [
        "if_clause",
        "elseif_clause",
        "else_clause",
        "endif_clause",
        "while_clause",
        "endwhile_clause",
    ]
    argument_actor_types = [
        "normal_command",
        "function_definition",
        "macro_definition",
        "block_definition",
        "foreach_clause",
        "endforeach_clause",
        "if_clause",
        "elseif_clause",
        "else_clause",
        "endif_clause",
        "while_clause",
        "endwhile_clause",
    ]

    def generic_visit(self, node_data):
        if node_data["type"] == "normal_command":
            command_identifier = self.ast.get_data(
                self.ast.get_children_by_type(node_data, "identifier")
            )["content"].upper()
            if command_identifier in self.BUILT_IN_COMMANDS:
                return node_data, "built_in"
            else:
                return (node_data, "user_defined")
        elif node_data["type"] in self.callable_definer_types:
            return node_data, "callable_definer"
        elif node_data["type"] in self.code_block_types:
            return node_data, "code_block"
        elif node_data["type"] in self.conditional_types:
            return node_data, "conditional"

        actor_node_data = max(
            filter(
                lambda ancestor_data: ancestor_data["type"]
                in self.argument_actor_types,
                self.ast.get_ancestors(node_data).values(),
            ),
            key=lambda ancestor_data: ancestor_data["level"],
        )
        return self.generic_visit(actor_node_data)
