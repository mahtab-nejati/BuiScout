import networkx as nx
from networkx.drawing.nx_agraph import write_dot
import pygraphviz as pgv
from functools import reduce
from copy import deepcopy
import importlib
from utils.helpers import parse_label
from utils.configurations import LANGUAGES


class AST(nx.DiGraph):
    """
    Represents a build specification file state (version).
    """
    def __init__(self, *args, file_name=None, commit_hash=None, language_support_tools=None, **kwargs):
        super(AST, self).__init__(*args, **kwargs)
        
        # SET language support tools
        self.language_support_tools = language_support_tools
        
        # Set file and commit_hash
        self.file_name = file_name
        self.commit_hash = commit_hash
        
        # Remove extra nodes
        none_nodes = list(
            filter(lambda node: node[-1].get("label") is None, self.nodes.items())
        )
        for node in none_nodes:
            self.remove_node(node[0])

        # Set node attributes
        # The head of the AST (self.language_support_tools.ROOT_TYPE) has level=0.
        self.set_node_attributes()
        self.set_nodes_levels()

        # Set AST attributes
        # Also sets self.depth = max(levels)+1
        self.root = self.get_root()
        self.depth = max(
            [0] + list(map(lambda node: node["level"] + 1, self.nodes.values()))
        )
        self.affected_nodes = self.get_affected_nodes()
        self.summarized_nodes = dict()

        # Slice up changes
        self.slice = self.get_slice()

        # Set up the NameGetter for language support
        self.NameGetter = self.language_support_tools.NameGetter(self)

    def export_dot(self, path, *args, **kwargs):
        """
        Export the AST into a .dot file (included in the path)
        """
        write_dot(self, path)

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
        The head of the AST (self.language_support_tools.ROOT_TYPE) has level=0.
        """
        depth = 0 
        current_level_nodes = dict(filter(lambda node: node[-1]['type']==self.language_support_tools.ROOT_TYPE, self.nodes.items()))
        
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
        # del node[-1]['color'] # TODO: kept for visualization purposes

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
        return self.NameGetter.visit(node_data)

    def get_location(self, node_data, *args, **kwargs):
        """
        Returns the location of the node_data
        """
        if self.file_name:
            file_name = self.file_name
        else:
            file_name = "<UNKNOWN_FILE>"
        return f' at {file_name}:{node_data["s_pos"]}-{node_data["e_pos"]}'

    def get_root(self, *args, **kwargs):
        """
        Returns the root node of the cluster as a dict of {'node_id': dict(nod_data)}
        """
        return dict(filter(lambda node: node[-1]['type']==self.language_support_tools.ROOT_TYPE,
                           self.nodes.items()))
                
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
        if node_data["type"] != self.language_support_tools.ROOT_TYPE:
            parent_data = self.get_data(self.get_parent(node_data))
            ancestors = {
                parent_data["id"]: parent_data,
                **self.get_ancestors(parent_data),
            }
        else:
            return {node_data["id"]: node_data}
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
        return {child["id"]: {child}}

    def get_affected_nodes(self, *args, **kwargs):
        """
        Returns the affected nodes in the change from the AST
        as a dict of {'node_id': dict(nod_data)}.
        Currently excludes comments as GumTree underperforms and
        poses overplotting problems.
        """
        affected_nodes =  dict(filter(lambda node: node[-1]['operation']!='no-op',
                                      self.nodes.items()))
        ignored_nodes = filter(lambda node_data: node_data['type'] in self.language_support_tools.IGNORED_TYPES, affected_nodes.values())
        for ignored_node_data in ignored_nodes: # TODO: Convert to non-loop
            ignored_subtree_nodes = self.get_subtree_nodes(ignored_node_data)
            affected_nodes = dict(
                filter(
                    lambda node: node[-1]["id"] not in ignored_subtree_nodes,
                    affected_nodes.items(),
                )
            )
        return affected_nodes

    def get_slice(self, *args, **kwargs):
        """
        Returns contaminated slice from the cluster as a SlicedAST() object.
        TODO: Redo (recursive)
        """
        # Initialize slice data
        affected_nodes = self.affected_nodes
        impact_depth = max(
            [0]
            + list(map(lambda node_data: node_data["level"], affected_nodes.values()))
        )
        current_slice = dict(zip(list(range(self.depth)), [None] * self.depth))
        current_slice[0] = self.root

        # Slice upwards
        for l in range(impact_depth, 0, -1):
            if current_slice[l] is None:
                current_slice[l] = dict().copy()
            current_slice[l].update(
                dict(
                    filter(lambda node: node[-1]["level"] == l, affected_nodes.items())
                )
            )

            for pl in range(l - 1, 0, -1):
                if current_slice[pl] is None:
                    current_slice[pl] = dict().copy()
                current_slice[pl].update(
                    reduce(
                        lambda a, b: {**a, **b},
                        [{}]
                        + list(
                            map(
                                lambda node_data: self.get_parent(node_data),
                                current_slice[pl + 1].values(),
                            )
                        ),
                    )
                )

        # Slice downwards
        for l in range(1, self.depth - 1):
            if current_slice[l] is None:
                current_slice[l] = dict().copy()
            if current_slice[l + 1] is None:
                current_slice[l + 1] = dict().copy()
            current_slice[l + 1].update(
                reduce(
                    lambda a, b: {**a, **b},
                    [{}]
                    + list(
                        map(
                            lambda node_data: self.get_children(node_data),
                            current_slice[l].values(),
                        )
                    ),
                )
            )

        # Clean slice data
        current_slice = dict(
            filter(
                lambda level_nodes: level_nodes[1] is not None, current_slice.items()
            )
        )
        slice_nodes = reduce(
            lambda a, b: {**a, **b}, [{}] + list(current_slice.values())
        )
        slice_edges = list(
            filter(
                lambda edge: edge[0] in slice_nodes and edge[1] in slice_nodes,
                self.edges.data(),
            )
        )

        # Create slice
        return ASTSlice(self.name, slice_nodes, slice_edges, language_support_tools=self.language_support_tools)
    
    def get_subtree_nodes(self, head_data, *args, **kwargs):
        """
        Returns the subtree with head_data as the head of the subtree
        as a dictionary of {'node_id':{node_data}}
        TODO: Redo (recursive)
        """
        subtree_nodes = {head_data["id"]: head_data}
        current_level_nodes = deepcopy(subtree_nodes)
        while current_level_nodes.keys():
            next_level_nodes = dict()
            for node_data in current_level_nodes.values():
                next_level_nodes.update(self.get_children(node_data))
            subtree_nodes.update(deepcopy(current_level_nodes))
            current_level_nodes = dict(next_level_nodes)
        return subtree_nodes

    def unparse_subtree(self, head_data, *args, **kwargs):
        """
        Unparses the nodes in a subtree with the head_data as the root
        and returns a naive stringification of the parsed subtree.
        """
        subtree_nodes = self.get_subtree_nodes(head_data)
        return "".join(
            map(
                lambda cp: cp[0],
                sorted(
                    map(
                        lambda node_data: (node_data["content"], node_data["s_pos"]),
                        subtree_nodes.values(),
                    ),
                    key=lambda cp: cp[-1],
                ),
            )
        )

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
            raise KeyError('SUMMARIZATION_METHOD can be "SUBTREE" or "NODE"')
        self.summarized_nodes[method].update(summarized)

    def get_summarization_status(self, node_data, method, *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Returns True if node is already summarized the the specified method.
        """
        return node_data["id"] in self.summarized_nodes[method]


