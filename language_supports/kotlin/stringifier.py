from utils.visitors import NodeVisitor


class Stringifier(NodeVisitor):
    def generic_visit(self, node_data):
        return f'***{node_data["type"]}***'