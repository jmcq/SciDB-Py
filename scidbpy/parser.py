"""
Python implementation of a simple SciDB lexer/parser
This implementation uses PLY, the Python Lex/Yacc interface.
"""
from ply import lex, yacc

# Unsupported:
#
#   CREATE ARRAY distance <miles:double> [i=0:9,10,0];  
#   SELECT * FROM attributes(champions) WHERE nullable = true;
#   LOAD raw FROM '../examples/raw.scidb';
#   CREATE ARRAY namesRedimensioned 
#        <b:int64 null, c:int64, avgD:double null> 
#        [surname(string)=5,5,0]
#   SELECT * INTO championsAbridged FROM project(champions,person); 
#
#   <time:double null>
#
#   aggregate(m3x3,min(val) as m)
#   redimension(A,Position,
#               min(val) as minVal, 
#               avg(val) as avgVal, 
#               max(val) as maxVal);
#
#   [i=0:*,5,0]
#
#   iif(i=j,100+i,i*4+j)
#   filter(m4x4,val<100); etc.
#
#   load_library('dense_linear_algebra');  
#   gesvd(product,'S');  
#   list('arrays')
#   save(storage_array,'/tmp/storage_array.txt',-2,'dcsv');
#   show('multiply(A,B)','afl');
#
#   insert (B@1, A)
#
#   boolean: <, <=, <>, =, >, >=


class AFLLexer(object):
    # List of token names
    tokens = ('NAME', 'NUMBER',
              'COMMA', 'PERIOD', 'SEMICOLON', 'COLON',
              'LPAREN', 'RPAREN',  'LANGLE', 'RANGLE', 'LBRACKET', 'RBRACKET',
              'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD', 'EQUAL')

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
    t_EQUAL   = r'\='
    t_PLUS    = r'\+'
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_DIVIDE  = r'/'
    t_MOD     = r'\%'

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


class AFLParser(object):
    tokens = AFLLexer.tokens

    precedence = (('nonassoc', 'EQUAL'),
                  ('left','PLUS','MINUS'),
                  ('left','TIMES','DIVIDE', 'MOD'),
                  ('right','UMINUS'))

    def __init__(self):
        self.sdb_lexer = AFLLexer()
        self.yacc = yacc.yacc(module=self)

    def p_querylist(self, t):
        """querylist : function
                     | function SEMICOLON
                     | function SEMICOLON querylist"""
        

    def p_function(self, t):
        """function : NAME LPAREN RPAREN
                    | NAME LPAREN arguments RPAREN"""
        pass

    def p_arguments(self, t):
        """arguments : expression
                     | expression COMMA arguments"""
        pass

    def p_expression_binary_op(self, t):
        """expression : expression PLUS expression
                      | expression MINUS expression
                      | expression TIMES expression
                      | expression DIVIDE expression
                      | expression MOD expression"""
        pass

    def p_expression_unary_op(self, t):
        """expression : MINUS expression %prec UMINUS"""
        pass

    def p_expression_group(self, t):
        """expression : LPAREN expression RPAREN"""

    def p_expression(self, t):
        """expression : function
                      | NAME
                      | NAME PERIOD NAME
                      | NUMBER
                      | typespec dimspec"""
        pass

    def p_typespec(self, t):
        """typespec : LANGLE typelist RANGLE"""
        pass

    def p_onetype(self, t):
        """onetype : NAME COLON NAME"""
        pass

    def p_typelist(self, t):
        """typelist : onetype
                    | onetype COMMA typelist"""
        pass

    def p_dimspec(self, t):
        """dimspec : LBRACKET dimlist RBRACKET"""
        pass

    def p_onedim(self, t):
        """onedim : NAME EQUAL NUMBER COLON NUMBER COMMA NUMBER COMMA NUMBER
                  | NAME EQUAL NUMBER COLON TIMES COMMA NUMBER COMMA NUMBER"""
        pass

    def p_dimlist(self, t):
        """dimlist : onedim
                   | onedim COMMA dimlist"""
        pass

    def p_error(self, t):
        raise ValueError("Syntax error at '{0}'".format(t.value))

    def parse(self, data):
        self.yacc.parse(data, lexer=self.sdb_lexer.lexer)


if __name__ == "__main__":
    test_data = """func1(1.05, 2, -3 * (2 - 4), abcd45);"""
    #func2(foo(A.val, 2.0), bar());
    #store(build(<subVal:double>[i=0:0,1,0],0),zeros)"""
    #AFLLexer().test(test_data)
    AFLParser().parse(test_data)
