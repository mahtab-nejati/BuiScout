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
        self.is_contaminated = node_data["operation"] != "no-op"

        # Storing reachability condition
        self.reachability = reachability.copy()

        # Storing the dict of {node_id: Def}
        self.def_points = {}
        # Storing the dict of {node_id: Use}
        self.use_points = {}

    def set_contamination(self):
        self.is_contaminated = True

    def add_def_point(self, def_point):
        """
        Add def_point (Def object) to the list of defs if it's not already added
        """
        if not self.is_listed_def_point(def_point):
            self.def_points[def_point.node_data["id"]] = def_point

    def is_listed_def_point(self, def_point, *args, **kwargs):
        return def_point.node_data["id"] in self.def_points

    def add_use_point(self, use_point):
        """
        Add use_point (Use object) to the list of uses if it's not already added
        """
        if not self.is_listed_use_point(use_point):
            self.use_points[use_point.node_data["id"]] = use_point

    def is_listed_use_point(self, use_point, *args, **kwargs):
        return use_point.node_data["id"] in self.use_points

    def to_json(self):
        return {
            "actor_name": self.name,
            "actor_node_id": self.node_data["id"],
            "actor_node_operation": self.node_data["operation"],
            "actor_node_contamination": self.is_contaminated,
            "reachability": " ^ ".join(self.reachability),
            "def_node_ids": list(self.def_points.keys()),
            "use_node_ids": list(self.use_points.keys()),
        }
