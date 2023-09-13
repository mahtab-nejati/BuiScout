from utils.exceptions import DebugException


class Use(object):
    """
    Model a Use point.
    Objects are called use_point
    """

    def __init__(self, node_data, use_type, actor_point, ast):
        self.ast = ast
        self.type = use_type

        # Storing the node_data
        self.node_data = node_data

        self.name = self.ast.get_name(self.node_data)
        if self.name is None:
            raise DebugException(
                f"{self.node_data['type']} requires NameGetter revisit"
            )
        self.is_contaminated = node_data["operation"] != "no-op"

        # Storing actor_point
        self.actor_point = actor_point

    def set_contamination(self):
        self.is_contaminated = True

    def is_user_of(self, def_point):
        """
        Checks if both the self (user) refers to the
        same name as the def_name and returns.
        """
        return self.name == def_point.name

    def to_json(self, propagation_slice_mode=False):
        if propagation_slice_mode:
            return {
                "def_type": self.type,
                "def_name": self.name,
                "def_node_id": self.node_data["id"],
                "def_node_operation": self.node_data["operation"],
                "def_node_type": self.node_data["type"],
                "def_node_content": self.node_data["content"],
                "def_node_s_pos": self.node_data["s_pos"],
                "def_node_e_pos": self.node_data["e_pos"],
                "def_node_level": self.node_data["level"],
                "actor_node_id": self.actor_point.node_data["id"],
                "reachability": " ^ ".join(self.actor_point.reachability),
                "code": self.actor_point.ast.unparse(
                    self.actor_point.node_data, masked_types=["body"]
                ),
            }
        return {
            "use_type": self.type,
            "use_name": self.name,
            "use_node_id": self.node_data["id"],
            "use_node_contamination": self.is_contaminated,
            "actor_node_id": self.actor_point.node_data["id"],
        }
