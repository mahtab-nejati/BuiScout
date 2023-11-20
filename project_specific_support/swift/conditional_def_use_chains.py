import language_supports.cmake as cmake


class ConditionalDefUseChains(cmake.ConditionalDefUseChains):
    """
    ##################################
    #### project-specific support ####
    ############## swift #############
    ##################################
    """

    def visit_ADD_SWIFT_TOOL_SUBDIRECTORY(self, node_data):
        self.visit_user_defined_add_subdirectory(node_data)

    def visit_ADD_SWIFT_LIB_SUBDIRECTORY(self, node_data):
        self.visit_user_defined_add_subdirectory(node_data)

    def visit_user_defined_add_subdirectory(self, node_data):
        self.visit_user_defined_normal_command(node_data)
        self.visit_ADD_SUBDIRECTORY(node_data)
