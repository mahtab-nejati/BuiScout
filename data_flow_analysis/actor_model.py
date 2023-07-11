from utils.exceptions import DebugException


class Actor(object):
    """
    Model an Actor point.
    Objects are called actor_point
    """

    def __init__(self, node_data, reachability, ast):
        self.ast = ast

        # Storing the node_data
        self.node_data = node_data

        self.name = self.ast.get_name(self.node_data)
        if self.name is None:
            raise DebugException(
                f"{self.node_data['type']} requires NameGetter revisit"
            )

        # Storing reachability condition
        self.reachability = reachability.copy()

        # Storing the id of all def_node defined by this actor
        self.def_point_ids = []
        # Storing the id of all use_node used by this actor
        self.use_point_ids = []

    def add_def_point_id(self, def_node_id):
        """
        Add def_node_id (id of the def_node) to the list of defs if it's not already added
        """
        if not self.is_listed_def_point(def_node_id):
            self.def_point_ids.append(def_node_id)

    def is_listed_def_point(self, def_node_id, *args, **kwargs):
        return def_node_id in self.def_point_ids

    def add_use_point_id(self, use_point_id):
        """
        Add use_node_id (id of the use_node) to the list of uses if it's not already added
        """
        if not self.is_listed_use_point(use_point_id):
            self.use_point_ids.append(use_point_id)

    def is_listed_use_point(self, use_point_id, *args, **kwargs):
        return use_point_id in self.use_point_ids

    def to_json(self):
        return {
            "actor_name": self.name,
            "actor_node_id": self.node_data["id"],
            "reachability": " ^ ".join(self.reachability),
            "def_node_ids": self.def_point_ids,
            "use_node_ids": self.use_point_ids,
        }
