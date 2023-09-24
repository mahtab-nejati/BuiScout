import json
import pandas as pd
from functools import reduce
from collections import defaultdict
from utils.visitors import NodeVisitor
from .def_model import Def
from .use_model import Use
from .actor_model import Actor


class ConditionalDefUseChains(NodeVisitor):
    """
    NOTE: Reach the comments inside __init__() to understand attributes.
    """

    Actor = Actor
    Def = Def
    Use = Use

    def __init__(self, ast, sysdiff, scope=None, parent=None):
        """
        ast: ast_model.AST
        """
        self.ast = ast

        if scope:
            self.scope = scope
        else:
            self.scope = self.ast.get_data(self.ast.root)["id"]

        # The ConditionalDefUseChains object of the parent scope
        self.parent = parent
        self.parent_names_available = True
        # A list of ConditionalDefUseChains objects of the children scopes
        self.children = []

        self.ast_stack = []

        self.sysdiff = sysdiff

        # Store current reachability conditions based on conditional statements
        if parent is None:
            self.reachability_stack = []
            self.reachability_actor_id_stack = []
        else:
            self.reachability_stack = parent.reachability_stack.copy()
            self.reachability_actor_id_stack = parent.reachability_actor_id_stack.copy()

        # Stores a mapping between def nodes and their object (Def)
        # in the form of {'node_id': [Def]}
        # We store a list of Def objects for each node
        # because a Callable body can be processed multiple
        # times at call location and in case the callable
        # does not create a new scope, points will get overwritten.
        # Examples of such cases are macros or the include command in CMake.
        self.def_points = defaultdict(list)
        # Stores a mapping between use nodes and their object (Use)
        # in the form of {'node_id': [Use]}
        # We store a list of Use objects for each node
        # because a Callable body can be processed multiple
        # times at call location and in case the callable
        # does not create a new scope, points will get overwritten.
        # Examples of such cases are macros or the include command in CMake.
        self.use_points = defaultdict(list)
        # Stores a mapping between actor nodes and their object (Actor)
        # in the form of {'node_id': [Actor]}
        # We store a list of Actor objects for each node
        # because a Callable body can be processed multiple
        # times at call location and in case the callable
        # does not create a new scope, points will get overwritten.
        # Examples of such cases are macros or the include command in CMake.
        self.actor_points = defaultdict(list)

        # Stores a mapping of the name to its definition points {'name': [Def]}
        self.defined_names = defaultdict(list)
        # Stores a mapping of the name to its use points {'name': [Use]}
        self.used_names = defaultdict(list)
        # Stores a mapping of the name to undefined users {'name': [Use]}
        self.undefined_names = defaultdict(list)

    def get_definitions_by_name(self, node_data, get_from_parent_scopes=True):
        """
        Looks up use (node_data) in current and all ancestor contexts
        Returns the list of defs linked to the node_data
        """
        name = self.ast.get_name(node_data)
        defined_names = self.defined_names[name]
        if self.parent_names_available and get_from_parent_scopes:
            parent = self.parent
            while not parent is None:
                defined_names = parent.defined_names["name"] + defined_names
                parent = parent.parent
        return defined_names

    def register_new_use_point(
        self, use_node_data, actor_point, use_type="VAR", preferred_name=None
    ):
        """
        By default, adds the use_point to all applicable def_points defined
        prior to the use_point, REGARDLESS OF REACHABILITY.

        HOWEVER, the subclass of ConditionalDefUseChains in language support can define a method
        called "compare_reachability_conditions(def_point, use_point)" which consumes
        the def_point and use_point objects and returns:
                    "=" (equal reachability condition)
                    "<" (def reachability is subset of (loser than) use reachability)
                    ">" (def reachability is superset of (tighter than) use reachability)
                    "!" (contradiction exists in reachabilities)
                    "?" (unable to find a concrete relation between)

        if "compare_reachability_conditions(def_point, use_point)" returns:
                - "=" or "<":
                    Indicates that the def_point is on all reachable paths to the use-point.
                    Therefore, the use_point is added to the current def_point only and
                    prior def_points are ignored.
                - "?" or ">":
                    Indicates the use_point is/might be on the same reachable path as def_point
                    but might also be on other def_points' reachable paths.
                    Therefore, the use_point is added to the current def_point and
                    prior def_points are also considered.
                - "!":
                    Indicates the use_point and def_point never happen on the same reachable path.
                    Therefore, the use_point is NOT added to the current def_point but
                    prior def_points are stil considered.

        """
        use_point = self.Use(use_node_data, use_type, actor_point, self.ast)
        if preferred_name:
            use_point.name = preferred_name
        actor_point.add_use_point(use_point)
        self.use_points[use_point.node_data["id"]].append(use_point)
        self.used_names[use_point.name].append(use_point)
        defined_names = self.get_definitions_by_name(use_point.node_data)
        if defined_names:
            reachability_checker = getattr(
                self, "compare_reachability_conditions", None
            )
            if reachability_checker is None:
                list(
                    map(
                        lambda def_point: def_point.add_use_point(use_point),
                        defined_names,
                    )
                )
                return
            for def_point in reversed(defined_names):
                reachability_status = reachability_checker(def_point, use_point)
                if reachability_status in ["=", "<"]:
                    def_point.add_use_point(use_point)
                    break
                if reachability_status in ["!"]:
                    continue
                if reachability_status in [">", "?"]:
                    def_point.add_use_point(use_point)
                    continue
        else:
            self.undefined_names[use_point.name].append(use_point)
        return use_point

    def register_new_def_point(
        self, def_node_data, actor_point, def_type="VAR", prefix=None, suffix=None
    ):
        def_point = self.Def(
            def_node_data, def_type, actor_point, self.ast, prefix=prefix, suffix=suffix
        )
        actor_point.add_def_point(def_point)
        self.def_points[def_point.node_data["id"]].append(def_point)
        self.defined_names[def_point.name].append(def_point)
        return def_point

    def register_new_actor_point(self, node_data):
        actor_node_data = self.ast.get_actor(node_data)
        actor_point = self.Actor(
            actor_node_data,
            self.reachability_stack,
            self.reachability_actor_id_stack,
            self.ast,
        )
        self.actor_points[actor_node_data["id"]].append(actor_point)
        return actor_point

    def register_def_point_to_parent_scope(self, def_point):
        """
        Consumes a Def object and registers it to the parent scope.
        """
        self.parent.defined_names[def_point.name].append(def_point)
        self.parent.def_points[def_point.node_data["id"]].append(def_point)
        self.parent.actor_points[def_point.actor_point.node_data["id"]].append(
            def_point.actor_point
        )

    def add_condition_to_reachability_stack(self, condition_node_data, actor_point):
        self.reachability_stack.append(
            self.ast.unparse(condition_node_data).strip("()").strip()
        )
        self.reachability_actor_id_stack.append(actor_point.id)

    def remove_condition_from_reachability_stack(self, last_n=1):
        del self.reachability_stack[-last_n:]
        del self.reachability_actor_id_stack[-last_n:]

    def negate_last_condition_in_reachability_stack(self, negation_symbol="NOT"):
        # Usefull for else_if structure
        self.reachability_stack[
            -1
        ] = f"{negation_symbol} ({self.reachability_stack[-1]})"

    def analyze(self):
        self.generic_visit(self.ast.get_data(self.ast.root))
        self.sysdiff.set_data_flow_file_analysis(self.ast.file_path, self.ast.name)

    def get_all_def_points(self):
        return reduce(lambda a, b: [*a, *b], self.def_points.values(), [])

    def get_all_use_points(self):
        return reduce(lambda a, b: [*a, *b], self.use_points.values(), [])

    def get_all_actor_points(self):
        return reduce(lambda a, b: [*a, *b], self.actor_points.values(), [])

    def to_json(self, propagation_slice_mode=False):
        if propagation_slice_mode:
            def_points = filter(
                lambda point: point.is_contaminated, self.get_all_def_points()
            )
            use_points = filter(
                lambda point: point.is_contaminated, self.get_all_use_points()
            )
            actor_points = filter(
                lambda point: point.is_contaminated, self.get_all_actor_points()
            )
        else:
            def_points = self.get_all_def_points()
            use_points = self.get_all_use_points()
            actor_points = self.get_all_actor_points()
        cdu_chains_output = {
            "commit_hash": self.ast.commit_hash,
            "cluster": self.ast.name,
            "scope": self.scope,
            "parent_scopes": None if self.parent is None else self.parent.scope,
            "def_points": list(
                map(
                    lambda def_point: def_point.to_json(propagation_slice_mode),
                    def_points,
                )
            ),
            "use_points": list(
                map(
                    lambda use_point: use_point.to_json(propagation_slice_mode),
                    use_points,
                )
            ),
            "actor_points": list(
                map(
                    lambda actor_point: actor_point.to_json(propagation_slice_mode),
                    actor_points,
                )
            ),
            "undefined_names": reduce(
                lambda a, b: [*a, *b],
                reduce(
                    lambda a, b: [*a, *b],
                    map(
                        lambda use_point_list: (
                            list(
                                map(
                                    lambda use_point: use_point.to_json(),
                                    use_point_list,
                                )
                            ),
                        ),
                        self.undefined_names.values(),
                    ),
                    [],
                ),
                [],
            ),
        }

        return cdu_chains_output

    def export_cdu_json(self, save_path):
        save_path.mkdir(parents=True, exist_ok=True)
        if self.sysdiff.analysis_mode == "change_location":
            self.ast.export_json(save_path / "diffs")
        with open(
            save_path / f"{self.ast.name}_cdu_output_{self.scope}.json", "w"
        ) as f:
            json.dump(self.to_json(), f)

    def to_csv(self, propagation_slice_mode=False):
        data = self.to_json(propagation_slice_mode)
        if data["def_points"]:
            def_points_df = pd.DataFrame(data["def_points"])
            cols = list(def_points_df.columns)
            def_points_df["scope"] = self.scope
            def_points_df["parent_scopes"] = (
                None if self.parent is None else self.parent.scope
            )
            def_points_df = def_points_df[["scope", *cols]]
        else:
            def_points_df = pd.DataFrame()

        if data["use_points"]:
            use_points_df = pd.DataFrame(data["use_points"])
            cols = list(use_points_df.columns)
            use_points_df["scope"] = self.scope
            use_points_df = use_points_df[["scope", *cols]]
        else:
            use_points_df = pd.DataFrame()

        if data["actor_points"]:
            actor_points_df = pd.DataFrame(data["actor_points"])
            cols = list(actor_points_df.columns)
            actor_points_df["scope"] = self.scope
            actor_points_df = actor_points_df[["scope", *cols]]
        else:
            actor_points_df = pd.DataFrame()

        if propagation_slice_mode:
            undefined_names_df = None
        else:
            undefined_names_df = pd.DataFrame(data["undefined_names"])
            cols = list(undefined_names_df.columns)
            undefined_names_df["scope"] = self.scope
            undefined_names_df = undefined_names_df[["scope", *cols]]

        return def_points_df, use_points_df, actor_points_df, undefined_names_df

    def export_cdu_csv(self, save_path):
        save_path.mkdir(parents=True, exist_ok=True)
        if self.sysdiff.analysis_mode == "change_location":
            self.ast.export_csv(save_path / "diffs")
        (
            def_points_df,
            use_points_df,
            actor_points_df,
            undefined_names_df,
        ) = self.to_csv()
        def_points_df.to_csv(
            save_path / f"{self.ast.name}_def_points_{self.scope}.csv", index=False
        )
        use_points_df.to_csv(
            save_path / f"{self.ast.name}_use_points_{self.scope}.csv", index=False
        )
        actor_points_df.to_csv(
            save_path / f"{self.ast.name}_actor_points_{self.scope}.csv", index=False
        )
        undefined_names_df.to_csv(
            save_path / f"{self.ast.name}_undefined_names_{self.scope}.csv", index=False
        )

    def get_propagation_slices(self):
        """
        This method must be implemented in the language support subclass. As the result,
        Def/Use/Actor objects that are affected have their .is_contaminated attribute set to True.

        NOTE: Make sure you uss the .set_contamination() method to set the .is_contaminated attribute to True
        for all contaminated Def/Use/Actor objects.

        Each propagation slice is a list of dictionaries representing the
        propagation relationships in the form of a Knowledge Graph (KD).
        Each entry of the list is one relationship stored as a dictionary.
        The dictionaries have the following structure:
            {
                'subject': some_object (Def,Use,Actor),
                'subject_id': 'str_id',
                'subject_type': the_class,
                'propagation_rule': 'str_rule',
                'object': some_object (Def,Use,Actor),
                'object_id': 'str_id',
                'object_type': the_class,
            }

        NOTE: When exporting the output, the "subject" and "object" keys are dropped as it is expected to export
        them in a different file and refer to them with their id.
        """
        pass

    def get_contaminated_points(self):
        def_points = list(
            filter(lambda point: point.is_contaminated, self.get_all_def_points())
        )
        use_points = list(
            filter(lambda point: point.is_contaminated, self.get_all_use_points())
        )
        actor_points = list(
            filter(lambda point: point.is_contaminated, self.get_all_actor_points())
        )
        return def_points + use_points + actor_points
