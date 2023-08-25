import language_supports.cmake as cmake


class DefUseChains(cmake.DefUseChains):
    """
    ##################################
    #### project-specific support ####
    ############# zephyr #############
    ##################################
    """

    def visit_user_defined_normal_command(self, node_data):
        self.register_new_use_point(node_data, "COMMAND")

        command_identifier = self.ast.unparse(
            self.ast.get_data(self.ast.get_children_by_type(node_data, "identifier"))
        ).upper()

        if command_identifier.endswith(("_IFDEF")):
            arguments = self.get_sorted_arguments_data_list(
                node_data, command_identifier
            )
            self.add_condition_to_reachability_stack(arguments[0])

            method = "visit_" + command_identifier
            visitor = getattr(self, method, self.generic_visit)
            visitor(node_data)

            self.remove_condition_from_reachability_stack()

        return self.generic_visit(node_data)

    def visit_ADD_SUBDIRECTORY_IFDEF(self, node_data):
        """
        Use example:
            https://cmake.org/pipermail/cmake/2007-November/017897.html
            https://stackoverflow.com/a/6891527
            https://stackoverflow.com/a/49989597
            https://stackoverflow.com/a/48510440
        """
        arguments = self.get_sorted_arguments_data_list(
            node_data, "ADD_SUBDIRECTORY_IFDEF"
        )

        arguments = self.get_sorted_arguments_data_list(node_data, "ADD_SUBDIRECTORY")

        # For file-level analysis (No system provided)
        if self.sysdiff is None:
            return self.generic_visit(node_data)

        added_directory_path = self.ast.unparse(arguments[1])
        added_file = self.resolve_add_subdirectory_file_path_best_effort(
            added_directory_path
        )

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
