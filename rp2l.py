#!/usr/bin/env python

try:
    import locale
    locale.setlocale(locale.LC_ALL, '')
except:
    pass

from docutils.parsers import rst
from docutils import nodes
from docutils.core import publish_cmdline, default_description
from docutils.parsers.rst.roles import register_canonical_role
from docutils.writers.latex2e import Writer as Latex2eWriter
from docutils.writers.latex2e import LaTeXTranslator
from docutils.parsers.rst import directives
from var_to_latex import VariableToLatex
from pytexutils import lhs
import sys

def parse_py_line(line):
    if line.find('='):
        l,r = line.split('=')
        return l,r
    else:
        return '',line

# executed py directives

# Define py node:
class py(nodes.Element):
    tagname = '#py'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex

# Define pyno node:
class pyno(nodes.Element):
    tagname = '#pyno'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex

class py_echo_area(nodes.Element):
    tagname= '#py_echo_area'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex


# Register role:
def py_role(role, rawtext, text, lineno, inliner,
                    options={}, content=[]):
    i = rawtext.find('`')
    code = rawtext[i+1:-1]
    try:
        code = code
    except SyntaxError, msg:
        msg = inliner.reporter.error(msg, line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]
    node = py(rawtext, code)
    return [node], []
register_canonical_role('py', py_role)


class py_directive(rst.Directive):
    has_content = True
    # echo_values = ('verbatim','none')
    # format_values = ('%0.3f','%0.9f')
    
    # def format(argument):
    #     return directives.choice(argument, py_directive.format_values)

    # def echo(argument):
    #     return directives.choice(argument, py_directive.echo_values)

    option_spec = {'echo': directives.unchanged,
                   'fmt': directives.unchanged,
                   }


    def run(self):
        echo = self.state.document.settings.py_echo
        fmt = self.state.document.settings.py_fmt
        if not hasattr(sys.modules['__main__'],'py_directive_namespace'):
            setattr(sys.modules['__main__'],'py_directive_namespace', {})
        if self.options.has_key('echo'):
            echo = self.options['echo']
        if self.options.has_key('fmt'):
            fmt = self.options['fmt']

        if echo == 'verbatim':
            echo_code_latex = ""
            for n,l in enumerate(self.content):
                echo_code_latex += l
                if n != len(self.content)-1:
                    echo_code_latex += '\n'
        elif echo == 'none':
            echo_code_latex = ''

        for n,line in enumerate(self.content):
            curlhs,currhs = parse_py_line(line)
            exec line in sys.modules['__main__'].py_directive_namespace
            curvar = eval(currhs,sys.modules['__main__'].py_directive_namespace)
            curlatex = VariableToLatex(curvar,curlhs,fmt=fmt)[0][0]
            if n == 0:
                latex=curlatex
            else:
                latex+='\\\\'
                latex+=curlatex
            if n==len(self.content)-1 and len(self.content)>1:
                latex+='\\\\'

        py_node = py(self.block_text,latex)                
        if echo != 'none':
            echo_code = py_echo_area(self.block_text,echo_code_latex)
            return [echo_code,py_node]
        else:
            return [py_node]

class pyno_directive(rst.Directive):
    has_content = True

    def run(self):
        if not hasattr(sys.modules['__main__'],'py_directive_namespace'):
            setattr(sys.modules['__main__'],'py_directive_namespace', {})
        latex = ''
        for n,line in enumerate(self.content):
            exec line in sys.modules['__main__'].py_directive_namespace
        py_node = pyno(self.block_text,latex)
        return [py_node]


def visit_py(self,node):
    inline = isinstance(node.parent, nodes.TextElement)
    attrs = node.attributes
    if inline:
        self.body.append('$%s$' % node.latex)
    else:
        self.body.extend(['\\begin{equation}\\begin{split}\n',
                          node.latex,
                          '\n\\end{split}\\end{equation}\n'])
def depart_py(self,node):
    pass

def visit_py_echo_area(self,node):
    self.body.extend(['\n\n\\begin{lstlisting}\n',node.latex,'\n\\end{lstlisting}\n'])

def depart_py_echo_area(self,node):
    pass

def visit_pyno(self,node):
    pass

def depart_pyno(self,node):
    pass



# Latex Math Stuff

# Define LaTeX math node:
class latex_math(nodes.Element):
    tagname = '#latex-math'
    def __init__(self, rawsource, latex):
        nodes.Element.__init__(self, rawsource)
        self.latex = latex

# Register role:
def latex_math_role(role, rawtext, text, lineno, inliner,
                    options={'label':None}, content=[]):
    i = rawtext.find('`')
    latex = rawtext[i+1:-1]
    node = latex_math(rawtext, latex)
    return [node], []
register_canonical_role('latex-math', latex_math_role)

class latex_math_directive(rst.Directive):
    has_content = True
    def run(self): 
        latex = ''.join(self.content)
        node = latex_math(self.block_text, latex)
        return [node]
# Add visit/depart methods to HTML-Translator:
def visit_latex_math(self, node):
    inline = isinstance(node.parent, nodes.TextElement)
    if inline:
        self.body.append('$%s$' % node.latex)
    else:
        self.body.extend(['\\begin{equation}\\begin{split}',
                          node.latex,
                          '\\end{split}\\end{equation}'])
        
def depart_latex_math(self, node):
    pass
    

# Register everything and add to Translator

directives.register_directive('latex-math', latex_math_directive)
directives.register_directive('py', py_directive)
directives.register_directive('pyno', pyno_directive)

LaTeXTranslator.visit_latex_math = visit_latex_math
LaTeXTranslator.depart_latex_math = depart_latex_math
LaTeXTranslator.visit_py = visit_py
LaTeXTranslator.depart_py = depart_py
LaTeXTranslator.visit_pyno = visit_pyno
LaTeXTranslator.depart_pyno = depart_pyno
LaTeXTranslator.visit_py_echo_area = visit_py_echo_area
LaTeXTranslator.depart_py_echo_area = depart_py_echo_area


# Publish the commandline
Latex2eWriter.settings_spec = (Latex2eWriter.settings_spec[0],\
                               Latex2eWriter.settings_spec[1],\
                               Latex2eWriter.settings_spec[2] + \
                               (('Specify default echo. Default is "none".',\
                                 ['--py-echo'],\
                                 {'default':'none'}),\
                                ('Specify format of floats. Default is "%0.4f".',\
                                 ['--py-fmt'],\
                                 {'default':'%0.4f'})))

description = ('Generates LaTeX documents from standalone reStructuredText '
               'sources.  ' + default_description)

publish_cmdline(writer_name='latex', description=description)







    
