import itertools
from utils.exceptions import DebugException


class Actor(object):
    """
    Model an Actor point.
    Objects are called actor_point
    """

    # Please make sure to reset this for each commit
    # (see system_diff_model.py > SystemDiff.__init__())
    id_generator = itertools.count(start=1)

    def __init__(
        self,
        node_data,
        reachability,
        reachability_actor_ids,
        ast,
        actor_type="built_in",
        scope=None,
        file=None,
    ):
        self.id = f"{ast.commit_hash}_{ast.name}_actor_{next(Actor.id_generator)}"
        self.ast = ast
        self.type = actor_type
        self.scope = scope
        self.file = file

        # Storing the node_data
        self.node_data = node_data

        self.name = self.ast.get_name(self.node_data)
        if self.name is None:
            raise DebugException(
                f"{self.node_data['type']} requires NameGetter revisit"
            )
        self.is_modified = node_data["operation"] != "no-op"
        self.is_value_affected = False
        self.is_reach_affected = False
        self.is_import_reach_affected = False
        self.is_upstream = False
        self.is_in_propagation_slice = self.is_modified
        self.is_processed_for_propagation = False

        # Storing reachability condition
        self.reachability = reachability.copy()
        self.reachability_actor_ids = reachability_actor_ids.copy()

        # Storing the list of [Defs]
        self.def_points = []
        # Storing the list of [Uses]
        self.use_points = []

    def set_is_modified(self):
        self.is_modified = True
        self.is_in_propagation_slice = True

    def set_is_value_affected(self):
        self.is_value_affected = True
        self.is_in_propagation_slice = True

    def set_is_reach_affected(self):
        self.is_reach_affected = True
        self.is_in_propagation_slice = True

    def set_is_import_reach_affected(self):
        self.is_reach_affected = True
        self.is_import_reach_affected = True
        self.is_in_propagation_slice = True

    def set_is_upstream(self):
        self.is_upstream = True
        self.is_in_propagation_slice = True

    def set_is_processed_for_propagation(self):
        self.is_processed_for_propagation = True

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
                "reachability": self.reachability,
                "reachability_actor_ids": self.reachability_actor_ids,
                "code": self.ast.unparse(self.node_data, masked_types=["body"]),
                "def_ids": list(map(lambda point: point.id, self.def_points)),
                "use_ids": list(map(lambda point: point.id, self.use_points)),
            }
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "node_id": self.node_data["id"],
            "is_modified": self.is_modified,
            "is_value_affected": self.is_value_affected,
            "is_reach_affected": self.is_reach_affected,
            "is_upstream": self.is_upstream,
            "reachability": self.reachability,
            "reachability_actor_ids": self.reachability_actor_ids,
            "def_ids": list(map(lambda point: point.id, self.def_points)),
            "use_ids": list(map(lambda point: point.id, self.use_points)),
        }
