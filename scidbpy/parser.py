"""
Python implementation of a simple SciDB lexer/parser
This implementation uses PLY, the Python Lex/Yacc interface.
"""
import warnings
from ply import lex, yacc
from scidb_lexicon import SCIDB_LEXICON_DICT, SCIDB_TYPE_DICT

# Unsupported:
#
# AQL queries:
#   [x] CREATE ARRAY distance <miles:double> [i=0:9,10,0];
#       SELECT * FROM attributes(champions) WHERE nullable = true;
#       LOAD raw FROM '../examples/raw.scidb';
#       SELECT * INTO championsAbridged FROM project(champions,person);


class SciDBLexer(object):
    """This class lexes SciDB queries.  It is primarily geared toward
    AFL queries, but supports some AQL queries as well.
    """
    # List of reserved keywords
    reserved = {'as': 'AS',
                'null': 'NULL',
                'CREATE': 'CREATE',
                'DROP': 'DROP',
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


#----------------------------------------------------------------------
# Classes to build abstract syntax trees from parsed queries
#
# The primary goal here is to recognize when arrays are referenced in
# queries.  The parsing by design has no relation to the actual SciDB
# database, and thus will not check for correct syntax, existence of
# referenced arrays, attributes, and dimensions, etc.
#
# There are several challenges with this:
#
#   - determining the difference between array names, attribute names, and
#     dimension names.  This is largely contextual.  For example, when an
#     aggregate operation like min() is called, we can safely assume that
#     the argument is an attribute.  When an operation like store() is
#     called, we can safely assume that the argument is an array name.
#
#   - recognizing "as" statements which create aliases of arrays, attributes,
#     and dimensions.
#
#   - recognizing when arrays are created and removed.  Creation is done
#     via "CREATE ARRAY" statements in AQL, and "store()" statements in
#     AFL.  Complicating things is that store() can modify existing arrays.
#     Removing arrays is done via "DROP ARRAY" in AQL, and "remote()"
#     statements in AFL.


# bitmasks for defining argument types
SCIDB_ARRAY = 1 << 0
SCIDB_ATTRIBUTE = 1 << 1
SCIDB_DIMENSION = 1 << 2
SCIDB_INTEGER = 1 << 3
SCIDB_FLOAT = 1 << 4
SCIDB_STRING = 1 << 5
SCICB_BOOL = 1 << 6
SCIDB_SCHEMA = 1 << 7
SCIDB_FUNCRESULT = 1 << 8
SCIDB_NUMERIC = (SCIDB_ATTRIBUTE | SCIDB_DIMENSION
                 | SCIDB_INTEGER | SCIDB_FLOAT)
SCIDB_EXPRESSION = SCIDB_NUMERIC | SCIDB_FUNCRESULT


class Node(object):
    lexicon = SCIDB_LEXICON_DICT

    def __init__(self, p):
        self.args = p[1:]
        self.rettype = None
        self.aliased_labels = {}
        self.ambiguous_labels = []
        self.arrays_referenced = []
        self.arrays_created = []
        self.arrays_deleted = []
        self._initialize(p)

    def __repr__(self):
        return ' '.join(map(str, self.args[1:]))

    def _initialize(self, p):
        for pi in p[1:]:
            if isinstance(pi, (list, tuple)):
                piter = pi
            else:
                piter = [pi]
                
            for pi in piter:
                if isinstance(pi, Node):
                    for attr in ['arrays_referenced', 'arrays_created',
                                 'arrays_deleted', 'ambiguous_labels']:
                        getattr(self, attr).extend(getattr(pi, attr))
                    for attr in ['aliased_labels']:
                        getattr(self, attr).update(getattr(pi, attr))


class AQLNode(Node):
    pass


class AQLDropArray(AQLNode):
    def __initialize(self, p):
        self.arrays_deleted = [self.args[2]]
        self.arrays_referenced = [self.args[2]]

    def __repr__(self):
        return "DROP ARRAY {2}".format(*self.args)


class AQLCreateArray(AQLNode):
    def _initialize(self, p):
        self.arrays_created = [self.args[2]]
        self.arrays_referenced = [self.args[2]]

    def __repr__(self):
        return "CREATE ARRAY {2} {3}".format(*self.args)


class AFLNode(Node):
    pass


class Expression(AFLNode):
    def _expr_init(self, item, sliceitem):
        if hasattr(item, 'retvalue'):
            self.retvalue = item.retvalue
        else:
            self.retvalue = sliceitem.type

        if sliceitem.type == 'NAME':
            self.expr_name = sliceitem.value
            self.ambiguous_labels = [sliceitem.value]
        else:
            self.expr_name = None
        

    def _initialize(self, p):
        AFLNode._initialize(self, p)
        self._expr_init(p[1], p.slice[1])

    def __repr__(self):
        return str(self.args[0])


class ArrayVersion(AFLNode):
    def _initialize(self, p):
        self.retvalue = 'ARRAY'
        self.arrays_referenced = [p[1]]

    def __repr__(self):
        return "{0}@{2}".format(*self.args)


class Function(AFLNode):
    @property
    def funcname(self):
        return self.args[0]

    def _initialize(self, p):
        AFLNode._initialize(self, p)
        func_spec = self.lexicon.get(self.funcname, None)

        # TODO:
        # use the specification to check arguments and to disambiguate
        # array names, dimension names, and attribute names.

        if not func_spec:
            warnings.warn("Unrecognized function '{0}'".format(self.funcname))
        else:
            self.rettype = func_spec.rettype

    def __repr__(self):
        if len(self.args) == 3:
            return "{0}()".format(self.args[0])
        else:
            return "{0}({1})".format(self.args[0],
                                     ', '.join(map(str, self.args[2])))


class BinaryOperation(Function):
    @property
    def funcname(self):
        return self.args[1]

    def __repr__(self):
        return "{0} {1} {2}".format(*self.args)


class UnaryOperation(Function):
    @property
    def funcname(self):
        return self.args[0]

    def __repr__(self):
        return "{0}{1}".format(*self.args)


class ExpressionGroup(Expression):
    def _initialize(self, p):
        AFLNode._initialize(self, p)
        self._expr_init(p[2], p.slice[2])

    def __repr__(self):
        return "({1})".format(*self.args)


class AsExpression(AFLNode):
    def _initialize(self, p):
        AFLNode._initialize(self, p)
        if hasattr(p[1], 'retvalue'):
            self.retvalue = p[1].retvalue
        if hasattr(p[1], 'aliased_labels'):
            self.aliased_labels.update(p[1].aliased_labels)
            self.aliased_labels[p[3]] = p[1]

    def __repr__(self):
        return "{0} as {2}".format(*self.args)


class ObjectAttribute(AFLNode):
    def _initialize(self, p):
        AFLNode._initialize(self, p)
        self.arrays_referenced = [self.args[0]]
        self.retvalue = 'ATTRIBUTE'

    def __repr__(self):
        return "{0}.{2}".format(*self.args)


class AttrSpec(AFLNode):
    def __repr__(self):
        return "{0}:{2}".format(*self.args)


class ItemType(AFLNode):
    def __repr__(self):
        return ' '.join(map(str, self.args))


class DimSpec(AFLNode):
    def __repr__(self):
        return "{0}={2}:{4},{6},{8}".format(*self.args)


class ArraySpec(AFLNode):
    def __initialize__(self, p):
        AFLNode.__initialize__(self, p)
        self.retvalue = 'SCHEMA'

    def __repr__(self):
        return "<{0}>[{1}]".format(', '.join(map(str, self.args[1])),
                                   ', '.join(map(str, self.args[4])))


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
        """aqlquery : aqlcreatearray
                    | aqldroparray"""
        p[0] = p[1]

    def p_aqlcreatearray(self, p):
        """aqlcreatearray : CREATE ARRAY NAME arrayspec"""
        p[0] = AQLCreateArray(p)

    def p_aqldroparray(self, p):
        """aqldroparray : DROP ARRAY NAME"""
        p[0] = AQLDropArray(p)

    def p_aflquery(self, p):
        """aflquery : function"""
        p[0] = p[1]

    def p_function(self, p):
        """function : NAME LPAREN RPAREN
                    | NAME LPAREN arguments RPAREN"""
        # Get a list of all function arguments
        p[0] = Function(p)

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
        p[0] = BinaryOperation(p)

    def p_expression_unary_op(self, p):
        """expression : MINUS expression %prec UMINUS"""
        p[0] = UnaryOperation(p)

    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = ExpressionGroup(p)

    def p_expression(self, p):
        """expression : function
                      | arrayspec
                      | arrayref
                      | objattribute
                      | NAME
                      | NUMBER
                      | INTEGER
                      | STRING"""
        if isinstance(p[1], Node):
            p[0] = p[1]
        else:
            p[0] = Expression(p)

    def p_expression_as(self, p):
        """expression : expression AS NAME"""
        p[0] = AsExpression(p)

    def p_arrayref(self, p):
        """arrayref : NAME ATMARK INTEGER"""
        p[0] = ArrayVersion(p)

    def p_objattribute(self, p):
        """objattribute : NAME PERIOD NAME"""
        p[0] = ObjectAttribute(p)

    def p_arrayspec(self, p):
        """arrayspec : LANGLE attrlist RANGLE LBRACKET dimlist RBRACKET"""
        p[0] = ArraySpec(p)

    def p_attrlist(self, p):
        """attrlist : attrspec
                    | attrspec COMMA attrlist"""
        p[0] = [p[1]]
        if len(p) == 4:
            p[0].extend(p[3])

    def p_attrspec(self, p):
        """attrspec : NAME COLON itemtype"""
        p[0] = AttrSpec(p)

    def p_itemtype(self, p):
        """itemtype : NAME
                    | NAME NULL"""
        p[0] = ItemType(p)

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
        p[0] = DimSpec(p)

    def p_error(self, p):
        raise ValueError("Syntax error at '{0}'".format(p.value))

    def parse(self, data):
        self.yacc.parse(data, lexer=self.sdb_lexer.lexer)
        return self

    def query_list(self):
        return self.yacc.symstack[-1].value

    def test_inout(self, data):
        self.parse(data)

        input_queries = filter(lambda x:x,
                               map(str.strip, data.split('\n')))
        output_queries = self.query_list()

        print
        for q1, q2 in zip(input_queries, output_queries):
            print ' ', q1
            print ' ', q2
            print ' ', q2.aliased_labels
            print ' ', q2.ambiguous_labels
            print ' ', q2.arrays_referenced
            print ' ', q2.arrays_created
            print ' ', q2.arrays_deleted
            print


if __name__ == "__main__":
    test_data = """
    CREATE ARRAY A <f0:double> [i0=0:9,1000,0,i1=0:9,1000,0];
    store(build(A,iif(A.i0=A.i1,1,0)), A);
    store(build(A,iif(A.i0=A.i1,2,1)), B);
    multiply(A, B);
    remove(A);
    """

    #SciDBLexer().test(test_data)
    SciDBParser().test_inout(test_data)
    
