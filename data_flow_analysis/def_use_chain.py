import json
from collections import defaultdict
from utils.visitors import NodeVisitor
from .def_model import Def
from .use_model import Use


class DefUseChains(NodeVisitor):
    """
    Module visitor that gathers two kinds of informations:
        - local_chains: {'node_id': List[Def]}, a mapping between a node and the list
          of variables defined in this node,
        - chains: {'node_id': Def}, a mapping between def nodes and their chains.
    """

    def __init__(self, ast, sysdiff=None):
        """
        ast: ast_model.AST
        """
        self.ast = ast

        self.ast_stack = []

        self.sysdiff = sysdiff

        # Stores a mapping between a node and the list of
        # variables defined in the subtree under the node
        # in the form of {'node_id': List[Def]}
        # TODO: FIX for system level (does not update beyond include node)
        self.local_chains = defaultdict(list)
        # Stores a mapping between def nodes and their chain object (Def)
        # in the form of {'node_id': Def}
        self.def_points = defaultdict(list)
        # Stores a mapping of the name to its definition points {'name': [Def]}
        self.defined_names = defaultdict(list)
        # Stores a mapping of the name to undefined users {'name': [use_node]}
        self.undefined_names = defaultdict(list)

    def get_definitions_by_name(self, node_data):
        """
        Looks up use (node_data) in current context
        Returns the list of defs linked to the node_data
        """
        # TODO: Implement the ast.get_name(node_data)
        name = self.ast.get_name(node_data)
        return self.defined_names[name]

    def add_user(self, use_node):
        user = self.create_and_get_user(use_node)
        # TODO (Low): Is there any method to get rid of the for loop?
        if user.name in self.defined_names:
            for definition in self.defined_names[user.name]:
                definition.add_user(user)
        else:
            self.trace_undefined_name(user)

    def trace_undefined_name(self, user):
        self.undefined_names[user.name].append(user)

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

    def register_new_definition(self, def_node):
        definition = self.create_and_get_definition(def_node)
        self.update_local_chains(definition)
        self.update_chains(definition)
        self.update_defined_names(definition)
        return definition

    def create_and_get_definition(self, def_node):
        return Def(def_node, self.ast)

    def create_and_get_user(self, use_node):
        return Use(use_node, self.ast)

    def _add_to_local_chains(self, definition, local_node_data=None):
        if local_node_data is None:
            self.local_chains[definition.def_node["id"]].append(definition)
        else:
            self.local_chains[local_node_data["id"]].append(definition)

    def update_local_chains(self, definition):
        self._add_to_local_chains(definition)
        ancestors = self.ast.get_ancestors(definition.def_node)
        # TODO (low): Get rid of the for loop.
        # Use something like the map function commented out below
        # TODO (low): Fix for included files... It should happen in system_diff_model.SystemDiff
        for node_data in ancestors.values():
            self._add_to_local_chains(definition, node_data)
        # map(
        #     lambda node_data: self.add_to_local_chains(definition, node_data),
        #     ancestors.values(),
        # )

    def update_chains(self, definition):
        self.def_points[definition.def_node["id"]] = definition

    def update_defined_names(self, definition):
        self.defined_names[definition.name].append(definition)

    def update_undefined_names(self, name, user):
        self.undefined_names[name].append(user)

    def analyze(self):
        self.generic_visit(self.ast.get_data(self.ast.root))

    def to_json(self):
        chains = {
            "commit_hash": self.ast.commit_hash,
            "local_chains": dict(
                map(
                    lambda local_chain: (
                        local_chain[0],
                        list(map(lambda def_obj: def_obj.to_json(), local_chain[1])),
                    ),
                    self.local_chains.items(),
                )
            ),
            "def_points": dict(
                map(
                    lambda chain: (chain[0], chain[1].to_json()),
                    self.def_points.items(),
                )
            ),
            "defined_names": dict(
                map(
                    lambda defined_name: (
                        defined_name[0],
                        list(map(lambda def_obj: def_obj.to_json(), defined_name[1])),
                    ),
                    self.defined_names.items(),
                )
            ),
            "undefined_names": dict(
                map(
                    lambda undef: (
                        undef[0],
                        list(map(lambda user: user.to_json(), undef[1])),
                    ),
                    self.undefined_names.items(),
                )
            ),
        }
        return chains

    def save_chains(self, save_path):
        save_path.mkdir(parents=True, exist_ok=True)
        with open(save_path / "du_output.json", "w") as f:
            json.dump(self.to_json(), f)
