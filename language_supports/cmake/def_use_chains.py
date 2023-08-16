import data_flow_analysis as cm
from utils.configurations import PATH_RESOLUTIONS
from utils.exceptions import MissingArgumentsException, DebugException


class DefUseChains(cm.DefUseChains):
    manual_resolution = PATH_RESOLUTIONS

    def get_expected_arguments_node_data(self, command_node_data, command_id):
        """
        Retruns the "arguments" node's node_data (the parent of the list of arguments).
        Throws MissingArgumentsException if the node does not exist.
        """
        arguments_node_data = self.ast.get_data(
            self.ast.get_children_by_type(command_node_data, "arguments")
        )
        if not arguments_node_data:
            raise MissingArgumentsException(
                command_id, self.ast.get_location(command_node_data)
            )
        return arguments_node_data

    def get_sorted_arguments_data_list(self, command_node_data, command_id):
        """
        Returns the list of argument nodes' node_data of the command node, sorted by position.
        """
        # Check for MissingArgumentsException
        arguments_node_data = self.get_expected_arguments_node_data(
            command_node_data, command_id
        )

        # node_data of each argument, positionally sorted
        return sorted(
            self.ast.get_children(arguments_node_data).values(),
            key=lambda argument_node_data: argument_node_data["s_pos"],
        )

    def get_manually_resolved_path(self, file_path):
        resolved_path_item = list(
            filter(
                lambda item: (item["caller_file_path"] in [self.ast.file_path, "*"])
                and (item["callee_file_path"] == file_path),
                self.manual_resolution,
            )
        )
        if len(resolved_path_item) == 1:
            return resolved_path_item[0]["callee_resolved_path"]
        if len(resolved_path_item) > 1:
            raise DebugException(f"Multiple manual resolutions: {resolved_path_item}")
        return None

    def resolve_included_file_path_best_effort(self, file_path):
        resolution = self.get_manually_resolved_path(file_path.replace(" ", ""))
        if resolution:
            return resolution

        candidate_path = file_path.replace(" ", "")
        candidate_path = candidate_path.split("}")[-1]
        if not candidate_path:
            return None

        current_directory = self.sysdiff.get_file_directory(self.ast.file_path)

        if candidate_path in self.sysdiff.file_data:
            return candidate_path

        if candidate_path + ".cmake" in self.sysdiff.file_data:
            return candidate_path + ".cmake"

        if candidate_path.rstrip("/") + "/CMakeLists.txt" in self.sysdiff.file_data:
            return candidate_path.rstrip("/") + "/CMakeLists.txt"

        if (
            current_directory + candidate_path.lstrip("/") + ".cmake"
            in self.sysdiff.file_data
        ):
            return current_directory + candidate_path.lstrip("/") + ".cmake"

        if (
            current_directory + candidate_path.strip("/") + "/CMakeLists.txt"
            in self.sysdiff.file_data
        ):
            return current_directory + candidate_path.rstrip("/") + "/CMakeLists.txt"

        file_keys = list(self.sysdiff.file_data.keys())

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    candidate_path.rstrip("/") + "/CMakeLists.txt"
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0]
        elif len(desparate_list) > 1:
            return desparate_list

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    "/" + candidate_path.lstrip("/") + ".cmake"
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0]
        elif len(desparate_list) > 1:
            return desparate_list

        return None

    def resolve_add_subdirectory_file_path_best_effort(self, file_path):
        resolution = self.get_manually_resolved_path(file_path)
        if resolution:
            return resolution

        candidate_path = file_path.replace(" ", "")
        candidate_path = candidate_path.split("}")[-1]
        if not candidate_path:
            return None

        current_directory = self.sysdiff.get_file_directory(self.ast.file_path)

        if candidate_path.rstrip("/") + "/CMakeLists.txt" in self.sysdiff.file_data:
            return candidate_path.rstrip("/") + "/CMakeLists.txt"

        if (
            current_directory + candidate_path.strip("/") + "/CMakeLists.txt"
            in self.sysdiff.file_data
        ):
            return current_directory + candidate_path.rstrip("/") + "/CMakeLists.txt"

        file_keys = list(self.sysdiff.file_data.keys())

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    candidate_path.rstrip("/") + "/CMakeLists.txt"
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0]
        elif len(desparate_list) > 1:
            return desparate_list

        return None

    def visit_function_definition(self, node_data):
        self.register_new_def_point(node_data)

        # header_data = self.ast.get_data(
        #     self.ast.get_children_by_type(node_data, "function_header")
        # )

        # body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))

        return self.generic_visit(node_data)

    def visit_function_header(self, node_data):
        return self.generic_visit(node_data)

    def visit_macro_definition(self, node_data):
        self.register_new_def_point(node_data)

        # header_data = self.ast.get_data(
        #     self.ast.get_children_by_type(node_data, "macro_header")
        # )
        # body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))

        return self.generic_visit(node_data)

    def visit_macro_header(self, node_data):
        return self.generic_visit(node_data)

    def visit_if_statement(self, node_data):
        stacked_condition_count = (
            len(list(self.ast.get_children_by_type(node_data, "elseif_clause").keys()))
            + 1  # For the if_clause
        )
        self.generic_visit(node_data)

        self.remove_condition_from_reachability_stack(last_n=stacked_condition_count)
        return

    def visit_if_clause(self, node_data):
        condition_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "condition")
        )
        self.visit_conditional_expression(condition_node_data)
        self.add_condition_to_reachability_stack(condition_node_data)

        body_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "body")
        )
        if body_node_data:
            return self.generic_visit(body_node_data)

    def visit_elseif_clause(self, node_data):
        condition_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "condition")
        )
        self.visit_conditional_expression(
            condition_node_data, negate_last_condition=True
        )
        self.add_condition_to_reachability_stack(condition_node_data)

        body_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "body")
        )
        if body_node_data:
            return self.generic_visit(body_node_data)

    def visit_else_clause(self, node_data):
        condition_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "condition")
        )
        self.visit_conditional_expression(
            condition_node_data, negate_last_condition=True
        )

        body_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "body")
        )
        if body_node_data:
            return self.generic_visit(body_node_data)

    # def visit_endif_clause(self, node_data):
    #     return self.visit_conditional_expression(node_data)

    def visit_while_statement(self, node_data):
        self.generic_visit(node_data)
        self.remove_condition_from_reachability_stack(last_n=1)
        return

    def visit_while_clause(self, node_data):
        condition_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "condition")
        )
        self.visit_conditional_expression(condition_node_data)
        self.add_condition_to_reachability_stack(condition_node_data)

        body_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "body")
        )
        if body_node_data:
            return self.generic_visit(body_node_data)

    # def visit_endwhile_clause(self, node_data):
    #     return self.visit_conditional_expression(node_data)

    def visit_conditional_expression(self, node_data, negate_last_condition=False):
        if negate_last_condition:
            self.negate_last_condition_in_reachability_stack(negation_symbol="NOT")

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
            self.ast.get_children_by_type(node_data, "unquoted_argument").values(),
            key=lambda data: data["s_pos"],
        )
        for argument in arguments:
            if self.ast.unparse_subtree(argument).upper() not in operators:
                self.register_new_use_point(argument)

        return self.generic_visit(node_data)

    def visit_foreach_clause(self, node_data):
        """
        # TODO (High): Look into the scoping.
        """
        condition_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "condition")
        )
        arguments = sorted(
            filter(
                lambda argument_data: argument_data["type"] not in ["(", ")"],
                self.ast.get_children(condition_node_data).values(),
            ),
            key=lambda data: data["s_pos"],
        )
        def_node = arguments.pop(0)
        self.register_new_def_point(def_node)
        return self.generic_visit(node_data)

    # def visit_endforeach_clause(self, node_data):
    #     pass

    def visit_normal_command(self, node_data):
        command_identifier = self.ast.unparse_subtree(
            self.ast.get_data(self.ast.get_children_by_type(node_data, "identifier"))
        ).upper()
        if command_identifier.startswith("CTEST_"):
            method = f"visit_CTEST_CMDs"
        else:
            method = f"visit_{command_identifier}"
        visitor = getattr(self, method, self.visit_user_defined_normal_command)
        return visitor(node_data)

    def visit_user_defined_normal_command(self, node_data):
        self.register_new_use_point(node_data)
        return self.generic_visit(node_data)

    ############################
    ###### CMake Commands ######
    ############################
    # All functions are designed based on current latest
    # release of CMake, documentations available at:
    # https://cmake.org/cmake/help/v3.27/manual/cmake-commands.7.html

    ########## Scripting Commands:

    def visit_A(self, node_data):
        return self.generic_visit(node_data)

    def visit_BREAK(self, node_data):
        return

    def visit_CMAKE_HOST_SYSTEM_INFORMATION(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "CMAKE_HOST_SYSTEM_INFORMATION"
        )

        self.register_new_def_point(arguments[1])

        return self.generic_visit(node_data)

    def visit_CMAKE_LANGUAGE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "CMAKE_LANGUAGE")

        operation = self.ast.unparse_subtree(arguments[0]).upper()

        if operation == "GET_MESSAGE_LOG_LEVEL":
            self.register_new_def_point(arguments[1])

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() in [
                "ID_VAR",
                "GET_CALL_IDS",
                "GET_CALL",
            ]:
                self.register_new_def_point(arguments[i + 1])
                continue
            if self.ast.unparse_subtree(argument).upper() == "CALL":
                # Inspect and implement the cmake_language command with CALL keyword
                print(
                    f"Observe command for implementation (incomplete): {self.ast.unparse_subtree(node_data)}"
                )
                continue

        return self.generic_visit(node_data)

    def visit_CMAKE_MINIMUM_REQUIRED(self, node_data):
        return self.generic_visit(node_data)

    def visit_CMAKE_PARSE_ARGUMENTS(self, node_data):
        return self.generic_visit(node_data)

    def visit_CMAKE_PATH(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "CMAKE_PATH")

        operation = self.ast.unparse_subtree(arguments[0]).upper()

        current_target_operations = ["COMPARE", "CONVERT"]
        if not operation in current_target_operations:
            self.register_new_use_point(arguments[1])

        if operation == "CONVERT":
            self.register_new_def_point(arguments[3])
            return self.generic_visit(node_data)

        current_target_operations = [
            "GET",
            "HAS_ROOT_NAME",
            "HAS_ROOT_DIRECTORY",
            "HAS_ROOT_PATH",
            "HAS_FILENAME",
            "HAS_EXTENSION",
            "HAS_STEM",
            "HAS_RELATIVE_PART",
            "HAS_PARENT_PATH",
            "IS_ABSOLUTE",
            "IS_RELATIVE",
            "NATIVE_PATH",
            "HASH",
        ]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[-1])
            return self.generic_visit(node_data)

        current_target_operations = [
            "APPEND",
            "APPEND_STRING",
            "REMOVE_FILENAME",
            "REPLACE_FILENAME",
            "REMOVE_EXTENSION",
            "REPLACE_EXTENSION",
            "NORMAL_PATH",
            "RELATIVE_PATH",
            "ABSOLUTE_PATH",
        ]
        if operation in current_target_operations:
            for i, argument in enumerate(arguments):
                if self.ast.unparse_subtree(argument).upper() == "OUTPUT_VARIABLE":
                    self.register_new_def_point(arguments[i + 1])
                    break

        return self.generic_visit(node_data)

    def visit_CMAKE_POLICY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "CMAKE_POLICY")

        operation = self.ast.unparse_subtree(arguments[0]).upper()

        if operation == "GET":
            self.register_new_def_point(arguments[-1])

        return self.generic_visit(node_data)

    def visit_CONFIGURE_FILE(self, node_data):
        return self.generic_visit(node_data)

    def visit_EXECUTE_PROCESS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "EXECUTE_PROCESS")

        current_target_keywords = [
            "RESULT_VARIABLE",
            "RESULTS_VARIABLE",
            "OUTPUT_VARIABLE",
            "ERROR_VARIABLE",
        ]

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() in current_target_keywords:
                self.register_new_def_point(arguments[i + 1])

        return self.generic_visit(node_data)

    def visit_FILE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FILE")

        operation = self.ast.unparse_subtree(arguments[0]).upper()

        current_target_operations = ["GLOB", "GLOB_RECURSE", "RELATIVE_PATH"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[1])
            return self.generic_visit(node_data)

        current_target_operations = [
            "READ",
            "STRINGS",
            "TIMESTAMP",
            "SIZE",
            "READ_SYMLINK",
            "REAL_PATH",
            "TO_CMAKE_PATH",
            "TO_NATIVE_PATH",
            "MD5",
            "SHA1",
            "SHA224",
            "SHA256",
            "SHA384",
            "SHA512",
            "SHA3_224",
            "SHA3_256",
            "SHA3_384",
            "SHA3_512",
        ]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[2])

        return self.generic_visit(node_data)

    def visit_FIND_FILE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_FILE")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_FIND_LIBRARY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_LIBRARY")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_FIND_PACKAGE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_PACKAGE")

        keywords = [
            "EXACT",
            "QUIET",
            "REQUIRED",
            "COMPONENTS",
            "OPTIONAL_COMPONENTS",
            "CONFIG" "NO_MODULE",
            "GLOBAL",
            "NO_POLICY_SCOPE",
            "BYPASS_PROVIDER",
            "NAMES",
            "CONFIGS",
            "HINTS",
            "PATHS",
            "REGISTRY_VIEW",
            "PATH_SUFFIXES",
            "NO_DEFAULT_PATH",
            "NO_PACKAGE_ROOT_PATH",
            "NO_CMAKE_PATH",
            "NO_CMAKE_ENVIRONMENT_PATH",
            "NO_SYSTEM_ENVIRONMENT_PATH",
            "NO_CMAKE_PACKAGE_REGISTRY",
            "NO_CMAKE_BUILDS_PATH",
            "NO_CMAKE_SYSTEM_PATH",
            "NO_CMAKE_INSTALL_PREFIX",
            "NO_CMAKE_SYSTEM_PACKAGE_REGISTRY",
            "CMAKE_FIND_ROOT_PATH_BOTH",
            "ONLY_CMAKE_FIND_ROOT_PATH",
            "NO_CMAKE_FIND_ROOT_PATH",
        ]

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "NAMES":
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse_subtree(arg).upper() in keywords:
                        break
                    self.register_new_def_point(arg)
                return self.generic_visit(node_data)

        self.register_new_def_point(arguments[0])
        return self.generic_visit(node_data)

    def visit_FIND_PATH(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_PATH")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_FIND_PROGRAM(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_PROGRAM")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_GET_CMAKE_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "GET_CMAKE_PROPERTY")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_GET_DIRECTORY_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_DIRECTORY_PROPERTY"
        )

        self.register_new_def_point(arguments[0])

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "DEFINITION":
                print(
                    f"Observe command for implementation (incomplete): {self.ast.unparse_subtree(node_data)}"
                )

        return self.generic_visit(node_data)

    def visit_GET_FILENAME_COMPONENT(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_FILENAME_COMPONENT"
        )

        self.register_new_def_point(arguments[0])

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "PROGRAM_ARGS":
                self.register_new_def_point(arguments[i + 1])

        return self.generic_visit(node_data)

    def visit_GET_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "GET_PROPERTY")

        self.register_new_def_point(arguments[0])

        for i, argument in enumerate(arguments):
            keyword = self.ast.unparse_subtree(argument).upper()
            current_target_keywords = [
                "TARGET",
                "SOURCE",
                "TARGET_DIRECTORY",
                "INSTALL",
                "TEST",
                "CACHE",
                "PROPERTY",
            ]
            if keyword == "DIRECTORY":
                if not self.ast.unparse_subtree(argument[i + 1]).upper() == "PROPERTY":
                    self.register_new_use_point(arguments[i + 1])
            elif keyword in current_target_keywords:
                self.register_new_use_point(arguments[i + 1])

        return self.generic_visit(node_data)

    def visit_INCLUDE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "INCLUDE")

        for i, argument in enumerate(arguments[1:]):
            if self.ast.unparse_subtree(argument).upper() == "RESULT_VARIABLE":
                self.register_new_use_point(arguments[i + 1])
                break

        # For file-level analysis (No system provided)
        if self.sysdiff is None:
            return self.generic_visit(node_data)

        included_file_path = self.ast.unparse_subtree(arguments[0])
        included_file = self.resolve_included_file_path_best_effort(included_file_path)

        if included_file == self.ast.file_path:
            print(
                f"Skipping recursive resolution for {self.ast.unparse_subtree(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For manual file path resolution setup
        if isinstance(included_file, list):
            print(
                f"Multiple path found for {self.ast.unparse_subtree(node_data)}: {' , '.join(included_file)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For files that do not exist in the project
        # or files that are refered to using a variable
        if included_file is None:
            print(
                f"Cannot resolve path for {self.ast.unparse_subtree(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For manaully skipped files
        if included_file.upper() == "SKIP":
            print(
                f"Skipping manually set for {self.ast.unparse_subtree(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For files with GumTree error
        if self.sysdiff.file_data[included_file]["diff"] is None:
            print(f"Parser error for {self.ast.unparse_subtree(node_data)}")
            return self.generic_visit(node_data)

        self.ast_stack.append(self.ast)
        self.ast = getattr(self.sysdiff.file_data[included_file]["diff"], self.ast.name)

        # Working on included file
        self.generic_visit(self.ast.get_data(self.ast.root))
        self.sysdiff.set_data_flow_reach_file(self.ast.file_path, self.ast.name)
        # Finished working on included file

        self.ast = self.ast_stack.pop()
        return self.generic_visit(node_data)

    def visit_LIST(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "LIST")

        operation = self.ast.unparse_subtree(arguments[0]).upper()

        self.register_new_use_point(arguments[1])

        current_target_operations = ["LENGTH", "GET", "JOIN", "SUBLIST", "FIND"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[-1])

        current_target_operations = [
            "POP_BACK",
            "POP_FRONT",
        ]
        if operation in current_target_operations:
            if len(arguments) > 2:
                for def_node in arguments[2:]:
                    self.register_new_def_point(def_node)

        # TODO (Decision): The following commented operations modify the list
        # but do not change the content (only reordering and cleaning).
        # Do we need to consider them?
        current_target_operations = [
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
        if operation in current_target_operations:
            self.register_new_def_point(arguments[1])

        return self.generic_visit(node_data)

    def visit_MARK_AS_ADVANCED(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "MARK_AS_ADVANCED")

        keywords = ["CLEAR", "FORCE"]
        start_index = 0
        if self.ast.unparse_subtree(arguments[0]).upper() in keywords:
            start_index = 1

        for argument in arguments[start_index:]:
            self.register_new_use_point(argument)

        return self.generic_visit(node_data)

    def visit_MATH(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "MATH")

        self.register_new_def_point(arguments[1])

        return self.generic_visit(node_data)

    def visit_OPTION(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "OPTION")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_RETURN(self, node_data):
        try:
            arguments = self.get_sorted_arguments_data_list(node_data, "RETURN")
        except MissingArgumentsException:
            return self.generic_visit(node_data)

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "PROPAGATE":
                for arg in argument[i + 1 :]:
                    self.register_new_use_point(arg)

        self.generic_visit(node_data)

    def visit_SEPARATE_ARGUMENTS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "SEPARATE_ARGUMENTS")

        if len(arguments) == 1:
            self.register_new_use_point(arguments[0])

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_SET(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "SET")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_SET_DIRECTORY_PROPERTIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_DIRECTORY_PROPERTIES"
        )

        print(
            f"Observe command for implementation: {self.ast.unparse_subtree(node_data)}"
        )

    def visit_SET_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "SET_PROPERTY")

        keywords = [
            "GLOBAL",
            "DIRECTORY",
            "TARGET",
            "SOURCE",
            "TARGET_DIRECTORY",
            "INSTALL",
            "TEST",
            "CACHE",
            "APPEND",
            "APPEND_STRING",
            "PROPERTY",
        ]

        for i, argument in enumerate(arguments):
            unparsed_argument = self.ast.unparse_subtree(argument)
            if unparsed_argument == "TARGET":
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse_subtree(arg) not in keywords:
                        self.register_new_use_point(arg)
                    else:
                        break
            elif unparsed_argument == "PROPERTY":
                self.register_new_def_point(arguments[i + 1])

        return self.generic_visit(node_data)

    def visit_SITE_NAME(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "SITE_NAME")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_STRING(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "STRING")

        operation = self.ast.unparse_subtree(arguments[0])

        if operation == "REGEX":
            sub_operation = self.ast.unparse_subtree(arguments[1])
            if sub_operation == "REPLACE":
                self.register_new_def_point(arguments[4])
            else:
                self.register_new_def_point(arguments[3])
            return self.generic_visit(node_data)

        if operation == "json":
            self.register_new_def_point(arguments[1])
            if self.ast.unparse_subtree(arguments[2]) == "ERROR_VARIABLE":
                self.register_new_def_point(arguments[3])
            return self.generic_visit(node_data)

        current_target_operations = [
            "APPEND",
            "PREPEND",
            "CONCAT",
            "TIMESTAMP",
            "UUID",
            "MD5",
            "SHA1",
            "SHA224",
            "SHA256",
            "SHA384",
            "SHA512",
            "SHA3_224",
            "SHA3_256",
            "SHA3_384",
            "SHA3_512",
        ]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[1])
            return self.generic_visit(node_data)

        current_target_operations = ["JOIN", "CONFIGURE"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[2])
            return self.generic_visit(node_data)

        current_target_operations = ["FIND", "REPLACE"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[3])
            return self.generic_visit(node_data)

        current_target_operations = [
            "TOLOWER",
            "TOUPPER",
            "LENGTH",
            "SUBSTRING",
            "STRIP",
            "GENEX_STRIP",
            "REPEAT",
            "COMPARE",
            "ASCII",
            "HEX",
            "MAKE_C_IDENTIFIER",
            "RANDOM",
        ]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[-1])
            return self.generic_visit(node_data)

        return self.generic_visit(node_data)

    def visit_UNSET(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "UNSET")

        self.register_new_use_point(arguments[0])
        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    ########## Project Commands:

    def visit_ADD_COMPILE_DEFINITIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "ADD_COMPILE_DEFINITIONS"
        )

        # NOTE from documentations: Definitions are specified using the syntax VAR or VAR=value
        print(
            f"Observe command for implementation: {self.ast.unparse_subtree(node_data)}"
        )

    def visit_ADD_CUSTOM_COMMAND(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_CUSTOM_COMMAND")

        if self.ast.unparse_subtree(arguments[0]).upper() == "TARGET":
            self.register_new_use_point(arguments[1])

        return self.generic_visit(node_data)

    def visit_ADD_CUSTOM_TARGET(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_CUSTOM_TARGET")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_ADD_DEFINITIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_DEFINITIONS")

        print(
            f"Observe command for implementation: {self.ast.unparse_subtree(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_ADD_DEPENDENCIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_DEPENDENCIES")

        for argument in arguments:
            self.register_new_use_point(argument)

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_ADD_EXECUTABLE(self, node_data):
        """
        Documentation: https://cmake.org/cmake/help/v3.0/command/add_executable.html
        NOTE: Not adding sources as use points because they are either file names
        or will be variable_ref which will be caught when running generic_visit
        on node_data at the end.
        """
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_EXECUTABLE")

        self.register_new_def_point(arguments[0])

        operation = self.ast.unparse_subtree(arguments[1]).upper()

        if operation == "IMPORTED":
            # TODO: After Scoping is implemented, consider if GLOBAL keyword exists?
            pass
        elif operation == "ALIAS":
            assert len(arguments) == 3
            self.register_new_use_point(arguments[-1])

        return self.generic_visit(node_data)

    def visit_ADD_LIBRARY(self, node_data):
        """
        NOTE: Not adding sources as use points because they are either file names
        or will be variable_ref which will be caught when running generic_visit
        on node_data at the end.
        TODO: See object library and check object reference
        TODO: See imported library and check global with scoping
        """
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_LIBRARY")

        self.register_new_def_point(arguments[0])
        if len(arguments) == 1:
            return self.generic_visit(node_data)

        operation = self.ast.unparse_subtree(arguments[1]).upper()

        if operation == "ALIAS":
            assert len(arguments) == 3
            self.register_new_use_point(arguments[-1])

        return self.generic_visit(node_data)

    def visit_ADD_SUBDIRECTORY(self, node_data):
        """
        Use example:
            https://cmake.org/pipermail/cmake/2007-November/017897.html
            https://stackoverflow.com/a/6891527
            https://stackoverflow.com/a/49989597
            https://stackoverflow.com/a/48510440
        """
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_SUBDIRECTORY")

        # For file-level analysis (No system provided)
        if self.sysdiff is None:
            return self.generic_visit(node_data)

        added_directory_path = self.ast.unparse_subtree(arguments[0])
        added_file = self.resolve_add_subdirectory_file_path_best_effort(
            added_directory_path
        )

        if added_file == self.ast.file_path:
            print(
                f"Skipping recursive resolution for {self.ast.unparse_subtree(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For manual file path resolution setup
        if isinstance(added_file, list):
            print(
                f"Multiple path found for {self.ast.unparse_subtree(node_data)}: {' , '.join(added_file)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For files that do not exist in the project
        # or files that are refered to using a variable
        if added_file is None:
            print(
                f"Cannot resolve path for {self.ast.unparse_subtree(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For manaully skipped files
        if added_file.upper() == "SKIP":
            print(
                f"Skipping manually set for {self.ast.unparse_subtree(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For files with GumTree error
        if self.sysdiff.file_data[added_file]["diff"] is None:
            print(f"Parser error for {self.ast.unparse_subtree(node_data)}")
            return self.generic_visit(node_data)

        self.ast_stack.append(self.ast)
        self.ast = getattr(self.sysdiff.file_data[added_file]["diff"], self.ast.name)

        # Working on added file
        self.generic_visit(self.ast.get_data(self.ast.root))
        self.sysdiff.set_data_flow_reach_file(self.ast.file_path, self.ast.name)
        # Finished working on added file

        self.ast = self.ast_stack.pop()
        return self.generic_visit(node_data)

    def visit_ADD_TEST(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_TEST")

        # NOTE: There is an old signature at the end of documentation page.
        print(
            f"Observe command for implementation: {self.ast.unparse_subtree(node_data)}"
        )

    def visit_AUX_SOURCE_DIRECTORY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "AUX_SOURCE_DIRECTORY"
        )

        self.register_new_def_point(arguments[-1])

        return self.generic_visit(node_data)

    def visit_BUILD_COMMAND(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "BUILD_COMMAND")

        self.register_new_def_point(arguments[0])

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "TARGET":
                self.register_new_use_point(arguments[i + 1])
                break

        return self.generic_visit(node_data)

    def visit_CREATE_TEST_SOURCELIST(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "CREATE_TEST_SOURCELIST"
        )

        print(
            f"Observe command for implementation: {self.ast.unparse_subtree(node_data)}"
        )

    def visit_DEFINE_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "DEFINE_PROPERTY")

        self.register_new_def_point(arguments[2])

        if (
            self.ast.unparse_subtree(arguments[-2]).upper()
            == "INITIALIZE_FROM_VARIABLE"
        ):
            self.register_new_def_point(arguments[-1])

        return self.generic_visit(node_data)

    def visit_EXPORT(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "EXPORT")

        operation = self.ast.unparse_subtree(arguments[0]).upper()

        keywords = [
            "NAMESPACE",
            "APPEND",
            "FILE",
            "EXPORT_LINK_INTERFACE_LIBRARIES",
            "CXX_MODULES_DIRECTORY",
            "ANDROID_MK",
        ]
        if operation == "TARGETS":
            for argument in arguments[1:]:
                if self.ast.unparse_subtree(argument).upper() in keywords:
                    break
                else:
                    self.register_new_use_point(argument)
        else:
            self.register_new_def_point(arguments[1])

        return self.generic_visit(node_data)

    def visit_FLTK_WRAP_UI(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FLTK_WRAP_UI")

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_GET_SOURCE_FILE_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_SOURCE_FILE_PROPERTY"
        )

        self.register_new_def_point(arguments[0])
        self.register_new_use_point(arguments[-1])

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "TARGET_DIRECTORY":
                self.register_new_use_point(arguments[i + 1])
                break

        return self.generic_visit(node_data)

    def visit_GET_TARGET_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_TARGET_PROPERTY"
        )

        self.register_new_def_point(arguments[0])
        self.register_new_use_point(arguments[1])
        self.register_new_use_point(arguments[-1])

        return self.generic_visit(node_data)

    def visit_GET_TEST_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "GET_TEST_PROPERTY")

        self.register_new_use_point(arguments[0])
        self.register_new_use_point(arguments[1])
        self.register_new_def_point(arguments[-1])

        return self.generic_visit(node_data)

    def visit_INCLUDE_EXTERNAL_MSPROJECT(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "INCLUDE_EXTERNAL_MSPROJECT"
        )

        self.register_new_def_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_INSTALL(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "INSTALL")

        operation = self.ast.unparse_subtree(arguments[0]).upper()

        current_target_keywords = [
            "EXPORT",
            "RUNTIME_DEPENDENCIES",
            "RUNTIME_DEPENDENCY_SET",
            "LIBRARY",
            "RUNTIME",
            "OBJECTS",
            "FRAMEWORK",
            "BUNDLE",
            "PRIVATE_HEADER",
            "PUBLIC_HEADER",
            "RESOURCE",
            "FILE_SET",
            "CXX_MODULES_BMI",
            "DESTINATION",
            "PERMISSIONS",
            "CONFIGURATIONS",
            "COMPONENT",
            "NAMELINK_COMPONENT",
            "OPTIONAL",
            "EXCLUDE_FROM_ALL",
            "NAMELINK_ONLY",
            "NAMELINK_SKIP",
            "INCLUDES",
            "DESTINATION",
        ]

        current_target_operations = ["TARGETS", "IMPORTED_RUNTIME_ARTIFACTS"]
        if operation in current_target_operations:
            for argument in arguments[1:]:
                if (
                    self.ast.unparse_subtree(argument).upper()
                    in current_target_keywords
                ):
                    break
                self.register_new_use_point(argument)

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse_subtree(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_REMOVE_DEFINITIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "REMOVE_DEFINITIONS")

        print(
            f"Observe command for implementation: {self.ast.unparse_subtree(node_data)}"
        )

    def visit_SET_SOURCE_FILES_PROPERTIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_SOURCE_FILES_PROPERTIES"
        )

        print(
            f"Observe command for implementation: {self.ast.unparse_subtree(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_SET_TARGET_PROPERTIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_TARGET_PROPERTIES"
        )

        for argument in arguments:
            if self.ast.unparse_subtree(argument).upper() == "PROPERTIES":
                break
            self.register_new_use_point(argument)
            self.register_new_def_point(argument)

        return self.generic_visit(node_data)

    def visit_SET_TESTS_PROPERTIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_TESTS_PROPERTIES"
        )

        print(
            f"Observe command for implementation: {self.ast.unparse_subtree(node_data)}"
        )

    def visit_TARGET_COMPILE_DEFINITIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_DEFINITIONS"
        )

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TARGET_COMPILE_FEATURES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_FEATURES"
        )

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TARGET_COMPILE_OPTIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_OPTIONS"
        )

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TARGET_INCLUDE_DIRECTORIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_INCLUDE_DIRECTORIES"
        )

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TARGET_LINK_DIRECTORIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_DIRECTORIES"
        )

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TARGET_LINK_LIBRARIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_LIBRARIES"
        )

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TARGET_LINK_OPTIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_OPTIONS"
        )

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TARGET_PRECOMPILE_HEADERS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_PRECOMPILE_HEADERS"
        )

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TARGET_SOURCES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "TARGET_SOURCES")

        self.register_new_use_point(arguments[0])

        return self.generic_visit(node_data)

    def visit_TRY_COMPILE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "TRY_COMPILE")

        self.register_new_def_point(arguments[0])

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "TARGET":
                self.register_new_use_point(arguments[i + 1])
                continue
            if self.ast.unparse_subtree(argument).upper() == "SOURCE_FROM_VAR":
                self.register_new_use_point(arguments[i + 2])
                continue
            if self.ast.unparse_subtree(argument).upper() == "OUTPUT_VARIABLE":
                self.register_new_def_point(arguments[i + 1])
                continue
            if self.ast.unparse_subtree(argument).upper() == "COPY_FILE_ERROR":
                self.register_new_def_point(arguments[i + 1])
                continue

        return self.generic_visit(node_data)

    def visit_TRY_RUN(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "TRY_RUN")

        self.register_new_def_point(arguments[0])
        self.register_new_def_point(arguments[1])

        current_target_keywords = [
            "COMPILE_OUTPUT_VARIABLE",
            "COPY_FILE_ERROR",
            "RUN_OUTPUT_VARIABLE",
            "RUN_OUTPUT_STDOUT_VARIABLE",
            "RUN_OUTPUT_STDERR_VARIABLE",
        ]

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "SOURCE_FROM_VAR":
                self.register_new_use_point(arguments[i + 2])
                continue
            if self.ast.unparse_subtree(argument).upper() in current_target_keywords:
                self.register_new_def_point(arguments[i + 1])
                continue

        return self.generic_visit(node_data)

    ########## CTesgt Commands:

    def visit_CTEST_CMDs(self, node_data):
        """
        self.visit_normal_command(node_data) is adjusted such that all CTEST_*
        commands are redirected to this method.
        """
        arguments = self.get_sorted_arguments_data_list(node_data, "CTEST_BUILD")

        current_target_keywords = [
            "NUMBER_ERRORS",
            "NUMBER_WARNINGS",
            "RETURN_VALUE",
            "CAPTURE_CMAKE_ERROR",
            "DEFECT_COUNT",
            "BUILD_ID",
        ]

        for i, argument in enumerate(arguments):
            if self.ast.unparse_subtree(argument).upper() == "TARGET":
                self.register_new_use_point(arguments[i + 1])
                continue
            if self.ast.unparse_subtree(argument).upper() in current_target_keywords:
                self.register_new_def_point(arguments[i + 1])
                continue

        return self.generic_visit(node_data)

    ############################
    #### CMake Commands End ####
    ############################

    def visit_bracket_argument(self, node_data):
        # TODO
        # when it's def point
        # when it's use point
        # # NOTE: No generic_visit required
        # # as the inner scape sequnces, regex,
        # # and variable refs are not evaluated.
        # self.generic_visit(node_data)
        return

    def visit_quoted_argument(self, node_data):
        # TODO
        # when it's def point
        # when it's use point
        return self.generic_visit(node_data)

    def visit_unquoted_argument(self, node_data):
        # TODO
        # when it's def point
        # when it's use point
        return self.generic_visit(node_data)

    def visit_variable_ref(self, node_data):
        # TODO (High)
        self.register_new_use_point(node_data)
        # For nested variable references
        return self.generic_visit(node_data)
