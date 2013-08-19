import ply.yacc as yacc
from scidb_lexer import SciDBLexer

tokens = SciDBLexer.tokens

precedence = (('left','PLUS','MINUS'),
              ('left','TIMES','DIVIDE'),
              ('right','UMINUS'))

def p_querylist(t):
    """querylist : statement
                 | statement SEMICOLON
                 | statement SEMICOLON querylist"""
    pass


def p_statement(t):
    """statement : IDENTIFIER LPAREN arguments RPAREN"""
    pass


def p_arguments(t):
    """arguments : expression
                 | expression COMMA arguments"""
    pass


def p_expression(t):
    """expression : LPAREN expression RPAREN
                  | MINUS expression %prec UMINUS
                  | expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | statement
                  | IDENTIFIER
                  | NUMBER"""
    pass


def p_error(t):
    raise ValueError("Syntax error at '{0}'".format(t.value))


if __name__ == "__main__":
    import ply.yacc as yacc
    yacc.yacc()

    lexer = SciDBLexer().build()
    data = """func(1.05, 2, 3 * 4, abcd45);
              func(foo(2.0));"""
    yacc.parse(data, lexer=lexer)
