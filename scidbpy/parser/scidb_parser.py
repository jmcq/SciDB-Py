import ply.yacc as yacc
from scidb_lexer import SciDBLexer

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
        """statement : IDENTIFIER LPAREN RPAREN
                     | IDENTIFIER LPAREN arguments RPAREN"""
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
                      | IDENTIFIER
                      | IDENTIFIER PERIOD IDENTIFIER
                      | NUMBER"""
        pass

    def p_error(self, t):
        raise ValueError("Syntax error at '{0}'".format(t.value))

    def parse(self, data):
        self.yacc.parse(data, lexer=self.sdb_lexer.lexer)


if __name__ == "__main__":
    p = SciDBParser()
    data = """func(1.05, 2, 3 * 4, abcd45);
              func(foo(A.val, 2.0));"""
    p.parse(data)
