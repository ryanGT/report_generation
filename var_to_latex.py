import numpy
from scipy import isscalar, shape, imag, real, array, angle
import sympy

from IPython.Debugger import Pdb
import pdb
s = sympy.var('s')

sympy_profile = {'mainvar' : s, \
                 'mat_str' : 'bmatrix', \
                 'mat_delim' : None, \
                 'inline' : None, \
                 'descending' : True,
                 }
                 

def isNum(item):
    """Check to see if an item is of some numeric data type."""
    numclasses = [float, int, complex]
    for curclass in numclasses:
        if isinstance(item, curclass):
            return True
    return False


def AbsEpsilonCheck(val, eps=1e-12):
    if not isNum(val):
        return val
    elif abs(val) < eps:
        return 0
    else:
        return val


def ComplexNumToStr(val, eps=1e-12, fmt='%0.4g', polar=False):
    #print('In ComplexNumToStr, val='+str(val))
    if hasattr(val,'ToLatex'):
        return val.ToLatex(eps=eps, fmt=fmt)
    val = AbsEpsilonCheck(val)#this zeros out any vals that have very small absolute values
    test = bool(isinstance(val, complex))
    #print('test = '+str(test))
    if isinstance(val, complex):
        realstr = ''
        imagstr = ''
        rpart = real(val)
        ipart = imag(val)
        if abs(ipart) < eps:
            return fmt % rpart
        elif abs(rpart) < eps:
            return fmt%ipart+'j'
        else:
            realstr = fmt % rpart
            imagstr = fmt % ipart+'j'
            if ipart > 0:
                rectstr = realstr+'+'+imagstr
            else:
                rectstr = realstr+imagstr
            outstr = rectstr
            if polar:
                polarstr = fmt%abs(val) + '  \\angle '+fmt%angle(val,1)+'^\\circ'
                outstr += ' \\; \\textrm{or} \\; ' +polarstr
            return outstr
    else:
        return fmt % val
            
    


def RowToLatex(rowin, fmt='%0.4g', eps=1e-12):
    if hasattr(rowin,'ToLatex'):
        return rowin.ToLatex(eps=eps, fmt=fmt)
    elif isscalar(rowin):
        #return fmt % rowin
        return ComplexNumToStr(rowin, eps=eps, fmt=fmt)
    elif is_sympy(rowin):
        return sympy.latex(rowin, profile=sympy_profile)
    else:
        strlist =  [ComplexNumToStr(item, eps=eps, fmt=fmt) for item in rowin]
    return ' & '.join(strlist)


def IsOneD(arrayin):
    """Check is arrayin is a one dimensional array (i.e. a vector)."""
    if type(arrayin) == numpy.ndarray:
        if len(shape(arrayin)) == 1:
            return True
    return False


def IsLongArray(arrayin, thresh=10):
    if IsOneD(arrayin):
        if arrayin.shape[0] > thresh:
            return True
    return False


def ShortOneDArrayToLatex(arrayin, mylhs, fmt='%0.4g'):
    curstr = mylhs +' = '
    N = arrayin.shape[0]
    curstr += '\\left[ \\begin{array}{'+'c'*N+'}' 
    outlist = [curstr]
    outlist.extend(_ArrayToLaTex(arrayin, fmt=fmt))
    outlist.append('\\end{array} \\right]')
    return outlist, 'equation'


def OneDArrayToLatex(arrayin, mylhs, fmt='%0.4g', maxelem=10, wrap=5):
    """Attempt to intelligently auto-output one dimensional arrays,
    including large ones.  If the len of the array is less than
    maxelem, simply output the whole thing.  Otherwise, put the first
    wrap elements on one line, some dots (...), and then the last wrap
    elements on the second line.

    Returns both a list of latex lines and the appropriate latex
    equation environment string, i.e. either 'equation' or 'eqnarray'."""
    N = arrayin.shape[0]
    if N < maxelem:
        #print('Calling ShortOneDArrayToLatex')
        return ShortOneDArrayToLatex(arrayin, mylhs, fmt=fmt)
    else:
        curstr = mylhs +' & = &'
        curstr += '\\left[ \\begin{array}{'+'c'*wrap+'}' 
        outlist = [curstr]
        row1 = arrayin[0:wrap]
        row1str = RowToLatex(row1, fmt=fmt)
        outlist.append(row1str)
        end1 = '\\end{array} \\right.  \\ldots \\\\'
        outlist.append(end1)
        start2 = '& & \\left. \\begin{array}{'+'c'*wrap+'}'
        outlist.append(start2)
        row2 = arrayin[-wrap:]
        row2str = RowToLatex(row2, fmt=fmt)
        outlist.append(row2str)
        end2 = '\\end{array} \\right]'
        outlist.append(end2)
        return outlist, 'eqnarray'


