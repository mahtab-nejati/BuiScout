from utils.visitors import NodeVisitor


class ExtendedProcessor(NodeVisitor):
    """
    To skip, uncomment the generic_visit method definition below.
    """

    # def generic_visit(self, node_data):
    #     return

    def check_and_update_node_operation(self, node_data):
        if node_data["operation"] != "no-op":
            return self.generic_visit(node_data)

        subtree_nodes = self.ast.get_subtree_nodes(node_data)
        affected_nodes = filter(
            lambda subtree_node_data: subtree_node_data["operation"] != "no-op",
            subtree_nodes.values(),
        )
        for _ in affected_nodes:
            self.ast.update_node_operation(node_data, "updated")
            break

        return self.generic_visit(node_data)

    def visit_function_definition(self, node_data):
        return self.check_and_update_node_operation(node_data)

    def visit_macro_definition(self, node_data):
        return self.check_and_update_node_operation(node_data)

    def visit_normal_command(self, node_data):
        return self.check_and_update_node_operation(node_data)

    def visit_condition(self, node_data):
        parent_data = self.ast.get_data(self.ast.get_parent(node_data))
        if parent_data["operation"] != "no-op":
            return self.generic_visit(node_data)

        subtree_nodes = self.ast.get_subtree_nodes(node_data)
        affected_nodes = filter(
            lambda subtree_node_data: subtree_node_data["operation"] != "no-op",
            subtree_nodes.values(),
        )
        for _ in affected_nodes:
            self.ast.update_node_operation(parent_data, "updated")
            break

        return self.generic_visit(node_data)
