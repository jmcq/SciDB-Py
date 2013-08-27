from scidbpy.parser import SciDBParser, QueryTree
import matplotlib.pyplot as plt
import networkx as nx

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

G = QT.as_networkx()

nx.draw_graphviz(G)
plt.show()
