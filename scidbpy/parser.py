"""
Python implementation of a simple SciDB lexer/parser
This implementation uses PLY, the Python Lex/Yacc interface.
"""
from ply import lex, yacc

# Unsupported:
#
# AQL queries:
#   [x] CREATE ARRAY distance <miles:double> [i=0:9,10,0];
#       SELECT * FROM attributes(champions) WHERE nullable = true;
#       LOAD raw FROM '../examples/raw.scidb';
#       SELECT * INTO championsAbridged FROM project(champions,person);


class SciDBLexer(object):
    # List of reserved keywords
    reserved = {'as': 'AS',
                'null': 'NULL',
                'CREATE': 'CREATE',
                'ARRAY': 'ARRAY'}

    # List of token names
    tokens = ['NAME', 'INTEGER', 'NUMBER', 'STRING',
              'COMMA', 'PERIOD', 'SEMICOLON', 'COLON', 'ATMARK',
              'LPAREN', 'RPAREN',  'LANGLE', 'RANGLE', 'LBRACKET', 'RBRACKET',
              'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
              'EQUAL', 'NEQUAL', 'LTEQUAL', 'GTEQUAL',
              ] + list(reserved.values())

    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Regular expression rules for simple tokens & strings
    def t_NAME(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = self.reserved.get(t.value, 'NAME')
        if t.type == 'NAME':
            t.type = self.reserved.get(t.value.upper(), 'NAME')
        return t

    t_NUMBER = r'[0-9]+(\.[0-9]*)'
    t_INTEGER = r'[0-9]+'
    t_STRING = r"""("[^"]*")|('[^']*')"""

    # Punctuation
    t_COMMA = r','
    t_PERIOD = r'\.'
    t_SEMICOLON = r'\;'
    t_COLON = r'\:'
    t_ATMARK = r'@'

    # Brackets and braces
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LANGLE = r'\<'
    t_RANGLE = r'\>'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'

    # arithmetic operations
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_MOD = r'\%'

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
        print t.value
        raise ValueError("SciDBLexer: Illegal character "
                         "'{0}'".format(t.value[0]))

    def test(self, data):
        self.lexer.input(data)
        for tok in self.lexer:
            print tok


class Node(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class AQLNode(Node):
    def __repr__(self):
        return ' '.join(map(str, self.args))


class AQLCreateArray(AQLNode):
    def __repr__(self):
        return "CREATE ARRAY {0} {1}".format(*self.args)


class AFLNode(Node):
    def __repr__(self):
        return "{0}({1})".format(self.args[0],
                                 ', '.join(map(str, self.args[1:])))


class Expression(AFLNode):
    def __repr__(self):
        if len(self.args) != 1:
            raise ValueError("Multiple arguments in expression")
        return '{0}'.format(self.args[0])


class ArrayVersion(AFLNode):
    def __repr__(self):
        return "{0}@{1}".format(self.args[0], self.args[1])


class Function(AFLNode):
    pass


class BinaryOperation(AFLNode):
    def __repr__(self):
        return "{0} {1} {2}".format(self.args[1], self.args[0], self.args[2])


class UnaryOperation(AFLNode):
    def __repr__(self):
        return "{0}{1}".format(*self.args)


class ExpressionGroup(AFLNode):
    def __repr__(self):
        return "({0})".format(*self.args)


class AsExpression(AFLNode):
    def __repr__(self):
        return "{0} as {1}".format(*self.args)


class ObjectAttribute(AFLNode):
    def __repr__(self):
        return "{0}.{1}".format(*self.args)


class AttrSpec(AFLNode):
    def __repr__(self):
        return "{0}:{1}".format(*self.args)


class DimSpec(AFLNode):
    def __repr__(self):
        return "{0}={1}:{2},{3},{4}".format(*self.args)


class ArraySpec(AFLNode):
    def __repr__(self):
        return "<{0}>[{1}]".format(', '.join(map(str, self.args[0])),
                                   ', '.join(map(str, self.args[1])))


class SciDBParser(object):
    tokens = SciDBLexer.tokens

    precedence = (('nonassoc', 'EQUAL', 'LANGLE', 'RANGLE',
                   'NEQUAL', 'LTEQUAL', 'GTEQUAL'),
                  ('left', 'PLUS', 'MINUS'),
                  ('left', 'TIMES', 'DIVIDE', 'MOD'),
                  ('right', 'UMINUS'))

    def __init__(self):
        self.sdb_lexer = SciDBLexer()
        self.yacc = yacc.yacc(module=self)

    def p_querylist(self, p):
        """querylist : aflquery
                     | aflquery SEMICOLON
                     | aflquery SEMICOLON querylist
                     | aqlquery
                     | aqlquery SEMICOLON
                     | aqlquery SEMICOLON querylist"""
        # Put all queries in a single list
        p[0] = [p[1]]
        if len(p) == 4:
            p[0].extend(p[3])

    def p_aqlquery(self, p):
        """aqlquery : aqlcreatearray"""
        p[0] = p[1]

    def p_aqlcreatearray(self, p):
        """aqlcreatearray : CREATE ARRAY NAME arrayspec"""
        p[0] = AQLCreateArray(*p[3:])

    def p_aflquery(self, p):
        """aflquery : function"""
        p[0] = p[1]

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
                      | arrayref
                      | objattribute
                      | NAME
                      | NUMBER
                      | INTEGER
                      | STRING"""
        p[0] = Expression(p[1])

    def p_expression_as(self, p):
        """expression : expression AS NAME"""
        p[0] = AsExpression(p[1], p[3])

    def p_arrayref(self, p):
        """arrayref : NAME ATMARK INTEGER"""
        p[0] = ArrayVersion(p[1], p[3])

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
        """attrspec : NAME COLON NAME
                    | NAME COLON NAME NULL"""
        if len(p) == 4:
            p[0] = AttrSpec(p[1], p[3])
        else:
            p[0] = AttrSpec(p[1], "{0} {1}".format(p[3], p[4]))

    def p_dimlist(self, p):
        """dimlist : dimspec
                   | dimspec COMMA dimlist"""
        p[0] = [p[1]]
        if len(p) == 4:
            p[0].extend(p[3])

    def p_dimspec(self, p):
        """
        dimspec : NAME EQUAL INTEGER COLON INTEGER COMMA INTEGER COMMA INTEGER
                | NAME EQUAL INTEGER COLON TIMES COMMA INTEGER COMMA INTEGER
        """
        p[0] = DimSpec(p[1], p[3], p[5], p[7], p[9])

    def p_error(self, p):
        raise ValueError("Syntax error at '{0}'".format(p.value))

    def parse(self, data):
        self.yacc.parse(data, lexer=self.sdb_lexer.lexer)

    def query_list(self):
        return self.yacc.symstack[-1].value


if __name__ == "__main__":
    test_data = """func1(<i0:int, f0:float null>[i=0:9,1000,0], -3 * (2 - 4));
       func2(A@1 as Q, iif(i=0,i,Q.j), filter(Q, Q.val<=2));
       show("multiply(A, B)",'afl');
       CREATE ARRAY distance <miles:double> [i=0:9,10,0];"""
    #SciDBLexer().test(test_data)
    #exit()

    parser = SciDBParser()
    parser.parse(test_data)
    
    input_queries = map(str.strip, test_data.split('\n'))
    output_queries = parser.query_list()

    for q1, q2 in zip(input_queries, output_queries):
        print ' ', q1
        print ' ', q2
        print
