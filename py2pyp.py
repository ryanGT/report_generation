import os, re, pdb

import env_popper
reload(env_popper)

import txt_mixin
reload(txt_mixin)

clean_re = re.compile('#(pyfig|pyno|pybody|caption:|filename:|label:)')


class python_file(txt_mixin.txt_file_with_list):
    def __init__(self, pathin, outputpath=None, def_env=None):
        if outputpath:
            self.pyp_path = outputpath
        else:
            pne, ext = os.path.splitext(pathin)
            self.pyp_path = pne + '.pyp'
        folder, filename = os.path.split(pathin)
        if not folder:
            folder = os.getcwd()
        self.folder = folder
        self.figfolder = os.path.join(folder,'figs')
        txt_mixin.txt_file_with_list.__init__(self, pathin)
        self.popper = env_popper.python_report_popper(self.list)
        self.namespace = {}


    def Find_Envs(self):
        self.envs = self.popper.Execute()
        

    def Execute(self, **kwargs):
        self.namespace = {}
        self.Find_Envs()
        for env in self.envs:
            env.Execute(self.namespace, figfolder=self.figfolder, \
                        **kwargs)

    def clean_comments(self):
        clean_lines = []
        for line in self.list:
            q = clean_re.search(line)
            if not q:
                clean_lines.append(line)
        self.clean_lines = clean_lines
        return self.clean_lines


    def To_PYP(self, full_echo=0, usetex=False, **kwargs):
        pyp_list = []
        print('usetex=%s' % usetex)
        if full_echo > 0:
            self.clean_comments()
        if full_echo == 1:
##             if usetex:
##                 pyp_list.append('')
##                 pyp_list.append('\\textbf{\\large Python Code}')
            pyp_list.append('code{')
            pyp_list.extend(self.clean_lines)
            pyp_list.append('}')
            if usetex:
                pyp_list.append('\\pagebreak')
                pyp_list.append('\\textbf{\\Large Discussion}')
                pyp_list.append('')
        for env in self.envs:
            cur_list = env.To_PYP(usetex=usetex, **kwargs)
            pyp_list.extend(cur_list)
        self.pyp_list = pyp_list


    def save(self):
        self.writefile(self.pyp_path, listin=self.pyp_list)
        return self.pyp_path
        

if __name__ == '__main__':
    import os
    mydir = '/home/ryan/siue/Research/saturation'
    filename = 'input_shaping_vs_non.py'
    mypath = os.path.join(mydir, filename)
    mypy = python_file(mypath)
    mypy.Execute()
    mypy.To_PYP()
    mypy.save()
    
