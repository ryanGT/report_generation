import txt_mixin
from IPython.core.debugger import Pdb
import os
import basic_file_ops


ws = '    '#four space for white space on indented environments

class jupyter_rst_post_processor(txt_mixin.txt_file_with_list):
    def __init__(self, pathin, replacepath=None):
        txt_mixin.txt_file_with_list.__init__(self, pathin)
        self.replacepath = replacepath


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

        assert '=' not in lhs, "lhs contains equal sign: %s" % lhs
        return lhs


    def check_math(self, ind):
        """the jupyter notebook rst seems to use .. math:: a=b for
        equations from markdown that I don't need to mess with.  If
        then length of the math line is greater than 10 and/or it
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

    
    def process_math_environments(self):
        """Find the left hand side (lhs) for all .. math:: environments"""
        next_ind = -1
        Nlim = 50000

        for i in range(Nlim):
            # sort of a while 1, but with a limit
            start_ind = next_ind + 1
            next_ind = self.list.findnext('.. math::', ind=start_ind)
            if next_ind is None:
                break
            if self.check_math(next_ind):
                #skip this one
                continue
            rhs, rhsind = self.find_rhs(next_ind)
            rhs = rhs.strip()
            if '=' in rhs:
                #skip this one
                continue
            lhs = self.find_lhs(next_ind-1)
            eqn = ws + '%s = %s' % (lhs, rhs)
            eqn_out = self.process_eqn(eqn)
            self.list[rhsind] = eqn_out
            
            

if __name__ == '__main__':
    pathin = "/Users/kraussry/Google Drive/Teaching/445/lectures/lecture_19_Jacobians_Take_2/jacobian_derivations/quiz_3_robot_Jacobian.rst"
    replacepath = "/Users/kraussry/Google Drive/Teaching/445/lectures/lecture_19_Jacobians_Take_2/jacobian_derivations/replacelist.csv"
    my_processor = jupyter_rst_post_processor(pathin,replacepath)
    my_processor.process_math_environments()
    my_processor.save()
