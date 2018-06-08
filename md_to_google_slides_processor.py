import txt_mixin
from IPython.core.debugger import Pdb
import os, shutil, glob, pdb
import basic_file_ops
import re
import copy, pickle
import eqns_to_png

webroot_pat = "http://www4.gvsu.edu/kraussry/445_lectures/lecture_%0.2i"
web_hd_find = "http://www4.gvsu.edu/kraussry/"
web_hd_rep = "/Volumes/facweb-private/KRAUSSRY/"
eqn_p = re.compile(r'\$+(.*?)\$+')
title_pat = re.compile('^#+ (.*)')
fig_pat = re.compile('^!\[.*\]\((.*)\)')
fig_pat2 = re.compile(r'\\includegraphics\[.*\]{(.*?)}')
png_eqn_pat = 'auto_slides_eqn_%0.2i'
eqn_dir = 'eqns'

pkl_name = 'auto_eqns.pkl'

def simplify_eqn(eq_text):
    eq_out = copy.copy(eq_text)
    rep_dict = {'\\mathbf':' ', \
                '\\begin{matrix}':' ', \
                '\\end{matrix}':' ', \
                '\\left[':'\\[', \
                '\\right]':'\\]'}

    for F, R in rep_dict.items():
        eq_out = eq_out.replace(F,R)
    return eq_out

    
def look_up_eqn(eqn_str):
    if os.path.exists(pkl_name):
        eqn_dict = pickle.load(open(pkl_name,'rb'))
    else:
        eqn_dict = {}

    if eqn_str in eqn_dict:
        return eqn_dict[eqn_str]#should be a webaddr
    else:
        return None


def append_eqn_to_dict(eqn_str, webaddr):
    if os.path.exists(pkl_name):
        eqn_dict = pickle.load(open(pkl_name, 'rb'))
    else:
        eqn_dict = {}

    if eqn_str not in eqn_dict:
        eqn_dict[eqn_str] = webaddr
        pickle.dump(eqn_dict, open(pkl_name, 'wb'))


skip_eqns = False
#skip_eqns = True


def copy_image_to_web(filename, lectnum):
    webroot = webroot_pat % lectnum
    smbpath_root = convert_webpath_to_facweb_smb_path(webroot)
    smb_class_root, folder = os.path.split(smbpath_root)
    if not os.path.exists(smb_class_root):
        print('warning: web folder does not exist: %s' % smb_class_root)
        return

    if not os.path.exists(smbpath_root):
        os.mkdir(smbpath_root)
        
    webpath = os.path.join(webroot, filename)
    smbpath_img = convert_webpath_to_facweb_smb_path(webpath)
    if not os.path.exists(smbpath_img):
        # auto copying to webpath
        shutil.copyfile(filename, smbpath_img)

    return webpath


def clean_bullets(listin):
    listout = []

    for line in listin:
        if line:
            # this is also filtering blank lines
            if (line[0] == '-') and (line[1] == ' '):
                line = '*' + line[1:]
            listout.append(line)

    return listout
    
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



def latex_cmds_to_skip(linein):
    mylist = ['\\includepdf','\\pagebreak', \
              '\\begin{center}', '\\end{center}']
    
    for cmd in mylist:
        if linein.find(cmd) > -1:
            return True

    # None found if we made it through the loop
    return False


