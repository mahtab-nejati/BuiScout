from utils.visitors import NodeVisitor


class ActorGetter(NodeVisitor):
    argument_actor_types = [
        "normal_command",
        "function_definition",
        "macro_definition",
        "block_definition",
        "if_clause",
        "elseif_clause",
        "else_clause",
        "endif_clause",
        "while_clause",
        "endwhile_clause",
        "foreach_clause",
        "endforeach_clause",
    ]
    conditional_actor_types = [
        "if_clause",
        "elseif_clause",
        "else_clause",
        "while_clause",
    ]

    def generic_visit(self, node_data):
        if node_data["type"] in self.argument_actor_types:
            return node_data

        return max(
            filter(
                lambda ancestor_data: ancestor_data["type"]
                in self.argument_actor_types,
                self.ast.get_ancestors(node_data).values(),
            ),
            key=lambda ancestor_data: ancestor_data["level"],
        )
