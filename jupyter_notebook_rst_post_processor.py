import txt_mixin
from IPython.core.debugger import Pdb
import os
import basic_file_ops
import re

ws = '    '#four space for white space on indented environments

p_hide = re.compile('# *hide')

def find_hide(block):
    for line in block:
        q = p_hide.search(line)
        if q:
            return True
        
"""As of May 2018, all Python blocks are now in '.. code:: ipython3'
directives and the output is in '.. parsed-literal::'  I think this breaks
pretty much everything."""

code_pat = '.. code:: ipython3'

class jupyter_rst_post_processor(txt_mixin.txt_file_with_list):
    def __init__(self, pathin, replacepath=None, outputonly=False):
        txt_mixin.txt_file_with_list.__init__(self, pathin)
        self.replacepath = replacepath
        self.outputonly = outputonly


    def read_replace_path(self):
        mylist = basic_file_ops.readfile(self.replacepath)
        repdict = {}
        for line in mylist:
            lhs, rhs = line.split(',',1)
            lhs = lhs.strip()
            rhs = rhs.strip()
            repdict[lhs] = rhs
        self.repdict = repdict

        
    def save(self):
        folder, namein = os.path.split(self.pathin)
        fno, ext = os.path.splitext(namein)
        nameout = fno + '_out.rst'
        pathout = os.path.join(folder, nameout)
        self.pathout = pathout
        txt_mixin.txt_file_with_list.save(self, self.pathout)
        return self.pathout
    
        
    def find_lhs(self, linenum):
        """search backwards for the first non-blank line.  Assume this
        line contains only the variable name that is in the math block.

        Assumed output:

        .. code:: python
            a = 7
            b = 3
            b


        .. math::
           3
        """
        lhs = None

        for i in range(50):#50 lines up seems like a lot
            clean_line = self.list[linenum-i].strip()

            if clean_line:
                lhs = clean_line
                break

        assert lhs is not None, \
               "did not find a non-blank line above line %s" % linenum
        
        lhs = clean_line

        if '=' in lhs:
            msg = "lhs contains equal sign: %s, line: %i" % (lhs, linenum)
            raise ValueError(msg)
        return lhs


    def check_math(self, ind):
        """the jupyter notebook rst seems to use .. math:: a=b for
        equations from markdown that I don't need to mess with.  If
        the length of the math line is greater than 10 and/or it
        contains an equal sign, skip it."""
        curline = self.list[ind]
        curline = curline.strip()
        if len(curline) > 11:
            return True
        elif '=' in curline:
            return True
        else:
            return False

        
    def find_rhs(self, ind):
        """Assuming ind points to the .. math:: line, there should be
        one blank line and then the latex output.  Find the latex
        output and return the linenumber that it is on."""
        assert self.list[ind+1] == '', "expected blank line here: %s" % \
               self.list[ind+1]
        assert self.list[ind+2], "expected non-blank on line %i" % ind+2
        rhs = self.list[ind+2]
        return rhs, ind+2

                        
    def process_eqn(self, eqnin):
        eqnout = eqnin#do search and replace in a minute

        if self.replacepath is not None:
            #do search and replace only if replacepath is given
            if not hasattr(self, "repdict"):
                self.read_replace_path()

            for findstr, repstr in self.repdict.items():
                eqnout = eqnout.replace(findstr, repstr)
        
        return eqnout


    def find_start_of_next_python_block(self, start_ind):
        next_ind = self.list.findnext(code_pat, ind=start_ind)
        return next_ind


    def find_end_of_python_block(self, start_ind):
        for i in range(1,1000):
            curline = self.list[start_ind+i]
            if curline:
                first_char = curline[0]
                check_char = first_char.strip()
                if check_char:
                    # Note that if we never get to this point,
                    # the function with return None
                    return start_ind + i


    def get_block(self, start_ind, end_ind):
        block = self.list[start_ind:end_ind]
        return block

    
    def pop_hidden_python_blocks(self):
        """Remove from self.list all python blocks that contain
        '#hide' or '# hide'.  Alternatively, remove all python blocks
        if self.outputonly is True."""

        i = 0
        N = len(self.list)

        while i < N:
            start_ind = self.find_start_of_next_python_block(i)
            if start_ind is None:
                break
            end_ind = self.find_end_of_python_block(start_ind)
            block = self.get_block(start_ind, end_ind)
            hide_this = find_hide(block)
            if self.outputonly or hide_this:
                self.list[start_ind:end_ind] = []
                N = len(self.list)# the list is now shorter
            else:
                i = end_ind + 1
            
    
    def process_math_environments(self):
        """Find the left hand side (lhs) for all .. math:: environments
        and then do search and replace on variables"""
        next_ind = -1
        Nlim = 50000

        for i in range(Nlim):
            # sort of a while 1, but with a limit
            start_ind = next_ind + 1
            next_ind = self.list.findnext('.. math::', ind=start_ind)
            if next_ind is None:
                break
            if self.check_math(next_ind):
                # this function (check_math) checks to see if the
                # math environment is really inline or otherwise
                # not caused by python code
                #
                # if this is an inline math environment, skip this one
                continue
            rhs, rhsind = self.find_rhs(next_ind)
            rhs = rhs.strip()
            if '=' in rhs:
                #skip this one
                continue
            lhs = self.find_lhs(next_ind-1)#<-- do I want to pop the rhs
                                           # off of the last
                                           # line of the python
                                           # environment if I am
                                           # sure it is just for echo?
            eqn = ws + '%s = %s' % (lhs, rhs)
            eqn_out = self.process_eqn(eqn)
            self.list[rhsind] = eqn_out
            
            
    def main(self):
        self.process_math_environments()# find lhs's and do search and replace
        # hide/pop python environments as appropriate
        # - pop all if output only
        # - pop those that contain #hide
        self.pop_hidden_python_blocks()

        pathout = self.save()
        return pathout


if __name__ == '__main__':
    case = 2

    if case == 1:
        pathin = "/Users/kraussry/Google Drive/Teaching/445/lectures/lecture_19_Jacobians_Take_2/jacobian_derivations/quiz_3_robot_Jacobian.rst"
        replacepath = "/Users/kraussry/Google Drive/Teaching/445/lectures/lecture_19_Jacobians_Take_2/jacobian_derivations/replacelist.csv"
        my_processor = jupyter_rst_post_processor(pathin,replacepath)
        my_processor.process_math_environments()
        my_processor.save()

    elif case == 2:
        pathin = "/Users/kraussry/Google Drive/Teaching/345/lectures/lecture_04_partial_fractions_part_2/cubic_root_cases.rst"
        my_processor = jupyter_rst_post_processor(pathin)#,replacepath)
        my_processor.main()
        
