import itertools
from utils.exceptions import DebugException


class Use(object):
    """
    Model a Use point.
    Objects are called use_point
    """

    # Please make sure to reset this for each commit
    # (see system_diff_model.py > SystemDiff.__init__())
    id_generator = itertools.count(start=1)

    def __init__(self, node_data, use_type, actor_point, ast):
        self.id = f"{ast.commit_hash}_{ast.name}_{next(Use.id_generator)}"
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
                "use_id": self.id,
                "use_type": self.type,
                "use_name": self.name,
                "use_node_id": self.node_data["id"],
                "use_node_operation": self.node_data["operation"],
                "use_node_type": self.node_data["type"],
                "use_node_s_pos": self.node_data["s_pos"],
                "use_node_e_pos": self.node_data["e_pos"],
                "use_node_level": self.node_data["level"],
                "actor_id": self.actor_point.id,
                "reachability": self.actor_point.reachability,
                "reachability_actor_ids": self.actor_point.reachability_actor_ids,
                "code": self.actor_point.ast.unparse(
                    self.actor_point.node_data, masked_types=["body"]
                ),
            }
        return {
            "use_id": self.id,
            "use_type": self.type,
            "use_name": self.name,
            "use_node_id": self.node_data["id"],
            "use_node_contamination": self.is_contaminated,
            "actor_id": self.actor_point.id,
        }
