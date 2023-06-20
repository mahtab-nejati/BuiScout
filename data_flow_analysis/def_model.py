class Def(object):
    """
    Model a Def point and its users (chain).
    """

    def __init__(self, def_node, ast):
        self.ast = ast
        self.def_node = def_node
        self.name = self.ast.get_name(self.def_node)
        if self.name is None:
            raise DebugException(f"{self.def_node['type']} requires NameGetter revisit")
        self.use_nodes = []

    def add_use_node(self, use_node, use_ast):
        """
        Add use_node to the list of users if it is a user of the self.def_node
        In a system-level analysis, used nodes can be in other files, hence passing in the use_ast.
        """
        if self.is_user(use_node, use_ast):
            self.use_nodes.append(use_node)

    def is_user(self, use_node, use_ast):
        """
        A wrapper for method uses_{self.def_node["type"]}
        Methods must be implemented at a language support level.
        In a system-level analysis, used nodes can be in other files, hence passing in the use_ast.
        """
        if use_ast.get_name(use_node) == self.name:
            return True
        return False

    def is_listed_user(self, use_node, *args, **kwargs):
        return use_node in self.use_nodes

    def to_json(self):
        return {
            "def_name": self.name,
            "def_node": self.def_node,
            "use_nodes": self.use_nodes,
        }
