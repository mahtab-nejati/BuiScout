from pathlib import Path
import language_supports.cmake as cmake
from utils.configurations import ROOT_FILE
from utils.exceptions import DebugException


class ConditionalDefUseChains(cmake.ConditionalDefUseChains):
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
                return (
                    True,
                    list(
                        filter(
                            lambda res: res in self.sysdiff.file_data,
                            map(
                                lambda arch: f"arch/{arch}/CMakeLists.txt",
                                self.sysdiff.configs["arch"],
                            ),
                        )
                    ),
                )

        # TODO: Come up with a general solution
        if self.ast.file_path == "arch/posix/CMakeLists.txt":
            if (
                file_path
                == "${CMAKE_HOST_SYSTEM_NAME}.${CMAKE_HOST_SYSTEM_PROCESSOR}.cmake"
            ):
                return True, "arch/posix/Linux.aarch64.cmake"

        if self.ast.file_path == "boards/CMakeLists.txt":
            if file_path == "${BOARD_DIR}":
                return (
                    True,
                    list(
                        filter(
                            lambda res: res in self.sysdiff.file_data,
                            map(
                                lambda boards: f"{boards}/CMakeLists.txt",
                                self.sysdiff.configs["boards"],
                            ),
                        )
                    ),
                )

        if self.ast.file_path == "CMakeLists.txt":
            if file_path == "${SOC_DIR}/${ARCH}":
                return True, list(
                    filter(
                        lambda res: res in self.sysdiff.file_data,
                        map(
                            lambda arch: f"soc/{arch}/CMakeLists.txt",
                            self.sysdiff.configs["arch"],
                        ),
                    )
                )
            if file_path == "${SOC_DIR}/${ARCH}/${SOC_PATH}":
                return True, list(
                    map(
                        lambda soc_family: f"{soc_family}/CMakeLists.txt",
                        filter(
                            lambda soc_family: (
                                (
                                    f"{soc_family}/CMakeLists.txt"
                                    in self.sysdiff.file_data
                                )
                                and (
                                    not (
                                        f"{'/'.join(soc_family.split('/')[:-1])}/CMakeLists.txt"
                                        in self.sysdiff.file_data
                                    )
                                )
                            ),
                            self.sysdiff.configs["soc_family"],
                        ),
                    ),
                )

        if self.ast.file_path in list(
            map(lambda arch: f"soc/{arch}/CMakeLists.txt", self.sysdiff.configs["arch"])
        ):
            if file_path in ["${SOC_FAMILY}", "${SOC_NAME}"]:
                return True, list(
                    map(
                        lambda soc_family: f"{soc_family}/CMakeLists.txt",
                        filter(
                            lambda soc_family: (
                                (
                                    soc_family.startswith(
                                        (
                                            "/".join(self.ast.file_path.split("/")[:-1])
                                            + "/"
                                        )
                                    )
                                )
                                and (
                                    f"{soc_family}/CMakeLists.txt"
                                    in self.sysdiff.file_data
                                )
                            ),
                            self.sysdiff.configs["soc_family"],
                        ),
                    )
                )

        if self.ast.file_path in list(
            map(
                lambda soc_family: f"{soc_family}/CMakeLists.txt",
                self.sysdiff.configs["soc_family"],
            )
        ):
            if file_path == "${SOC_SERIES}":
                return True, list(
                    map(
                        lambda soc_series: f"{soc_series}/CMakeLists.txt",
                        filter(
                            lambda soc_series: (
                                (
                                    soc_series.startswith(
                                        (
                                            "/".join(self.ast.file_path.split("/")[:-1])
                                            + "/"
                                        )
                                    )
                                )
                                and (
                                    f"{soc_series}/CMakeLists.txt"
                                    in self.sysdiff.file_data
                                )
                            ),
                            self.sysdiff.configs["soc_series"],
                        ),
                    )
                )

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

        (
            resolution_success,
            added_file,
        ) = self.resolve_added_subdirectory_file_path_best_effort(arguments[1])

        if not resolution_success:
            # For failures due to multiple resolutions
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

        if isinstance(added_file, str):
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
                in self.sysdiff.file_data[added_file]["language_specific_info"][
                    "importers"
                ]
            ):
                print(
                    f"Skipping recursive resolution for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return self.generic_visit(node_data)

            # Resolving to entry point
            if added_file == ROOT_FILE:
                print(
                    f"Resolving to project's entry point for {self.ast.unparse(node_data)} called from {self.ast.file_path}"
                )
                return self.generic_visit(node_data)

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

        return self.generic_visit(node_data)
