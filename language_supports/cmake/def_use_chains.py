from pathlib import Path
import data_flow_analysis as cm
from utils.configurations import PATH_RESOLUTIONS, ROOT_PATH, ROOT_FILE
from utils.exceptions import MissingArgumentsException, DebugException

# CMake Modules based on the official documentation
# https://cmake.org/cmake/help/v3.27/manual/cmake-modules.7.html
with open(ROOT_PATH / "language_supports/cmake/cmake_modules.txt", "r") as f:
    CMAKE_MODULES = list(map(lambda entry: entry.strip("\n"), f.readlines()))


class DefUseChains(cm.DefUseChains):
    manual_resolution = PATH_RESOLUTIONS
    exclude_resolutions = CMAKE_MODULES

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

    def get_manually_resolved_path(self, file_path_node):
        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")

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

    def resolve_included_file_path_best_effort(self, file_path_node):
        resolution = self.get_manually_resolved_path(file_path_node)
        if resolution:
            return resolution

        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")
        candidate_path = file_path.split("}")[-1]
        if not candidate_path:
            return None
        candidate_path = candidate_path.strip("./")

        current_directory = (
            self.sysdiff.get_file_directory(self.ast.file_path).strip("/") + "/"
        )
        if current_directory == "/":
            current_directory = ""

        if current_directory + candidate_path in self.sysdiff.file_data:
            return current_directory + candidate_path

        if current_directory + candidate_path + ".cmake" in self.sysdiff.file_data:
            return current_directory + candidate_path + ".cmake"

        if candidate_path in self.sysdiff.file_data:
            return candidate_path

        if candidate_path + ".cmake" in self.sysdiff.file_data:
            return candidate_path + ".cmake"

        file_keys = list(
            map(
                lambda file_key: ("/" + file_key.strip("/")),
                self.sysdiff.file_data.keys(),
            )
        )

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    "/" + current_directory + candidate_path
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return list(map(lambda file_key: file_key.strip("/"), desparate_list))

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    "/" + current_directory + candidate_path + ".cmake"
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return list(map(lambda file_key: file_key.strip("/"), desparate_list))

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith("/" + candidate_path),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return list(map(lambda file_key: file_key.strip("/"), desparate_list))

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith("/" + candidate_path + ".cmake"),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return list(map(lambda file_key: file_key.strip("/"), desparate_list))

        return None

    def resolve_add_subdirectory_file_path_best_effort(self, file_path_node):
        resolution = self.get_manually_resolved_path(file_path_node)
        if resolution:
            return resolution

        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")
        candidate_path = file_path.split("}")[-1]
        if not candidate_path:
            return None
        candidate_path = candidate_path.strip("./")

        current_directory = (
            self.sysdiff.get_file_directory(self.ast.file_path).strip("/") + "/"
        )
        if current_directory == "/":
            current_directory = ""

        if (
            current_directory + candidate_path + "/CMakeLists.txt"
            in self.sysdiff.file_data
        ):
            return current_directory + candidate_path + "/CMakeLists.txt"

        if candidate_path + "/CMakeLists.txt" in self.sysdiff.file_data:
            return candidate_path + "/CMakeLists.txt"

        file_keys = list(
            map(
                lambda file_key: ("/" + file_key.strip("/")),
                self.sysdiff.file_data.keys(),
            )
        )

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    "/" + current_directory + candidate_path + "/CMakeLists.txt"
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return list(map(lambda file_key: file_key.strip("/"), desparate_list))

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    "/" + candidate_path + "/CMakeLists.txt"
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return list(map(lambda file_key: file_key.strip("/"), desparate_list))

        return None

    def visit_function_definition(self, node_data):
        self.register_new_def_point(node_data, "FUNCTION")

        # header_data = self.ast.get_data(
        #     self.ast.get_children_by_type(node_data, "function_header")
        # )

        # body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))

        return self.generic_visit(node_data)

    def visit_function_header(self, node_data):
        return self.generic_visit(node_data)

    def visit_macro_definition(self, node_data):
        self.register_new_def_point(node_data, "MACRO")

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
            if self.ast.unparse(argument).upper() not in operators:
                self.register_new_use_point(argument, "VARIABLE")

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
        self.register_new_def_point(def_node, "VARIABLE")
        return self.generic_visit(node_data)

    # def visit_endforeach_clause(self, node_data):
    #     pass

    def visit_normal_command(self, node_data):
        command_identifier = self.ast.unparse(
            self.ast.get_data(self.ast.get_children_by_type(node_data, "identifier"))
        ).upper()
        method = f"visit_{command_identifier}"
        visitor = getattr(self, method, self.visit_user_defined_normal_command)
        return visitor(node_data)

    def visit_user_defined_normal_command(self, node_data):
        self.register_new_use_point(node_data, "COMMAND")
        return self.generic_visit(node_data)

    ############################
    ###### CMake Commands ######
    ############################
    # All functions are designed based on current latest
    # release of CMake, documentations available at:
    # https://cmake.org/cmake/help/v3.27/manual/cmake-commands.7.html

    ########## Scripting Commands:

    def visit_BREAK(self, node_data):
        return

    def visit_CMAKE_HOST_SYSTEM_INFORMATION(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "CMAKE_HOST_SYSTEM_INFORMATION"
        )

        self.register_new_def_point(arguments[1], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_CMAKE_LANGUAGE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "CMAKE_LANGUAGE")

        operation = self.ast.unparse(arguments[0]).upper()

        if operation == "GET_MESSAGE_LOG_LEVEL":
            self.register_new_def_point(arguments[1], "VARIABLE")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() in [
                "ID_VAR",
                "GET_CALL_IDS",
                "GET_CALL",
            ]:
                self.register_new_def_point(arguments[i + 1], "VARIABLE")
                continue
            if self.ast.unparse(argument).upper() == "CALL":
                print(
                    f"Observe command for implementation (incomplete for CALL keyword): {self.ast.unparse(node_data)}"
                )
                continue

        return self.generic_visit(node_data)

    def visit_CMAKE_MINIMUM_REQUIRED(self, node_data):
        return self.generic_visit(node_data)

    def visit_CMAKE_PARSE_ARGUMENTS(self, node_data):
        return self.generic_visit(node_data)

    def visit_CMAKE_PATH(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "CMAKE_PATH")

        operation = self.ast.unparse(arguments[0]).upper()

        current_target_operations = ["COMPARE", "CONVERT"]
        if not operation in current_target_operations:
            self.register_new_use_point(arguments[1], "VARIABLE")

        if operation == "CONVERT":
            self.register_new_def_point(arguments[3], "VARIABLE")
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
            self.register_new_def_point(arguments[-1], "VARIABLE")
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
                if self.ast.unparse(argument).upper() == "OUTPUT_VARIABLE":
                    self.register_new_def_point(arguments[i + 1], "VARIABLE")
                    break

        return self.generic_visit(node_data)

    def visit_CMAKE_POLICY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "CMAKE_POLICY")

        operation = self.ast.unparse(arguments[0]).upper()

        if operation == "GET":
            self.register_new_def_point(arguments[-1], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_CONFIGURE_FILE(self, node_data):
        return self.generic_visit(node_data)

    def visit_CONTINUE(self, node_data):
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
            if self.ast.unparse(argument).upper() in current_target_keywords:
                self.register_new_def_point(arguments[i + 1], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_FILE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FILE")

        operation = self.ast.unparse(arguments[0]).upper()

        current_target_operations = ["GLOB", "GLOB_RECURSE", "RELATIVE_PATH"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[1], "VARIABLE")
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
            self.register_new_def_point(arguments[2], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_FIND_FILE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_FILE")

        self.register_new_def_point(arguments[0], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_FIND_LIBRARY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_LIBRARY")

        self.register_new_def_point(arguments[0], "VARIABLE")

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
            if self.ast.unparse(argument).upper() == "NAMES":
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse(arg).upper() in keywords:
                        break
                    self.register_new_def_point(arg, "VARIABLE")
                return self.generic_visit(node_data)

        self.register_new_def_point(arguments[0], "VARIABLE")
        return self.generic_visit(node_data)

    def visit_FIND_PATH(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_PATH")

        self.register_new_def_point(arguments[0], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_FIND_PROGRAM(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_PROGRAM")

        self.register_new_def_point(arguments[0], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_GET_CMAKE_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "GET_CMAKE_PROPERTY")

        self.register_new_def_point(arguments[0], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_GET_DIRECTORY_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_DIRECTORY_PROPERTY"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "DEFINITION":
                print(
                    f"Observe command for implementation (incomplete for DEFINITION keyword): {self.ast.unparse(node_data)}"
                )

        return self.generic_visit(node_data)

    def visit_GET_FILENAME_COMPONENT(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_FILENAME_COMPONENT"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "PROGRAM_ARGS":
                print(
                    f"Observe command for implementation (incomplete for PROGRAM_ARGS keyword): {self.ast.unparse(node_data)}"
                )

        return self.generic_visit(node_data)

    def visit_GET_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "GET_PROPERTY")

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            keyword = self.ast.unparse(argument).upper()
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
                if self.ast.unparse(arguments[i + 1]).upper() != "PROPERTY":
                    print(
                        f"Observe command for implementation (incomplete for keywords): {self.ast.unparse(node_data)}"
                    )
            elif keyword in current_target_keywords:
                print(
                    f"Observe command for implementation (incomplete for keywords): {self.ast.unparse(node_data)}"
                )
                # TODO SET USE_TYPE
                self.register_new_use_point(arguments[i + 1], "UNKNOWN")

        return self.generic_visit(node_data)

    def visit_INCLUDE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "INCLUDE")

        for i, argument in enumerate(arguments[1:]):
            if self.ast.unparse(argument).upper() == "RESULT_VARIABLE":
                self.register_new_def_point(arguments[i + 1], "VARIABLE")
                break

        # For file-level analysis (No system provided)
        if self.sysdiff is None:
            return self.generic_visit(node_data)

        included_file_path = self.ast.unparse(arguments[0])

        # Exclude CMake module
        if included_file_path in self.exclude_resolutions:
            print(
                f"Excluding a CMake module {self.ast.unparse(node_data)}: {included_file_path} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        included_file = self.resolve_included_file_path_best_effort(arguments[0])

        # For manual file path resolution setup
        if isinstance(included_file, list):
            print(
                f"Multiple path found for {self.ast.unparse(node_data)}: {' , '.join(included_file)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For files that do not exist in the project
        # or files that are refered to using a variable
        if included_file is None:
            print(
                f"Cannot resolve path for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For manaully skipped files
        if included_file.upper() == "SKIP":
            print(
                f"Skipping manually set for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For files with GumTree error
        if self.sysdiff.file_data[included_file]["diff"] is None:
            print(f"Parser error for {self.ast.unparse(node_data)}")
            return self.generic_visit(node_data)

        # Recursive resolution
        if (included_file == self.ast.file_path) or (
            node_data["id"]
            in self.sysdiff.file_data[included_file]["language_specific_info"][
                "importers"
            ]
        ):
            print(
                f"Skipping recursive resolution for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # Resolving to entry point
        if included_file == ROOT_FILE:
            print(
                f"Resolving to project's entry point for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # Successful resolution
        self.sysdiff.file_data[included_file]["language_specific_info"][
            "importers"
        ].append(node_data["id"])
        self.ast_stack.append(self.ast)
        self.ast = getattr(self.sysdiff.file_data[included_file]["diff"], self.ast.name)

        # Working on included file
        self.generic_visit(self.ast.get_data(self.ast.root))
        self.sysdiff.set_data_flow_reach_file(self.ast.file_path, self.ast.name)
        # Finished working on included file

        self.ast = self.ast_stack.pop()
        return self.generic_visit(node_data)

    def visit_INCLUDE_GUARD(self, node_data):
        return self.generic_visit(node_data)

    def visit_LIST(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "LIST")

        operation = self.ast.unparse(arguments[0]).upper()

        self.register_new_use_point(arguments[1], "VARIABLE")

        current_target_operations = ["LENGTH", "GET", "JOIN", "SUBLIST", "FIND"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[-1], "VARIABLE")

        current_target_operations = [
            "POP_BACK",
            "POP_FRONT",
        ]
        if operation in current_target_operations:
            if len(arguments) > 2:
                for def_node in arguments[2:]:
                    self.register_new_def_point(def_node, "VARIABLE")

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
            "REMOVE_DUPLICATES",
            "TRANSFORM",
            "REVERSE",
            "SORT",
        ]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[1], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_MARK_AS_ADVANCED(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "MARK_AS_ADVANCED")

        keywords = ["CLEAR", "FORCE"]
        start_index = 0
        if self.ast.unparse(arguments[0]).upper() in keywords:
            start_index = 1

        for argument in arguments[start_index:]:
            self.register_new_use_point(argument, "VARIABLE")
            self.register_new_def_point(argument, "VARIABLE")

        return self.generic_visit(node_data)

    def visit_MATH(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "MATH")

        self.register_new_def_point(arguments[1], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_MESSAGE(self, node_data):
        return self.generic_visit(node_data)

    def visit_OPTION(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "OPTION")

        self.register_new_def_point(arguments[0], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_RETURN(self, node_data):
        try:
            arguments = self.get_sorted_arguments_data_list(node_data, "RETURN")
        except MissingArgumentsException:
            return self.generic_visit(node_data)

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "PROPAGATE":
                for arg in argument[i + 1 :]:
                    self.register_new_use_point(arg, "VARIABLE")
                    self.register_new_def_point(arg, "VARIABLE")

        self.generic_visit(node_data)

    def visit_SEPARATE_ARGUMENTS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "SEPARATE_ARGUMENTS")

        self.register_new_def_point(arguments[0], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_SET(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "SET")

        if self.ast.unparse(arguments[-1]).upper() == "PARENT_SCOPE":
            pass
        self.register_new_def_point(arguments[0], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_SET_DIRECTORY_PROPERTIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_DIRECTORY_PROPERTIES"
        )

        print(f"Observe command for implementation: {self.ast.unparse(node_data)}")

        return self.generic_visit(node_data)

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
            unparsed_argument = self.ast.unparse(argument)
            if unparsed_argument == "TARGET":
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse(arg) not in keywords:
                        self.register_new_use_point(arg, "TARGET")
                        self.register_new_def_point(arg, "TARGET")
                    else:
                        break

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_SITE_NAME(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "SITE_NAME")

        self.register_new_def_point(arguments[0], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_STRING(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "STRING")

        operation = self.ast.unparse(arguments[0]).upper()

        if operation == "REGEX":
            sub_operation = self.ast.unparse(arguments[1])
            if sub_operation == "REPLACE":
                self.register_new_def_point(arguments[4], "VARIABLE")
            else:
                self.register_new_def_point(arguments[3], "VARIABLE")
            return self.generic_visit(node_data)

        if operation == "JSON":
            self.register_new_def_point(arguments[1], "VARIABLE")
            if self.ast.unparse(arguments[2]).upper() == "ERROR_VARIABLE":
                self.register_new_def_point(arguments[3], "VARIABLE")
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
            self.register_new_def_point(arguments[1], "VARIABLE")
            return self.generic_visit(node_data)

        current_target_operations = ["JOIN", "CONFIGURE"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[2], "VARIABLE")
            return self.generic_visit(node_data)

        current_target_operations = ["FIND", "REPLACE"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[3], "VARIABLE")
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
            self.register_new_def_point(arguments[-1], "VARIABLE")
            return self.generic_visit(node_data)

        return self.generic_visit(node_data)

    def visit_UNSET(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "UNSET")

        self.register_new_use_point(arguments[0], "VARIABLE")
        self.register_new_def_point(arguments[0], "VARIABLE")

        if self.ast.unparse(arguments[-1]).upper() == "PARENT_SCOPE":
            pass

        return self.generic_visit(node_data)

    def visit_VARIABLE_WATCH(self, node_data):
        return self.generic_visit(node_data)

    ########## Project Commands:

    def visit_ADD_COMPILE_DEFINITIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "ADD_COMPILE_DEFINITIONS"
        )

        # NOTE from documentations: Definitions are specified using the syntax VAR or VAR=value
        print(f"Observe command for implementation: {self.ast.unparse(node_data)}")

        return self.generic_visit(node_data)

    def visit_ADD_COMPILE_OPTIONS(self, node_data):
        return self.generic_visit(node_data)

    def visit_ADD_CUSTOM_COMMAND(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_CUSTOM_COMMAND")

        if self.ast.unparse(arguments[0]).upper() == "TARGET":
            self.register_new_use_point(arguments[1], "TARGET")

        return self.generic_visit(node_data)

    def visit_ADD_CUSTOM_TARGET(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_CUSTOM_TARGET")

        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_ADD_DEFINITIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_DEFINITIONS")

        print(f"Observe command for implementation: {self.ast.unparse(node_data)}")

        return self.generic_visit(node_data)

    def visit_ADD_DEPENDENCIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_DEPENDENCIES")

        for argument in arguments:
            self.register_new_use_point(argument, "TARGET")

        self.register_new_use_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_ADD_EXECUTABLE(self, node_data):
        """
        Documentation: https://cmake.org/cmake/help/v3.0/command/add_executable.html
        NOTE: Not adding sources as use points because they are either file names
        or will be variable_ref which will be caught when running generic_visit
        on node_data at the end.
        """
        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_EXECUTABLE")

        self.register_new_def_point(arguments[0], "TARGET")

        try:
            operation = self.ast.unparse(arguments[1]).upper()
        except IndexError:
            return self.generic_visit(node_data)

        if operation == "IMPORTED":
            # TODO: After Scoping is implemented, consider if GLOBAL keyword exists?
            pass
        elif operation == "ALIAS":
            assert len(arguments) == 3
            self.register_new_use_point(arguments[-1], "TARGET")

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

        self.register_new_def_point(arguments[0], "TARGET")

        try:
            operation = self.ast.unparse(arguments[1]).upper()
        except IndexError:
            return self.generic_visit(node_data)

        if operation == "ALIAS":
            assert len(arguments) == 3
            self.register_new_use_point(arguments[-1], "TARGET")

        return self.generic_visit(node_data)

    def visit_ADD_LINK_OPTIONS(self, node_data):
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

        added_file = self.resolve_add_subdirectory_file_path_best_effort(arguments[0])

        # For manual file path resolution setup
        if isinstance(added_file, list):
            print(
                f"Multiple path found for {self.ast.unparse(node_data)}: {' , '.join(added_file)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For files that do not exist in the project
        # or files that are refered to using a variable
        if added_file is None:
            print(
                f"Cannot resolve path for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For manaully skipped files
        if added_file.upper() == "SKIP":
            print(
                f"Skipping manually set for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # For files with GumTree error
        if self.sysdiff.file_data[added_file]["diff"] is None:
            print(f"Parser error for {self.ast.unparse(node_data)}")
            return self.generic_visit(node_data)

        # Recursive resolution
        if (added_file == self.ast.file_path) or (
            node_data["id"]
            in self.sysdiff.file_data[added_file]["language_specific_info"]["importers"]
        ):
            print(
                f"Skipping recursive resolution for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            return self.generic_visit(node_data)

        # Successful resolution
        self.sysdiff.file_data[added_file]["language_specific_info"][
            "importers"
        ].append(node_data["id"])

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
        print(f"Observe command for implementation: {self.ast.unparse(node_data)}")

        return self.generic_visit(node_data)

    def visit_AUX_SOURCE_DIRECTORY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "AUX_SOURCE_DIRECTORY"
        )

        self.register_new_def_point(arguments[-1], "VARIABLE")

        return self.generic_visit(node_data)

    def visit_BUILD_COMMAND(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "BUILD_COMMAND")

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "TARGET":
                self.register_new_use_point(arguments[i + 1], "TARGET")
                break

        return self.generic_visit(node_data)

    def visit_CMAKE_FILE_API(self, node_data):
        return self.generic_visit(node_data)

    def visit_CREATE_TEST_SOURCELIST(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "CREATE_TEST_SOURCELIST"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_DEFINE_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "DEFINE_PROPERTY")

        # self.register_new_def_point(arguments[2], "PROPERTY")

        if self.ast.unparse(arguments[-2]).upper() == "INITIALIZE_FROM_VARIABLE":
            self.register_new_def_point(arguments[-1], "VARIABLE")

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_ENABLE_LANGUAGE(self, node_data):
        return self.generic_visit(node_data)

    def visit_ENABLE_TESTING(self, node_data):
        return self.generic_visit(node_data)

    def visit_EXPORT(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "EXPORT")

        operation = self.ast.unparse(arguments[0]).upper()

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
                if self.ast.unparse(argument).upper() in keywords:
                    break
                else:
                    self.register_new_use_point(argument, "TARGET")
        else:
            self.register_new_use_point(arguments[1], "TARGET")

        print(
            f"Observe command for implementation (knowledge): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_FLTK_WRAP_UI(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "FLTK_WRAP_UI")

        self.register_new_def_point(arguments[0], "VARIABLE", suffix="_FLTK_UI_SRCS")

        return self.generic_visit(node_data)

    def visit_GET_SOURCE_FILE_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_SOURCE_FILE_PROPERTY"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")
        # self.register_new_use_point(arguments[-1], "PROPERTY")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "TARGET_DIRECTORY":
                self.register_new_use_point(arguments[i + 1], "TARGET")
                break

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_GET_TARGET_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_TARGET_PROPERTY"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")
        self.register_new_use_point(arguments[1], "TARGET")
        # self.register_new_use_point(arguments[-1], "PROPERTY")

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_GET_TEST_PROPERTY(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "GET_TEST_PROPERTY")

        # self.register_new_use_point(arguments[0], "TEST")
        # self.register_new_use_point(arguments[1], "PROPERTY")
        self.register_new_def_point(arguments[-1], "VARIABLE")

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_INCLUDE_DIRECTORIES(self, node_data):
        return self.generic_visit(node_data)

    def visit_INCLUDE_EXTERNAL_MSPROJECT(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "INCLUDE_EXTERNAL_MSPROJECT"
        )

        self.register_new_def_point(arguments[0], "TARGET")

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_INCLUDE_REGULAR_EXPRESSION(self, node_data):
        return self.generic_visit(node_data)

    def visit_INSTALL(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "INSTALL")

        all_keywords = [  # Alphabetically ordered
            "ALL_COMPONENTS",
            "ARCHIVE",
            "BUNDLE",
            "CODE",
            "COMPONENT",
            "CONFIGURATIONS",
            "CXX_MODULES_BMI",
            "CXX_MODULES_DIRECTORY",
            "DESTINATION",
            "DIRECTORIES",
            "DIRECTORY",
            "DIRECTORY_PERMISSIONS",
            "EXCLUDE",
            "EXCLUDE_FROM_ALL",
            "EXPORT",
            "EXPORT_ANDROID_MK",
            "EXPORT_LINK_INTERFACE_LIBRARIES",
            "FILE",
            "FILES_MATCHING",
            "FILE_PERMISSIONS",
            "FILE_SET",
            "FRAMEWORK",
            "IMPORTED_RUNTIME_ARTIFACTS",
            "INCLUDES DESTINATION",
            "LIBRARY",
            "MESSAGE_NEVER",
            "NAMELINK_COMPONENT",
            "NAMELINK_ONLY",
            "NAMELINK_SKIP",
            "NAMESPACE",
            "OBJECTS",
            "OPTIONAL",
            "PATTERN",
            "PERMISSIONS",
            "POST_EXCLUDE_FILES",
            "POST_EXCLUDE_REGEXES",
            "POST_INCLUDE_FILES",
            "POST_INCLUDE_REGEXES",
            "PRE_EXCLUDE_REGEXES",
            "PRE_INCLUDE_REGEXES",
            "PRIVATE_HEADER",
            "PUBLIC_HEADER",
            "REGEX",
            "RENAME",
            "RESOURCE",
            "RUNTIME",
            "RUNTIME_DEPENDENCIES",
            "RUNTIME_DEPENDENCY_SET",
            "SCRIPT",
            "TARGETS",
            "TYPE",
            "USE_SOURCE_PERMISSIONS",
        ]

        target_keywords = ["TARGETS", "IMPORTED_RUNTIME_ARTIFACTS"]
        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() in target_keywords:
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse(arg).upper() in all_keywords:
                        break
                    self.register_new_use_point(arg, "TARGET")

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_LINK_DIRECTORIES(self, node_data):
        return self.generic_visit(node_data)

    def visit_LINK_LIBRARIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "LINK_LIBRARIES")

        print(f"Observe command for implementation: {self.ast.unparse(node_data)}")

        return self.generic_visit(node_data)

    def visit_LOAD_CACHE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "LOAD_CACHE")

        print(f"Observe command for implementation: {self.ast.unparse(node_data)}")

        return self.generic_visit(node_data)

    def visit_PROJECT(self, node_data):
        return self.generic_visit(node_data)

    def visit_REMOVE_DEFINITIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "REMOVE_DEFINITIONS")

        print(f"Observe command for implementation: {self.ast.unparse(node_data)}")

        return self.generic_visit(node_data)

    def visit_SET_SOURCE_FILES_PROPERTIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_SOURCE_FILES_PROPERTIES"
        )

        current_target_keywords = [
            "DIRECTORY",
            "TARGET_DIRECTORY",
            "PROPERTIES",
        ]

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "TARGET_DIRECTORY":
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse(arg).upper() in current_target_keywords:
                        break
                    self.register_new_use_point(arg, "TARGET")
                break

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_SET_TARGET_PROPERTIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_TARGET_PROPERTIES"
        )

        for argument in arguments:
            if self.ast.unparse(argument).upper() == "PROPERTIES":
                break
            self.register_new_use_point(argument, "TARGET")
            self.register_new_def_point(argument, "TARGET")

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_SET_TESTS_PROPERTIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_TESTS_PROPERTIES"
        )

        print(f"Observe command for implementation: {self.ast.unparse(node_data)}")

        return self.generic_visit(node_data)

    def visit_SOURCE_GROUP(self, node_data):
        return self.generic_visit(node_data)

    def visit_TARGET_COMPILE_DEFINITIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_DEFINITIONS"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_TARGET_COMPILE_FEATURES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_FEATURES"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_TARGET_COMPILE_OPTIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_OPTIONS"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_TARGET_INCLUDE_DIRECTORIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_INCLUDE_DIRECTORIES"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_TARGET_LINK_DIRECTORIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_DIRECTORIES"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_TARGET_LINK_LIBRARIES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_LIBRARIES"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        print(
            f"Observe command for implementation (incomplete): {self.ast.unparse(node_data)}"
        )

        return self.generic_visit(node_data)

    def visit_TARGET_LINK_OPTIONS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_OPTIONS"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_TARGET_PRECOMPILE_HEADERS(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_PRECOMPILE_HEADERS"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_TARGET_SOURCES(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "TARGET_SOURCES")

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        return self.generic_visit(node_data)

    def visit_TRY_COMPILE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "TRY_COMPILE")

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "TARGET":
                self.register_new_use_point(arguments[i + 1], "TARGET")
                continue
            if self.ast.unparse(argument).upper() == "SOURCE_FROM_VAR":
                self.register_new_use_point(arguments[i + 2], "VARIABLE")
                continue
            if self.ast.unparse(argument).upper() == "OUTPUT_VARIABLE":
                self.register_new_def_point(arguments[i + 1], "VARIABLE")
                continue
            if self.ast.unparse(argument).upper() == "COPY_FILE_ERROR":
                self.register_new_def_point(arguments[i + 1], "VARIABLE")
                continue

        return self.generic_visit(node_data)

    def visit_TRY_RUN(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "TRY_RUN")

        self.register_new_def_point(arguments[0], "VARIABLE")
        self.register_new_def_point(arguments[1], "VARIABLE")

        current_target_keywords = [
            "COMPILE_OUTPUT_VARIABLE",
            "COPY_FILE_ERROR",
            "OUTPUT_VARIABLE",
            "RUN_OUTPUT_VARIABLE",
            "RUN_OUTPUT_STDOUT_VARIABLE",
            "RUN_OUTPUT_STDERR_VARIABLE",
        ]

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() in [
                "SOURCE_FROM_VAR",
                "WORKING_DIRECTORY",
            ]:
                self.register_new_use_point(arguments[i + 2], "VARIABLE")
                continue
            if self.ast.unparse(argument).upper() in current_target_keywords:
                self.register_new_def_point(arguments[i + 1], "VARIABLE")
                continue

        return self.generic_visit(node_data)

    ########## CTesgt Commands:

    def visit_CTEST_BUILD(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_CONFIGURE(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_COVERAGE(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_EMPTY_BINARY_DIRECTORY(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_MEMCHECK(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_READ_CUSTOM_FILES(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_RUN_SCRIPT(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_SLEEP(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_START(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_SUBMIT(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_TEST(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_UPDATE(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_UPLOAD(self, node_data):
        return self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_CMDs(self, node_data):
        """
        All CTEST_* commands are redirected to this method.
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
            if self.ast.unparse(argument).upper() == "TARGET":
                self.register_new_use_point(arguments[i + 1], "TARGET")
                continue
            if self.ast.unparse(argument).upper() in current_target_keywords:
                self.register_new_def_point(arguments[i + 1], "VARIABLE")
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
        self.register_new_use_point(node_data, "VARIABLE")
        # For nested variable references
        return self.generic_visit(node_data)
