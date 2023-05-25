"""
Shadowed code from https://github.com/serge-sans-paille/beniget/blob/f03705245ba68ebea7bbb74898622067fefe998e/beniget/beniget.py
Modified to make compatible with CMake AST.
"""

from collections import defaultdict
from utils.visitors import NodeVisitor


class Def(object):
    """
    Model a Def point and its users.
    """

    def __init__(self, def_node, ast):
        self.ast = ast
        self.def_node = def_node
        self.name = self.ast.get_name(self.def_node)
        if self.name is None:
            print(f"{self.def_node} requires NameGetter revisit")
        self.use_nodes = []

    def add_use_node(self, use_node, ast):
        """
        Add use_node to the list of users if it is a user of the self.def_node
        """
        if self.is_user(use_node):
            self.use_nodes.append(use_node)
            return True
        return False

    def is_user(self, use_node):
        """
        A wrapper for method uses_{self.def_node["type"]}
        Methods must be implemented at a language support level.
        """
        method = "uses_" + self.def_node["type"]
        user_detector = getattr(self, method, self.generic_uses_def)
        return user_detector(use_node)

    def is_listed_user(self, use_node, *args, **kwargs):
        return use_node in self.use_nodes


class DefUseChains(NodeVisitor):
    """
    Module visitor that gathers two kinds of informations:
        - locals: {'node_id': List[Def]}, a mapping between a node and the list
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
        self.chains = {}
        # Stores a mapping of the name to its definition points {'name': [Def]}
        self.defined_names = defaultdict(list)
        # Stores a mapping of the name to undefined users {'name': [use_node]}
        self.undefined_names = defaultdict(list)

    def unbound_identifier(self, name, node_data):
        location = self.ast.get_location(node_data)
        print(f'W: unbound identifier "{name}"{location}')

    def invalid_name_lookup(self, name, defs):
        """
        Identify if a local variable is used before assignment.
        # TODO: Revisit this method when implementing scopes.
        # If it's a global variable, what's the point?
        """
        return name in defs

    def get_definitions_by_name(self, use_node):
        """
        Looks up use (node_data) in current context
        Returns the list of defs linked to the use (node_data)
        """
        # TODO: Implement the ast.get_name(node_data)
        name = self.ast.get_name(use_node)
        return self.defined_names[name]

    def add_user(self, use_node):
        name = self.ast.get_name(use_node)
        map(
            lambda definition: definition.add_use_node(use_node),
            self.defined_names[name],
        )

    def process_body(self, head_data):
        """
        Takes the root/body node_data
        and processes the body as a separate unit.
        Will help with branching and scopes.
        """
        ordered_children_data = sorted(
            self.ast.get_children(head_data).values(),
            key=lambda node_data: node_data["s_pos"],
        )
        for child_data in ordered_children_data:
            self.visit(child_data)

    def process_undefineds(self):
        """
        # TODO: Needs more work with scoping.
        """
        for undefined_name, undefined_user in self.undefined_names.items():
            if undefined_name in self.defined_names:
                for newdef in self.defined_names[undefined_name]:
                    for user in undefined_user:
                        newdef.add_use_node(user)
            del self.undefined_names[undefined_name]

    def visit_root(self):
        self.module = self.ast.get_data(self.ast.root)
        self.process_body(self.module)

    def create_and_get_definition(self, def_node):
        return Def(def_node, self.ast)

    def add_to_local_chains(self, definition):
        self.local_chains[definition.def_node["id"]].append(definition)
        ancestors = self.ast.get_ancestors(definition.def_node)
        map(
            lambda node_data: self.local_chains[node_data["id"]].append(definition),
            ancestors.values(),
        )
        print("check add_to_local_chains")

    def add_to_chains(self, definition):
        self.chains[definition.def_node["id"]] = definition

    def add_to_defined_names(self, definition):
        self.defined_names[definition.name].append(definition)

    def add_to_undefined_names(self, name, use_node):
        self.undefined_names[name].append(use_node)


# class UseDefChains(object):
#     """
#     DefUseChains adaptor that builds a mapping between each user
#     and the Def that defines this user:
#         - chains: Dict[node, List[Def]], a mapping between nodes and the Defs
#           that define it.
#     """

#     def __init__(self, defuses):
#         self.chains = {}
#         for chain in defuses.chains.values():
#             if isinstance(chain.node, ast.Name):
#                 self.chains.setdefault(chain.node, [])
#             for use in chain.users():
#                 self.chains.setdefault(use.node, []).append(chain)

#         for chain in defuses._builtins.values():
#             for use in chain.users():
#                 self.chains.setdefault(use.node, []).append(chain)

#     def __str__(self):
#         out = []
#         for k, uses in self.chains.items():
#             kname = Def(k).name()
#             kstr = "{} <- {{{}}}".format(
#                 kname, ", ".join(sorted(use.name() for use in uses))
#             )
#             out.append((kname, kstr))
#         out.sort()
#         return ", ".join(s for k, s in out)
