import networkx as nx
import pandas as pd
import importlib, json
from pathlib import Path
from copy import deepcopy
from .ast_model import AST


class ASTDiff(object):
    """
    Represents a pair of ASTs with their corresponding diff.
    Initialization:
        diff = ASTDiff(*utils.read_dotdiff(path), file_path, file_saved_as, commit_hash)
    The output of utils.read_dotdiff(path) includes
    the source and destination nx.DiGraph objects
    and the dictionary {source_node: destination_node} of matched nodes.
    """

    def __init__(
        self,
        source,
        destination,
        matches,
        file_action,
        file_path,
        file_saved_as,
        commit_hash,
        LANGUAGE,
        *args,
        **kwargs,
    ):
        # Import language support tools but not saved as an attribute
        # for pickling reasons
        language_support_tools = importlib.import_module(
            f"language_supports.{LANGUAGE}"
        )
        self.LANGUAGE = LANGUAGE
        self.IGNORED_TYPES = language_support_tools.IGNORED_TYPES

        self.file_action = file_action
        self.file_path = file_path
        self.file_saved_as = file_saved_as
        self.commit_hash = commit_hash

        # If change does not affect the file:
        if self.file_action is None:
            # Replace the empty/old source with a deepcopy of destination
            # and prep for initialization
            source = deepcopy(destination)
            source.name = "source"
            # Fix source AST node IDs (_dst_ to _src_)
            nx.relabel_nodes(
                source,
                dict(
                    map(
                        lambda node_id: (node_id, node_id.replace("_dst_", "_src_")),
                        source.nodes,
                    )
                ),
                copy=False,
            )

            # Create ASTs and clearing changes in ASTs
            self.source = AST(
                source,
                file_path=file_path,
                file_saved_as=file_saved_as,
                commit_hash=commit_hash,
                LANGUAGE=self.LANGUAGE,
                diff=self,
            )
            # Clear all changes
            self.source.clear_node_operarions()

            self.destination = AST(
                destination,
                file_path=file_path,
                file_saved_as=file_saved_as,
                commit_hash=commit_hash,
                LANGUAGE=self.LANGUAGE,
                diff=self,
            )
            # Clear all changes
            self.destination.clear_node_operarions()

            # Set up matches (all nodes in source and destination match)
            self.source_match = dict(
                map(
                    lambda node_id: (
                        f"{self.file_saved_as}:{node_id}",
                        f'{self.file_saved_as}:{node_id.replace("_src_", "_dst_")}',
                    ),
                    source.nodes,
                )
            )
            self.destination_match = dict(
                map(lambda pair: (pair[1], pair[0]), self.source_match.items())
            )

        # If change affects the file:
        else:
            self.source = AST(
                source,
                file_path=file_path,
                file_saved_as=file_saved_as,
                commit_hash=commit_hash,
                LANGUAGE=LANGUAGE,
                diff=self,
            )
            self.destination = AST(
                destination,
                file_path=file_path,
                file_saved_as=file_saved_as,
                commit_hash=commit_hash,
                LANGUAGE=self.LANGUAGE,
                diff=self,
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

        self.destination.extended_processor.visit(
            self.destination.get_data(self.destination.root)
        )
        self.source.extended_processor.visit(self.source.get_data(self.source.root))
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
        if self.file_action is None:
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
                and node_data["type"] not in self.IGNORED_TYPES,
                self.source.affected_nodes.values(),
            )
            for node_data in in_process:
                self.summarize_deletion(node_data, method)

            # ADDITIONS
            in_process = filter(
                lambda node_data: node_data["level"] == level
                and node_data["operation"] == "added"
                and not self.destination.get_summarization_status(node_data, method)
                and node_data["type"] not in self.IGNORED_TYPES,
                self.destination.affected_nodes.values(),
            )
            for node_data in in_process:
                self.summarize_addition(node_data, method)

            # MOVEMENTS
            in_process = filter(
                lambda node_data: node_data["level"] == level
                and node_data["operation"] == "moved"
                and not self.source.get_summarization_status(node_data, method)
                and node_data["type"] not in self.IGNORED_TYPES,
                self.source.affected_nodes.values(),
            )
            for node_data in in_process:
                self.summarize_movement(node_data, method)

            # UPDATES
            in_process = filter(
                lambda node_data: node_data["level"] == level
                and node_data["operation"] == "updated"
                and not self.source.get_summarization_status(node_data, method)
                and node_data["type"] not in self.IGNORED_TYPES,
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

    def reveal_match(self, node_data, *args, **kwargs):
        """
        Returns the match of the AST and node for external purposes
        as a pair of AST, dict(nod_data).
        Returns None, dict() if no match exists.
        """

        if node_data["id"] in self.source_match:
            match_id = self.source_match[node_data["id"]]
            return self.destination, self.destination.nodes[match_id]

        if node_data["id"] in self.destination_match:
            match_id = self.destination_match[node_data["id"]]
            return self.source, self.source.nodes[match_id]

        return None, dict()

    def export_json(self, save_path):
        save_path = Path(save_path) / "diffs"
        save_path.mkdir(parents=True, exist_ok=True)
        self.source.export_json(save_path)
        self.destination.export_json(save_path)
        with open(
            save_path / self.file_saved_as / f"matches_{self.file_saved_as}.json", "w"
        ) as f:
            json.dump(
                {"src_match": self.source_match, "dst_match": self.destination_match}, f
            )

    def export_csv(self, save_path):
        save_path = Path(save_path) / "diffs"
        save_path.mkdir(parents=True, exist_ok=True)
        self.source.export_csv(save_path)
        self.destination.export_csv(save_path)
        matches_df = pd.DataFrame(
            list(
                map(
                    lambda pair: {"source": pair[0], "destination": pair[1]},
                    self.source_match.items(),
                )
            )
        )
        matches_df.to_csv(
            save_path / self.file_saved_as / f"matches_{self.file_saved_as}.csv",
            index=False,
        )
