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

    def __init__(
        self,
        node_data,
        use_type,
        actor_point,
        ast,
        preferred_name=None,
        scope=None,
        file=None,
    ):
        self.id = f"{ast.commit_hash}_{ast.name}_use_{next(Use.id_generator)}"
        self.ast = ast
        self.type = use_type
        self.scope = scope
        self.file = file

        # Storing the node_data
        self.node_data = node_data

        self.real_name = self.ast.get_name(self.node_data)
        if self.real_name is None:
            raise DebugException(
                f"{self.node_data['type']} requires NameGetter revisit"
            )
        if preferred_name:
            self.name = preferred_name
        else:
            self.name = self.real_name
        self.is_modified = node_data["operation"] != "no-op"
        self.is_value_affected = False
        self.is_reach_affected = False
        self.is_upstream = False
        self.is_in_propagation_slice = self.is_modified
        self.is_processed_for_propagation = False

        # Storing actor_point
        self.actor_point = actor_point

    def set_is_modified(self):
        self.is_modified = True
        self.is_in_propagation_slice = True
        self.actor_point.is_in_propagation_slice = True

    def set_is_value_affected(self):
        self.is_value_affected = True
        self.is_in_propagation_slice = True
        self.actor_point.is_in_propagation_slice = True

    def set_is_reach_affected(self):
        self.is_reach_affected = True
        self.is_in_propagation_slice = True
        self.actor_point.is_in_propagation_slice = True

    def set_is_upstream(self):
        self.is_upstream = True
        self.is_in_propagation_slice = True
        self.actor_point.is_in_propagation_slice = True

    def set_is_processed_for_propagation(self):
        self.is_processed_for_propagation = True

    def is_user_of(self, def_point):
        """
        Checks if both the self (user) refers to the
        same name as the def_name and returns.
        """
        return self.name == def_point.name

    def to_json(self, propagation_slice_mode=False):
        if propagation_slice_mode:
            return {
                "id": self.id,
                "type": self.type,
                "name": self.name,
                "is_modified": self.is_modified,
                "is_value_affected": self.is_value_affected,
                "is_reach_affected": self.is_reach_affected,
                "is_upstream": self.is_upstream,
                "node_id": self.node_data["id"],
                "node_operation": self.node_data["operation"],
                "node_type": self.node_data["type"],
                "node_s_pos": self.node_data["s_pos"],
                "node_e_pos": self.node_data["e_pos"],
                "node_level": self.node_data["level"],
                "actor_id": self.actor_point.id,
                "reachability": self.actor_point.reachability,
                "reachability_actor_ids": self.actor_point.reachability_actor_ids,
                "code": self.actor_point.ast.unparse(
                    self.actor_point.node_data, masked_types=["body"]
                ),
            }
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "is_modified": self.is_modified,
            "is_value_affected": self.is_value_affected,
            "is_reach_affected": self.is_reach_affected,
            "is_upstream": self.is_upstream,
            "node_id": self.node_data["id"],
            "actor_id": self.actor_point.id,
        }
