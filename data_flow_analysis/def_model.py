from utils.exceptions import DebugException


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
        self.actor_node = self.ast.get_actor(self.def_node)
        self.actor_name = self.ast.get_name(self.actor_node)
        self.users = []

    def add_user(self, user):
        """
        Add use_node to the list of users if it is a user of the self.def_node
        """
        if self.is_user(user):
            self.users.append(user)

    def is_user(self, user):
        """
        Checks if both the user and self (definition) refer to the
        same name and returns True if they do.
        """
        return user.is_user_of(self.name)

    def is_listed_user(self, user, *args, **kwargs):
        return user.use_node["id"] in set(lambda user: user.use_node["id"], self.users)

    def to_json(self):
        return {
            "def_name": self.name,
            "def_node": self.def_node,
            "actor_name": self.actor_name,
            "actor_node": self.actor_node,
            "users": list(map(lambda user: user.to_json(), self.users)),
        }
