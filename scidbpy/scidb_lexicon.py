import re
from ply import lex, yacc


SCIDB_LEXICON = """
DEF numeric abs(numeric)
DEF numeric ceil(numeric)
DEF numeric floor(numeric)
DEF numeric sqrt(numeric)
DEF numeric pow(numeric, numeric)
DEF numeric iif(bool, numeric, numeric)
DEF bool is_nan(numeric)
DEF bool is_null(numeric)
DEF bool not(numeric)
DEF numeric acos(numeric)
DEF numeric asin(numeric)
DEF numeric atan(numeric)
DEF numeric cos(numeric)
DEF numeric sin(numeric)
DEF numeric tan(numeric)
DEF numeric exp(numeric)
DEF numeric log(numeric)
DEF numeric log10(numeric)
DEF numeric approxdc(numeric)
DEF numeric avg(numeric)
DEF numeric count(numeric)
DEF numeric max(numeric)
DEF numeric min(numeric)
DEF numeric stdev(numeric)
DEF numeric sum(numeric)
DEF numeric var(numeric)

UNOP numeric -(numeric)
BINOP numeric +(numeric, numeric)
BINOP numeric -(numeric, numeric)
BINOP numeric *(numeric, numeric)
BINOP numeric /(numeric, numeric)
BINOP numeric %(numeric, numeric)
BINOP bool <(numeric, numeric)
BINOP bool <=(numeric, numeric)
BINOP bool <>(numeric, numeric)
BINOP bool >=(numeric, numeric)
BINOP bool >(numeric, numeric)
BINOP bool =(numeric, numeric)

DEF void store(array, array)
DEF void build(array|schema, numeric)
DEF void apply(array, [attr, numeric]+)
DEF void project(array, [attr]+)
"""


SCIDB_VOID = 1 << 0
SCIDB_BOOL = 1 << 1
SCIDB_NUMERIC = 1 << 2
SCIDB_ARRAY = 1 << 3
SCIDB_SCHEMA = 1 << 4
SCIDB_ATTR = 1 << 5
SCIDB_DIM = 1 << 6


class FunctionObj(object):
    objtype = 'DEF'
    def __init__(self, rettype, name, args, optargs, optrepeats):
        self.rettype = rettype
        self.name = name
        self.args = args
        self.optargs = optargs
        self.optrepeats = optrepeats

    def __repr__(self):
        args = ', '.join('|'.join(arg)
                         for arg in self.args)
        optargs = '[{0}]'.format(', '.join('|'.join(arg)
                                           for arg in self.optargs))
        if optargs.strip(' []'):
            args = '{0}, {1}{2}'.format(args, optargs, self.optrepeats[0])

        return "{0} {1} {2}({3})".format(self.objtype,
                                         self.rettype,
                                         self.name,
                                         args)


class BinOp(FunctionObj):
    objtype = 'BINOP'


class UnOp(FunctionObj):
    objtype = 'UNOP'


Obj_dict = dict([(c.objtype, c) for c in (FunctionObj, BinOp, UnOp)])


