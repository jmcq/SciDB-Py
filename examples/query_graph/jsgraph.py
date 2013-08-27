"""JS viewer for graph

Adapted from https://networkx.lanl.gov/trac/browser/networkx/examples/javascript/force.py
"""
from scidbpy.parser import SciDBParser, QueryTree
import matplotlib.pyplot as plt
import networkx as nx
import json
from networkx.readwrite import json_graph
import http_server

test_data = """
CREATE ARRAY A <f0:double> [i0=0:9,1000,0,i1=0:9,1000,0];
store(build(A,iif(A.i0=A.i1,1,0)), A);
store(build(A,iif(A.i0=A.i1,2,1)), B);
multiply(A, B);
remove(A);
DROP ARRAY B;
"""

parser = SciDBParser().parse(test_data)

QT = QueryTree(parser.query_list())

G = QT.as_networkx(string_labels=True)
# write json formatted data
d = json_graph.node_link_data(G) # node-link format to serialize
# write json 
json.dump(d, open('jsgraph/jsgraph.json','w'))
print('Wrote node-link JSON data to jsgraph/jsgraph.json')
# open URL in running web browser
http_server.load_url('jsgraph/jsgraph.html')
print('Or copy all files in jsgraph/ to webserver and '
      'load jsgraph/jsgraph.html')
