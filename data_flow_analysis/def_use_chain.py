from collections import defaultdict
from utils.visitors import NodeVisitor
from utils.exceptions import DebugException
from .def_model import Def


class DefUseChains(NodeVisitor):
    """
    Module visitor that gathers two kinds of informations:
        - local_chains: {'node_id': List[Def]}, a mapping between a node and the list
          of variables defined in this node,
        - chains: {'node_id': Def}, a mapping between def nodes and their chains.
    """

    def __init__(self, ast):
        """
        ast: ast_model.AST
        """
        self.ast = ast

        # Stores a mapping between a node and the list of
        # variables defined in the subtree under the node
        # in the form of {'node_id': List[Def]}
        self.local_chains = defaultdict(list)
        # Stores a mapping between def nodes and their chain object (Def)
        # in the form of {'node_id': Def}
        self.chains = defaultdict(list)
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
        name = self.ast.get_name(use_node)
        # TODO (Low): Is there any method to get rid of the for loop?
        if name in self.defined_names:
            for definition in self.defined_names[name]:
                definition.add_use_node(use_node)
        else:
            self.trace_undefined_name(use_node)

    def trace_undefined_name(self, use_node):
        self.undefined_names[self.ast.get_name(use_node)].append(use_node)

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
        for node_data in ancestors.values():
            self._add_to_local_chains(definition, node_data)
        # map(
        #     lambda node_data: self.add_to_local_chains(definition, node_data),
        #     ancestors.values(),
        # )

    def update_chains(self, definition):
        self.chains[definition.def_node["id"]] = definition

    def update_defined_names(self, definition):
        self.defined_names[definition.name].append(definition)

    def update_undefined_names(self, name, use_node):
        self.undefined_names[name].append(use_node)

    def analyze(self):
        self.generic_visit(self.ast.get_data(self.ast.root))

    def save_chains(self, save_path):
        pass
