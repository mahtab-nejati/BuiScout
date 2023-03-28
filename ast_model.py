import networkx as nx
from networkx.drawing.nx_agraph import read_dot, write_dot
import pygraphviz as pgv
from functools import reduce
from copy import deepcopy
import importlib

LANGUAGE = 'cmake'
rg = importlib.import_module(f'node_stringifier.{LANGUAGE}_node_stringifier')


class PairedAST(nx.DiGraph):
    
    def __init__(self, *args, **kwargs):
        """
        Initializes the AST pair as a nx.DiGraph.
        Cleans the AST pair and sets node/AST pair attributes.
        """
        super(PairedAST, self).__init__(*args, **kwargs)

        # Remove extra nodes
        none_nodes = list(filter(lambda node: node[-1].get('label') is None, self.nodes.items()))
        for node in none_nodes:
            self.remove_node(node[0])

        # Set node attributes
        # The head of the AST (rg.ROOT_TYPE) has level=0.
        self.set_node_attributes()
        self.set_nodes_levels()

        # Set AST pair attributes
        # Also sets self.depth = max(levels)+1
        self.depth = max([0]+list(map(lambda node: node['level']+1, self.nodes.values())))
        self.node_types = set(map(lambda node: node['type'], self.nodes.values()))
        self.affected_nodes = {'source': self.get_affected_nodes('source'),
                               'destination': self.get_affected_nodes('destination')}
        self.summarized_nodes = {'source':dict(),
                                 'destination':dict()}
        self.roots = {'source': self.get_root('source'),
                      'destination': self.get_root('destination')}
        
        # Slice up changes
        self.slices = {'source': self.get_slice('source'),
                       'destination': self.get_slice('destination')}
        self.slices['change'] = nx.union(self.slices['source'], self.slices['destination'])
        # TODO: add matching edges to the slice? (messes up the visualization)
        # self.slice.add_edges_from(list(filter(lambda edge: 
        #                                       edge[0] in self.slice.nodes() and edge[1] in self.slice.nodes(),
        #                                       self.get_matching_edges())))

        # Initialize summary of the change
        self.summary = []
    
    def set_node_attributes(self, *args, **kwargs):
        """
        Parses node label and cleans it into a dict of {'node_id': dict(nod_data)}
        using the self.clean_node_attributes.
        Sets the extracted cleaned data as node attributes.
        """
        node_attrs = list(map(lambda node: self.clean_node_attributes(node[0], node[-1]), self.nodes.items()))
        nx.set_node_attributes(self, reduce(lambda a, b: {**a, **b}, node_attrs))
    
    def set_nodes_levels(self, *args, **kwargs):
        """
        Sets the attribute "level" for nodes and self.depth for AST pair.
        The head of the AST (rg.ROOT_TYPE) has level=0.
        """
        depth = 0 
        current_level_nodes = dict(filter(lambda node: node[-1]['type']==rg.ROOT_TYPE, self.nodes.items()))
        while current_level_nodes.keys():
            next_level_nodes = dict()
            for node_id, node_data in current_level_nodes.items():
                nx.set_node_attributes(self, {node_id:{'level': depth}})
                next_level_nodes.update(self.get_children(node_data))
            depth += 1
            current_level_nodes = dict(next_level_nodes)
                
    def clean_node_attributes(self, node_id, node_data, *args, **kwargs):
        """
        Parses node label and cleans it into a dict of {'node_id': dict(nod_data)}
        """
        content = node_data['label'].split('@#$$#@')
        color = node_data['color']
        
        del node_data['label']
        # del node[-1]['color'] # TODO: kept for visualization purposes
        
        if color=='red':
            operation="deleted"
        elif color=='green':
            operation="added"
        elif color=='blue':
            operation = "moved"
        elif color=='orange':
            operation = "updated"
        else:
            operation = "no-op"
        attrs = {node_id: {"id": node_id,
                           "cluster": 'source' if '_src_' in node_id else 'destination',
                           "type": content[0].strip() if content[0].strip()!="" else 'quotation',
                           "content": '\n'.join(content[1:-2]).strip() if content[0].strip()!="" else '"',
                           "operation": operation,
                           "s_pos": int(content[-2].strip()),
                           "e_pos": int(content[-1].strip())}}
        attrs[node_id]['label'] = f'cluster: {attrs[node_id]["cluster"]}\ntype: {attrs[node_id]["type"]}\n'
        attrs[node_id]['label'] += f'content: {attrs[node_id]["content"]}\npostion: {attrs[node_id]["s_pos"]}-{attrs[node_id]["e_pos"]}'
        return attrs
 
    def get_data(self, node, *args, **kwargs):
        """
        Retruns the node attributes when node is a dictionary {'node_id': dict(nod_data)}
        with only one or zero entries (nodes)
        """
        try:
            return list(node.values())[0]
        except IndexError:
            return {}
    
    def get_root(self, cluster, *args, **kwargs):
        """
        Returns the root node of the cluster as a dict of {'node_id': dict(nod_data)}
        """
        return dict(filter(lambda node: node[-1]['cluster']==cluster and node[-1]['type']==rg.ROOT_TYPE,
                           self.nodes.items()))
                
    def get_parent(self, node_data, *args, **kwargs):
        """
        Returns the parent of the node as a dict of {'node_id': dict(nod_data)}
        """
        return dict(map(lambda parent_id: (parent_id, self.nodes[parent_id]),
                        filter(lambda parent_id: self.nodes[parent_id]['cluster']==node_data['cluster'],
                               self.predecessors(node_data['id']))))
    
    def get_children(self, node_data, *args, **kwargs):
        """
        Returns the children of the node as a dict of {'node_id': dict(nod_data)}
        """
        return dict(map(lambda child_id: (child_id, self.nodes[child_id]),
                        filter(lambda child_id: self.nodes[child_id]['cluster']==node_data['cluster'],
                               self.successors(node_data['id']))))
    
    def get_typed_children(self, node_data, child_type, *args, **kwargs):
        """
        Returns the children of the node with child_type as a dict of {'node_id': dict(nod_data)}
        """
        return dict(filter(lambda node: node[-1]['type']==child_type,
                    self.get_children(node_data).items()))

    def get_match(self, node_data, *args, **kwargs):
        """
        Returns the match of the node in the other cluster
        as a dict of {'node_id': dict(nod_data)}.
        Returns dict() if no match exists.
        """
        if node_data['cluster']=='source':
            target_node_set = self.successors(node_data['id'])
        elif node_data['cluster']=='destination':
            target_node_set = self.predecessors(node_data['id'])
        else:
            target_node_set = []
        return dict(map(lambda match_id: (match_id, self.nodes[match_id]),
                        filter(lambda match_id: self.nodes[match_id]['cluster']!=node_data['cluster'],
                               target_node_set)))
    
    def get_matching_edges(self, *args, **kwargs):
        """
        Returns the list of matching edges between the clusters.
        """
        return list(filter(lambda edge: edge[-1].get('style')=='dashed', self.edges.data()))
        
    def get_affected_nodes(self, cluster, *args, **kwargs):
        """
        Returns the affected nodes in the change from the cluster
        as a dict of {'node_id': dict(nod_data)}.
        Currently excludes comments as GumTree underperforms and
        poses overplotting problems.
        """
        affected_nodes =  dict(filter(lambda node:
                                      node[-1]['cluster']==cluster and node[-1]['operation']!='no-op',
                                      self.nodes.items()))
        ignored_nodes = filter(lambda node_data: node_data['type'] in rg.IGNORED_TYPES, affected_nodes.values())
        for ignored_node_data in ignored_nodes:
            ignored_subtree_nodes = self.get_subtree_nodes(ignored_node_data)
            affected_nodes = dict(filter(lambda node: node[-1]['id'] not in ignored_subtree_nodes,
                                         affected_nodes.items()))
        return affected_nodes

    def get_slice(self, cluster, *args, **kwargs):
        """
        Returns contaminated slice from the cluster as a SlicedAST() object.
        """

        # Initialize slice data
        affected_nodes = self.affected_nodes[cluster]
        impact_depth = max([0]+list(map(lambda node_data: node_data['level'], affected_nodes.values())))
        current_slice = dict(zip(list(range(self.depth)), [None]*self.depth))
        current_slice[0] = self.roots[cluster]
        
        # Slice upwards
        for l in range(impact_depth, 0, -1):
            if current_slice[l] is None:
                current_slice[l] = dict().copy()
            current_slice[l].update(dict(filter(lambda node: node[-1]['level']==l,
                                                affected_nodes.items())))
            
            for pl in range(l-1, 0, -1):
                if current_slice[pl] is None:
                    current_slice[pl] = dict().copy()
                current_slice[pl].update(reduce(lambda a, b: {**a, **b},
                                                [{}]+list(map(lambda node_data: self.get_parent(node_data),
                                                              current_slice[pl+1].values()))))
        
        # Slice downwards
        for l in range(1, self.depth-1):
            if current_slice[l] is None:
                current_slice[l] = dict().copy()
            if current_slice[l+1] is None:
                current_slice[l+1] = dict().copy()
            current_slice[l+1].update(reduce(lambda a, b: {**a, **b}, 
                                             [{}]+list(map(lambda node_data: self.get_children(node_data),
                                                           current_slice[l].values()))))

        # Clean slice data
        slice_nodes = reduce(lambda a, b: {**a, **b}, [{}]+list(current_slice.values()))
        slice_edges = list(filter(lambda edge: edge[0] in slice_nodes and edge[1] in slice_nodes, self.edges.data()))
        
        # Create slice
        return SlicedAST(cluster, slice_nodes, slice_edges)
    
    def get_subtree_nodes(self, head_data, *args, **kwargs):
        subtree_nodes = {head_data['id']: head_data}
        current_level_nodes = deepcopy(subtree_nodes)
        while current_level_nodes.keys():
            next_level_nodes = dict()
            for node_data in current_level_nodes.values():
                next_level_nodes.update(self.get_children(node_data))
            subtree_nodes.update(deepcopy(current_level_nodes))
            current_level_nodes = dict(next_level_nodes)
        return subtree_nodes

    def parse_subtree(self, head_data, *args, **kwargs):
        subtree_nodes = self.get_subtree_nodes(head_data)
        return ''.join(map(lambda cp: cp[0], 
                            sorted(map(lambda node_data: (node_data['content'], node_data['s_pos']),
                                       subtree_nodes.values()),
                                   key=lambda cp: cp[-1])))

    def update_summarization_status(self, head_data, *args, **kwargs):
        subtree = self.get_subtree_nodes(head_data)
        summerized = dict(filter(lambda node: node[-1]['operation']==head_data['operation'] or node[-1]['operation']=='no-op',
                                 subtree.items()))
        self.summarized_nodes['source'].update(dict(filter(lambda node: node[-1]['cluster']=='source',
                                                           summerized.items())))
        
        self.summarized_nodes['destination'].update(dict(filter(lambda node: node[-1]['cluster']=='destination',
                                                                summerized.items())))
        
    def get_summarization_status(self, node_data, *args, **kwargs):
        return node_data['id'] in self.summarized_nodes[node_data['cluster']]

    def export_dot(self, path, *args, **kwargs):
        write_dot(self, path)

    def summarize(self, *args, **kwargs):
        for level in range(self.depth):
            # DELETIONS
            in_process = filter(lambda node_data: node_data['level']==level and node_data['operation']=='deleted' and\
                                                    not self.get_summarization_status(node_data) and node_data['type'] not in rg.IGNORED_TYPES,
                                self.affected_nodes['source'].values())
            for node_data in in_process:
                self.summarize_deletion(node_data)

            # ADDITIONS
            in_process = filter(lambda node_data: node_data['level']==level and node_data['operation']=='added' and\
                                                    not self.get_summarization_status(node_data) and node_data['type'] not in rg.IGNORED_TYPES,
                                self.affected_nodes['destination'].values())
            for node_data in in_process:
                self.summarize_addition(node_data)
            
            # MOVEMENTS
            in_process = filter(lambda node_data: node_data['level']==level and node_data['operation']=='moved' and\
                                                    not self.get_summarization_status(node_data) and node_data['type'] not in rg.IGNORED_TYPES,
                                self.affected_nodes['source'].values())
            for node_data in in_process:
                self.summarize_movement(node_data)

            # UPDATES
            in_process = filter(lambda node_data: node_data['level']==level and node_data['operation']=='updated' and\
                                                    not self.get_summarization_status(node_data) and node_data['type'] not in rg.IGNORED_TYPES,
                                self.affected_nodes['source'].values())
            for node_data in in_process:
                self.summarize_update(node_data)


        return self.summary
    
    def summarize_deletion(self, node_data, *args, **kwargs):
        self.summary.append({'operation': 'deleted',
                             'source_node': node_data['type'],
                             'source_node_summary': rg.stringify(self, node_data),
                             'source_position': f'{node_data["s_pos"]}-{node_data["e_pos"]}',
                             'destination_node': None,
                             'destination_node_summary': None,
                             'destination_postion': None})
        
        self.update_summarization_status(node_data)
            
    def summarize_addition(self, node_data, *args, **kwargs):
        self.summary.append({'operation': 'added',
                             'source_node': None,
                             'source_node_summary': None,
                             'source_position': None,
                             'destination_node': node_data['type'],
                             'destination_node_summary': rg.stringify(self, node_data),
                             'destination_postion': f'{node_data["s_pos"]}-{node_data["e_pos"]}'})
        
        self.update_summarization_status(node_data)

    def summarize_movement(self, node_data, *args, **kwargs):
        source_node = node_data
        source_parent = self.get_data(self.get_parent(source_node))
        source_parent_match = self.get_data(self.get_match(source_parent))
        destination_node = self.get_data(self.get_match(source_node))
        destination_parent = self.get_data(self.get_parent(destination_node))
        if source_parent_match and source_parent_match['id'] == destination_parent['id']:
            movement_type = 'moved_same_parent'
        else:
            movement_type = 'moved_changed_parent'
        self.summary.append({'operation': movement_type,
                             'source_node': source_node['type'],
                             'source_node_summary': rg.stringify(self, source_node),
                             'source_position': f'{source_node["s_pos"]}-{source_node["e_pos"]}',
                             'destination_node': destination_node['type'],
                             'destination_node_summary': rg.stringify(self, destination_node),
                             'destination_postion': f'{destination_node["s_pos"]}-{destination_node["e_pos"]}'})
        
        self.update_summarization_status(source_node)
        self.update_summarization_status(destination_node)
    
    def summarize_update(self, node_data, *args, **kwargs):
        source_node = node_data
        destination_node = self.get_data(self.get_match(source_node))
        self.summary.append({'operation': 'updated',
                             'source_node': source_node['type'],
                             'source_node_summary': rg.stringify(self, source_node),
                             'source_position': f'{source_node["s_pos"]}-{source_node["e_pos"]}',
                             'destination_node': destination_node['type'],
                             'destination_node_summary': rg.stringify(self, destination_node),
                             'destination_postion': f'{destination_node["s_pos"]}-{destination_node["e_pos"]}'})
        
        self.update_summarization_status(source_node)
        self.update_summarization_status(destination_node)

    
class SlicedAST(PairedAST):
    def __init__(self, cluster=None, nodes={}, edges=[], *args, **kwargs):
        if edges:
            super(PairedAST, self).__init__(edges)
            nx.set_node_attributes(self, nodes)
        else:
            super(PairedAST, self).__init__()
            self.add_nodes_from(nodes)
            nx.set_node_attributes(self, nodes)

        self.cluster = cluster
        self.depth = max([0]+list(map(lambda node: node[1].get('level')+1, self.nodes.items())))
        self.root = self.get_root(self.cluster)
    
    def get_root(self, *args, **kwargs):
        if self.cluster is None:
            return super(SlicedAST, self).get_root(*args, **kwargs)
        else:
            return super(SlicedAST, self).get_root(self.cluster)
    
    def get_affected_nodes(self, *args, **kwargs):
        if self.cluster is None:
            return super(SlicedAST, self).get_affected_nodes(*args, **kwargs)
        else:
            return super(SlicedAST, self).get_affected_nodes(self.cluster)
    
    def get_slice(self, *args, **kwargs):
        pass