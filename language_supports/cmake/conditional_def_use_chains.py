from pathlib import Path
from functools import reduce
import data_flow_analysis as cm
from utils.configurations import PATH_RESOLUTIONS, ROOT_PATH, ROOT_FILE
from utils.exceptions import MissingArgumentsException, DebugException

# CMake Modules based on the official documentation
# https://cmake.org/cmake/help/v3.27/manual/cmake-modules.7.html
with open(ROOT_PATH / "language_supports/cmake/cmake_modules.txt", "r") as f:
    CMAKE_MODULES = list(map(lambda entry: entry.strip("\n"), f.readlines()))


class ConditionalDefUseChains(cm.ConditionalDefUseChains):
    manual_resolution = PATH_RESOLUTIONS
    exclude_resolutions = CMAKE_MODULES

    def compare_reachability_conditions(self, def_point, use_point):
        """
        Consumes the def_point (or the def reachability stack) and
        the use_point (or the use reachability stack) objects and returns:
                    "=" (equal reachability condition)
                    "<" (def reachability is subset of use reachability)
                    ">" (use reachability is subset of def reachability)
                    "!" (contradiction exists in reachabilities)
                    "?" (unable to find a concrete relation between)

        The comparison is NAIVE.
        """
        if isinstance(def_point, list) and isinstance(use_point, list):
            def_conditions = set(def_point)
            use_conditions = set(def_point)
        else:
            if def_point.type == "PROPERTY" or use_point.type == "PROPERTY":
                return "?"

            def_conditions = set(def_point.actor_point.reachability)
            use_conditions = set(use_point.actor_point.reachability)

        def_conditions.difference_update({""})
        use_conditions.difference_update({""})

        if def_conditions == use_conditions:
            return "="
        if def_conditions.issubset(use_conditions):
            return "<"
        if use_conditions.issubset(def_conditions):
            return ">"

        if set(map(lambda cond: f"NOT ({cond})", def_conditions)).intersection(
            use_conditions
        ):
            return "!"
        if set(map(lambda cond: f"NOT ({cond})", use_conditions)).intersection(
            def_conditions
        ):
            return "!"

        return "?"

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
        """
        Returns (success_flag, resolution)
        """
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
            return True, resolved_path_item[0]["callee_resolved_path"]
        if len(resolved_path_item) > 1:
            return True, resolved_path_item
        return False, None

    def resolve_included_file_path_best_effort(self, file_path_node):
        """
        Returns (success_flag, resolution)
        """
        manual_success, resolution = self.get_manually_resolved_path(file_path_node)
        if manual_success:
            return True, resolution

        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")
        candidate_path = file_path.split("}")[-1]
        if not candidate_path:
            return False, None
        candidate_path = candidate_path.strip("./")

        current_directory = (
            self.sysdiff.get_file_directory(self.ast.file_path).strip("/") + "/"
        )
        if current_directory == "/":
            current_directory = ""

        if current_directory + candidate_path in self.sysdiff.file_data:
            return True, current_directory + candidate_path

        if current_directory + candidate_path + ".cmake" in self.sysdiff.file_data:
            return True, current_directory + candidate_path + ".cmake"

        if candidate_path in self.sysdiff.file_data:
            return True, candidate_path

        if candidate_path + ".cmake" in self.sysdiff.file_data:
            return True, candidate_path + ".cmake"

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
            return True, desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return False, list(
                map(lambda file_key: file_key.strip("/"), desparate_list)
            )

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    "/" + current_directory + candidate_path + ".cmake"
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return True, desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return False, list(
                map(lambda file_key: file_key.strip("/"), desparate_list)
            )

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith("/" + candidate_path),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return True, desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return False, list(
                map(lambda file_key: file_key.strip("/"), desparate_list)
            )

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith("/" + candidate_path + ".cmake"),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return True, desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return False, list(
                map(lambda file_key: file_key.strip("/"), desparate_list)
            )

        return False, None

    def resolve_added_subdirectory_file_path_best_effort(self, file_path_node):
        """
        Returns (success_flag, resolution)
        """
        manual_success, resolution = self.get_manually_resolved_path(file_path_node)
        if manual_success:
            return True, resolution

        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")
        candidate_path = file_path.split("}")[-1]
        if not candidate_path:
            return False, None
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
            return True, current_directory + candidate_path + "/CMakeLists.txt"

        if candidate_path + "/CMakeLists.txt" in self.sysdiff.file_data:
            return True, candidate_path + "/CMakeLists.txt"

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
            return True, desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return False, list(
                map(lambda file_key: file_key.strip("/"), desparate_list)
            )

        desparate_list = list(
            filter(
                lambda file_key: file_key.endswith(
                    "/" + candidate_path + "/CMakeLists.txt"
                ),
                file_keys,
            )
        )
        if len(desparate_list) == 1:
            return True, desparate_list[0].strip("/")
        elif len(desparate_list) > 1:
            return False, list(
                map(lambda file_key: file_key.strip("/"), desparate_list)
            )

        return False, None

    def visit_function_definition(self, node_data):
        print(f"Function definition {self.ast.get_name(node_data)}")
        self.register_new_def_point(node_data, "FUNCTION")

        return self.process_callable_definition_location(node_data, "function")

    def visit_function_header(self, node_data):
        arguments_node = self.ast.get_children_by_type(node_data, "arguments")
        if arguments_node:
            arguments = self.ast.get_children(
                self.ast.get_data(arguments_node)
            ).values()
            list(
                map(
                    lambda argument: self.register_new_def_point(argument, "VARIABLE"),
                    arguments,
                )
            )
        return

    def visit_macro_definition(self, node_data):
        print(f"Macro definition {self.ast.get_name(node_data)}")
        self.register_new_def_point(node_data, "MACRO")

        return self.process_callable_definition_location(node_data, "macro")

    def visit_macro_header(self, node_data):
        arguments_node = self.ast.get_children_by_type(node_data, "arguments")
        if arguments_node:
            arguments = self.ast.get_children(
                self.ast.get_data(arguments_node)
            ).values()
            list(
                map(
                    lambda argument: self.register_new_def_point(argument, "VARIABLE"),
                    arguments,
                )
            )
        return

    def process_callable_definition_location(self, node_data, callable_type):
        """
        This method only analyzes the definition of a function/macro
        so that changes to a callable that has never been used also get analyzed
        """
        target_ast = self.ast
        child_scope = self.sysdiff.ConditionalDefUseChains(
            target_ast, scope=node_data["id"], parent=self, sysdiff=self.sysdiff
        )
        child_scope.parent_names_available = False

        self.children.append(child_scope)
        self.sysdiff.append_to_chains(child_scope)

        header_data = child_scope.ast.get_data(
            child_scope.ast.get_children_by_type(node_data, f"{callable_type}_header")
        )
        child_scope.visit(header_data)
        body_data = child_scope.ast.get_data(
            child_scope.ast.get_children_by_type(node_data, "body")
        )
        if body_data:
            child_scope.visit(body_data)
        return

    def process_callable_call_location(self, node_data, def_point):
        self.register_new_use_point(node_data, def_point.type)
        self.generic_visit(node_data)
        if def_point.type == "FUNCTION":
            print(
                f"Support needed for callable variable translation for function {def_point.name}, scope {node_data['id']}"
            )
            target_ast = def_point.ast
            child_scope = self.sysdiff.ConditionalDefUseChains(
                target_ast,
                scope=node_data["id"],
                parent=self,
                sysdiff=self.sysdiff,
            )
            self.children.append(child_scope)
            self.sysdiff.append_to_chains(child_scope)

            definer_node = def_point.node_data
            header_data = child_scope.ast.get_data(
                child_scope.ast.get_children_by_type(definer_node, "function_header")
            )
            child_scope.visit(header_data)
            body_data = child_scope.ast.get_data(
                child_scope.ast.get_children_by_type(definer_node, "body")
            )
            if body_data:
                child_scope.visit(body_data)
        elif def_point.type == "MACRO":
            print(
                f"Support needed for callable variable translation for macro {def_point.name}, scope {node_data['id'].replace(':','_')}"
            )
            self.ast_stack.append(self.ast)

            self.ast = def_point.ast

            definer_node = def_point.node_data
            header_data = self.ast.get_data(
                self.ast.get_children_by_type(definer_node, "macro_header")
            )
            self.visit(header_data)
            body_data = self.ast.get_data(
                self.ast.get_children_by_type(definer_node, "body")
            )
            self.visit(body_data)

            self.ast = self.ast_stack.pop()

    def visit_block_definition(self, node_data):
        header_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "block_header")
        )
        arguments = sorted(
            self.ast.get_children(
                self.ast.get_data(
                    self.ast.get_children_by_type(header_data, "arguments")
                )
            ).values(),
            key=lambda argument_node_data: argument_node_data["s_pos"],
        )
        body_data = self.ast.get_data(self.ast.get_children_by_type(node_data, "body"))

        new_scope = False

        if len(arguments) == 0:
            new_scope = True
        if self.ast.unparse(arguments[0]).upper() != "SCOPE_FOR":
            new_scope = True
        for argument in arguments:
            if self.ast.unparse(argument).upper() == "VARIABLES":
                new_scope = True
                break

        if new_scope:
            child_scope = self.sysdiff.ConditionalDefUseChains(
                self.ast, scope=node_data["id"], parent=self, sysdiff=self.sysdiff
            )
            self.children.append(child_scope)
            self.sysdiff.append_to_chains(child_scope)

            child_scope.visit(body_data)

            for i, argument in enumerate(arguments):
                if self.ast.unparse(argument).upper() == "PROPAGATE":
                    for arg in arguments[i + 1 :]:
                        var_name = self.ast.get_name(arg)
                        def_points = child_scope.get_definitions_by_name(
                            var_name, False
                        )
                        for def_point in def_points:
                            self.defined_names[var_name].append(def_point)
                            self.def_points[def_point.node_data["id"]] = def_point
                            self.actor_points[
                                def_point.actor_point.node_data["id"]
                            ] = def_point.actor_point

        else:
            return self.generic_visit(node_data)

    def visit_if_statement(self, node_data):
        stacked_condition_count = (
            len(list(self.ast.get_children_by_type(node_data, "elseif_clause").keys()))
            + len(list(self.ast.get_children_by_type(node_data, "else_clause").keys()))
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
        self.add_condition_to_reachability_stack(condition_node_data, node_data["id"])

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
        self.add_condition_to_reachability_stack(condition_node_data, node_data["id"])

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
        self.add_condition_to_reachability_stack(condition_node_data, node_data["id"])

        body_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "body")
        )
        if body_node_data:
            return self.generic_visit(body_node_data)

    def visit_while_statement(self, node_data):
        self.generic_visit(node_data)
        self.remove_condition_from_reachability_stack(last_n=1)
        return

    def visit_while_clause(self, node_data):
        condition_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "condition")
        )
        self.visit_conditional_expression(condition_node_data)
        self.add_condition_to_reachability_stack(condition_node_data, node_data["id"])

        body_node_data = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "body")
        )
        if body_node_data:
            return self.generic_visit(body_node_data)

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

        self.generic_visit(node_data)

        self.def_points[def_node["id"]].lock = True

    def visit_normal_command(self, node_data):
        command_identifier = self.ast.unparse(
            self.ast.get_data(self.ast.get_children_by_type(node_data, "identifier"))
        ).upper()
        method = f"visit_{command_identifier}"
        visitor = getattr(self, method, self.visit_user_defined_normal_command)
        return visitor(node_data)

    def visit_user_defined_normal_command(self, node_data):
        # # TODO: Should we uncomment the following 3 commented lines
        # # and allow for analysis of function inside functions
        # # at definition location processing time?
        # temp_flag = self.parent_names_available
        # self.parent_names_available = True
        def_points = self.get_definitions_by_name(node_data, True)
        # self.parent_names_available = temp_flag
        if len(def_points) > 0:
            reachability_checker = getattr(
                self, "compare_reachability_conditions", None
            )
            if reachability_checker is None:
                list(
                    map(
                        lambda def_point: self.process_callable_call_location(
                            node_data, def_point
                        ),
                        def_points,
                    )
                )
                return
            for def_point in reversed(def_points):
                reachability_status = reachability_checker(
                    def_point.actor_point.reachability.copy(),
                    self.reachability_stack.copy(),
                )
                if reachability_status in ["=", "<"]:
                    self.process_callable_call_location(node_data, def_point)
                    break
                if reachability_status in ["!"]:
                    continue
                if reachability_status in [">", "?"]:
                    self.process_callable_call_location(node_data, def_point)
                    continue
        elif not self.parent_names_available:
            self.register_new_use_point(node_data, "SOME_COMMAND")
            self.generic_visit(node_data)
        elif self.parent_names_available:
            self.register_new_use_point(node_data, "UNKNOWN_COMMAND")
            self.generic_visit(node_data)
        return

    ############################
    ###### CMake Commands ######
    ############################
    # All functions are designed based on current latest
    # release of CMake, documentations available at:
    # https://cmake.org/cmake/help/v3.27/manual/cmake-commands.7.html

    ########## Scripting Commands:

    def visit_BREAK(self, node_data):
        self.generic_visit(node_data)

    def visit_CMAKE_HOST_SYSTEM_INFORMATION(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "CMAKE_HOST_SYSTEM_INFORMATION"
        )

        self.register_new_def_point(arguments[1], "VARIABLE")

    def visit_CMAKE_LANGUAGE(self, node_data):
        self.generic_visit(node_data)

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
                    f"Support needed for command arguments for CALL keyword in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
                )
                continue

    def visit_CMAKE_MINIMUM_REQUIRED(self, node_data):
        self.generic_visit(node_data)

    def visit_CMAKE_PARSE_ARGUMENTS(self, node_data):
        self.generic_visit(node_data)

    def visit_CMAKE_PATH(self, node_data):
        self.generic_visit(node_data)

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

    def visit_CMAKE_POLICY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "CMAKE_POLICY")

        operation = self.ast.unparse(arguments[0]).upper()

        if operation == "GET":
            self.register_new_def_point(arguments[-1], "VARIABLE")

    def visit_CONFIGURE_FILE(self, node_data):
        self.generic_visit(node_data)

    def visit_CONTINUE(self, node_data):
        self.generic_visit(node_data)

    def visit_EXECUTE_PROCESS(self, node_data):
        self.generic_visit(node_data)

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

    def visit_FILE(self, node_data):
        self.generic_visit(node_data)

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

    def visit_FIND_FILE(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_FILE")

        self.register_new_def_point(arguments[0], "VARIABLE")

    def visit_FIND_LIBRARY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_LIBRARY")

        self.register_new_def_point(arguments[0], "VARIABLE")

    def visit_FIND_PACKAGE(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_PACKAGE")
        print(
            f"Support needed for including modules using {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

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

    def visit_FIND_PATH(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_PATH")

        self.register_new_def_point(arguments[0], "VARIABLE")

    def visit_FIND_PROGRAM(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "FIND_PROGRAM")

        self.register_new_def_point(arguments[0], "VARIABLE")

    def visit_GET_CMAKE_PROPERTY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "GET_CMAKE_PROPERTY")

        self.register_new_def_point(arguments[0], "VARIABLE")
        self.register_new_use_point(arguments[1], "PROPERTY")

    def visit_GET_DIRECTORY_PROPERTY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_DIRECTORY_PROPERTY"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "DEFINITION":
                self.register_new_def_point(arguments[i + 1], "VARIABLE")
                return self.generic_visit(node_data)

        self.register_new_use_point(arguments[-1], "PROPERTY")

    def visit_GET_FILENAME_COMPONENT(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_FILENAME_COMPONENT"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "PROGRAM_ARGS":
                print(
                    f"Support needed for command arguments for PROGRAM_ARGS keyword in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
                )

    def visit_GET_PROPERTY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "GET_PROPERTY")

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            keyword = self.ast.unparse(argument).upper()
            if keyword in ["TARGET", "TARGET_DIRECTORY"]:
                self.register_new_use_point(arguments[i + 1], "TARGET")
            elif keyword == "TEST":
                self.register_new_use_point(arguments[i + 1], "TEST")
            elif keyword == "PROPERTY":
                self.register_new_use_point(arguments[i + 1], "PROPERTY")
            elif keyword == "CACHE":
                self.register_new_use_point(arguments[i + 1], "VARIABLE")

    def visit_INCLUDE(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "INCLUDE")

        for i, argument in enumerate(arguments[1:]):
            if self.ast.unparse(argument).upper() == "RESULT_VARIABLE":
                self.register_new_def_point(arguments[i + 1], "VARIABLE")
                break

        # For file-level analysis (No system provided)
        if self.sysdiff is None:
            return

        included_file_path = self.ast.unparse(arguments[0])

        # Exclude CMake module
        if included_file_path in self.exclude_resolutions:
            print(
                f"INCLUDE resolution excluded a CMake module for {self.ast.unparse(node_data)}: {included_file_path} called from {self.ast.file_path}"
            )
            return

        resolution_success, included_file = self.resolve_included_file_path_best_effort(
            arguments[0]
        )

        if not resolution_success:
            # For failures due to multiple resolutions
            if isinstance(included_file, list):
                print(
                    f"INCLUDE resolution found multiple paths for {self.ast.unparse(node_data)}: {' , '.join(included_file)} called from {self.ast.file_path}"
                )
                return

            # For files that do not exist in the project
            # or files that are refered to using a variable
            if included_file is None:
                print(
                    f"INCLUDE resolution cannot resolve path for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return

        # Successful resolution
        if isinstance(included_file, str):
            # For manaully skipped files
            if included_file.upper() == "SKIP":
                print(
                    f"INCLUDE resolution skipping manually set for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return

            # For files with GumTree error
            if self.sysdiff.file_data[included_file]["diff"] is None:
                print(
                    f"INCLUDE resolution skipping a file with parser error for {self.ast.unparse(node_data)}"
                )
                return

            # Recursive resolution
            if (included_file == self.ast.file_path) or (
                node_data["id"]
                in self.sysdiff.file_data[included_file]["language_specific_info"][
                    "importers"
                ]
            ):
                print(
                    f"INCLUDE resolution lead to recursive resolution for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return

            # Resolving to entry point
            if included_file == ROOT_FILE:
                print(
                    f"INCLUDE resolution lead to project's entry point for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return

            included_file = [included_file]

        self.ast_stack.append(self.ast)

        for resolution in included_file:
            self.sysdiff.file_data[resolution]["language_specific_info"][
                "importers"
            ].append(node_data["id"])
            self.ast = getattr(
                self.sysdiff.file_data[resolution]["diff"], self.ast.name
            )

            # Working on included file
            self.generic_visit(self.ast.get_data(self.ast.root))
            self.sysdiff.set_data_flow_reach_file(self.ast.file_path, self.ast.name)
            # Finished working on included file

        self.ast = self.ast_stack.pop()

    def visit_INCLUDE_GUARD(self, node_data):
        self.generic_visit(node_data)

    def visit_LIST(self, node_data):
        self.generic_visit(node_data)

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

    def visit_MARK_AS_ADVANCED(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "MARK_AS_ADVANCED")

        keywords = ["CLEAR", "FORCE"]
        start_index = 0
        if self.ast.unparse(arguments[0]).upper() in keywords:
            start_index = 1

        for argument in arguments[start_index:]:
            self.register_new_use_point(argument, "VARIABLE")
            self.register_new_def_point(argument, "VARIABLE")

    def visit_MATH(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "MATH")

        self.register_new_def_point(arguments[1], "VARIABLE")

    def visit_MESSAGE(self, node_data):
        self.generic_visit(node_data)

    def visit_OPTION(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "OPTION")

        self.register_new_def_point(arguments[0], "VARIABLE")

    def visit_RETURN(self, node_data):
        self.generic_visit(node_data)

        try:
            arguments = self.get_sorted_arguments_data_list(node_data, "RETURN")
        except MissingArgumentsException:
            return

        print(
            f"Support needed for PROPAGATE keyword in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

        # for i, argument in enumerate(arguments):
        #     if self.ast.unparse(argument).upper() == "PROPAGATE":
        #         for arg in argument[i + 1 :]:
        #             self.register_new_use_point(arg, "VARIABLE")
        #             self.register_new_def_point(arg, "VARIABLE")

    def visit_SEPARATE_ARGUMENTS(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "SEPARATE_ARGUMENTS")

        self.register_new_def_point(arguments[0], "VARIABLE")

        for argument in arguments:
            if self.ast.unparse(argument).upper() == "PROGRAM":
                print(
                    f"Support needed for command arguments for PROGRAM keyword in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
                )

    def visit_SET(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "SET")

        self.register_new_def_point(arguments[0], "VARIABLE")

        if self.ast.unparse(arguments[-1]).upper() == "PARENT_SCOPE":
            def_point = self.def_points[arguments[0]["id"]]
            self.register_def_point_to_parent_scope(def_point)

    def visit_SET_DIRECTORY_PROPERTIES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_DIRECTORY_PROPERTIES"
        )

        for i, argument in enumerate(arguments):
            if (i % 2) == 1:
                self.register_new_def_point(argument, "PROPERTY")

    def visit_SET_PROPERTY(self, node_data):
        self.generic_visit(node_data)

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
            unparsed_argument = self.ast.unparse(argument).upper()
            if unparsed_argument == "TARGET":
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse(arg).upper() not in keywords:
                        self.register_new_use_point(arg, "TARGET")
                        self.register_new_def_point(arg, "TARGET")
                    else:
                        break
            elif unparsed_argument == "TEST":
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse(arg).upper() not in keywords:
                        self.register_new_use_point(arg, "TEST")
                        self.register_new_def_point(arg, "TEST")
                    else:
                        break
            if unparsed_argument == "CACHE":
                for arg in arguments[i + 1 :]:
                    if self.ast.unparse(arg).upper() not in keywords:
                        self.register_new_use_point(arg, "VARIABLE")
                        self.register_new_def_point(arg, "VARIABLE")
                    else:
                        break
            elif unparsed_argument == "PROPERTY":
                self.register_new_def_point(arguments[i + 1], "PROPERTY")

    def visit_SITE_NAME(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "SITE_NAME")

        self.register_new_def_point(arguments[0], "VARIABLE")

    def visit_STRING(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "STRING")

        operation = self.ast.unparse(arguments[0]).upper()

        if operation == "REGEX":
            sub_operation = self.ast.unparse(arguments[1])
            if sub_operation == "REPLACE":
                self.register_new_def_point(arguments[4], "VARIABLE")
            else:
                self.register_new_def_point(arguments[3], "VARIABLE")
            return

        if operation == "JSON":
            self.register_new_def_point(arguments[1], "VARIABLE")
            if self.ast.unparse(arguments[2]).upper() == "ERROR_VARIABLE":
                self.register_new_def_point(arguments[3], "VARIABLE")
            return

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
            return

        current_target_operations = ["JOIN", "CONFIGURE"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[2], "VARIABLE")
            return

        current_target_operations = ["FIND", "REPLACE"]
        if operation in current_target_operations:
            self.register_new_def_point(arguments[3], "VARIABLE")
            return

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
            return

    def visit_UNSET(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "UNSET")

        self.register_new_use_point(arguments[0], "VARIABLE")
        self.register_new_def_point(arguments[0], "VARIABLE")

        if self.ast.unparse(arguments[-1]).upper() == "PARENT_SCOPE":
            def_point = self.def_points[arguments[0]["id"]]
            self.register_def_point_to_parent_scope(def_point)

    def visit_VARIABLE_WATCH(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "VARIABLE_WATCH")

        self.register_new_use_point(arguments[0], "VARIABLE")
        if len(arguments) == 2:
            self.register_new_use_point(arguments[-1], "COMMAND")

    ########## Project Commands:

    def visit_ADD_COMPILE_DEFINITIONS(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "ADD_COMPILE_DEFINITIONS"
        )

        # NOTE from documentations: Definitions are specified using the syntax VAR or VAR=value
        print(
            f"Support needed for definitions in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

    def visit_ADD_COMPILE_OPTIONS(self, node_data):
        self.generic_visit(node_data)

    def visit_ADD_CUSTOM_COMMAND(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_CUSTOM_COMMAND")

        if self.ast.unparse(arguments[0]).upper() == "TARGET":
            self.register_new_use_point(arguments[1], "TARGET")

        print(
            f"Support needed for depndencies and command arguments in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

        # keywords = [
        #     "APPEND",
        #     "ARGS",
        #     "BYPRODUCTS",
        #     "COMMAND",
        #     "COMMAND_EXPAND_LISTS",
        #     "COMMENT",
        #     "DEPENDS",
        #     "DEPENDS_EXPLICIT_ONLY",
        #     "DEPFILE",
        #     "IMPLICIT_DEPENDS",
        #     "JOB_POOL",
        #     "MAIN_DEPENDENCY",
        #     "OUTPUT",
        #     "POST_BUILD",
        #     "PRE_BUILD",
        #     "PRE_LINK",
        #     "USES_TERMINAL",
        #     "VERBATIM",
        #     "WORKING_DIRECTORY",
        # ]
        # for i, argument in enumerate(arguments):
        #     if self.ast.unparse(argument).upper() == "DEPENDS":
        #         for arg in arguments[i + 1]:
        #             if self.ast.unparse(arg).upper() in keywords:
        #                 break
        #             defined_names = self.get_definitions_by_name(arg)
        #             if list(
        #                 filter(
        #                     lambda def_point: def_point.type == "TARGET", defined_names
        #                 )
        #             ):
        #                 self.register_new_use_point(arg, "TARGET")

    def visit_ADD_CUSTOM_TARGET(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_CUSTOM_TARGET")

        self.register_new_def_point(arguments[0], "TARGET")

        print(
            f"Support needed for depndencies and command arguments in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

    def visit_ADD_DEFINITIONS(self, node_data):
        self.generic_visit(node_data)

        # try:
        #     arguments = self.get_sorted_arguments_data_list(
        #         node_data, "ADD_DEFINITIONS"
        #     )
        # except MissingArgumentsException:
        #     pass

        print(
            f"Support needed for definitions in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

    def visit_ADD_DEPENDENCIES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_DEPENDENCIES")

        for argument in arguments:
            self.register_new_use_point(argument, "TARGET")

        self.register_new_use_point(arguments[0], "TARGET")

    def visit_ADD_EXECUTABLE(self, node_data):
        """
        Documentation: https://cmake.org/cmake/help/v3.0/command/add_executable.html
        NOTE: Not adding sources as use points because they are either file names
        or will be variable_ref which will be caught when running generic_visit
        on node_data at the end.
        """
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_EXECUTABLE")

        self.register_new_def_point(arguments[0], "TARGET")

        try:
            operation = self.ast.unparse(arguments[1]).upper()
        except IndexError:
            return

        if operation == "IMPORTED":
            # TODO: After Scoping is implemented, consider if GLOBAL keyword exists?
            pass
        elif operation == "ALIAS":
            assert len(arguments) == 3
            self.register_new_use_point(arguments[-1], "TARGET")

    def visit_ADD_LIBRARY(self, node_data):
        """
        NOTE: Not adding sources as use points because they are either file names
        or will be variable_ref which will be caught when running generic_visit
        on node_data at the end.
        TODO: See object library and check object reference
        TODO: See imported library and check global with scoping
        """
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_LIBRARY")

        self.register_new_def_point(arguments[0], "TARGET")

        try:
            operation = self.ast.unparse(arguments[1]).upper()
        except IndexError:
            return

        if operation == "ALIAS":
            assert len(arguments) == 3
            self.register_new_use_point(arguments[-1], "TARGET")

    def visit_ADD_LINK_OPTIONS(self, node_data):
        self.generic_visit(node_data)

    def visit_ADD_SUBDIRECTORY(self, node_data):
        """
        Use example:
            https://cmake.org/pipermail/cmake/2007-November/017897.html
            https://stackoverflow.com/a/6891527
            https://stackoverflow.com/a/49989597
            https://stackoverflow.com/a/48510440
        """
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_SUBDIRECTORY")

        # For file-level analysis (No system provided)
        if self.sysdiff is None:
            return

        (
            resolution_success,
            added_file,
        ) = self.resolve_added_subdirectory_file_path_best_effort(arguments[0])

        if not resolution_success:
            # For failures due to multiple resolutions
            if isinstance(added_file, list):
                print(
                    f"ADD_SUBDIRECTORY resolution found multiple paths for {self.ast.unparse(node_data)}: {' , '.join(added_file)} called from {self.ast.file_path}"
                )
                return

            # For files that do not exist in the project
            # or files that are refered to using a variable
            if added_file is None:
                print(
                    f"ADD_SUBDIRECTORY resolution cannot resolve path for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return

        if isinstance(added_file, str):
            # For manaully skipped files
            if added_file.upper() == "SKIP":
                print(
                    f"ADD_SUBDIRECTORY resolution skipping manually set for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return

            # For files with GumTree error
            if self.sysdiff.file_data[added_file]["diff"] is None:
                print(f"Parser error for {self.ast.unparse(node_data)}")
                return

            # Recursive resolution
            if (added_file == self.ast.file_path) or (
                node_data["id"]
                in self.sysdiff.file_data[added_file]["language_specific_info"][
                    "importers"
                ]
            ):
                print(
                    f"ADD_SUBDIRECTORY resolution lead to recursive resolution for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return

            # Resolving to entry point
            if added_file == ROOT_FILE:
                print(
                    f"ADD_SUBDIRECTORY resolution lead to project's entry point for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return

            added_file = [added_file]

        # Successful resolution
        for resolution in added_file:
            self.sysdiff.file_data[resolution]["language_specific_info"][
                "importers"
            ].append(node_data["id"])

            target_ast = getattr(
                self.sysdiff.file_data[resolution]["diff"], self.ast.name
            )
            child_scope = self.sysdiff.ConditionalDefUseChains(
                target_ast, scope=node_data["id"], parent=self, sysdiff=self.sysdiff
            )
            self.children.append(child_scope)
            self.sysdiff.append_to_chains(child_scope)

            # Working on added file
            child_scope.analyze()
            self.sysdiff.set_data_flow_reach_file(
                child_scope.ast.file_path, child_scope.ast.name
            )
            # Finished working on added file

    def visit_ADD_TEST(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_TEST")

        if self.ast.unparse(arguments[0]).upper() == "NAME":
            self.register_new_def_point(arguments[1], "TEST")
        else:
            self.register_new_def_point(arguments[0], "TEST")

        print(
            f"Support needed for command arguments in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

    def visit_AUX_SOURCE_DIRECTORY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "AUX_SOURCE_DIRECTORY"
        )

        self.register_new_def_point(arguments[-1], "VARIABLE")

    def visit_BUILD_COMMAND(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "BUILD_COMMAND")

        self.register_new_def_point(arguments[0], "VARIABLE")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "TARGET":
                self.register_new_use_point(arguments[i + 1], "TARGET")
                break

    def visit_CMAKE_FILE_API(self, node_data):
        self.generic_visit(node_data)

    def visit_CREATE_TEST_SOURCELIST(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "CREATE_TEST_SOURCELIST"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")

        for argument in arguments[2:]:
            if self.ast.unparse(argument).upper() in ["EXTRA_INCLUDE", "FUNCTION"]:
                self.register_new_use_point(argument, "TEST")

    def visit_DEFINE_PROPERTY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "DEFINE_PROPERTY")

        self.register_new_def_point(arguments[2], "PROPERTY")

        if self.ast.unparse(arguments[-2]).upper() == "INITIALIZE_FROM_VARIABLE":
            self.register_new_def_point(arguments[-1], "VARIABLE")

    def visit_ENABLE_LANGUAGE(self, node_data):
        self.generic_visit(node_data)

    def visit_ENABLE_TESTING(self, node_data):
        self.generic_visit(node_data)

    def visit_EXPORT(self, node_data):
        self.generic_visit(node_data)

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

        if operation in ["EXPORT", "PACKAGE"]:
            print(
                f"Support needed for PACKAGE & EXPORT keywords in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
            )

    def visit_FLTK_WRAP_UI(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "FLTK_WRAP_UI")

        self.register_new_def_point(arguments[0], "VARIABLE", suffix="_FLTK_UI_SRCS")

    def visit_GET_SOURCE_FILE_PROPERTY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_SOURCE_FILE_PROPERTY"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")
        self.register_new_use_point(arguments[-1], "PROPERTY")

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() == "TARGET_DIRECTORY":
                self.register_new_use_point(arguments[i + 1], "TARGET")
                break

    def visit_GET_TARGET_PROPERTY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "GET_TARGET_PROPERTY"
        )

        self.register_new_def_point(arguments[0], "VARIABLE")
        self.register_new_use_point(arguments[1], "TARGET")
        self.register_new_use_point(arguments[-1], "PROPERTY")

    def visit_GET_TEST_PROPERTY(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "GET_TEST_PROPERTY")

        self.register_new_use_point(arguments[0], "TEST")
        self.register_new_use_point(arguments[1], "PROPERTY")
        self.register_new_def_point(arguments[-1], "VARIABLE")

    def visit_INCLUDE_DIRECTORIES(self, node_data):
        self.generic_visit(node_data)

    def visit_INCLUDE_EXTERNAL_MSPROJECT(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "INCLUDE_EXTERNAL_MSPROJECT"
        )

        self.register_new_def_point(arguments[0], "TARGET")

        keywrods = ["GUID", "PLATFORM", "TYPE"]

        i = 2
        while True:
            if len(arguments) > i:
                if self.ast.unparse(arguments[i]).upper() in keywrods:
                    i += 2
                else:
                    for arg in arguments[i:]:
                        self.register_new_use_point(arg, "TARGET")
                    break

    def visit_INCLUDE_REGULAR_EXPRESSION(self, node_data):
        self.generic_visit(node_data)

    def visit_INSTALL(self, node_data):
        self.generic_visit(node_data)

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
            f"Support needed (partial) for {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

    def visit_LINK_DIRECTORIES(self, node_data):
        self.generic_visit(node_data)

    def visit_LINK_LIBRARIES(self, node_data):
        self.generic_visit(node_data)

        # arguments = self.get_sorted_arguments_data_list(node_data, "LINK_LIBRARIES")

        print(
            f"Support needed for {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

    def visit_LOAD_CACHE(self, node_data):
        """
        No support for the old and discouraged signature.
        see: https://cmake.org/cmake/help/v3.27/command/load_cache.html
        """
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "LOAD_CACHE")

        for i, argument in enumerate(arguments):
            unparsed_argument = self.ast.unparse(argument).upper()
            if unparsed_argument == "READ_WITH_PREFIX":
                prefix = self.ast.unparse(arguments[i + 1])
                for arg in arguments[i + 2 :]:
                    self.register_new_use_point(arg, "VARIABLE")
                    self.register_new_def_point(arg, "VARIABLE", prefix=prefix)
                break

    def visit_PROJECT(self, node_data):
        self.generic_visit(node_data)

    def visit_REMOVE_DEFINITIONS(self, node_data):
        self.generic_visit(node_data)

        # arguments = self.get_sorted_arguments_data_list(node_data, "REMOVE_DEFINITIONS")

        print(
            f"Support needed for definitions in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

    def visit_SET_SOURCE_FILES_PROPERTIES(self, node_data):
        self.generic_visit(node_data)

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
            elif self.ast.unparse(argument).upper() == "PROPERTIES":
                j = i + 1
                while True:
                    if len(arguments) > j:
                        self.register_new_def_point(arguments[j], "PROPERTY")
                        j += 2
                    else:
                        break
                break

    def visit_SET_TARGET_PROPERTIES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_TARGET_PROPERTIES"
        )

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() != "PROPERTIES":
                self.register_new_use_point(argument, "TARGET")
                self.register_new_def_point(argument, "TARGET")
            else:
                j = i + 1
                while True:
                    if len(arguments) > j:
                        self.register_new_def_point(arguments[j], "PROPERTY")
                        j += 2
                    else:
                        break
                break

    def visit_SET_TESTS_PROPERTIES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "SET_TESTS_PROPERTIES"
        )

        for i, argument in enumerate(arguments):
            if self.ast.unparse(argument).upper() != "PROPERTIES":
                self.register_new_use_point(argument, "TEST")
                self.register_new_def_point(argument, "TEST")
            else:
                j = i + 1
                while True:
                    if len(arguments) > j:
                        self.register_new_def_point(arguments[j], "PROPERTY")
                        j += 2
                    else:
                        break
                break

    def visit_SOURCE_GROUP(self, node_data):
        self.generic_visit(node_data)

    def visit_TARGET_COMPILE_DEFINITIONS(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_DEFINITIONS"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        print(
            f"Support needed for definitions in {self.ast.unparse(node_data)}, called from {self.ast.file_path}"
        )

    def visit_TARGET_COMPILE_FEATURES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_FEATURES"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

    def visit_TARGET_COMPILE_OPTIONS(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_COMPILE_OPTIONS"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

    def visit_TARGET_INCLUDE_DIRECTORIES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_INCLUDE_DIRECTORIES"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

    def visit_TARGET_LINK_DIRECTORIES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_DIRECTORIES"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

    def visit_TARGET_LINK_LIBRARIES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_LIBRARIES"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        keywords = [
            "PRIVATE",
            "PUBLIC",
            "INTERFACE",
            "LINK_PRIVATE",
            "LINK_PUBLIC",
            "LINK_INTERFACE_LIBRARIES",
        ]

        for i, argument in enumerate(arguments):
            if i == 0:
                continue
            if not self.ast.unparse(argument).upper() in keywords:
                defined_names = self.get_definitions_by_name(argument)
                if list(
                    filter(lambda def_point: def_point.type == "TARGET", defined_names)
                ):
                    self.register_new_use_point(argument, "TARGET")

    def visit_TARGET_LINK_OPTIONS(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_LINK_OPTIONS"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

    def visit_TARGET_PRECOMPILE_HEADERS(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(
            node_data, "TARGET_PRECOMPILE_HEADERS"
        )

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

        if self.ast.unparse(arguments[1]).upper() == "REUSE_FROM":
            self.register_new_use_point(arguments[2], "TARGET")

    def visit_TARGET_SOURCES(self, node_data):
        self.generic_visit(node_data)

        arguments = self.get_sorted_arguments_data_list(node_data, "TARGET_SOURCES")

        self.register_new_use_point(arguments[0], "TARGET")
        self.register_new_def_point(arguments[0], "TARGET")

    def visit_TRY_COMPILE(self, node_data):
        self.generic_visit(node_data)

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

    def visit_TRY_RUN(self, node_data):
        self.generic_visit(node_data)

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

    ########## CTesgt Commands:

    def visit_CTEST_BUILD(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_CONFIGURE(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_COVERAGE(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_EMPTY_BINARY_DIRECTORY(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_MEMCHECK(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_READ_CUSTOM_FILES(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_RUN_SCRIPT(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_SLEEP(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_START(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_SUBMIT(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_TEST(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_UPDATE(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_UPLOAD(self, node_data):
        self.visit_CTEST_CMDs(node_data)

    def visit_CTEST_CMDs(self, node_data):
        """
        All CTEST_* commands are redirected to this method.
        """
        self.generic_visit(node_data)

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
        self.generic_visit(node_data)

    def visit_unquoted_argument(self, node_data):
        # TODO
        # when it's def point
        # when it's use point
        self.generic_visit(node_data)

    def visit_variable_ref(self, node_data):
        self.generic_visit(node_data)

        # TODO (High)
        self.register_new_use_point(node_data, "VARIABLE")
        # For nested variable references

    #############################
    ###### SLICING THE CDU ######
    #############################

    def get_propagation_slices(self):
        """
        This method must be implemented in the language support subclass. As the result,
        Def/Use/Actor objects that are affected have their .is_contaminated attribute set to True.
        Use the .set_contamination() method to set the .is_contaminated attribute to True.
        """
        self.contamination_summary = []
        self.slice_downwards()
        self.slice_upwards()
        return self.contamination_summary

    def updatecontamination_summary(self, entries):
        for entry in entries:
            if list(
                filter(
                    lambda recored_entry: (recored_entry["subject"] == entry["subject"])
                    and (recored_entry["propagation_rule"] == entry["propagation_rule"])
                    and (recored_entry["object"] == entry["object"]),
                    self.contamination_summary,
                )
            ):
                continue
            self.contamination_summary.append(entry)

    def slice_downwards(self):
        previous_summary_length = len(self.contamination_summary)
        modified_def_points = list(
            filter(
                lambda point: point.is_contaminated,
                self.def_points.values(),
            )
        )
        modified_use_points = list(
            filter(
                lambda point: point.is_contaminated,
                self.use_points.values(),
            )
        )
        modified_actor_points = list(
            filter(
                lambda point: point.is_contaminated,
                self.actor_points.values(),
            )
        )

        # def_point is_directly_used_at use_point
        for def_point in modified_def_points:
            if def_point.use_points:
                self.updatecontamination_summary(
                    list(
                        map(
                            lambda use_point: {
                                "subject": def_point,
                                "propagation_rule": "is_directly_used_at"
                                + ("" if not use_point.set_contamination() else ""),
                                "object": use_point,
                            },
                            def_point.use_points,
                        )
                    )
                )

        for use_point in modified_use_points:
            # use_point is_used_in_definition_of def_point
            if use_point.actor_point.def_points:
                self.updatecontamination_summary(
                    list(
                        map(
                            lambda def_point: {
                                "subject": use_point,
                                "propagation_rule": "is_used_in_definition_of"
                                + ("" if not def_point.set_contamination() else ""),
                                "object": def_point,
                            },
                            use_point.actor_point.def_points.values(),
                        )
                    )
                )

            # use_point affects_reachability_of_def/use/scope def_point/use_point/cdu_chain
            if (
                use_point.actor_point.node_data["type"]
                in self.ast.node_actors.conditional_actor_types
            ):
                ast = use_point.ast
                actor_node = use_point.actor_point.node_data
                actor_parent = ast.get_data(ast.get_parent(actor_node))
                actor_siblings = sorted(
                    ast.get_children(actor_parent).values(),
                    key=lambda child_node_data: child_node_data["s_pos"],
                )
                index = actor_siblings.index(actor_node)
                actor_siblings = actor_siblings[index + 1 :]
                affected_nodes_this_scope = ast.get_subtree_nodes(
                    ast.get_data(ast.get_children_by_type(actor_node, "body"))
                )
                affected_nodes_this_scope.update(
                    reduce(
                        lambda a, b: {**a, **b},
                        map(
                            lambda sibling: ast.get_subtree_nodees(sibling),
                            actor_siblings,
                        ),
                        {},
                    )
                )

                affected_use_point_ids = set(
                    affected_nodes_this_scope.keys()
                ).intersection(set(self.use_points.keys()))

                if affected_use_point_ids:
                    # use_point affects_reachability_of_use use_point
                    self.updatecontamination_summary(
                        list(
                            map(
                                lambda point: {
                                    "subject": use_point,
                                    "propagation_rule": "affects_reachability_of_use"
                                    + ("" if not point.set_contamination() else ""),
                                    "object": point,
                                },
                                filter(
                                    lambda point: point.node_data["id"]
                                    in affected_use_point_ids,
                                    self.use_points.values(),
                                ),
                            )
                        )
                    )

                affected_def_point_ids = set(
                    affected_nodes_this_scope.keys()
                ).intersection(set(self.def_points.keys()))

                if affected_def_point_ids:
                    # use_point affects_reachability_of_def def_point
                    self.updatecontamination_summary(
                        list(
                            map(
                                lambda point: {
                                    "subject": use_point,
                                    "propagation_rule": "affects_reachability_of_def"
                                    + ("" if not point.set_contamination() else ""),
                                    "object": point,
                                },
                                filter(
                                    lambda point: point.node_data["id"]
                                    in affected_def_point_ids,
                                    self.def_points.values(),
                                ),
                            )
                        )
                    )

                affected_children_scopes = set(
                    affected_nodes_this_scope.keys()
                ).intersection(
                    set(map(lambda child_chain: child_chain.scope, self.children))
                )
                if affected_children_scopes:
                    children = [
                        child
                        for child in self.children
                        if child.scope in affected_children_scopes
                    ]

                    while children:
                        next_children = []
                        for child_chain in children:
                            # use_point affects_reachability_of_scope cdu_chain
                            self.contamination_summary.append(
                                {
                                    "subject": use_point,
                                    "propagation_rule": "affects_reachability_of_scope",
                                    "object": child_chain,
                                }
                            )
                            # use_point affects_reachability_of_use use_point
                            self.updatecontamination_summary(
                                list(
                                    map(
                                        lambda point: {
                                            "subject": use_point,
                                            "propagation_rule": "affects_reachability_of_use"
                                            + (
                                                ""
                                                if not point.set_contamination()
                                                else ""
                                            ),
                                            "object": point,
                                        },
                                        child_chain.use_points.values(),
                                    )
                                )
                            )
                            # use_point affects_reachability_of_def def_point
                            self.updatecontamination_summary(
                                list(
                                    map(
                                        lambda point: {
                                            "subject": use_point,
                                            "propagation_rule": "affects_reachability_of_def"
                                            + (
                                                ""
                                                if not point.set_contamination()
                                                else ""
                                            ),
                                            "object": point,
                                        },
                                        child_chain.def_points.values(),
                                    )
                                )
                            )
                            next_children += child_chain.children
                        children = next_children

        # actor_point affects_definition_of use_point
        for actor_point in modified_actor_points:
            non_modified_def_points = list(
                filter(
                    lambda def_point: def_point.node_data["operation"] == "no-op",
                    actor_point.def_points.values(),
                )
            )
            if non_modified_def_points:
                self.updatecontamination_summary(
                    list(
                        map(
                            lambda def_point: {
                                "subject": actor_point,
                                "propagation_rule": "affects_definition_of"
                                + ("" if not def_point.set_contamination() else ""),
                                "object": def_point,
                            },
                            non_modified_def_points,
                        )
                    )
                )

        if len(self.contamination_summary) != previous_summary_length:
            self.slice_downwards()

    def slice_upwards(self):
        modified_use_points = list(
            filter(
                lambda point: point.node_data["operation"] != "no-op",
                self.use_points.values(),
            )
        )

        chain = self

        while chain:
            for use_point in modified_use_points:
                self.contamination_summary += list(
                    map(
                        lambda def_point: {
                            "subject": def_point,
                            "propagation_rule": "is_directly_used_at"
                            + ("" if not def_point.set_contamination() else ""),
                            "object": use_point,
                        },
                        filter(
                            lambda def_point: use_point in def_point.use_points,
                            chain.def_points.values(),
                        ),
                    )
                )

            chain = chain.parent
