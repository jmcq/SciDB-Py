import re
import collections

Token = collections.namedtuple('Token', ['type', 'value'])


# TODO: create classes for functions, expressions, 'as', etc.
#       recursively reconstruct query strings


class SciDBQueryParser(object):
    """
    Implementation of a Recursive Descent Parser for SciDB Queries
    """
    master_pat = re.compile('|'.join([r'(?P<STRING>[a-zA-Z\_]\w*)',
                                      r'(?P<DOT>\.)',
                                      r'(?P<NUM>\d+)',
                                      r'(?P<PLUSMINUS>[\+\-])',
                                      r'(?P<TIMESDIV>[\*/])',
                                      r'(?P<COMMA>,)',
                                      r'(?P<LPAREN>\()',
                                      r'(?P<RPAREN>\))',
                                      r'(?P<WS>\s+)']))

    @classmethod
    def generate_tokens(cls, text):
        scanner = cls.master_pat.scanner(text)
        for m in iter(scanner.match, None):
            tok = Token(m.lastgroup, m.group())
            if tok.type != 'WS':
                yield tok

    def parse(self, text):
        self.tokens = self.generate_tokens(text)
        self.tok = None  # Last symbol consumed
        self.nexttok = None  # Next symbol tokenized
        self._advance()  # Look at the first token
        return self.topfunc()

    def _advance(self):
        """Advance one token ahead"""
        self.tok, self.nexttok = self.nexttok, next(self.tokens, None)

    def _accept(self, toktype):
        """Test and consume the next token if it matches toktype"""
        if self.nexttok and self.nexttok.type == toktype:
            self._advance()
            return True
        else:
            return False

    def _expect(self, toktype):
        """Consume the next token if it matches toktype or raise SyntaxError"""
        if not self._accept(toktype):
            raise SyntaxError("Expected %s" % toktype)

    def topfunc(self):
        """
        topfunc ::= STRING(expr, expr, ... expr)
        """
        result = self.funcval()
        if not isinstance(result, tuple):
            raise SyntaxError("Expected top level to be a function")
        if self.nexttok is not None:
            raise SyntaxError("Extra something after function")
        return result

    def expr(self):
        """
        expr ::= expr + term
             |   expr - term
             |   term
        """
        left = self.term()
        if self._accept('PLUSMINUS'):
            op = self.tok.value
            return op, [left, self.expr()]
        else:
            return left

    def term(self):
        """
        term ::= term * factor
             |   term / factor
             |   factor
        """
        left = self.factor()
        if self._accept('TIMESDIV'):
            op = self.tok.value
            return op, [left, self.term()]
        else:
            return left

    def factor(self):
        """
        factor ::= ( expr )
               |   funcval_as
        """
        if self._accept('LPAREN'):
            result = self.expr()
            self._expect('RPAREN')
        else:
            result = self.funcval_as()
        return result

    def funcval_as(self):
        """
        funcval_as ::= funcval as STRING
                   |   funcval
        """
        f = self.funcval()
        if self._accept('STRING'):
            if self.tok.value == 'as':
                self._expect('STRING')
                return ('as', [f, self.tok.value])
            else:
                raise SyntaxError("Expected 'as' keyword after function")
        return f

    def funcval(self):
        """
        func ::= STRING(expr, expr, ... expr)
             |   STRING.STRING
             |   STRING
             |   NUM
        """
        if self._accept('STRING'):
            name = self.tok.value
            if self._accept('LPAREN'):
                args = []
                while True:
                    args.append(self.expr())
                    if not self._accept('COMMA'):
                        break
                self._expect('RPAREN')
                return (name, args)
            elif self._accept('DOT'):
                self._expect('STRING')
                return 'attr', [name, self.tok.value]
            else:
                return name
        else:
            self._expect('NUM')
            return self.tok.value


if __name__ == '__main__':
    Q = SciDBQueryParser()
    print Q.parse('foo(bar(1) as X, 2 * (A + B))')