class text(object):
    def __init__(self, linein, parent, webroot):
        self.line = linein
        self.raw_line = copy.copy(self.line)
        self.parent = parent
        self.webroot = webroot


    def get_and_inc_eqn_number(self):
        return self.parent.get_and_inc_eqn_number()


    def prep_eqn_web_dir(self):
        assert os.path.exists(web_hd_rep), "web folder not mounted"
        self.mounted_web_path = self.webroot.replace(web_hd_find, web_hd_rep)
        if not os.path.exists(self.mounted_web_path):
            os.mkdir(self.mounted_web_path)

        self.mounted_eqn_dir = os.path.join(self.mounted_web_path, 'eqns')
        if not os.path.exists(self.mounted_eqn_dir):
            os.mkdir(self.mounted_eqn_dir)
        print('mounted_eqn_dir: %s' % self.mounted_eqn_dir)
        

    def find_and_copy_equation(self, basename):
        self.prep_eqn_web_dir()
        #find cropped png in local folder
        src_pat = os.path.join(eqn_dir, basename + '*crop*.png')
        src_list = glob.glob(src_pat)
        assert len(src_list) > 0, "did not find a match for %s" % src_pat
        msg2 = "found more than one match for %s: %s" % (src_pat, src_list)
        assert len(src_list) == 1, msg2
        src_path = src_list[0]
        folder, fn = os.path.split(src_path)
        dst = os.path.join(self.mounted_eqn_dir, fn)
        if not skip_eqns:
            shutil.copyfile(src_path, dst)
        web_addr = dst.replace(web_hd_rep, web_hd_find)
        return web_addr
        

    def eqn_to_web_png(self, eq_text):
        eqn_num = eqns_to_png.find_eqn_num(png_eqn_pat)
        basename = png_eqn_pat % eqn_num

        eqns_to_png.expr_to_png(eq_text, basename, \
                                add_bg=False, pad=10)
        webaddr = self.find_and_copy_equation(basename)
        append_eqn_to_dict(eq_text, webaddr)
        return webaddr
    

    def process_equations(self):
        """Find and process equations in the section/slide.  Equations
        should be enclosed within one or two dollar signs.  I need to
        handle both of those well.  I kind of need to handle the
        equations in order even though some will have one dollar sign
        and others will have more than one.  This may be a none issue
        with propoer regexp creation.

        Equations are converted to png and uploaded to my university
        webfolder.

        What do I do with the equation text after the png has been
        created?

        Equations cannot span mulitiple lines, since we are handling them
        here in a method that operates on one line of one subsection.

        Similarly, equation numbering is weird because most lines will
        have one or two equations and the counter would need to be at
        the slide or presentation level.  So, I am letting eqns_to_png
        handle numbering based on what is already saved in the folder.
        But how can this work unless we delete them all at the start
        or processing?
        """
        # cycle through the lines, searching and processing all equations
        # in each line
        
        
        for i in range(10):
            # limited while 1; 10 equations per line seems like plenty
            q = eqn_p.search(self.line)

            if q:
                # process one equation
                eq_text = q.group(1)
                ###!#print('eq_text = %s' % eq_text)
                #Pdb().set_trace()
                # work up the family tree to the presentation to
                # find eqn number
                webaddr = look_up_eqn(eq_text)
                if not webaddr:
                    webaddr = self.eqn_to_web_png(eq_text)
                simp_str = simplify_eqn(eq_text)
                rep_str = '**EQN: ** %s ![](%s)' % (simp_str, webaddr)
                #self.line = eqn_p.sub(rep_str, self.line, 1)
                #################
                # I need to replace the equation without using re and
                # I don't know the eqn number (unless I get it from
                # webaddr).  And it would be nice if whatever I replace
                # it with was helpful.
                #################
                self.line = self.line.replace('$$','$')
                find_str = '$' + eq_text + '$'
                
                self.line = self.line.replace(find_str, rep_str, 1)
                ###!#print('self.line = %s' % self.line)
                # We will ultimately need to insert the web path
                # to the eqn png here or somewhere
            else:
                break

    def skip_check(self):
        """check to see if line should be skipped in output"""
        func_list = [latex_cmds_to_skip]

        skip_me = False

        for func in func_list:
            if func(self.line):
                skip_me = True
                break

        return skip_me
        

    def to_gslides_md(self):
        if self.skip_check():
            # return an empty string and exit
            return None
        self.process_equations()#<-- we only want to do this if we are
                                # generating google slides; we want to leave
                                # the equations alone for the main outline
                                # file.
                                # Since this is in the to_gslides_md method,
                                # I am assuming this is fine.
        return self.line


def pdf_to_padded_png(pathin, width=1600, height=1000):
    cmd0 = 'pdf_to_png_2016.py %s' % pathin
    os.system(cmd0)
    fno, ext = os.path.splitext(pathin)
    start_png_name = fno + '.png'
    cmd = 'mytrim.py %s' % start_png_name
    os.system(cmd)    
    fn2 = fno +'_trimmed.png'
    cmd2 = 'resize_and_pad_image_for_jupyter_slides.py %s -w %i --height %i' % \
           (fn2, width, height)
    os.system(cmd2)
    os.remove(fn2)
    fno2, ext = os.path.splitext(fn2)
    out_name = fno2 + '_padded.png'
    return out_name

def find_padded_png(pathin):
    fno, ext = os.path.splitext(pathin)
    glob_pat = fno + "*pad*.png"
    glob_list = glob.glob(glob_pat)
    if len(glob_list) == 1:
        return glob_list[0]
    else:
        return None
    

def pdf_to_png(pathin):
    path_no_ext, ext = os.path.splitext(pathin)
    if ext == '.png':
        # do nothing
        return pathin
    elif ext == '.pdf':
        search_res = find_padded_png(pathin)
        if search_res:
            return search_res
        else:
            # process pdf to png, cropped and padded
            png_path = pdf_to_padded_png(pathin)
            return png_path
    else:
        print('I do not know what to do with this ext: %s' % ext)
        
        
