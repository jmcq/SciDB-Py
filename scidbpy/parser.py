"""
Python implementation of a simple SciDB lexer/parser
This implementation uses PLY, the Python Lex/Yacc interface.
"""
from ply import lex, yacc

# Unsupported:
#
# AQL queries:
#   CREATE ARRAY distance <miles:double> [i=0:9,10,0];  
#   SELECT * FROM attributes(champions) WHERE nullable = true;
#   LOAD raw FROM '../examples/raw.scidb';
#   CREATE ARRAY namesRedimensioned 
#        <b:int64 null, c:int64, avgD:double null> 
#        [surname(string)=5,5,0]
#   SELECT * INTO championsAbridged FROM project(champions,person); 
#
# Keywords with spaces:
#   <time:double null>
#
# As-statements
#   aggregate(m3x3,min(val) as m)
#   redimension(A,Position,
#               min(val) as minVal, 
#               avg(val) as avgVal, 
#               max(val) as maxVal);
#
# Strings
#   load_library('dense_linear_algebra');  
#   gesvd(product,'S');  
#   list('arrays')
#   save(storage_array,'/tmp/storage_array.txt',-2,'dcsv');
#   show('multiply(A,B)','afl');
#
# Previous array versions
#   insert (B@1, A)


class AFLLexer(object):
    # List of token names
    tokens = ('NAME', 'NUMBER',
              'COMMA', 'PERIOD', 'SEMICOLON', 'COLON',
              'LPAREN', 'RPAREN',  'LANGLE', 'RANGLE', 'LBRACKET', 'RBRACKET',
              'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
              'EQUAL', 'NEQUAL', 'LTEQUAL', 'GTEQUAL',
              )

    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Regular expression rules for simple tokens
    t_NAME = r'[a-zA-Z_][a-zA-Z_0-9]*'
    t_NUMBER = r'[0-9]+(\.[0-9]*)?'

    # Punctuation
    t_COMMA = r','
    t_PERIOD = r'\.'
    t_SEMICOLON = r'\;'
    t_COLON = r'\:'

    # Brackets and braces
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LANGLE = r'\<'
    t_RANGLE = r'\>'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'

    # arithmetic operations
    t_PLUS    = r'\+'
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_DIVIDE  = r'/'
    t_MOD     = r'\%'

    # binary operations
    t_EQUAL = r'\='
    t_NEQUAL = r'\<\>'
    t_LTEQUAL = r'\<\='
    t_GTEQUAL = r'\>\='

    # ignore spaces and tabs
    t_ignore = ' \t'

    # count line numbers
    def t_newline(self, t):
        r'[\n\r]+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        raise ValueError("AFLLexer: Illegal character "
                         "'{0}'".format(t.value[0]))

    def test(self, data):
        self.lexer.input(data)
        for tok in self.lexer:
            print tok


