from utils.visitors import NodeVisitor


class ActorGetter(NodeVisitor):
    def generic_visit(self, node_data):
        return node_data
