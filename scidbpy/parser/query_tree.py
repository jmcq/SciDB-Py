import itertools
from collections import defaultdict

from .parser import SciDBParser


class QueryTree(object):
    def __init__(self, query_list):
        self.query_list = query_list
        self.node_list = [QueryTreeNode(q, i)
                          for i, q in enumerate(self.query_list)]
        self.head_nodes = []

        for i, head_node in enumerate(self.node_list):
            head_node = self.node_list[i]
            if len(head_node.upward_links) == 0:
                self.head_nodes.append(head_node)
            for arr_name in head_node.arrays_referenced:
                if arr_name not in head_node.upward_links:
                    head_node.find_network_links(arr_name,
                                                 self.node_list[i + 1:])

    def as_networkx(self, string_labels=True):
        import networkx
        G = networkx.DiGraph()
        edges = [(node, child)
                 for node in self.node_list
                 for child in itertools.chain(*node.downward_links.values())]

        if string_labels:
            edges = [(str(node), str(child)) for (node, child) in edges]

        G.add_edges_from(edges)
        return G

    def display(self):
        print
        for head_node in self.head_nodes:
            head_node.display()


class QueryTreeNode(object):
    def __init__(self, query, querynum):
        self.query = query
        self.arrays_referenced = self.query.arrays_referenced
        self.arrays_created = self.query.arrays_created
        self.arrays_deleted = self.query.arrays_deleted
        self.downward_links = defaultdict(list)
        self.upward_links = defaultdict(list)

    def find_network_links(self, arr_name, possible_children):
        # if array is deleted, no need to search for children
        if arr_name in self.arrays_deleted:
            return
        for i, node in enumerate(possible_children):
            if arr_name in node.arrays_referenced:
                self.downward_links[arr_name].append(node)
                node.upward_links[arr_name].append(self)
                node.find_network_links(arr_name, possible_children[i + 1:])
                break

    def display(self, depth=0):
        print "{0}{1}".format(depth * '-', self.query)
        for name in self.downward_links:
            print
            print "{0}{1}".format((depth + 1) * '-', name)
            for node in self.downward_links[name]:
                node.display(depth + 1)

    def __repr__(self):
        return "{0}".format(self.query)


    


