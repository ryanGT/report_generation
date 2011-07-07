import rst_math_report

import sympy
from sympy.printing.latex import LatexPrinter as SympyLatexPrinter

from var_to_latex import ArrayToLaTex

import re
p1 = re.compile(r'\\begin{equation\*}(.*)\\end{equation\*}')
p2 = re.compile(r'\$(.*)\$')


def clean_sympy_latex(latex_in):
    latex_out = p1.sub('\\1',latex_in)
    latex_out = p2.sub('\\1',latex_out)
    return latex_out


class LatexPrinter(SympyLatexPrinter):
    def _print_ndarray(self, expr):
        out_str = ArrayToLaTex(expr,'')[0]
        if type(out_str) == list:
            out_str = '\n'.join(out_str)
        return out_str 


settings = {'mat_str':'bmatrix','mat_delim':None, \
            'wrap':'none','inline':False}                        

def expr_to_tex(expr):
    expr_tex = LatexPrinter(settings).doprint(expr)
    expr_tex = clean_sympy_latex(expr_tex)
    return expr_tex
    

class sympy_report(rst_math_report.report):
    def append_sympy_eqn(self, lhs, rhs, label=None):
        lhs_tex = expr_to_tex(lhs)
        rhs_tex = expr_to_tex(rhs)
        self.list.append('.. math::')
        self.list.append('')
        lineout = '   %s = %s' % (lhs_tex, rhs_tex)
        if label is not None:
            lineout += ' \\label{%s}' % label
        self.list.append(lineout)
        self.list.append('')
        

        