def ArrayToLaTex(arrayin, mylhs, fmt='%0.4g', ams=True, \
                 matstr='bmatrix', eps=1e-12):#matstr='smallmatrix'
    ########
    # Need to handle large arrays
    # intelligently.
    ########
    #if mylhs == 'vec_r':
    #    Pdb().set_trace()
    test = IsOneD(arrayin)
    #print('IsOneD='+str(test))
    if hasattr(arrayin, 'toarray'):
        arrayin = arrayin.toarray()
        print('called toarray on '+mylhs+' = '+str(mylhs))
    if IsOneD(arrayin):
        return OneDArrayToLatex(arrayin, mylhs, fmt=fmt)
    else:
        curstr = mylhs +' = '
        if ams:
            if matstr == 'smallmatrix':
                curstr += ' \\left[ '
            curstr += '\\begin{'+matstr+'}'
        else:
            row0 = myvar[0]
            N = len(row0)
            curstr += '\\left[ \\begin{array}{'+'c'*N+'}' 
        outlist  = [curstr]
        outlist.extend(_ArrayToLaTex(arrayin, fmt=fmt))
        if ams:
            outlist.append('\\end{'+matstr+'}')
            if matstr == 'smallmatrix':
                outlist.append(' \\right] ')
        else:
            outlist.append('\\end{array} \\right]')
        return outlist, 'equation'


def _ArrayToLaTex(arrayin, fmt='%0.4g'):
        outlist = []
        first = 1
        for row in arrayin:
            currow = RowToLatex(row)
            if first:
                first = 0
            else:
                outlist.append('\\\\')
            outlist.append(currow)
        return outlist


def NumToLatex(ent,fmt='%0.5g',eps=1e-20, printeps=False, polar=True):
    """The polar option right now outputs rectangular and polar.  If
    polar=False, output just the rectangular."""
    #print('in _latexelem, eps='+str(eps))
    if isinstance(ent,str):
        temp=str(ent)
        if temp[-2:]=='.0':
            temp=temp[:-2]
        temp=temp.replace('*',' \\; ')
        return temp
    if hasattr(ent,'ToLatex'):
        #print('calling ToLatex method')
        return ent.ToLatex(fmt=fmt, eps=eps)
    if ent==0.0:
        return '0'
    if abs(ent)<eps:
        if printeps:
            return 'O(\\varepsilon)'
        else:
            return '0'
    return ComplexNumToStr(ent, fmt=fmt, polar=polar)
##     realstr=''
##     imagstr=''
##     rpart=real(ent)
##     ipart=imag(ent)
##     if type(fmt)==tuple or type(fmt)==list:
##         rfmt=fmt[0]
##         ifmt=fmt[1]
##     else:
##         rfmt=fmt
##         ifmt=fmt
##     if abs(rpart)>eps and rpart!=0:
##         realstr=rfmt%rpart
##     if realstr:#there needs to be a sign character on the imag even if it's positive
##         if '+' not in ifmt:
##             ifmt=ifmt[0]+'+'+ifmt[1:]
##     if abs(ipart)>eps and ipart!=0:
##         imagstr=ifmt%ipart+'j'#'$\\jmath$'
##     return realstr+imagstr

def is_sympy(myvar):
##     typestr = str(type(myvar))
##     ind = typestr.find('sympy.')
##     out = bool( ind >- 1 )
    out = isinstance(myvar, sympy.core.basic.Basic)
    return out


def VariableToLatex(myvar, mylhs, ams=True, matstr='bmatrix', \
                    fmt='%0.5g', eps=1.0e-12, replacelist=None, \
                    **kwargs):
    """Convert variable myvar to LaTeX by checking whether
    or not it is a scalar.

    If ams is True, assume the LaTeX header includes
    \usepackage{amsmath} so that bmatrix is used rather than \left[
    \begin{array}{ccccc} ... \end{array} \right].

    This function always returns a list so that the output is
    consistant for scalar and matrix variables.  For scalars, the list
    will contain only one line.

    env may be either 'equation' or 'eqnarray'."""
    if hasattr(myvar,'ToLatex'):
        #print('calling ToLatex method')
        strout = myvar.ToLatex(fmt=fmt, eps=eps)
        if hasattr(myvar, 'latexenv'):
            env = myvar.latexenv
        else:
            env = 'equation'
        if strout.find('=') > -1:
            outlist = [strout]
        else:
            outlist = [mylhs +' = '+strout]
    elif type(myvar) == dict:
        outlist = [mylhs +' = '+str(myvar)]
        env = 'equation'
    elif isscalar(myvar):
        outlist = [mylhs +' = '+NumToLatex(myvar)]
        env = 'equation'#need a number to latex convert that handles nice formatting
    elif is_sympy(myvar):
        outlist = [mylhs +' = '+sympy.latex(myvar, profile=sympy_profile)]
        env = 'equation'
    else:
        #print('calling ArrayToLaTex on variable with lhs '+mylhs+'.  str(myvar)='+str(myvar))
        outlist, env = ArrayToLaTex(myvar, mylhs, ams=ams)
    if replacelist is not None:
        outlist = replacelist.Replace(outlist)
    return outlist, env

