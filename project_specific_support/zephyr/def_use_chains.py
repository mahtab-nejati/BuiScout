from pathlib import Path
import language_supports.cmake as cmake
from utils.configurations import REPOSITORY
from utils.exceptions import DebugException


class DefUseChains(cmake.DefUseChains):
    """
    ##################################
    #### project-specific support ####
    ############# zephyr #############
    ##################################
    """

    def get_manually_resolved_path(self, file_path_node):
        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")

        if self.ast.file_path == "arch/CMakeLists.txt":
            if file_path == "${ARCH_DIR}/${ARCH}":
                directory = Path(REPOSITORY) / "arch"
                resolutions = list(
                    filter(
                        lambda r: (
                            not r.endswith(("/.DS_Store", "/CMakeLists.txt", "/common"))
                        ),
                        map(
                            lambda p: str(p).replace(REPOSITORY + "/", ""),
                            directory.iterdir(),
                        ),
                    )
                )
                return {"mode": "parallel", "resolution": resolutions}

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

    def visit_user_defined_normal_command(self, node_data):
        #  TODO: Fix after implementing callables and scopes
        # command_identifier = self.ast.unparse(
        #     self.ast.get_data(self.ast.get_children_by_type(node_data, "identifier"))
        # ).upper()
        # if command_identifier.endswith(("_IFDEF")):
        #     arguments = self.get_sorted_arguments_data_list(
        #         node_data, command_identifier
        #     )
        #     self.add_condition_to_reachability_stack_ifdef(arguments[0])
        #     self.remove_condition_from_reachability_stack()
        return super().visit_user_defined_normal_command(node_data)

    def add_condition_to_reachability_stack_ifdef(self, condition_node_data):
        condition = "${ " + self.ast.unparse(condition_node_data) + " }"
        self.reachability_stack.append(condition)

    def visit_ADD_SUBDIRECTORY_IFDEF(self, node_data):
        arguments = self.get_sorted_arguments_data_list(
            node_data, "ADD_SUBDIRECTORY_IFDEF"
        )

        self.add_condition_to_reachability_stack_ifdef(arguments[0])

        # For file-level analysis (No system provided)
        if self.sysdiff is None:
            self.remove_condition_from_reachability_stack()
            return self.generic_visit(node_data)

        added_file = self.resolve_add_subdirectory_file_path_best_effort(arguments[1])

        # For manual file path resolution setup
        if isinstance(added_file, list):
            print(
                f"Multiple path found for {self.ast.unparse(node_data)}: {' , '.join(added_file)} called from {self.ast.file_path}"
            )
            self.remove_condition_from_reachability_stack()
            return self.generic_visit(node_data)

        # For files that do not exist in the project
        # or files that are refered to using a variable
        if added_file is None:
            print(
                f"Cannot resolve path for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            self.remove_condition_from_reachability_stack()
            return self.generic_visit(node_data)

        # For manaully skipped files
        if added_file.upper() == "SKIP":
            print(
                f"Skipping manually set for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            self.remove_condition_from_reachability_stack()
            return self.generic_visit(node_data)

        # For files with GumTree error
        if self.sysdiff.file_data[added_file]["diff"] is None:
            print(f"Parser error for {self.ast.unparse(node_data)}")
            self.remove_condition_from_reachability_stack()
            return self.generic_visit(node_data)

        # Recursive resolution
        if (added_file == self.ast.file_path) or (
            node_data["id"]
            in self.sysdiff.file_data[added_file]["language_specific_info"]["importers"]
        ):
            print(
                f"Skipping recursive resolution for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
            )
            self.remove_condition_from_reachability_stack()
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
        self.remove_condition_from_reachability_stack()
        return self.generic_visit(node_data)

    def project_specific_add_directory(self, node_data, added_files):
        mode = added_files["mode"]
        resolutions = added_files["resolution"]

        for directory in resolutions:
            if directory + "/CMakeLists.txt" in self.sysdiff.file_data:
                print(directory + "/CMakeLists.txt")
