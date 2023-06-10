import importlib
from .ast_model import AST


class ASTDiff(object):
    """
    Represents a pair of ASTs with their corresponding diff.
    Initialization:
        diff = ASTDiff(*utils.read_dotdiff(path), file_name, commit_hash)
    The output of utils.read_dotdiff(path) includes
    the source and destination nx.DiGraph objects
    and the dictionary {source_node: destination_node} of matched nodes.
    """

    def __init__(
        self,
        source,
        destination,
        matches,
        file_name,
        commit_hash,
        LANGUAGE,
        *args,
        **kwargs,
    ):
        self.language_support_tools = importlib.import_module(
            f"language_supports.{LANGUAGE}"
        )
        self.file_name = file_name
        self.commit_hash = commit_hash
        self.source = AST(
            source,
            file_name=file_name,
            commit_hash=commit_hash,
            language_support_tools=self.language_support_tools,
        )
        self.destination = AST(
            destination,
            file_name=file_name,
            commit_hash=commit_hash,
            language_support_tools=self.language_support_tools,
        )
        self.source_match = dict(
            map(
                lambda pair: (
                    self.source.node_id_map[pair[0]],
                    self.destination.node_id_map[pair[1]],
                ),
                matches.items(),
            )
        )
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

    def clear_change(self):
        """
        Clears all the differences between the two versions of the file
        by setting the source and matches to None and clearing node operations
        in the destination AST.
        """
        self.source = None
        self.source_match = None
        self.destination_match = None

        self.destination.clear_node_operarions()

    def summarize(self, method="SUBTREE", *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Summarizes the changes of the head_data node (method=="NODE")
        or the subtree with head_data node as the head (method=="SUBTREE")
        and returns the summary entry to the self.summary[method] (a list)
        """
        if self.source is None:
            return [].copy()
        if method in self.summary:
            return self.summary[method]
        else:
            self.summary[method] = [].copy()

        self.source.summarized_nodes[method] = dict()
        self.destination.summarized_nodes[method] = dict()

        depth = max([self.source.depth, self.destination.depth])

        for level in range(depth):
            # DELETIONS
            in_process = filter(
                lambda node_data: node_data["level"] == level
                and node_data["operation"] == "deleted"
                and not self.source.get_summarization_status(node_data, method)
                and node_data["type"] not in self.language_support_tools.IGNORED_TYPES,
                self.source.affected_nodes.values(),
            )
            for node_data in in_process:
                self.summarize_deletion(node_data, method)

            # ADDITIONS
            in_process = filter(
                lambda node_data: node_data["level"] == level
                and node_data["operation"] == "added"
                and not self.destination.get_summarization_status(node_data, method)
                and node_data["type"] not in self.language_support_tools.IGNORED_TYPES,
                self.destination.affected_nodes.values(),
            )
            for node_data in in_process:
                self.summarize_addition(node_data, method)

            # MOVEMENTS
            in_process = filter(
                lambda node_data: node_data["level"] == level
                and node_data["operation"] == "moved"
                and not self.source.get_summarization_status(node_data, method)
                and node_data["type"] not in self.language_support_tools.IGNORED_TYPES,
                self.source.affected_nodes.values(),
            )
            for node_data in in_process:
                self.summarize_movement(node_data, method)

            # UPDATES
            in_process = filter(
                lambda node_data: node_data["level"] == level
                and node_data["operation"] == "updated"
                and not self.source.get_summarization_status(node_data, method)
                and node_data["type"] not in self.language_support_tools.IGNORED_TYPES,
                self.source.affected_nodes.values(),
            )
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
        self.summary[method].append(
            {
                "operation": "deleted",
                "source_node": node_data["type"],
                "source_node_summary": self.source.stringifier.visit(node_data),
                "source_position": f'{node_data["s_pos"]}-{node_data["e_pos"]}',
                "destination_node": None,
                "destination_node_summary": None,
                "destination_postion": None,
            }
        )

        self.source.update_summarization_status(node_data, method)

    def summarize_addition(self, node_data, method, *args, **kwargs):
        """
        Input method represents the summarization method and can be one of ["NODE" or "SUBTREE"]
        Summarizes the addition of the head_data node (method=="NODE")
        or the subtree with head_data node as the head (method=="SUBTREE")
        and adds the summary entry to the self.summary[method] (a list).
        Then, updates the summarizaiton status of the destination AST.
        """
        self.summary[method].append(
            {
                "operation": "added",
                "source_node": None,
                "source_node_summary": None,
                "source_position": None,
                "destination_node": node_data["type"],
                "destination_node_summary": self.destination.stringifier.visit(
                    node_data
                ),
                "destination_postion": f'{node_data["s_pos"]}-{node_data["e_pos"]}',
            }
        )

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
            movement_type = "moved_changed_parent"
        self.summary[method].append(
            {
                "operation": movement_type,
                "source_node": source_node["type"],
                "source_node_summary": self.source.stringifier.visit(source_node),
                "source_position": f'{source_node["s_pos"]}-{source_node["e_pos"]}',
                "destination_node": destination_node["type"],
                "destination_node_summary": self.destination.stringifier.visit(
                    destination_node
                ),
                "destination_postion": f'{destination_node["s_pos"]}-{destination_node["e_pos"]}',
            }
        )

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
        self.summary[method].append(
            {
                "operation": "updated",
                "source_node": source_node["type"],
                "source_node_summary": self.source.stringifier.visit(source_node),
                "source_position": f'{source_node["s_pos"]}-{source_node["e_pos"]}',
                "destination_node": destination_node["type"],
                "destination_node_summary": self.destination.stringifier.visit(
                    destination_node
                ),
                "destination_postion": f'{destination_node["s_pos"]}-{destination_node["e_pos"]}',
            }
        )

        self.source.update_summarization_status(source_node, method)
        self.destination.update_summarization_status(destination_node, method)


class SystemDiff(ASTDiff):
    pass