class ASTSlice(AST):
    """
    Represents the slice of the AST that contains only the contaminated
    nodes in the change.
    """
    def __init__(self, cluster=None, nodes={}, edges=[], language_support_tools=None, *args, **kwargs):
        
        self.language_support_tools = language_support_tools
        
        if edges:
            super(AST, self).__init__(edges)
            nx.set_node_attributes(self, nodes)
        else:
            super(AST, self).__init__()
            self.add_nodes_from(nodes)
            nx.set_node_attributes(self, nodes)
            
        self.cluster = cluster
        self.root = self.get_root()
        self.depth = max(
            [0] + list(map(lambda node: node[1].get("level") + 1, self.nodes.items()))
        )

    def get_slice(self, *args, **kwargs):
        pass


class ASTDiff(object):
    """
    Represents a pair of ASTs with their corresponding diff.
    Initialization:
        diff = ASTDiff(*utils.read_dotdiff(path), file_name, commit_hash)
    The output of utils.read_dotdiff(path) includes
    the source and destination nx.DiGraph objects
    and the dictionary {source_node: destination_node} of matched nodes.
    """
    def __init__(self, source, destination, matches, file_name, commit_hash, LANGUAGE, *args, **kwargs):
        self.language_support_tools = importlib.import_module(f'languages.{LANGUAGE}.supporters')
        self.file_name = file_name
        self.commit_hash = commit_hash
        self.source = AST(source, file_name=file_name, commit_hash=commit_hash, language_support_tools=self.language_support_tools)
        self.destination = AST(destination, file_name=file_name, commit_hash=commit_hash, language_support_tools=self.language_support_tools)
        self.source_match = matches
        self.destination_match = dict(
            map(lambda pair: (pair[1], pair[0]), self.source_match.items())
        )

        self.summary = dict()

    def get_match(self, node_data, *args, **kwargs):
        """
        Returns the match of the node in the other cluster
        as a dict of {'node_id': dict(nod_data)}.
        Returns dict() if no match exists.
        """

        if node_data["id"] in self.source_match:
            match_id = self.source_match[node_data["id"]]
            return {match_id: self.destination.nodes[match_id]}

        if node_data["id"] in self.destination_match:
            match_id = self.destination_match[node_data["id"]]
            return {match_id: self.source.nodes[match_id]}

        return dict()

    def summarize(self, method="SUBTREE", *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Summarizes the changes of the head_data node (method=="NODE")
        or the subtree with head_data node as the head (method=="SUBTREE")
        and returns the summary entry to the self.summary[method] (a list)
        """
        if method in self.summary:
            return self.summary[method]
        else:
            self.summary[method] = [].copy()

        self.source.summarized_nodes[method] = dict()
        self.destination.summarized_nodes[method] = dict()

        depth = max([self.source.depth, self.destination.depth])

        for level in range(depth):
            # DELETIONS
            in_process = filter(lambda node_data: node_data['level']==level and node_data['operation']=='deleted' and\
                                                    not self.source.get_summarization_status(node_data, method) and node_data['type'] not in self.language_support_tools.IGNORED_TYPES,
                                self.source.affected_nodes.values())
            for node_data in in_process:
                self.summarize_deletion(node_data, method)

            # ADDITIONS
            in_process = filter(lambda node_data: node_data['level']==level and node_data['operation']=='added' and\
                                                    not self.destination.get_summarization_status(node_data, method) and node_data['type'] not in self.language_support_tools.IGNORED_TYPES,
                                self.destination.affected_nodes.values())
            for node_data in in_process:
                self.summarize_addition(node_data, method)

            # MOVEMENTS
            in_process = filter(lambda node_data: node_data['level']==level and node_data['operation']=='moved' and\
                                                    not self.source.get_summarization_status(node_data, method) and node_data['type'] not in self.language_support_tools.IGNORED_TYPES,
                                self.source.affected_nodes.values())
            for node_data in in_process:
                self.summarize_movement(node_data, method)

            # UPDATES
            in_process = filter(lambda node_data: node_data['level']==level and node_data['operation']=='updated' and\
                                                    not self.source.get_summarization_status(node_data, method) and node_data['type'] not in self.language_support_tools.IGNORED_TYPES,
                                self.source.affected_nodes.values())
            for node_data in in_process:
                self.summarize_update(node_data, method)

        return self.summary[method]

    def summarize_deletion(self, node_data, method, *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Summarizes the deletion of the head_data node (method=="NODE")
        or the subtree with head_data node as the head (method=="SUBTREE")
        and adds the summary entry to the self.summary[method] (a list).
        Then, updates the summarizaiton status of the source AST.
        """
        self.summary[method].append({'operation': 'deleted',
                                     'source_node': node_data['type'],
                                     'source_node_summary': self.language_support_tools.stringify(self.source, node_data),
                                     'source_position': f'{node_data["s_pos"]}-{node_data["e_pos"]}',
                                     'destination_node': None,
                                     'destination_node_summary': None,
                                     'destination_postion': None})
        
        self.source.update_summarization_status(node_data, method)

    def summarize_addition(self, node_data, method, *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Summarizes the addition of the head_data node (method=="NODE")
        or the subtree with head_data node as the head (method=="SUBTREE")
        and adds the summary entry to the self.summary[method] (a list).
        Then, updates the summarizaiton status of the destination AST.
        """
        self.summary[method].append({'operation': 'added',
                                     'source_node': None,
                                     'source_node_summary': None,
                                     'source_position': None,
                                     'destination_node': node_data['type'],
                                     'destination_node_summary': self.language_support_tools.stringify(self.destination, node_data),
                                     'destination_postion': f'{node_data["s_pos"]}-{node_data["e_pos"]}'})
        
        self.destination.update_summarization_status(node_data, method)

    def summarize_movement(self, node_data, method, *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Summarizes the movement of the head_data node (method=="NODE")
        or the subtree with head_data node as the head (method=="SUBTREE")
        and adds the summary entry to the self.summary[method] (a list).
        Then, updates the summarizaiton status of the source and destination ASTs.
        """
        source_node = node_data
        source_parent = self.source.get_data(self.source.get_parent(source_node))
        source_parent_match = self.destination.get_data(self.get_match(source_parent))
        destination_node = self.destination.get_data(self.get_match(source_node))
        destination_parent = self.destination.get_data(
            self.destination.get_parent(destination_node)
        )
        if (
            source_parent_match
            and source_parent_match["id"] == destination_parent["id"]
        ):
            movement_type = "moved_same_parent"
        else:
            movement_type = 'moved_changed_parent'
        self.summary[method].append({'operation': movement_type,
                                     'source_node': source_node['type'],
                                     'source_node_summary': self.language_support_tools.stringify(self.source, source_node),
                                     'source_position': f'{source_node["s_pos"]}-{source_node["e_pos"]}',
                                     'destination_node': destination_node['type'],
                                     'destination_node_summary': self.language_support_tools.stringify(self.destination, destination_node),
                                     'destination_postion': f'{destination_node["s_pos"]}-{destination_node["e_pos"]}'})
        
        self.source.update_summarization_status(source_node, method)
        self.destination.update_summarization_status(destination_node, method)

    def summarize_update(self, node_data, method, *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Summarizes the update of the head_data node (method=="NODE")
        or the subtree with head_data node as the head (method=="SUBTREE")
        and adds the summary entry to the self.summary[method] (a list).
        Then, updates the summarizaiton status of the source and destination ASTs.
        """
        source_node = node_data
        destination_node = self.destination.get_data(self.get_match(source_node))
        self.summary[method].append({'operation': 'updated',
                                     'source_node': source_node['type'],
                                     'source_node_summary': self.language_support_tools.stringify(self.source, source_node),
                                     'source_position': f'{source_node["s_pos"]}-{source_node["e_pos"]}',
                                     'destination_node': destination_node['type'],
                                     'destination_node_summary': self.language_support_tools.stringify(self.destination, destination_node),
                                     'destination_postion': f'{destination_node["s_pos"]}-{destination_node["e_pos"]}'})
        
        self.source.update_summarization_status(source_node, method)
        self.destination.update_summarization_status(destination_node, method)
