"""
Shadowed code from https://github.com/python/cpython/blob/3.11/Lib/ast.py
Modified to make compatible with CMake AST.
"""


class NodeVisitor(object):
    """
    Adopted from https://github.com/python/cpython/blob/3.11/Lib/ast.py, modified.
    A node visitor base class that walks the abstract syntax tree and calls a
    visitor function for every node found. The `visit` method may return a
    value or perform some operation on the node.
    The input is the output of the ast.get_data(node).
    This class is meant to be subclassed, with the subclass adding visitor
    methods.
    Per default the visitor functions for the nodes are ``'visit_'`` +
    node_data['type']. So a `variable` node visit function would
    be `visit_variable`. This behavior can be changed by overriding
    the `visit` method. If no visitor function exists for a node
    (return value `None`) the `generic_visit` visitor is used instead.
    Don't use the `NodeVisitor` if you want to apply changes to nodes during
    traversing.
    """

    def __init__(self, ast):
        self.ast = ast

    def visit(self, node_data, *args, **kwargs):
        """
        Visit a node.
        The input is the output of the ast.get_data(node), i.e., node_data.
        """
        method = "visit_" + node_data["type"]
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node_data, *args, **kwargs)

    def generic_visit(self, node_data, *args, **kwargs):
        """
        Called if no explicit visitor function exists for a node.
        """
        children = sorted(
            list(self.ast.get_children(node_data).values()),
            key=lambda child_data: child_data["s_pos"],
        )
        for child_data in children:
            self.visit(child_data, *args, **kwargs)
