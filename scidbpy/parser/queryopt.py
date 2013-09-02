from parser import SciDBParser


#store(apply(A, sin_f0, sin(A.f0)), tmp)
#store(project(tmp, sin_f0), B)
#remove(tmp)
#    --->
#
#store(project(apply(A, sin_f0, sin(A.f0)), sin_f0), B)



def query_optimize(*queries):
    parsed_queries = sum((SciDBParser().parse(query).query_list()
                          for query in queries), [])

    for query in parsed_queries:
        
        print type(query.args[0]), query.args[0]


if __name__ == '__main__':
    queries = """
    store(apply(A, sin_f0, sin(A.f0)), tmp);
    store(project(tmp, sin_f0), B);
    remove(tmp);
    """
    query_optimize(queries)