class figure(text):
    def __init__(self, linein, webroot, pat=fig_pat):
        self.line = linein
        self.webroot = webroot
        self.pat = pat

        
    def to_gslides_md(self):
        q = self.pat.search(self.line)
        raw_src = q.group(1)
        #src = copy.copy(figpath)#save in case we need to copy it
        src = pdf_to_png(raw_src)#will change ext if was pdf in
        figpath = copy.copy(src)
        
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
            shutil.copyfile(src, smbpath_img)
            
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
        if mytitle in self.skip_list:
            return True
        else:
            return False

        
    def parse_lines(self):
        self.lines = []

        for line in self:
            test_str = line.strip()
            q = fig_pat.search(test_str)
            q2 = fig_pat2.search(test_str)
            if q:
                curline = figure(line, self.webroot, pat=fig_pat)
            elif q2:
                curline = figure(line, self.webroot, pat=fig_pat2)
            else:
                curline = text(line, parent=self, webroot=self.webroot)
                
            self.lines.append(curline)


    def am_I_notes(self):
        if self.title.lower().strip() == 'notes':
            return True
        else:
            return False

        
    def get_and_inc_eqn_number(self):
        return self.parent.get_and_inc_eqn_number()


    def to_gslides_md(self):
        if self.skip_me():
            return []
        else:
            list_out = []
            if self.am_I_notes():
                list_out.append('<!--')

            for line in self.lines:
                # check if this is the Notes title line
                # only write to the output if this is not the
                # Notes title line:
                cur_out = line.to_gslides_md()
                if cur_out is not None:
                    # Why am I appending a colon?
                    q = title_pat.search(cur_out)
                    if q:
                        #cur_out += ': \n'
                        cur_out += ' \n'
                    list_out.append(cur_out)

                
            if self.am_I_notes():
                list_out.append('-->')
                # dashes as bullets in the notes seems to make gslides mad
                #list_out = clean_bullets(list_out)
                
            return list_out
        
            
    def __init__(self, listin, webroot, parent):
        txt_mixin.txt_list.__init__(self, listin)
        self.webroot = webroot
        self.parent = parent
        self.skip_list = ['planning']
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
            mysub = subsection(chunk, webroot=self.webroot, parent=self)
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


    def get_and_inc_eqn_number(self):
        return self.parent.get_and_inc_eqn_number()
    
        
    def __init__(self, listin, webroot, parent):
        txt_mixin.txt_list.__init__(self, listin)
        self.webroot = webroot
        self.parent = parent
        self.skip_list = ['notes','planning']
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
        slide_num = 1
        chunks = break_into_chunks(self.list, pat='^# ')
        for chunk in chunks:
            cur_sec = section(chunk, self.webroot, parent=self)
            self.sections.append(cur_sec)
            slide_num += 1


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


    def get_and_inc_eqn_number(self):
        outnum = copy.copy(self.next_eqn)
        self.next_eqn += 1
        return outnum
    

    def remove_skip_lines(self):
        for line in self.list:
            if latex_cmds_to_skip(line):
                self.list.remove(line)
                

    def pop_header(self):
        """If there are lines at the top within --- that are before
        the first # heading, delete them."""
        first_dash_ind = self.list.findnext('---')
        if first_dash_ind is None:
            return
        first_H1_ind = self.list.findnext('# ')
        if first_H1_ind > first_dash_ind:
            second_dash_ind = self.list.findnext('---', first_dash_ind+1)
            if second_dash_ind < first_H1_ind:
                self.list[first_dash_ind:second_dash_ind+1] = []


    def find_string_lower(self, search_str):
        match_ind = None

        for i, line in enumerate(self.list):
            lower_line = line.lower()
            if lower_line.find(search_str) >-1:
                match_ind = i
                break

        return match_ind


    def find_start(self):
        """look for a line that contains ## start and remove everything
        before that line from self.list if ## start is found."""
        start_ind = self.find_string_lower("## start")
        if start_ind is not None:
            start_ind += 1
        return start_ind


    def find_stop(self):
        stop_ind = self.find_string_lower("## stop")
        return stop_ind
        
        
    def __init__(self, pathin, lectnum=1):
        txt_mixin.txt_file_with_list.__init__(self, pathin)
        self.next_eqn = 1
        self.lectnum = lectnum
        self.webroot = webroot_pat % lectnum
        self.pop_initial_blank_lines()
        self.process_includes()
        self.pop_header()
        self.remove_skip_lines()
        self.pop_initial_blank_lines()
        start_ind = self.find_start()
        stop_ind = self.find_stop()
        #Pdb().set_trace()
        self.list = txt_mixin.txt_list(self.list[start_ind:stop_ind])
        self.pop_initial_blank_lines()
        self.find_sections()




class md_outline_with_includes(md_file):
    def save_processed(self):
        fno, ext = os.path.splitext(self.pathin)
        out_name = fno + '_processed.md'
        basic_file_ops.writefile(out_name, self.list)
        return out_name

    
    def __init__(self, pathin, lectnum=1):
        txt_mixin.txt_file_with_list.__init__(self, pathin)
        self.pop_initial_blank_lines()
        self.process_includes()
        
    
