from utils.visitors import NodeVisitor


class Unparser(NodeVisitor):
    def get_sorted_children_data_list(self, node_data):
        """
        Returns the list of argument nodes' node_data of the command node, sorted by position.
        """
        return sorted(
            self.ast.get_children(node_data).values(),
            key=lambda child_data: child_data["s_pos"],
        )

    def get_sorted_children_unparsed_list(self, node_data, masked_types=[]):
        return list(
            map(
                lambda child_data: self.visit(child_data, masked_types),
                self.get_sorted_children_data_list(node_data),
            )
        )

    def visit(self, node_data, masked_types=[]):
        """
        Visit a node.
        The input is the output of the ast.get_data(node), i.e., node_data.
        """
        if node_data["type"] in masked_types:
            return "...MASKED_CONTENT..."

        if node_data["content"]:
            return node_data["content"]

        method = "visit_" + node_data["type"]
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node_data, masked_types)

    def generic_visit(self, node_data, masked_types=[]):
        return "".join(self.get_sorted_children_unparsed_list(node_data, masked_types))

    def visit_source_file(self, node_data, masked_types=[]):
        return "\n".join(
            self.get_sorted_children_unparsed_list(node_data, masked_types)
        ).replace("\n\n", "\n")

    def visit_body(self, node_data, masked_types=[]):
        return (
            "\n"
            + "\n".join(self.get_sorted_children_unparsed_list(node_data, masked_types))
            + "\n"
        ).replace("\n\n", "\n")

    def visit_condition(self, node_data, masked_types=[]):
        return (
            " ".join(self.get_sorted_children_unparsed_list(node_data, masked_types))
            .replace("( ", "(")
            .replace(" )", ")")
        )

    def visit_arguments(self, node_data, masked_types=[]):
        return (
            " ".join(self.get_sorted_children_unparsed_list(node_data, masked_types))
            .replace("( ", "(")
            .replace(" )", ")")
        )

    def visit_if_statement(self, node_data, masked_types=[]):
        return "\n".join(
            self.get_sorted_children_unparsed_list(node_data, masked_types)
        ).replace("\n\n", "\n")

    def visit_while_statement(self, node_data, masked_types=[]):
        return "\n".join(
            self.get_sorted_children_unparsed_list(node_data, masked_types)
        ).replace("\n\n", "\n")

    def visit_foreach_statement(self, node_data, masked_types=[]):
        return "\n".join(
            self.get_sorted_children_unparsed_list(node_data, masked_types)
        ).replace("\n\n", "\n")

    def visit_function_definition(self, node_data, masked_types=[]):
        return "\n".join(
            self.get_sorted_children_unparsed_list(node_data, masked_types)
        ).replace("\n\n", "\n")

    def visit_function_header(self, node_data, masked_types=[]):
        return (
            (
                " ".join(
                    self.get_sorted_children_unparsed_list(node_data, masked_types)
                )
                + " "
            )
            .replace(" ( ", "(")
            .replace(" ) ", ")")
        )

    def visit_macro_definition(self, node_data, masked_types=[]):
        return "\n".join(
            self.get_sorted_children_unparsed_list(node_data, masked_types)
        ).replace("\n\n", "\n")

    def visit_macro_header(self, node_data, masked_types=[]):
        return (
            (
                " ".join(
                    self.get_sorted_children_unparsed_list(node_data, masked_types)
                )
                + " "
            )
            .replace(" ( ", "(")
            .replace(" ) ", ")")
        )

    def visit_block_definition(self, node_data, masked_types=[]):
        return "\n".join(
            self.get_sorted_children_unparsed_list(node_data, masked_types)
        ).replace("\n\n", "\n")

    # def _old_unparse(self, node_data, masked_types=[]):
    #     subtree_nodes = self.ast.get_subtree_nodes(node_data)
    #     if masked_types:
    #         masked_nodes_heads = dict(
    #             filter(
    #                 lambda node_data: node_data[1]["type"] in masked_types,
    #                 subtree_nodes.items(),
    #             )
    #         )
    #         all_masked_nodes_ids = list(
    #             set(
    #                 reduce(
    #                     lambda a, b: {**a, **b},
    #                     map(
    #                         lambda masked_node_data: self.ast.get_subtree_nodes(
    #                             masked_node_data
    #                         ),
    #                         masked_nodes_heads.values(),
    #                     ),
    #                     {},
    #                 ).keys(),
    #             ).difference(set(masked_nodes_heads.keys()))
    #         )
    #         subtree_nodes = dict(
    #             filter(
    #                 lambda subtree_node_data: (
    #                     subtree_node_data[1]["id"] not in all_masked_nodes_ids
    #                 ),
    #                 subtree_nodes.items(),
    #             )
    #         )

    #     text = " ".join(
    #         map(
    #             lambda cp: "..." if cp[0] in masked_types else cp[1],
    #             sorted(
    #                 map(
    #                     lambda node_data: (
    #                         node_data["type"],
    #                         node_data["content"],
    #                         node_data["s_pos"],
    #                     ),
    #                     subtree_nodes.values(),
    #                 ),
    #                 key=lambda cp: cp[-1],
    #             ),
    #         )
    #     )

    #     dots = re.compile(r"(\.\.\.\s?)+")
    #     spaces = re.compile(r"\s+")

    #     text = dots.sub("... ", text)
    #     text = spaces.sub(" ", text)

    #     return text.strip()
