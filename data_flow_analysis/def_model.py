from utils.exceptions import DebugException


class Def(object):
    """
    Model a Def point.
    Objects are called def_point
    """

    def __init__(self, node_data, def_type, actor_point, ast, prefix=None, suffix=None):
        self.ast = ast
        self.type = def_type

        # Storing the node_data
        self.node_data = node_data

        self.name = self.ast.get_name(self.node_data)
        if self.name is None:
            raise DebugException(
                f"{self.node_data['type']} requires NameGetter revisit"
            )
        if prefix:
            self.name = prefix + self.name
        if suffix:
            self.name = self.name + suffix
        self.is_contaminated = node_data["operation"] != "no-op"

        # Storing actor_point
        self.actor_point = actor_point

        # Locking further addition of use_points
        # used when no further users are allowed
        self.lock = False

        # Storing use_points
        self.use_points = []

    def set_contamination(self):
        self.is_contaminated = True

    def add_use_point(self, use_point):
        """
        Add use_point to the list of use_points if it is a user of the self.node_data
        """
        if not self.lock:
            if self.is_user(use_point):
                self.use_points.append(use_point)

    def is_user(self, use_point):
        """
        Checks if both the use_point and self (definition) refer to the
        same name and returns True if they do.
        """
        return self.name == use_point.name

    def is_listed_use_point(self, use_point, *args, **kwargs):
        return use_point.node_data["id"] in set(
            lambda use_point: use_point.node_data["id"], self.use_points
        )

    def to_json(self, propagation_slice_mode=False):
        if propagation_slice_mode:
            return {
                "def_type": self.type,
                "def_name": self.name,
                "def_node_id": self.node_data["id"],
                "def_node_operation": self.node_data["operation"],
                "def_node_type": self.node_data["type"],
                "def_node_s_pos": self.node_data["s_pos"],
                "def_node_e_pos": self.node_data["e_pos"],
                "def_node_level": self.node_data["level"],
                "actor_node_id": self.actor_point.node_data["id"],
                "reachability": " ^ ".join(self.actor_point.reachability),
                "code": self.actor_point.ast.unparse(
                    self.actor_point.node_data, masked_types=["body"]
                ),
                "use_node_ids": list(
                    map(lambda use_point: use_point.node_data["id"], self.use_points)
                ),
                "non_contaminated_use_nodes": len(
                    list(
                        map(
                            lambda use_point: use_point.node_data["id"],
                            filter(
                                lambda use_point: not use_point.is_contaminated,
                                self.use_points,
                            ),
                        )
                    )
                ),
            }
        return {
            "def_type": self.type,
            "def_name": self.name,
            "def_node_id": self.node_data["id"],
            "def_node_contamination": self.is_contaminated,
            "actor_node_id": self.actor_point.node_data["id"],
            "use_node_ids": list(
                map(lambda use_point: use_point.node_data["id"], self.use_points)
            ),
        }
