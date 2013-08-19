"""
Python implementation of a simple SciDB lexer/parser
This implementation uses PLY, the Python Lex/Yacc interface.
"""
from ply import lex, yacc


class SciDBLexer(object):
    # List of token names
    tokens = ('NAME', 'NUMBER',
              'COMMA', 'SEMICOLON', 'PERIOD',
              'LPAREN', 'RPAREN',  'LANGLE', 'RANGLE', 'LBRACKET', 'RBRACKET',
              'PLUS', 'MINUS', 'TIMES', 'DIVIDE')

    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Regular expression rules for simple tokens
    t_NAME = r'[a-zA-Z_][a-zA-Z_0-9]*'
    t_NUMBER = r'[0-9]+(\.[0-9]*)?'

    # Punctuation
    t_COMMA = r','
    t_PERIOD = r'\.'
    t_SEMICOLON = r';'

    # Brackets and braces
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LANGLE = r'<'
    t_RANGLE = r'>'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'

    # arithmetic operations
    t_PLUS    = r'\+'
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_DIVIDE  = r'/'

    # ignore spaces and tabs
    t_ignore = ' \t'

    # count line numbers
    def t_newline(self, t):
        r'[\n\r]+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        raise ValueError("SciDBLexer: Illegal character "
                         "'{0}'".format(t.value[0]))

    def test(self, data):
        self.lexer.input(data)
        for tok in self.lexer:
            print tok


class SciDBParser(object):
    tokens = SciDBLexer.tokens

    precedence = (('left','PLUS','MINUS'),
                  ('left','TIMES','DIVIDE'),
                  ('right','UMINUS'))

    def __init__(self):
        self.sdb_lexer = SciDBLexer()
        self.yacc = yacc.yacc(module=self)

    def p_querylist(self, t):
        """querylist : statement
                     | statement SEMICOLON
                     | statement SEMICOLON querylist"""
        pass

    def p_statement(self, t):
        """statement : NAME LPAREN RPAREN
                     | NAME LPAREN arguments RPAREN"""
        pass

    def p_arguments(self, t):
        """arguments : expression
                     | expression COMMA arguments"""
        pass

    def p_expression(self, t):
        """expression : LPAREN expression RPAREN
                      | MINUS expression %prec UMINUS
                      | expression PLUS expression
                      | expression MINUS expression
                      | expression TIMES expression
                      | expression DIVIDE expression
                      | statement
                      | NAME
                      | NAME PERIOD NAME
                      | NUMBER"""
        pass

    def p_error(self, t):
        raise ValueError("Syntax error at '{0}'".format(t.value))

    def parse(self, data):
        self.yacc.parse(data, lexer=self.sdb_lexer.lexer)


if __name__ == "__main__":
    test_data = """func1(1.05, 2, -3 * (2 - 4), abcd45);
                   func2(foo(A.val, 2.0));"""
    #SciDBLexer().test(test_data
    SciDBParser().parse(test_data)
