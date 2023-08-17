from utils.exceptions import DebugException


class Def(object):
    """
    Model a Def point.
    Objects are called def_point
    """

    def __init__(self, node_data, def_type, actor_point, ast):
        self.ast = ast
        self.type = def_type

        # Storing the node_data
        self.node_data = node_data

        self.name = self.ast.get_name(self.node_data)
        if self.name is None:
            raise DebugException(
                f"{self.node_data['type']} requires NameGetter revisit"
            )

        # Storing actor_point
        self.actor_point = actor_point

        # Storing use_points
        self.use_points = []

    def add_use_point(self, use_point):
        """
        Add use_point to the list of use_points if it is a user of the self.node_data
        """
        if self.is_user(use_point):
            self.use_points.append(use_point)

    def is_user(self, use_point):
        """
        Checks if both the use_point and self (definition) refer to the
        same name and returns True if they do.
        """
        return use_point.is_user_of(self.name)

    def is_listed_use_point(self, use_point, *args, **kwargs):
        return use_point.node_data["id"] in set(
            lambda use_point: use_point.node_data["id"], self.use_points
        )

    def to_json(self):
        return {
            "def_type": self.type,
            "def_name": self.name,
            "def_node_id": self.node_data["id"],
            "actor_node_id": self.actor_point.node_data["id"],
            "use_node_ids": list(
                map(lambda use_point: use_point.node_data["id"], self.use_points)
            ),
        }
