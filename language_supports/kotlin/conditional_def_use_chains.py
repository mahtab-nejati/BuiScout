import data_flow_analysis as cm
from utils.exceptions import DebugException, MissingArgumentsException


class ConditionalDefUseChains(cm.ConditionalDefUseChains):
    def get_sorted_node_children_data_list(self, node_data):
        """
        Returns a list of node_data objects, representing children node_data, sorted by position.
        """
        # Check for MissingArgumentsException
        children = self.ast.get_children(node_data)

        # node_data of each argument, positionally sorted
        return sorted(
            children.values(),
            key=lambda child_node_data: child_node_data["s_pos"],
        )

    def visit_variable_declaration(self, node_data):
        self.register_new_def_point(node_data)

        return self.generic_visit(node_data)

    def visit_directly_assignable_expression(self, node_data):
        identifier = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "simple_identifier")
        )
        if not identifier:
            return self.generic_visit(node_data)
        self.register_new_def_point(identifier)

        return self.generic_visit(node_data)

    # Visit function arguments
    def visit_value_argument(self, node_data):
        identifier = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "simple_identifier")
        )
        if not identifier:
            return self.generic_visit(node_data)
        self.register_new_use_point(identifier)

        return self.generic_visit(node_data)

    def visit_call_expression(self, node_data):
        children = self.get_sorted_node_children_data_list(node_data)
        if (
            children[0]["type"] == "navigation_expression"
            and self.ast.unparse(children[0]) == "tasks . register"
        ):
            arguments = self.ast.get_subtree_nodes(children[1])
            function_arguments = list(
                filter(
                    lambda child_node_data: child_node_data["type"] == "value_argument",
                    arguments.values(),
                )
            )
            function_arguments_sorted = sorted(
                function_arguments,
                key=lambda child_node_data: child_node_data["s_pos"],
            )
            self.register_new_def_point(function_arguments_sorted[0])

        return self.generic_visit(node_data)

    def visit_function_declaration(self, node_data):
        identifier = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "simple_identifier")
        )
        if not identifier:
            return self.generic_visit(node_data)
        self.register_new_def_point(identifier)

        return self.generic_visit(node_data)

    def visit_class_declaration(self, node_data):
        identifier = self.ast.get_data(
            self.ast.get_children_by_type(node_data, "simple_identifier")
        )
        if not identifier:
            return self.generic_visit(node_data)
        self.register_new_def_point(identifier)

        return self.generic_visit(node_data)
