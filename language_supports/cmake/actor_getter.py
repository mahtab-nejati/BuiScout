from utils.visitors import NodeVisitor


class ActorGetter(NodeVisitor):
    argument_actor_types = [
        "normal_command",
        "if_statement",
        "while_statement",
        "foreach_statement",
    ]

    def generic_visit(self, node_data):
        return node_data

    def visit_function_definition(self, node_data):
        return self.generic_visit(node_data)

    def visit_macro_definition(self, node_data):
        return self.generic_visit(node_data)

    def visit_bracket_argument(self, node_data):
        return self.visit_argument(node_data)

    def visit_quoted_argument(self, node_data):
        return self.visit_argument(node_data)

    def visit_unquoted_argument(self, node_data):
        return self.visit_argument(node_data)

    def visit_variable_ref(self, node_data):
        return self.visit_argument(node_data)

    def visit_argument(self, node_data):
        return max(
            filter(
                lambda ancestor_data: ancestor_data["type"]
                in self.argument_actor_types,
                self.ast.get_ancestors(node_data).values(),
            ),
            key=lambda ancestor_data: ancestor_data["level"],
        )
