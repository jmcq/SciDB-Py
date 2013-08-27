from scidbpy.parser import SciDBParser, SciDBLexer

test_data = """
CREATE ARRAY A <f0:double> [i0=0:9,1000,0,i1=0:9,1000,0];
store(build(A,iif(A.i0=A.i1,1,0)), A);
store(build(A,iif(A.i0=A.i1,2,1)), B);
multiply(A, B);
remove(A);
DROP ARRAY B;
"""

#SciDBLexer().test(test_data)
SciDBParser().print_input_output(test_data)
