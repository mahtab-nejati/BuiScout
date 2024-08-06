import language_supports.cmake as cmake


class ConditionalDefUseChains(cmake.ConditionalDefUseChains):
    """
    ##################################
    #### project-specific support ####
    ############## swift #############
    ##################################
    """

    def resolve_add_subdirectory_file_path(self, file_path_node):
        resolved, resolutions = super().resolve_add_subdirectory_file_path(
            file_path_node
        )
        if resolved:
            return resolved, resolutions

        cluster = self.ast.name
        resolution_map = self.sysdiff.file_path_resolution_map[cluster]

        file_path = self.ast.unparse(file_path_node)
        file_path = file_path.strip('"').strip("'")
        file_path = file_path.replace(" ", "")

        if file_path.endswith("${CURL_VERSION_DIR}"):
            resolutions = list(
                map(
                    lambda pair: pair[1],
                    filter(
                        lambda pair: pair[0].endswith("/CMakeLists.txt")
                        and len(pair[0].strip("/").split("/")) == 4,
                        filter(
                            lambda pair: pair[0].startswith("extra/curl/curl-"),
                            resolution_map.items(),
                        ),
                    ),
                )
            )
            return True, resolutions

        if file_path.endswith("${ZLIB_VERSION_DIR}"):
            resolutions = list(
                map(
                    lambda pair: pair[1],
                    filter(
                        lambda pair: pair[0].endswith("/CMakeLists.txt")
                        and len(pair[0].strip("/").split("/")) == 4,
                        filter(
                            lambda pair: pair[0].startswith("extra/zlib/zlib-"),
                            resolution_map.items(),
                        ),
                    ),
                )
            )
            return True, resolutions

        if file_path.endswith("${LIBEVENT_BUNDLE_PATH}"):
            resolutions = list(
                map(
                    lambda pair: pair[1],
                    filter(
                        lambda pair: pair[0].endswith("/CMakeLists.txt")
                        and len(pair[0].strip("/").split("/")) == 4,
                        filter(
                            lambda pair: pair[0].startswith("extra/libevent/libevent-"),
                            resolution_map.items(),
                        ),
                    ),
                )
            )
            return True, resolutions

        if file_path.endswith("${CBOR_BUNDLE_SRC_PATH}"):
            resolutions = list(
                map(
                    lambda pair: pair[1],
                    filter(
                        lambda pair: pair[0].endswith("/CMakeLists.txt")
                        and len(pair[0].strip("/").split("/")) == 4,
                        filter(
                            lambda pair: pair[0].startswith("extra/libcbor/libcbor-"),
                            resolution_map.items(),
                        ),
                    ),
                )
            )
            return True, resolutions

        if file_path.endswith("${FIDO_BUNDLE_SRC_PATH}"):
            resolutions = list(
                map(
                    lambda pair: pair[1],
                    filter(
                        lambda pair: pair[0].endswith("/CMakeLists.txt")
                        and len(pair[0].strip("/").split("/")) == 4,
                        filter(
                            lambda pair: pair[0].startswith("extra/libfido2/libfido2-"),
                            resolution_map.items(),
                        ),
                    ),
                )
            )
            return True, resolutions

        if "${CURRENT_LIBEDIT_DIRECTORY}" in file_path:
            resolutions = list(
                map(
                    lambda pair: pair[1],
                    filter(
                        lambda pair: pair[0].endswith("/src/CMakeLists.txt")
                        and len(pair[0].strip("/").split("/")) == 5,
                        filter(
                            lambda pair: pair[0].startswith("extra/libedit/libedit-"),
                            resolution_map.items(),
                        ),
                    ),
                )
            )
            return True, resolutions

        return False, None

    def visit_CONFIGURE_COMPONENTS(self, node_data):
        self.visit_user_defined_normal_command(node_data)
        cluster = self.ast.name
        resolution_map = self.sysdiff.file_path_resolution_map[cluster]
        resolved_directories = list(
            sorted(
                filter(
                    lambda pair: pair[0].endswith("/CMakeLists.txt"),
                    filter(
                        lambda pair: pair[0].startswith(
                            ("components/", "/components/test/")
                        ),
                        resolution_map.items(),
                    ),
                ),
                key=lambda pair: len(pair[0].strip("/").split("/")),
            )
        )
        self.add_resolved_directories(
            "CONFIGURE_COMPONENTS", node_data, resolved_directories, cluster
        )

    def visit_CONFIGURE_PLUGINS(self, node_data):
        self.visit_user_defined_normal_command(node_data)
        cluster = self.ast.name
        resolution_map = self.sysdiff.file_path_resolution_map[cluster]
        resolved_directories = list(
            sorted(
                filter(
                    lambda pair: pair[0].endswith("/CMakeLists.txt"),
                    filter(
                        lambda pair: pair[0].startswith(("storage/", "plugin/")),
                        resolution_map.items(),
                    ),
                ),
                key=lambda pair: len(pair[0].strip("/").split("/")),
            )
        )
        self.add_resolved_directories(
            "CONFIGURE_PLUGINS", node_data, resolved_directories, cluster
        )

    def add_resolved_directories(
        self, importing_command, node_data, resolved_directories, cluster
    ):
        for _, resolution in resolved_directories:
            if self.sysdiff.file_data[resolution][f"data_flow_{cluster}_analysis"]:
                continue

            # For files with GumTree error
            if self.sysdiff.file_data[resolution]["diff"] is None:
                self.log_file_path_resolution(
                    f"{importing_command} (MySQL-Server)",
                    "PARSER_ERROR",
                    node_data,
                    found_paths=[resolution],
                )
                continue

            # Recursive resolution
            if (resolution == self.ast.file_path) or (
                node_data["id"]
                in self.sysdiff.file_data[resolution]["language_specific_info"][
                    "importers"
                ]
            ):
                self.log_file_path_resolution(
                    f"{importing_command} (MySQL-Server)",
                    "RECURSION",
                    node_data,
                    found_paths=[resolution],
                )
                continue

            # Resolving to entry point
            if resolution == self.sysdiff.current_entry_file:
                self.log_file_path_resolution(
                    f"{importing_command} (MySQL-Server)",
                    "ENTRY_POINT",
                    node_data,
                    found_paths=[resolution],
                )
                continue

            # Resolution is valid
            self.sysdiff.file_data[resolution]["language_specific_info"][
                "importers"
            ].append(node_data["id"])

            target_ast = getattr(
                self.sysdiff.file_data[resolution]["diff"], self.ast.name
            )
            child_scope = self.sysdiff.ConditionalDefUseChains(
                target_ast,
                self.sysdiff,
                scope=self.scope + "/" + node_data["id"],
                parent_scope=self,
                global_scope=self.global_scope,
            )
            self.children.append(child_scope)
            self.sysdiff.append_to_chains(child_scope)

            # Working on added file
            child_scope.analyze()
            self.sysdiff.set_data_flow_file_analysis(
                child_scope.ast.file_path, child_scope.ast.name
            )
            # Finished working on added file
