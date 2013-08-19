from ply import lex

class SciDBLexer(object):
    # List of token names
    tokens = ('IDENTIFIER', 'NUMBER',
              'LPAREN', 'RPAREN', 'COMMA', 'SEMICOLON', 'PERIOD',
              'PLUS', 'MINUS', 'TIMES', 'DIVIDE')

    # Regular expression rules for simple tokens
    t_IDENTIFIER = r'[a-zA-Z_][a-zA-Z_0-9]*'
    t_NUMBER = r'[0-9]+(\.[0-9]*)?'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA = r','
    t_PERIOD = r'\.'
    t_PLUS    = r'\+'
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_DIVIDE  = r'/'
    t_SEMICOLON = r';'

    t_ignore = ' \t'

    # Function to count line numbers
    def t_newline(self, t):
        r'[\n\r]+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        raise ValueError("Illegal character '{0}'".format(t.value[0]))


    def __init__(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def test(self, data):
        self.lexer.input(data)
        for tok in self.lexer:
            print tok

if __name__ == '__main__':
    sdbl = SciDBLexer()
    sdbl.build()

    data = """func(1.05, 2, 3 * 4, abcd45);"""
    sdbl.test(data)