class Node(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __repr__(self):
        return "{0}({1})".format(self.args[0],
                                 ', '.join(map(str, self.args[1:])))


class Function(Node):
    pass


class BinaryOperation(Node):
    def __repr__(self):
        return "{0} {1} {2}".format(self.args[1], self.args[0], self.args[2])


class UnaryOperation(Node):
    def __repr__(self):
        return "{0}{1}".format(*self.args)


class ExpressionGroup(Node):
    def __repr__(self):
        return "({0})".format(*self.args)


class ObjectAttribute(Node):
    def __repr__(self):
        return "{0}.{1}".format(*self.args)


class AttrSpec(Node):
    def __repr__(self):
        return "{0}:{1}".format(*self.args)


class DimSpec(Node):
    def __repr__(self):
        return "{0}={1}:{2},{3},{4}".format(*self.args)


class ArraySpec(Node):
    def __repr__(self):
        return "<{0}>[{1}]".format(','.join(map(str, self.args[0])),
                                   ','.join(map(str, self.args[1])))


class AFLParser(object):
    tokens = AFLLexer.tokens

    precedence = (('nonassoc', 'EQUAL', 'LANGLE', 'RANGLE',
                   'NEQUAL', 'LTEQUAL', 'GTEQUAL'),
                  ('left','PLUS','MINUS'),
                  ('left','TIMES','DIVIDE', 'MOD'),
                  ('right','UMINUS'))

    def __init__(self):
        self.sdb_lexer = AFLLexer()
        self.yacc = yacc.yacc(module=self)

    def p_querylist(self, p):
        """querylist : function
                     | function SEMICOLON
                     | function SEMICOLON querylist"""
        # Put all queries in a single list
        p[0] = [p[1]]
        if len(p) == 4:
            p[0].extend(p[3])

    def p_function(self, p):
        """function : NAME LPAREN RPAREN
                    | NAME LPAREN arguments RPAREN"""
        # Get a list of all function arguments
        p[0] = Function(p[1])
        if len(p) == 5:
            p[0].args += tuple(p[3])

    def p_arguments(self, p):
        """arguments : expression
                     | expression COMMA arguments"""
        # Put all arguments in a flat list
        p[0] = [p[1]]
        if len(p) == 4:
            p[0].extend(p[3])

    def p_expression_binary_op(self, p):
        """expression : expression PLUS expression
                      | expression MINUS expression
                      | expression TIMES expression
                      | expression DIVIDE expression
                      | expression MOD expression
                      | expression EQUAL expression
                      | expression LANGLE expression
                      | expression RANGLE expression
                      | expression NEQUAL expression
                      | expression LTEQUAL expression
                      | expression GTEQUAL expression"""
        p[0] = BinaryOperation(p[2], p[1], p[3])

    def p_expression_unary_op(self, p):
        """expression : MINUS expression %prec UMINUS"""
        p[0] = UnaryOperation(p[1], p[2])

    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = ExpressionGroup(p[2])

    def p_expression(self, p):
        """expression : function
                      | arrayspec
                      | objattribute
                      | NAME
                      | NUMBER"""
        p[0] = p[1]

    def p_objattribute(self, p):
        """objattribute : NAME PERIOD NAME"""
        p[0] = ObjectAttribute(p[1], p[3])

    def p_arrayspec(self, p):
        """arrayspec : LANGLE attrlist RANGLE LBRACKET dimlist RBRACKET"""
        p[0] = ArraySpec(p[2], p[5])

    def p_attrlist(self, p):
        """attrlist : attrspec
                    | attrspec COMMA attrlist"""
        p[0] = [p[1]]
        if len(p) == 4:
            p[0].extend(p[3])

    def p_attrspec(self, p):
        """attrspec : NAME COLON NAME"""
        p[0] = AttrSpec(p[1], p[3])

    def p_dimlist(self, p):
        """dimlist : dimspec
                   | dimspec COMMA dimlist"""
        p[0] = [p[1]]
        if len(p) == 4:
            p[0].extend(p[3])

    def p_dimspec(self, p):
        """dimspec : NAME EQUAL NUMBER COLON NUMBER COMMA NUMBER COMMA NUMBER
                   | NAME EQUAL NUMBER COLON TIMES COMMA NUMBER COMMA NUMBER"""
        p[0] = DimSpec(p[1], p[3], p[5], p[7], p[9])

    def p_error(self, p):
        raise ValueError("Syntax error at '{0}'".format(t.value))

    def parse(self, data):
        self.yacc.parse(data, lexer=self.sdb_lexer.lexer)

    def query_list(self):
        return self.yacc.symstack[-1].value


if __name__ == "__main__":
    test_data = """func1(<i0:int>[i=0:9,1000,0], 2, -3 * (2 - 4),
                         iif(i=j,100+i,i*4+j),
                         filter(A, val<=2));
      func2()"""
    #AFLLexer().test(test_data)

    parser = AFLParser()
    parser.parse(test_data)
    
    for query in parser.query_list():
        print query
