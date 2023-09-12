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
        self.contaminated = node_data["operation"] != "no-op"

        # Storing actor_point
        self.actor_point = actor_point

    def set_contamination(self):
        self.contaminated = True

    def is_user_of(self, def_point):
        """
        Checks if both the self (user) refers to the
        same name as the def_name and returns.
        """
        return self.name == def_point.name

    def to_json(self):
        return {
            "use_type": self.type,
            "use_name": self.name,
            "use_node_id": self.node_data["id"],
            "actor_node_id": self.actor_point.node_data["id"],
        }
