"""This module assumes that you have an html-flavored markdown file
that you want converted to a jupyter notebook.

Assumptions:

- One pound sign indicates a section title:
    - # Section Title
- Two pound signs indicate a slide title:
    - ## Slide Title

Conversion approach:

- remove markdown header (stuff between two --- lines)
- find each # Section Title line and put it in a cell
- find each ## Slide Title and then put everything up to the next one in a cell
    - probably separating the title from the body in separate cells
"""
#from IPython.core.debugger import Pdb
import txt_mixin, copy, os, re, basic_file_ops
level_pat = re.compile("(#+).*")

tail = """ ],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {
                "name": "ipython",
                "version": 3
            },
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.6.4"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 2
}"""

def check_level(linein):
    q = level_pat.search(linein)
    if q is None:
        return None
    else:
        return len(q.group(1).strip())
    

def replace_quotes_not_on_imgs(linein):
    if linein.find("img src") > -1:
        #do nothing
        return linein
    else:
        lineout = linein.replace('"','\\"')
        return lineout
        

def clean_line(linein, debug=0):
    rep_list = [('\\','\\\\'), \
                ('"','\\"'), \
                ('\t','    '), \
                ]
    lineout = linein
    if (lineout.find("$") > -1) and debug:
        print("before replace: %s" % lineout)
    for myfind, myrep in rep_list:
        lineout = lineout.replace(myfind, myrep)

    if (lineout.find("$") > -1) and debug:
        print("after replace: %s" % lineout)
    
    # lineout = replace_quotes_not_on_imgs(linein)
    # possibly more stuff later
    return lineout


class md_jupyter_file(txt_mixin.txt_file_with_list):
    def __init__(self, pathin=None,  **kwargs):
        txt_mixin.txt_file_with_list.__init__(self, pathin=pathin, **kwargs)
        if pathin is not None:
            fno, ext = os.path.splitext(pathin)
            self.outname = fno + '.ipynb'
        #self.main()


    def pop_blank_lines(self):
        for i in range(100):
            if self.list[0].strip():
                break
            else:
                self.list.pop(0)
                

    def init_list(self):
        self.ipynb_list = ['{', ' "cells": [']


    def out(self, lineout):
        self.ipynb_list.append(lineout)
        

    def add_tail(self):
        self.ipynb_list.append(tail)


    def remove_trailing_comma(self):
        assert self.ipynb_list[-1] == '  },', "trailing comma not found"
        self.ipynb_list[-1] = '   }'
        
    

    def pop_header(self):
        if self.list[0] == '---':
            found_end = False
            for i in range(1,20):
                if self.list[i].strip() == '---':
                    found_end = True
                    break
            if found_end:
                self.list[0:i+1] = []
                self.pop_blank_lines()


    def find_next_level_one_or_two(self, start_ind=0):
        ind = self.list.findnext("#", ind=start_ind, forcestart=1)
        if ind is None:
            return ind
        mylevel = check_level(self.list[ind])
        if mylevel > 2:
            return self.find_next_level_one_or_two(start_ind = ind+1)
        else:
            return ind


    def _start_markdown_cell(self):
        self.out('  {')
        self.out('   "cell_type": "markdown",')
        self.out('   "metadata": {},')
        self.out('   "source": [')


    def _close_markdown_cell(self):
        self.out('   ]')
        self.out('  },')


    def append_markdown_cell_single_line(self, line):
        self._start_markdown_cell()
        self.out('    "%s"' % line)
        self._close_markdown_cell()


    def append_multi_line_markdown_cell(self, lines, debug=0):
        # find first non-blank line
        for i in range(len(lines)):
            if lines[i].strip():
                start_ind = i
                break
            
        self._start_markdown_cell()
        for line in lines[start_ind:]:
            lineout = clean_line(line)
            outline = '    "%s\\n",' % lineout
            if debug:
                print(outline)
            self.out(outline)
        # delete trailing comma
        if self.ipynb_list[-1][-1] == ',':
            self.ipynb_list[-1] = self.ipynb_list[-1][0:-1]
        self._close_markdown_cell()
        
        
    def process_sections(self, debug=0, mystop=1000):
        end_ind = 0
        for i in range(1000):
            #print("i = %i" % i)
            if i > mystop:
                #print("breaking")
                break
            start_ind = self.find_next_level_one_or_two(start_ind=end_ind)
            start_line = self.list[start_ind]
            # put the section or slide heading in its own cell:
            self.append_markdown_cell_single_line(start_line)
            
            if check_level(start_line) == 1:
                # section heading, assumed to be a single line
                end_ind = start_ind + 1
            else:
                end_ind = self.find_next_level_one_or_two(start_ind=start_ind+1)
                self.append_multi_line_markdown_cell(self.list[start_ind+1:end_ind])

            if debug:
                print("start_ind = %s, start_line = %s" % (start_ind, start_line))
                if end_ind is not None:
                    print("end_ind = %s, end_line = %s" % (end_ind, self.list[end_ind]))
                else:
                    print("at end")
                print('='*10)
            if end_ind is None:
                break


    def save(self, overwrite=False):
        if overwrite or (not os.path.exists(self.outname)):
            outlist = [line + '\n' for line in self.ipynb_list]
            self.outlist = outlist
            f = open(self.outname, "w")
            f.writelines(outlist)
            f.close()
                    
                
    def main(self, mystop=1000):
        # mystop is used for debugging
        self.pop_header()
        self.init_list()
        #Pdb().set_trace()
        self.process_sections(mystop=mystop)
        #print("finished process_sections")
        self.remove_trailing_comma()
        self.add_tail()
        


def lecture_outline_jupyter_nb(title_line, outpath):
    myfile = md_jupyter_file()
    myfile.init_list()
    myfile.append_markdown_cell_single_line(title_line)
    myfile.append_markdown_cell_single_line('## Plan for today')
    myfile.append_markdown_cell_single_line('')
    #myfile.append_multi_line_markdown_cell(['- '])
    myfile.outname = outpath
    myfile.remove_trailing_comma()
    myfile.add_tail()
    myfile.save()


