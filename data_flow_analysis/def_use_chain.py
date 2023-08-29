import json
import pandas as pd
from functools import reduce
from collections import defaultdict
from utils.visitors import NodeVisitor
from .def_model import Def
from .use_model import Use
from .actor_model import Actor


class DefUseChains(NodeVisitor):
    """
    Module visitor that gathers two kinds of informations:
        - local_chains: {'node_id': List[Def]}, a mapping between a node and the list
          of variables defined in this node,
        - chains: {'node_id': Def}, a mapping between def nodes and their chains.
    """

    def __init__(self, ast, scope=None, parent=None, sysdiff=None):
        """
        ast: ast_model.AST
        """
        self.ast = ast

        if scope:
            self.scope = scope.replace(":", "_")
        else:
            self.scope = self.ast.get_data(self.ast.root)["id"].replace(":", "_")

        # The DefUseChains object of the parent scope
        self.parent = parent
        # A list of DefUseChains objects of the children scopes
        self.children = []

        self.ast_stack = []

        self.sysdiff = sysdiff

        # Store current reachability conditions based on conditional statements
        self.reachability_stack = []

        # Stores a mapping between def nodes and their object (Def)
        # in the form of {'node_id': Def}
        self.def_points = defaultdict(list)
        # Stores a mapping between use nodes and their object (Use)
        # in the form of {'node_id': Use}
        self.use_points = defaultdict(list)
        # Stores a mapping between actor nodes and their object (Actor)
        # in the form of {'node_id': Actor}
        self.actor_points = defaultdict(list)

        # Stores a mapping between a node and the list of
        # variables defined in the subtree under the node
        # in the form of {'node_id': List[Def]}
        # NOTE: Usefull for scoping and name spaces
        # TODO (Low): FIX for system level
        # (does not update beyond include node in CMake)
        self.local_chains = defaultdict(list)

        # Stores a mapping of the name to its definition points {'name': [Def]}
        self.defined_names = defaultdict(list)
        # Stores a mapping of the name to its use points {'name': [Use]}
        self.used_names = defaultdict(list)
        # Stores a mapping of the name to undefined users {'name': [Use]}
        self.undefined_names = defaultdict(list)

    # def process_undefineds(self):
    #     """
    #     # TODO: Needs more work with scoping.
    #     """
    #     for undefined_name, undefined_user in self.undefined_names.items():
    #         if undefined_name in self.defined_names:
    #             for newdef in self.defined_names[undefined_name]:
    #                 for user in undefined_user:
    #                     newdef.add_use_node(user)
    #         del self.undefined_names[undefined_name]

    def get_definitions_by_name(self, node_data):
        """
        Looks up use (node_data) in current and all ancestor contexts
        Returns the list of defs linked to the node_data
        """
        name = self.ast.get_name(node_data)
        defined_names = self.defined_names[name]
        parent = self.parent
        while not parent is None:
            defined_names = defined_names + parent.defined_names["name"]
            parent = parent.parent
        return defined_names

    def register_new_use_point(self, use_node_data, use_type="VAR"):
        use_point = self.create_and_get_use_point(use_node_data, use_type)
        self.use_points[use_point.node_data["id"]] = use_point
        self.used_names[use_point.name].append(use_point)
        defined_names = self.get_definitions_by_name(use_point.node_data)
        if defined_names:
            list(
                map(
                    lambda def_point: def_point.add_use_point(use_point),
                    defined_names,
                )
            )
        else:
            self.undefined_names[use_point.name].append(use_point)
        return use_point

    def register_new_def_point(self, def_node_data, def_type="VAR", suffix=None):
        def_point = self.create_and_get_def_point(
            def_node_data, def_type, suffix=suffix
        )
        self.def_points[def_point.node_data["id"]] = def_point
        self.defined_names[def_point.name].append(def_point)
        self.update_local_chains(def_point)
        return def_point

    def create_and_get_def_point(self, def_node, def_type, suffix=None):
        actor_point = self.get_or_create_actor_point(def_node)
        actor_point.add_def_point_id(def_node["id"])
        return Def(def_node, def_type, actor_point, self.ast, suffix=suffix)

    def create_and_get_use_point(self, use_node, use_type="VAR"):
        actor_point = self.get_or_create_actor_point(use_node)
        actor_point.add_use_point_id(use_node["id"])
        return Use(use_node, use_type, actor_point, self.ast)

    def get_or_create_actor_point(self, node_data):
        actor_node_data = self.ast.get_actor(node_data)
        if actor_node_data["id"] in self.actor_points:
            actor_point = self.actor_points[actor_node_data["id"]]
        else:
            actor_point = Actor(actor_node_data, self.reachability_stack, self.ast)
            self.actor_points[actor_node_data["id"]] = actor_point
        return actor_point

    def _add_to_local_chains(self, def_point, local_node_data=None):
        if local_node_data is None:
            self.local_chains[def_point.node_data["id"]].append(def_point)
        else:
            self.local_chains[local_node_data["id"]].append(def_point)

    def update_local_chains(self, def_point):
        self._add_to_local_chains(def_point)
        ancestors = self.ast.get_ancestors(def_point.node_data)
        # TODO (low): Get rid of the for loop.
        # Use something like the map function commented out below
        # TODO (low): Fix for included files... It should happen in system_diff_model.SystemDiff
        for node_data in ancestors.values():
            self._add_to_local_chains(def_point, node_data)
        # map(
        #     lambda node_data: self.add_to_local_chains(def_point, node_data),
        #     ancestors.values(),
        # )

    def add_condition_to_reachability_stack(self, condition_node_data):
        self.reachability_stack.append(
            self.ast.unparse(condition_node_data).strip("(").strip(")")
        )

    def remove_condition_from_reachability_stack(self, last_n=1):
        del self.reachability_stack[-last_n:]

    def negate_last_condition_in_reachability_stack(self, negation_symbol="NOT"):
        # Usefull for else_if structure
        self.reachability_stack[
            -1
        ] = f"{negation_symbol} ({self.reachability_stack[-1]})"

    def analyze(self):
        self.generic_visit(self.ast.get_data(self.ast.root))
        if self.sysdiff:
            self.sysdiff.set_data_flow_reach_file(self.ast.file_path, self.ast.name)

    def to_json(self):
        du_chains_output = {
            "commit_hash": self.ast.commit_hash,
            "cluster": self.ast.name,
            "scope": self.scope,
            "def_points": list(
                map(
                    lambda def_point: def_point.to_json(),
                    self.def_points.values(),
                )
            ),
            "use_points": list(
                map(
                    lambda use_point: use_point.to_json(),
                    self.use_points.values(),
                )
            ),
            "actor_points": list(
                map(
                    lambda actor_point: actor_point.to_json(),
                    self.actor_points.values(),
                )
            ),  # TODO CONTINUE HERE
            "undefined_names": reduce(
                lambda a, b: [*a, *b],
                reduce(
                    lambda a, b: [*a, *b],
                    map(
                        lambda use_point_list: (
                            list(
                                map(
                                    lambda use_point: use_point.to_json(),
                                    use_point_list,
                                )
                            ),
                        ),
                        self.undefined_names.values(),
                    ),
                    [],
                ),
                [],
            ),
        }

        return du_chains_output

    def export_json(self, save_path):
        save_path.mkdir(parents=True, exist_ok=True)
        if self.sysdiff is None:
            self.ast.export_json(save_path / "diffs")
        with open(save_path / f"{self.ast.name}_du_output_{self.scope}.json", "w") as f:
            json.dump(self.to_json(), f)

    def to_csv(self):
        data = self.to_json()
        def_points_df = pd.DataFrame(data["def_points"])
        cols = list(def_points_df.columns)
        def_points_df["scope"] = self.scope
        def_points_df = def_points_df[["scope", *cols]]

        use_points_df = pd.DataFrame(data["use_points"])
        cols = list(use_points_df.columns)
        use_points_df["scope"] = self.scope
        use_points_df = use_points_df[["scope", *cols]]

        actor_points_df = pd.DataFrame(data["actor_points"])
        cols = list(actor_points_df.columns)
        actor_points_df["scope"] = self.scope
        actor_points_df = actor_points_df[["scope", *cols]]

        undefined_names_df = pd.DataFrame(data["undefined_names"])
        cols = list(undefined_names_df.columns)
        undefined_names_df["scope"] = self.scope
        undefined_names_df = undefined_names_df[["scope", *cols]]

        return def_points_df, use_points_df, actor_points_df, undefined_names_df

    def export_csv(self, save_path):
        save_path.mkdir(parents=True, exist_ok=True)
        if self.sysdiff is None:
            self.ast.export_csv(save_path / "diffs")
        (
            def_points_df,
            use_points_df,
            actor_points_df,
            undefined_names_df,
        ) = self.to_csv()
        def_points_df.to_csv(
            save_path / f"{self.ast.name}_def_points_{self.scope}.csv", index=False
        )
        use_points_df.to_csv(
            save_path / f"{self.ast.name}_use_points_{self.scope}.csv", index=False
        )
        actor_points_df.to_csv(
            save_path / f"{self.ast.name}_actor_points_{self.scope}.csv", index=False
        )
        undefined_names_df.to_csv(
            save_path / f"{self.ast.name}_undefined_names_{self.scope}.csv", index=False
        )
