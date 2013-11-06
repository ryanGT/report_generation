"""This file creates a post processor for py_directive to allow
searching and replacing of patterns to make pretty variables in sage
latex pylit documents processed with rst2latex_pydirective.py"""

import os

def find_replacement_file(fn='frpatterns.txt'):
    """Search for a replacement file in the current directory and up
    the directory tree from the current directory."""
    import os#<-- should already be done, but it is inside a try block
    if os.path.exists(fn):
        #fn is in the current directory
        return fn

    curdir = os.getcwd()
    found = 0
    i = 0
    new_root = curdir
    while (not found) and (i < 100):
        new_root, folder = os.path.split(new_root)
        test_path = os.path.join(new_root, fn)
        if os.path.exists(test_path):
            found = 1
            return test_path
        elif not (new_root and folder):
            break
        i += 1

    if not found:
        return None


rep_path = find_replacement_file()


def load_replacement_list(replacement_file):
    f = open(replacement_file, 'rb')
    lines = f.readlines()
    f.close()
    find_list = []
    replace_list = []
    for line in lines:
        curline = line.strip()
        if curline:
            try:
                f, r = curline.split('&',1)
                find_list.append(f.strip())
                replace_list.append(r.strip())
            except ValueError:
                print('problem with line:' + curline)
    return find_list, replace_list

find_list = ['\\begin{equation*}','\\end{equation*}', \
             '\\begin{pmatrix}','\\end{pmatrix']

replace_list = ['','', \
                '\\begin{bmatrix}','\\end{bmatrix']

if rep_path:
    #it feels somewhat slopy to simply load these into the module
    #namespace, but it also seems to work with the use case of calling
    #rst2latex from the command line
    find_list1, replace_list1 = load_replacement_list(rep_path)
    find_list.extend(find_list1)
    replace_list.extend(replace_list1)


def _replace_latex(latex):
    print('latex (in) = ' + latex)
    latex_out = latex
    if type(latex_out) != str:
        latex_out = str(latex_out)
    for find_str, replace_str in zip(find_list, replace_list):
        latex_out = latex_out.replace(find_str, replace_str)
    print('latex_out = ' + latex_out)
    return latex_out

