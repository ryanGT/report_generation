import rst_math_report
#This module will probably only work within Sage, i.e. not run from
#Python or scipy

from sage.all import *

from IPython.Debugger import Pdb


class sage_report(rst_math_report.report):
    def __init__(self, *args, **kwargs):
        rst_math_report.report.__init__(self, *args, **kwargs)
        self.x1, self.x2 = var('x1,x2')

        
    def append_one_equation(self, lhs, rhs, \
                            label=None, ws=' '*4):
        if hasattr(rhs, '_latex_'):
            rhs_latex = rhs._latex_()
        elif type(rhs) == str:
            rhs_latex = rhs
        else:
            rhs_latex = latex(rhs)
        rst_math_report.report.append_one_equation(self, lhs, \
                                                   rhs_latex, \
                                                   label=label, \
                                                   ws=ws)

    def find_Vdot(self, V, f1, f2):
        Vdot = diff(V,self.x1)*f1 + diff(V,self.x2)*f2
        Vdot_e = Vdot.expand()
        return Vdot_e
    
    
    def report_one_problem(self, V, f1, f2, \
                           title=None, note=None, \
                           only_basic=False, label=None):
        if not only_basic:
            if title is not None:
                self.append_section_title(title)
            self.append_one_equation('f_1', f1)
            self.append_one_equation('f_2', f2)
        self.append_one_equation('V', V)
        Vdot_e = self.find_Vdot(V,f1,f2)
        self.append_one_equation('\\dot{V}', Vdot_e, label=label)

        if note is not None:
            if type(note) == str:
                note = [note]
            self.list.extend(note)
        return Vdot_e



