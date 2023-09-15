from utils.exceptions import DebugException


class Actor(object):
    """
    Model an Actor point.
    Objects are called actor_point
    """

    def __init__(self, node_data, reachability, reachability_actor_ids, ast):
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
        self.reachability_actor_ids = reachability_actor_ids.copy()

        # Storing the list of [Defs]
        self.def_points = []
        # Storing the list of [Uses]
        self.use_points = []

    def set_contamination(self):
        self.is_contaminated = True

    def add_def_point(self, def_point):
        """
        Add def_point (Def object) to the list of defs.
        Allows for multiple def_points for the same node
        for reachability reasons. Reachability is stored
        in the actor_point and same actor can be reached
        under different reachability conditions in the
        same scope if callables don't start a new scope.
        Examples of such cases are macros or the include
        command in CMake.
        """
        self.def_points.append(def_point)

    def add_use_point(self, use_point):
        """
        Add use_point (Use object) to the list of uses.
        Allows for multiple def_points for the same node
        for reachability reasons. Reachability is stored
        in the actor_point and same actor can be reached
        under different reachability conditions in the
        same scope if callables don't start a new scope.
        Examples of such cases are macros or the include
        command in CMake.
        """
        self.use_points.append(use_point)

    def to_json(self, propagation_slice_mode=False):
        if propagation_slice_mode:
            return {
                "actor_name": self.name,
                "actor_node_id": self.node_data["id"],
                "actor_node_operation": self.node_data["operation"],
                "actor_node_type": self.node_data["type"],
                "actor_node_s_pos": self.node_data["s_pos"],
                "actor_node_e_pos": self.node_data["e_pos"],
                "actor_node_level": self.node_data["level"],
                "reachability": " ^ ".join(self.reachability),
                "code": self.ast.unparse(self.node_data, masked_types=["body"]),
                "def_node_ids": list(
                    map(lambda point: point.node_data["id"], self.def_points)
                ),
                "use_node_ids": list(
                    map(lambda point: point.node_data["id"], self.use_points)
                ),
            }
        return {
            "actor_name": self.name,
            "actor_node_id": self.node_data["id"],
            "actor_node_contamination": self.is_contaminated,
            "reachability": " ^ ".join(self.reachability),
            "def_node_ids": list(
                map(lambda point: point.node_data["id"], self.def_points)
            ),
            "use_node_ids": list(
                map(lambda point: point.node_data["id"], self.use_points)
            ),
        }
