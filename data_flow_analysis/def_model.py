import itertools
from utils.exceptions import DebugException


class Def(object):
    """
    Model a Def point.
    Objects are called def_point
    """

    # Please make sure to reset this for each commit
    # (see system_diff_model.py > SystemDiff.__init__())
    id_generator = itertools.count(start=1)

    def __init__(
        self,
        node_data,
        def_type,
        actor_point,
        ast,
        prefix=None,
        suffix=None,
        preferred_name=None,
        scope=None,
        file=None,
    ):
        self.id = f"{ast.commit_hash}_{ast.name}_def_{next(Def.id_generator)}"
        self.ast = ast
        self.type = def_type
        self.scope = scope
        self.file = file

        # Storing the node_data
        self.node_data = node_data

        self.real_name = self.ast.get_name(self.node_data)
        if self.real_name is None:
            raise DebugException(
                f"{self.node_data['type']} requires NameGetter revisit"
            )
        self.name = self.real_name
        if prefix:
            self.name = prefix + self.name
        if suffix:
            self.name = self.name + suffix
        if preferred_name:
            self.name = preferred_name

        self.callable_arguments = []

        self.is_modified = node_data["operation"] != "no-op"
        self.is_value_affected = False
        self.is_reach_affected = False
        self.is_upstream = False
        self.is_in_propagation_slice = self.is_modified
        self.is_processed_for_propagation = False

        # Storing actor_point
        self.actor_point = actor_point

        # Locking further addition of use_points
        # used when no further users are allowed
        self.lock = False

        # Storing use_points
        self.use_points = []

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

    def add_callable_argument(self, use_point):
        if not self.lock:
            self.callable_arguments.append(use_point)

    def is_listed_use_point(self, use_point, *args, **kwargs):
        return use_point.node_data["id"] in set(
            lambda use_point: use_point.node_data["id"], self.use_points
        )

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
                "use_ids": list(
                    map(
                        lambda use_point: use_point.id,
                        self.use_points
                        + self.callable_arguments,  # TODO (Low) : Store seperately
                    )
                ),
                "non_contaminated_use_nodes": len(
                    list(
                        map(
                            lambda use_point: use_point.id,
                            filter(
                                lambda use_point: not use_point.is_in_propagation_slice,
                                self.use_points,
                            ),
                        )
                    )
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
            "use_ids": list(
                map(
                    lambda use_point: use_point.id,
                    self.use_points
                    + self.callable_arguments,  # TODO (Low) : Store seperately
                )
            ),
        }
