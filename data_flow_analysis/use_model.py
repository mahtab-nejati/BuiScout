from utils.exceptions import DebugException


class Use(object):
    """
    Model a Def point and its users (chain).
    """

    def __init__(self, use_node, ast):
        self.ast = ast
        self.use_node = use_node
        self.name = self.ast.get_name(self.use_node)
        if self.name is None:
            raise DebugException(f"{self.def_node['type']} requires NameGetter revisit")
        self.actor_node = self.ast.get_actor(self.use_node)
        self.actor_name = self.ast.get_name(self.actor_node)

    def is_user_of(self, def_name):
        """
        Checks if both the self (user) refers to the
        same name as the def_name and returns.
        """
        return True if def_name == self.name else False

    def to_json(self):
        return {
            "use_name": self.name,
            "use_node": self.use_node,
            "actor_name": self.actor_name,
            "actor_node": self.actor_node,
        }
