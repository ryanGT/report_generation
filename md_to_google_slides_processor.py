import txt_mixin
from IPython.core.debugger import Pdb
import os, shutil
import basic_file_ops
import re
import copy

webroot_pat = "http://www4.gvsu.edu/kraussry/445_lectures/lecture_%0.2i"
web_hd_find = "http://www4.gvsu.edu/kraussry/"
web_hd_rep = "/Volumes/facweb-private/KRAUSSRY/"

def convert_webpath_to_facweb_smb_path(pathin):
    """Replace a true webpath that starts with
    http://www4/gvsu.edu/kraussry
    with a path on my local harddrive that is the smb
    mounted location of my web page stuff"""
    pathout = pathin.replace(web_hd_find, web_hd_rep)
    return pathout

def break_into_chunks(listin, pat='^# '):
    """Break a list of md text lines into a list of chunks based on
    pat.  pat is used to determine whether we are breaking into sections 
    or subsections."""
    list_out = txt_mixin.txt_list([])
    inds = listin.findallre(pat)
    # if we are searching for subsections on a slide that has none,
    # inds will be empty
    if not inds:
        return [listin]
    
    start_ind = inds[0]

    if start_ind != 0:
        first_chunk = listin[0:start_ind]
        list_out.append(first_chunk)

    for end_ind in inds[1:]:
        chunk = listin[start_ind:end_ind]
        list_out.append(chunk)
        start_ind = end_ind

    last_chunk = listin[start_ind:]
    list_out.append(last_chunk)
    return list_out

title_pat = re.compile('^#+ (.*)')
fig_pat = re.compile('^!\[.*\]\((.*)\)')

class text(object):
    def __init__(self, linein):
        self.line = linein

    def to_gslides_md(self):
        return self.line
        
class figure(text):
    def __init__(self, linein, webroot):
        self.line = linein
        self.webroot = webroot

        
    def to_gslides_md(self):
        q = fig_pat.search(self.line)
        figpath = q.group(1)
        src = copy.copy(figpath)#save in case we need to copy it
        
        for i in range(10):
            folder, filename = os.path.split(figpath)
            if not folder:
                break
            else:
                figpath = filename

        webpath = os.path.join(self.webroot, filename)
        smbpath_root = convert_webpath_to_facweb_smb_path(self.webroot)
        if not os.path.exists(smbpath_root):
            print('warning: web folder does not exist: %s' % smbpath_root)

        smbpath_img = convert_webpath_to_facweb_smb_path(webpath)
        if not os.path.exists(smbpath_img):
            # auto copying to webpath
            shutil.copy2(src, smbpath_img)
            
        outline = '![](%s)' % webpath
            
        return outline



class subsection(txt_mixin.txt_list):
    def pop_initial_blank_lines(self):
        while not self[0]:
            self.pop(0)
            if len(self) == 0:
                break
            
    def get_title(self):
        if not self[0]:
            self.pop_initial_blank_lines()

        q = title_pat.search(self[0])
        if q:
            self.title = q.group(1)
        else:
            self.title = None


    def skip_me(self):
        mytitle = self.title.lower()
        if mytitle in ['notes','planning']:
            return True
        else:
            return False

        
    def parse_lines(self):
        self.lines = []

        for line in self:
            test_str = line.strip()
            q = fig_pat.search(test_str)
            if q:
                curline = figure(line, self.webroot)
            else:
                curline = text(line)
                
            self.lines.append(curline)


    def to_gslides_md(self):
        if self.skip_me():
            return []
        else:
            list_out = []
            for line in self.lines:
                cur_out = line.to_gslides_md()
                list_out.append(cur_out)

            return list_out
        
            
    def __init__(self, listin, webroot):
        txt_mixin.txt_list.__init__(self, listin)
        self.webroot = webroot
        self.pop_initial_blank_lines()
        self.get_title()
        self.parse_lines()
        

class section(subsection):
    def find_subsections(self):
        """The big challenge here is that a slide may have no subsections and
        if it does have one, there may be text before the subsection that is
        sort of not a true subsection (i.e. it will have no title).
        
        Do I force all sections to have at least one subsection and then 
        process subsections with no titles differently?

        Or is it easier to make slides that have text followed by
        subsections?  
            - everything below the first subsection would be
              assumed to be within a subsection

        Subsections would most likely either be left alone or popped in the
        case of notes.
        """
        subsections = txt_mixin.txt_list([])
        #Pdb().set_trace()
        chunks = break_into_chunks(self, pat='^## ')#<-- pop title first?
        for chunk in chunks:
            mysub = subsection(chunk, webroot=self.webroot)
            subsections.append(mysub)

        self.subsections = subsections

        
    def to_gslides_md(self):
        if self.skip_me():
            return []
        else:
            list_out = ['---','']
            
            for subsec in self.subsections:
                cur_list = subsec.to_gslides_md()
                list_out.extend(cur_list)

            return list_out

        
    def __init__(self, listin, webroot):
        txt_mixin.txt_list.__init__(self, listin)
        self.webroot = webroot
        self.pop_initial_blank_lines()
        self.get_title()
        self.find_subsections()
        
    
class md_file(txt_mixin.txt_file_with_list):
    def process_includes(self):
        """Repeatedly include all lines from included files until # include
        is no longer found"""
        pat = re.compile('^# *[Ii]nclude[ :]*(.*)')
        
        for i in range(10):
            inds = self.list.findallre('^# *[iI]nclude')
            if not inds:
                break
            else:
                # we are going to process the first one and then
                # recheck because we will mess up the indices
                # when we insert the new stuff
                ind0 = inds[0]
                ind_line = self.list.pop(ind0)
                q = pat.search(ind_line)
                mypath = q.group(1)
                newfile = txt_mixin.txt_file_with_list(mypath)
                self.list[ind0:ind0] = copy.copy(newfile.list)
            

    def find_sections(self):
        self.sections = []

        chunks = break_into_chunks(self.list, pat='^# ')
        for chunk in chunks:
            cur_sec = section(chunk, self.webroot)
            self.sections.append(cur_sec)


    def to_gslides_md(self):
        list_out = []

        for section in self.sections:
            cur_list = section.to_gslides_md()
            list_out.extend(cur_list)

        self.list_out = list_out


    def save_gslide_md(self):
        fno, ext = os.path.splitext(self.pathin)
        gslides_name = fno + '_gslides.md'
        return basic_file_ops.writefile(gslides_name, self.list_out)


    def pop_initial_blank_lines(self):
        while not self.list[0]:
            self.list.pop(0)

            
    def __init__(self, pathin, lectnum=1):
        txt_mixin.txt_file_with_list.__init__(self, pathin)
        self.lectnum = lectnum
        self.webroot = webroot_pat % lectnum
        self.pop_initial_blank_lines()
        self.process_includes()
        self.pop_initial_blank_lines()        
        self.find_sections()
