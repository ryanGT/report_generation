import txt_mixin, rst_creator, os

#import var_to_latex

mysectiondec = rst_creator.rst_section_dec()
titledec = rst_creator.rst_title_dec()
subsecdec = rst_creator.rst_subsection_dec()

class report(txt_mixin.txt_file_with_list):
    def insert_title(self, title):
        self.list.insert(0,'')
        self.list[0:0] = titledec(title)


    def append_section_title(self, title):
        self.list.append('')
        self.list.extend(mysectiondec(title))


    def append_comment(self, comment):
        if type(comment) == str:
            comment = [comment]
        self.list.extend(comment)
        

    def __init__(self, pathout, title=None):
        self.pathout = pathout
        self.list = txt_mixin.txt_list([])
        if title is not None:
            self.insert_title(title)

        self.list.append('.. include:: /home/ryan/git/report_generation/header.rst')
        self.list.append('')
        
        
    def append_one_equation(self, lhs, rhs, \
                            label=None, ws=' '*4):
        self.list.append('')
        self.list.append('.. latex-math::')
        self.list.append('')
        main_line = ws + '%s = %s' % (lhs, rhs)
        if label is not None:
            main_line += ' \\label{%s}' % label
        self.list.append(main_line)
        self.list.append('')


    def save(self):
        txt_mixin.txt_file_with_list.save(self, self.pathout)
        

    def run_rst(self):
        cmd = 'rst2latex_rwk.py ' + self.pathout
        os.system(cmd)
