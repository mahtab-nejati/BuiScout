from utils.visitors import NodeVisitor


class NameGetter(NodeVisitor):
    def generic_visit(self, node_data):
        return self.ast.unparse(node_data)
    
    def visit_variable_declaration(self,node_data):
        return self.ast.get_data(self.ast.get_children_by_type(node_data,"simple_identifier"))['content']

