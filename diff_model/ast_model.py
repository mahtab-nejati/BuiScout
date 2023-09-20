import json
import networkx as nx
import pandas as pd
from pathlib import Path
from networkx.drawing.nx_agraph import write_dot
from networkx.readwrite import json_graph
from functools import reduce
import importlib
from copy import deepcopy
from utils.helpers import parse_label
from utils.exceptions import (
    MissingRootException,
    ConfigurationException,
)


class AST(nx.DiGraph):
    """
    Represents a build specification file state (version).
    """

    def __init__(
        self,
        *args,
        file_path=None,
        file_saved_as=None,
        commit_hash=None,
        LANGUAGE=None,
        diff=None,
        **kwargs,
    ):
        super(AST, self).__init__(*args, **kwargs)
        # SET language support tools
        language_support_tools = importlib.import_module(
            f"language_supports.{LANGUAGE}"
        )
        self.LANGUAGE = LANGUAGE
        self.ROOT_TYPE = language_support_tools.ROOT_TYPE
        self.IGNORED_TYPES = language_support_tools.IGNORED_TYPES

        self.diff = diff

        # Set file and commit_hash
        self.file_path = file_path
        self.file_saved_as = file_saved_as
        self.commit_hash = commit_hash

        self.set_node_universal_ids()

        # Remove extra nodes
        none_nodes = list(
            filter(lambda node: node[-1].get("label") is None, self.nodes.items())
        )
        for node in none_nodes:
            self.remove_node(node[0])

        # Set node attributes
        # The head of the AST (self.ROOT_TYPE) has level=0.
        self.set_node_attributes()
        self.set_nodes_levels()

        # Set AST attributes
        # Also sets self.depth = max(levels)+1
        self.set_root()
        self.depth = max(
            [0] + list(map(lambda node: node["level"] + 1, self.nodes.values()))
        )
        self.set_affected_nodes()
        self.summarized_nodes = dict()

        # Slice up changes
        self.set_slice()

        # Set up language support tools
        self.extended_processor = language_support_tools.ExtendedProcessor(self)
        self.unparser = language_support_tools.Unparser(self)
        self.node_names = language_support_tools.NameGetter(self)
        self.node_actors = language_support_tools.ActorGetter(self)
        self.stringifier = language_support_tools.Stringifier(self)

    def export_dot(self, path, *args, **kwargs):
        """
        Export the AST into a .dot file (included in the path)
        """
        write_dot(self, path)

    def set_node_universal_ids(self):
        self.node_id_map = dict(
            map(
                lambda node_id: (
                    node_id,
                    f"{self.file_saved_as}:{node_id}",
                ),
                self.nodes,
            )
        )
        nx.relabel_nodes(self, self.node_id_map, copy=False)

    def set_node_attributes(self, *args, **kwargs):
        """
        Parses node label and cleans it into a dict of {'node_id': dict(nod_data)}
        using the self.clean_node_attributes.
        Sets the extracted cleaned data as node attributes.
        """
        node_attrs = list(
            map(
                lambda node: self.clean_node_attributes(node[0], node[-1]),
                self.nodes.items(),
            )
        )
        nx.set_node_attributes(self, reduce(lambda a, b: {**a, **b}, node_attrs))

    def set_nodes_levels(self, *args, **kwargs):
        """
        Sets the attribute "level" for nodes and self.depth for AST pair.
        The head of the AST (self.ROOT_TYPE) has level=0.
        """
        depth = 0
        current_level_nodes = dict(
            filter(
                lambda node: node[-1]["type"] == self.ROOT_TYPE,
                self.nodes.items(),
            )
        )

        while current_level_nodes.keys():
            next_level_nodes = dict()
            for node_id, node_data in current_level_nodes.items():
                nx.set_node_attributes(self, {node_id: {"level": depth}})
                next_level_nodes.update(self.get_children(node_data))
            depth += 1
            current_level_nodes = dict(next_level_nodes)

    def clean_node_attributes(self, node_id, node_data, *args, **kwargs):
        """
        Parses node label and cleans it into a dict of {'node_id': dict(nod_data)}
        """
        label_content = parse_label(node_data["label"])
        color = node_data["color"]

        del node_data["label"]

        if color == "red":
            operation = "deleted"
        elif color == "green":
            operation = "added"
        elif color == "blue":
            operation = "moved"
        elif color == "orange":
            operation = "updated"
        else:
            operation = "no-op"

        attrs = {node_id: {"id": node_id, "operation": operation, **label_content}}

        attrs[node_id][
            "label"
        ] = f'cluster: {self.name}\ntype: {attrs[node_id]["type"]}\n'

        attrs[node_id][
            "label"
        ] += f'content: {attrs[node_id]["content"]}\npostion: {attrs[node_id]["s_pos"]}-{attrs[node_id]["e_pos"]}'

        return attrs

    def update_node_operation(self, node_data, operation, *args, **kwargs):
        if node_data["operation"] != operation:
            self.nodes[node_data["id"]]["operation"] = operation

            if operation == "deleted":
                self.nodes[node_data["id"]]["color"] = "red"
            elif operation == "added":
                self.nodes[node_data["id"]]["color"] = "green"
            elif operation == "moved":
                self.nodes[node_data["id"]]["color"] = "blue"
            elif operation == "updated":
                self.nodes[node_data["id"]]["color"] = "orange"
            else:
                self.nodes[node_data["id"]]["color"] = "lightgrey"

            if not self.diff is None:
                match_AST, match_node_data = self.diff.reveal_match(node_data)
                if match_node_data:
                    match_AST.update_node_operation(match_node_data, operation)

        return

    def get_data(self, node, *args, **kwargs):
        """
        Retruns the node attributes when node is a dictionary {'node_id': dict(nod_data)}
        with only one or zero entries (nodes)
        """
        try:
            return list(node.values())[0]
        except IndexError:
            return {}

    def get_name(self, node_data, *args, **kwargs):
        """
        Returns the proper name of the node based on language-specific rules
        for data flow analysis
        """
        return self.node_names.visit(node_data)

    def get_actor(self, node_data, *args, **kwaargs):
        """
        Returns the proper actor that consumes the node based on language-specific rules
        for data flow analysis
        """
        return self.node_actors.visit(node_data)

    def get_location(self, node_data, *args, **kwargs):
        """
        Returns the location of the node_data
        """
        if self.file_saved_as:
            file_saved_as = self.file_saved_as
        else:
            file_saved_as = "<UNKNOWN_FILE>"
        return f' at {file_saved_as}:{node_data["s_pos"]}-{node_data["e_pos"]}'

    def set_root(self, *args, **kwargs):
        """
        Returns the root node of the cluster as a dict of {'node_id': dict(nod_data)}
        """
        root = dict(
            filter(
                lambda node: node[-1]["type"] == self.ROOT_TYPE,
                self.nodes.items(),
            )
        )
        if root:
            self.root = root
        else:
            raise MissingRootException(self.ROOT_TYPE, self.file_saved_as)

    def get_parent(self, node_data, *args, **kwargs):
        """
        Returns the parent of the node as a dict of {'node_id': dict(nod_data)}
        """
        return dict(
            map(
                lambda parent_id: (parent_id, self.nodes[parent_id]),
                self.predecessors(node_data["id"]),
            )
        )

    def get_ancestors(self, node_data, *args, **kwargs):
        """
        Returns the ancestors tree of the node (all nodes from root to node_data)
        as a dict of {'node_id': dict(nod_data)} sorted by level.
        """
        if node_data["type"] != self.ROOT_TYPE:
            parent_data = self.get_data(self.get_parent(node_data))
            ancestors = {
                parent_data["id"]: parent_data,
                **self.get_ancestors(parent_data),
            }
        else:
            return {}
        return dict(sorted(ancestors.items(), key=lambda node: node[1]["level"]))

    def get_children(self, node_data, *args, **kwargs):
        """
        Returns the children of the node as a dict of {'node_id': dict(nod_data)}
        """
        return dict(
            map(
                lambda child_id: (child_id, self.nodes[child_id]),
                self.successors(node_data["id"]),
            )
        )

    def get_children_by_type(self, node_data, child_type, *args, **kwargs):
        """
        Returns the children of the node with child_type as a dict of {'node_id': dict(nod_data)}
        """
        return dict(
            filter(
                lambda node: node[-1]["type"] == child_type,
                self.get_children(node_data).items(),
            )
        )

    def get_children_by_content(
        self, node_data, child_content, matching_method="exact", *args, **kwargs
    ):
        """
        Returns the children of the node with child_content as a dict of {'node_id': dict(nod_data)}.
        The matching_method argument specifies which nodes are returned and can be set to
        "exact", "contains", "starts_with", or "ends_with".
        """
        child_content = child_content.lower()
        if matching_method == "exact":
            return dict(
                filter(
                    lambda node: node[-1]["content"].lower() == child_content,
                    self.get_children(node_data).items(),
                )
            )
        if matching_method == "contains":
            return dict(
                filter(
                    lambda node: child_content in node[-1]["content"].lower(),
                    self.get_children(node_data).items(),
                )
            )
        if matching_method == "starts_with":
            return dict(
                filter(
                    lambda node: node[-1]["content"].lower().startswith(child_content),
                    self.get_children(node_data).items(),
                )
            )
        if matching_method == "ends_with":
            return dict(
                filter(
                    lambda node: node[-1]["content"].lower().endswith(child_content),
                    self.get_children(node_data).items(),
                )
            )

    def get_child_by_order(self, node_data, child_order, *args, **kwargs):
        """
        Returns one child (at child_order based on s_pos) as a dict of {'node_id': dict(nod_data)}.
        """
        child = sorted(
            list(self.get_children(node_data).values()),
            key=lambda node_data: node_data["s_pos"],
        )[child_order]
        return {child["id"]: child}

    def set_affected_nodes(self, *args, **kwargs):
        """
        Returns the affected nodes in the change from the AST
        as a dict of {'node_id': dict(nod_data)}.
        Currently excludes comments as GumTree underperforms and
        poses overplotting problems.
        """
        affected_nodes = dict(
            filter(lambda node: node[-1]["operation"] != "no-op", self.nodes.items())
        )
        ignored_nodes = list(
            filter(
                lambda node_data: node_data["type"] in self.IGNORED_TYPES,
                affected_nodes.values(),
            )
        )
        if ignored_nodes:
            ignored_subtree_nodes = reduce(
                lambda a, b: {**a, **b},
                map(
                    lambda ignored_node_data: self.get_subtree_nodes(ignored_node_data),
                    ignored_nodes,
                ),
            )
            affected_nodes = dict(
                filter(
                    lambda node: node[-1]["id"] not in ignored_subtree_nodes,
                    affected_nodes.items(),
                )
            )
        self.affected_nodes = affected_nodes

    def set_slice(self, *args, **kwargs):
        """
        Sets self.slice as the contaminated slice from the cluster as a SlicedAST() object.
        """
        if not self.affected_nodes.keys():
            slice_nodes = self.root
            slice_edges = []
        else:
            slice_nodes = deepcopy(self.affected_nodes)
            slice_nodes.update(
                reduce(
                    lambda a, b: {**a, **b},
                    map(
                        lambda node_data: self.get_ancestors(node_data),
                        slice_nodes.values(),
                    ),
                )
            )
            slice_nodes.update(
                reduce(
                    lambda a, b: {**a, **b},
                    map(
                        lambda node_data: self.get_subtree_nodes(node_data),
                        filter(  # TODO: Can provide better pruning with options...
                            lambda node_data: node_data["level"] == 1,
                            slice_nodes.values(),
                        ),
                    ),
                )
            )
            slice_edges = list(
                filter(
                    lambda edge: edge[0] in slice_nodes and edge[1] in slice_nodes,
                    self.edges.data(),
                )
            )

        # Create slice
        self.slice = ASTSlice(
            self.name,
            slice_nodes,
            slice_edges,
            LANGUAGE=self.LANGUAGE,
            diff=self.diff,
        )

    def get_subtree_nodes(self, head_data, *args, **kwargs):
        """
        Returns the subtree with head_data as the head of the subtree
        as a dictionary of {'node_id':{node_data}}
        """
        subtree_nodes = {head_data["id"]: head_data}
        next_level_nodes = reduce(
            lambda a, b: {**a, **b},
            map(
                lambda node_data: self.get_children(node_data),
                subtree_nodes.values(),
            ),
        )
        if next_level_nodes.keys():
            next_level_jungle = reduce(
                lambda a, b: {**a, **b},
                map(
                    lambda node_data: self.get_subtree_nodes(node_data),
                    next_level_nodes.values(),
                ),
            )
            subtree_nodes.update(next_level_jungle)
        return subtree_nodes

    def unparse(self, head_data, masked_types=[], *args, **kwargs):
        """
        Unparses the nodes in a subtree with the head_data as the root
        and returns a naive stringification of the parsed subtree.
        """
        return self.unparser.visit(head_data, masked_types)

    def update_summarization_status(self, head_data, method, *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Depending on the summarization method, adds the head_data (method=="NODE") or
        the node_data of a the nodes in the subtree with head_data as the head (method=="SUBTREE")
        to the self.summarized_nodes[method] (a dictionary)
        """

        if method == "SUBTREE":
            subtree = self.get_subtree_nodes(head_data)
            summarized = dict(
                filter(
                    lambda node: node[-1]["operation"] == head_data["operation"]
                    or node[-1]["operation"] == "no-op",
                    subtree.items(),
                )
            )
        elif method == "NODE":
            summarized = {head_data["id"]: head_data}
        else:
            raise ConfigurationException(
                'SUMMARIZATION_METHOD can be "SUBTREE" or "NODE"'
            )
        self.summarized_nodes[method].update(summarized)

    def get_summarization_status(self, node_data, method, *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Returns True if node is already summarized the the specified method.
        """
        return node_data["id"] in self.summarized_nodes[method]

    def clear_node_operarions(self):
        nx.set_node_attributes(self, "no-op", "operation")
        nx.set_node_attributes(self, "lightgrey", "color")

        self.affected_nodes = dict()
        self.summarized_nodes = dict()
        self.set_slice()

    def export_json(self, save_path):
        save_path = Path(save_path / self.file_saved_as)
        save_path.mkdir(parents=True, exist_ok=True)
        with open(save_path / f"{self.name}_ast_{self.file_saved_as}.json", "w") as f:
            json.dump(json_graph.node_link_data(self), f)

    def export_csv(self, save_path):
        save_path = Path(save_path / self.file_saved_as)
        save_path.mkdir(parents=True, exist_ok=True)
        data = json_graph.node_link_data(self)
        nodes = pd.DataFrame(data["nodes"])
        nodes.to_csv(
            save_path / f"{self.name}_ast_nodes_{self.file_saved_as}.csv",
            index=False,
        )
        links = pd.DataFrame(data["links"])
        links.to_csv(
            save_path / f"{self.name}_ast_links_{self.file_saved_as}.csv",
            index=False,
        )


class ASTSlice(AST):
    """
    Represents the slice of the AST that contains only the contaminated
    nodes in the change.
    """

    def __init__(
        self,
        name=None,
        nodes={},
        edges=[],
        LANGUAGE=None,
        diff=None,
        *args,
        **kwargs,
    ):
        # Import language support tools but not saved as an attribute
        # for pickling reasons
        language_support_tools = importlib.import_module(
            f"language_supports.{LANGUAGE}"
        )
        self.LANGUAGE = LANGUAGE
        self.ROOT_TYPE = language_support_tools.ROOT_TYPE
        self.IGNORED_TYPES = language_support_tools.IGNORED_TYPES

        self.diff = diff

        if edges:
            super(AST, self).__init__(edges)
            nx.set_node_attributes(self, nodes)
        else:
            super(AST, self).__init__()
            self.add_nodes_from(nodes)
            nx.set_node_attributes(self, nodes)

        self.name = name
        self.set_root()
        self.depth = max(
            [0] + list(map(lambda node: node[1].get("level") + 1, self.nodes.items()))
        )

        # Set up language support tools
        self.node_names = language_support_tools.NameGetter(self)
        self.stringifier = language_support_tools.Stringifier(self)

    def set_slice(self, *args, **kwargs):
        pass