class SciDBLexiconParser(object):
    # List of reserved keywords
    reserved = {'DEF': 'DECLTYPE',
                'BINOP': 'DECLTYPE',
                'UNOP': 'DECLTYPE',
                'void': 'TYPE',
                'bool': 'TYPE',
                'numeric': 'TYPE',
                'attr': 'TYPE',
                'dim': 'TYPE',
                'array': 'TYPE',
                'schema': 'TYPE'}

    tokens = ['NAME', 'COMMA', 'OR',
              'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET',
              'LT', 'GT', 'LTE', 'GTE', 'NEQ', 'EQ',
              'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
              'QMARK'] + list(set(reserved.values()))

    def __init__(self):
        self.lexer = lex.lex(module=self)
        self.yacc = yacc.yacc(module=self)

    def t_NAME(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = self.reserved.get(t.value, 'NAME')
        return t

    t_COMMA = ','
    t_OR = '\|'

    t_LPAREN = '\('
    t_RPAREN = r'\)'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'

    t_LT = r'<'
    t_GT = r'>'
    t_LTE = r'\<\='
    t_GTE = r'\>\='
    t_NEQ = r'\<\>'
    t_EQ = r'\='

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_MOD = r'\%'

    # ignore spaces and tabs
    t_ignore = ' \t'

    # count line numbers
    def t_newline(self, t):
        r'[\n\r]+'
        t.lexer.lineno += len(t.value)

    def t_error(self, t):
        raise ValueError("SciDBLexParser: Illegal character "
                         "'{0}'".format(t.value[0]))

    def lex(self, data):
        self.lexer.input(data)
        for tok in self.lexer:
            print tok

    # Parser tools

    def p_deflist(self, p):
        """deflist : def
                   | def deflist"""
        #p[0] = {p[1].name: p[1]}
        #if len(p) == 3 and p[2] is not None:
        #    p[0].update(p[2])
        p[0] = [p[1]]
        if len(p) == 3 and p[2] is not None:
            p[0].extend(p[2])

    def p_def(self, p):
        """def : DECLTYPE TYPE funcname LPAREN args RPAREN"""
        p[0] = Obj_dict[p[1]](p[2], p[3],
                              p[5]['args'],
                              p[5]['optargs'],
                              p[5]['optrepeats']) 

    def p_funcname(self, p):
        """funcname : NAME
                    | PLUS
                    | MINUS
                    | TIMES
                    | DIVIDE
                    | MOD
                    | LT
                    | GT
                    | LTE
                    | GTE
                    | NEQ
                    | EQ"""
        p[0] = p[1]

    def p_args(self, p):
        """args :
                | arg
                | optargs
                | arg COMMA args"""
        p[0] = {'args': [],
                'optargs': [],
                'optrepeats': []}
        if len(p) >= 2:
            if isinstance(p[1], dict):
                for key in ('args', 'optargs', 'optrepeats'):
                    p[0][key].extend(p[1].get(key, []))
            else:
                p[0]['args'].extend(p[1])
        if len(p) == 4:
            for key in ('args', 'optargs', 'optrepeats'):
                p[0][key].extend(p[3].get(key, []))

    def p_optargs(self, p):
        """optargs : LBRACKET args RBRACKET
                   | LBRACKET args RBRACKET PLUS
                   | LBRACKET args RBRACKET TIMES
                   | LBRACKET args RBRACKET QMARK"""
        if p[2].get('optargs'):
            raise ValueError("nested optional arguments not supported")
        p[0] = {'optargs': p[2]['args'],
                'optrepeats': ['']}
        if len(p) == 5:
            p[0]['optrepeats'] = [p[4]]

    def p_arg(self, p):
        """arg : TYPE
               | TYPE OR arg"""
        p[0] = {'args':[[p[1]]]}
        if len(p) > 2:
            p[0]['args'][0].extend(p[3]['args'][0])

    def p_error(self, p):
        raise ValueError("Syntax error at '{0}'".format(p.value))

    def parse(self, data):
       self.yacc.parse(data, lexer=self.lexer)

    def deflist(self):
        return self.yacc.symstack[-1].value

    def defdict(self):
        return dict([(d.name, d) for d in self.deflist()])



parser = SciDBLexiconParser()
parser.parse(SCIDB_LEXICON)
SCIDB_LEXICON_DICT = parser.defdict()


def test_parser():
    parser = SciDBLexiconParser()
    parser.parse(SCIDB_LEXICON)

    input_list = filter(lambda x:x,
                        map(str.strip, SCIDB_LEXICON.split('\n')))

    print "  Checking for mismatches:"
    count = 0
    for i, o in zip(input_list, parser.deflist()):
        if str(i) != str(o):
            count += 1
            print "   MISMATCH:"
            print "   ", i
            print "   ", o
    print "  Finished: found {0} mismatches".format(count)

if __name__ == '__main__':
    test_parser()

    obj = SCIDB_LEXICON_DICT['foo']
    print
    print obj
    for k in obj.__dict__:
        print '  ', k, obj.__dict__[k]
