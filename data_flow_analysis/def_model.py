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

    def add_use_node(self, use_node):
        """
        Add use_node to the list of users if it is a user of the self.def_node
        """
        if self.is_user(use_node):
            self.use_nodes.append(use_node)

    def is_user(self, use_node):
        """
        A wrapper for method uses_{self.def_node["type"]}
        Methods must be implemented at a language support level.
        """
        if self.ast.get_name(use_node) == self.name:
            return True
        return False

    def is_listed_user(self, use_node, *args, **kwargs):
        return use_node in self.use_nodes
