"""Example of writing JSON format graph data and using the D3 Javascript library to produce an HTML/Javascript drawing.

Adapted from http://graus.nu/blog/force-directed-graphs-playing-around-with-d3-js/
"""
#    Copyright (C) 2011-2012 by 
#    Aric Hagberg <hagberg@lanl.gov>
#    Dan Schult <dschult@colgate.edu>
#    Pieter Swart <swart@lanl.gov>
#    All rights reserved.
#    BSD license.
__author__ = """Aric Hagberg <aric.hagberg@gmail.com>"""
import json
import networkx as nx
from networkx.readwrite import json_graph
import http_server

G = nx.barbell_graph(6,3)
# this d3 example uses the name attribute for the mouse-hover value,
# so add a name to each node
for n in G:
    G.node[n]['name'] = n
# write json formatted data
d = json_graph.node_link_data(G) # node-link format to serialize
# write json 
json.dump(d, open('jsgraph/jsgraph.json','w'))
print('Wrote node-link JSON data to jsgraph/jsgraph.json')
# open URL in running web browser
http_server.load_url('jsgraph/jsgraph.html')
print('Or copy all files in jsgraph/ to webserver and load jsgraph/jsgraph.html')

