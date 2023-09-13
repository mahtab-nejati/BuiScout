from pathlib import Path
import language_supports.cmake as cmake
from utils.configurations import ROOT_FILE, REPOSITORY
from utils.exceptions import DebugException


class ConditionalDefUseChains(cmake.ConditionalDefUseChains):
    """
    ##################################
    #### project-specific support ####
    ############## hpx ###############
    ##################################
    """

    def get_manually_resolved_path(self, file_path_node):
        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")
        if file_path.lower() == "${subdir}":
            current_path = "/".join(self.ast.file_path.split("/")[:-1])
            return True, list(
                set(
                    filter(
                        lambda f: f in self.sysdiff.file_data,
                        map(
                            lambda r: str(r).replace(REPOSITORY + "/", "")
                            + "/CMakeLists.txt",
                            (Path(REPOSITORY) / current_path).iterdir(),
                        ),
                    )
                )
            )
        return super().get_manually_resolved_path(file_path_node)

    def resolve_hpx_included_file_path_best_effort(self, file_path_node):
        """
        Returns (success_flag, resolution)
        """
        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.replace(" ", "")
        candidate_path = file_path.split("}")[-1]
        if not candidate_path:
            return False, None
        candidate_path = "HPX_" + candidate_path.strip("./")

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

    def visit_HPX_INCLUDE(self, node_data):
        arguments = self.get_sorted_arguments_data_list(node_data, "HPX_INCLUDE")

        # For file-level analysis (No system provided)
        if self.sysdiff is None:
            self.remove_condition_from_reachability_stack()
            return self.generic_visit(node_data)

        for argument in arguments:
            (
                resolution_success,
                included_file,
            ) = self.resolve_hpx_included_file_path_best_effort(argument)

            if not resolution_success:
                # For failures due to multiple resolutions
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

            # Successful resolution
            if isinstance(included_file, str):
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

        return self.generic_visit(node_data)
