# List of token names
tokens = ('IDENTIFIER', 'NUMBER',
          'LPAREN', 'RPAREN', 'COMMA', 'SEMICOLON',
          'PLUS', 'MINUS', 'TIMES', 'DIVIDE')

# Regular expression rules for simple tokens
t_IDENTIFIER = r'[a-zA-Z_][a-zA-Z_0-9]*'
t_NUMBER = r'[0-9]+(\.[0-9]*)?'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COMMA = r','
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_SEMICOLON = r';'

t_ignore = ' \t'

# Function to count line numbers
def t_newline(t):
    r'[\n\r]+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    raise ValueError("Illegal character '{0}'".format(t.value[0]))


from ply import lex
lexer = lex.lex()

if __name__ == '__main__':
    data = """func(1.05, 2, 3 * 4, abcd45);"""

    lexer.input(data)

    for tok in lexer:
        print tok
