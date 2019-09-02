import txt_mixin, copy, os, re
import relpath

def remove_columns_filter(listin):
    for i in range(10000):
        ind = listin.findnext('\\column')
        if ind:
            listin.pop(ind)
        else:
            break
    return listin


def remove_pauses_filter(listin):
    for i in range(10000):
        ind = listin.findnext('\\pause')
        if ind:
            listin.pop(ind)
        else:
            break
    return listin
    


def remove_subsection_filter(listin, section_name, level_str='#'):
    """Remove everything from # section_name to the next #.  Since
       level_str is not forced to match the start of a line, it would
       match any line that contained # section_name.  Set level_str to
       '##' to force a second level subsection.
    """
    mypat = level_str + ' ' + section_name
    for i in range(10000):
        ind = listin.findnext(mypat)
        if ind:
            ind2 = listin.findnextre('^#',ind=ind+1)
            listin[ind:ind2] = []
        else:
            break
    return listin
    

def number_slides_for_handout(listin):
    """Put slide # in paranthesis after title to coordinate notes and
    slides"""
    myinds = listin.findall('## ',forcestart=1)
    slide_num = 1
    for ind in myinds:
        outstr = listin[ind] + " (Slide %i)" % slide_num
        slide_num += 1
        listin[ind] = outstr

    return listin
        

def bold_blue_notes_heading(listin):
    """Find any line that starts with # Notes (any number of #'s) and replace with
       \boldblue{Notes}
       level_str is not forced to match the start of a line, it would
       match any line that contained # section_name.  Set level_str to
       '##' to force a second level subsection.
    """
    mypat = '# Notes'
    repstr = '\\boldblue{Notes}'
    for i in range(10000):
        ind = listin.findnext(mypat)
        if ind:
            listin[ind] = repstr
        else:
            break
    return listin


def remove_notes_filter(listin):
    listout = remove_subsection_filter(listin, "Notes")
    listout = remove_subsection_filter(listout, "notes")
    return listout


def onlyslides_for_notes(listin):
    listout = remove_subsection_filter(listin, 'onlyslides')
    return listout


def onlynotes_for_slides(listin):
    listout = remove_subsection_filter(listin, 'onlynotes')
    return listout

    
def pop_word_filter(listin, myword):
    """Filter any row that contains myword.  Mostly used for latex beamer
    type stuff where myword is likely some latex command such as \\pause."""
    for i in range(10000):
        ind = listin.findnext(myword)
        if ind:
            listin.pop(ind)
        else:
            break
    return listin


def onlyslides_for_slides(listin):
    return pop_word_filter(listin, '# onlyslides')


def onlynotes_for_notes(listin):
    return pop_word_filter(listin, '# onlynotes')


def beamer_to_notes_filter(listin):
    pop_list = ['\\column','\\pause','\\vspace']
    for myword in pop_list:
        listin = pop_word_filter(listin, myword)

    return listin


p_myfig = re.compile(r'\\myfig{(.*)}{(.*)}')

def pdf_image_to_png(pdfpath):
    fno, ext = os.path.splitext(pdfpath)
    png_path = fno + '.png'
    if not os.path.exists(png_path):
        cmd = 'pdf_to_png_2016.py %s' % pdfpath
        os.system(cmd)
    return png_path


def png_path_to_img_line(png_path, width=600):
    lineout = '<img src="%s" width=%ipx>' % (png_path, width)
    return lineout


def beamer_img_path_to_html_path(img_path):
    """An image used in a beamer slide could be a pdf, jpg, or png (or
    possibly others).  If it is a pdf, the corresponding png needs to
    be created if it doesn't exist.  This function calls
    pdf_image_to_png to create the image if necessary and then returns
    the .png or .jpg filename."""
    fno, ext = os.path.splitext(img_path)
    if ext[0] == '.':
        ext = ext[1:]
    if ext == 'pdf':
        out_path =  pdf_image_to_png(img_path)
    elif ext in ['jpg','jpeg','png']:
        out_path = img_path
    return out_path


def beamer_img_path_to_html_line(img_path, width=600):
    out_path = beamer_img_path_to_html_path(img_path)
    if out_path.find("/Users/kraussry/") > -1:
        out_path = relpath.relpath(out_path)
    src_html_line = png_path_to_img_line(out_path, width=width)
    return src_html_line


def myfig_to_html_filter(listin, width=600):
    myinds = listin.findall('\\myfig{')
    for ind in myinds:
        match_line = listin[ind]
        print("match_line = %s" % match_line)
        q = p_myfig.search(match_line)
        filepath = q.group(2)
        ## check extension here
        lineout = beamer_img_path_to_html_line(filepath, width=width)
        listin[ind] = lineout
    return listin


p_put_image = re.compile(r'\\put.*{\\includegraphics.*{(.*)}}')


def process_picture_put_images(listin, width=600):
    pat = '\\begin{picture}'
    for i in range(1000):
        start_ind = listin.findnext(pat, forcestart=1)
        if not start_ind:
            print("exiting")
            break
        else:
            print("put start_ind = %s" % start_ind)
            print("start line: %s" % listin[start_ind])
            end_ind = listin.findnext('\\end{picture}', ind=start_ind, \
                                      forcestart=1)
            print("end line: %s" % listin[end_ind])
            pict_list = copy.copy(listin[start_ind:end_ind+1])
            pict_list.pop(0)
            pict_list.pop(-1)
            print("end_ind = %s" % end_ind)
            # we are left with either \put{ ...\includegraphics[]{}}
            # or stuff we can't deal with
            for j, curline in enumerate(pict_list):
                q = p_put_image.search(curline)
                filepath = q.group(1)
                png_path = pdf_image_to_png(filepath)
                lineout = png_path_to_img_line(png_path, width)
                pict_list[j] = lineout
        listin[start_ind:end_ind+1] = pict_list
    return listin


class md_filter_file(txt_mixin.txt_file_with_list):
    def __init__(self, pathin=None, filter_list=[], ext='_filtered.md', **kwargs):
        txt_mixin.txt_file_with_list.__init__(self, pathin=pathin, **kwargs)
        self.filter_list = filter_list
        self.raw_list = copy.copy(self.list)
        self.ext = ext


    def filter(self):
        for cur_filter in self.filter_list:
            listout = cur_filter(self.list)
            self.list = listout

        if self.only_last:
            self.remove_rest()


    def remove_rest(self):
        """Remove all but the last slide/subection; do this by finding the
        first and last instance of ## Title and removing everything from the 
        first title up to the last title
        """
        ind1 = self.list.findnextre('^#')#<-- first section or subsection after header
        ind_list = self.list.findallre('^## ')
        ind2 = ind_list[-1]
        self.list[ind1:ind2] = []
        

    def save(self):
        fno, old_ext = os.path.splitext(self.pathin)
        self.pathout = fno + self.ext
        print("pathin = %s" % self.pathin)
        print("pathout = %s" % self.pathout)
        txt_mixin.txt_file_with_list.save(self, self.pathout)






# Note: bold_blue_notes_heading probably needs to be last, since it messes with # Notes
notes_list = [beamer_to_notes_filter, onlyslides_for_notes, onlynotes_for_notes, \
              bold_blue_notes_heading, number_slides_for_handout]


class notes_md_filter_file(md_filter_file):
    def __init__(self, pathin=None, filter_list=notes_list, ext='_notes.md', **kwargs):
        md_filter_file.__init__(self, pathin=pathin, filter_list=filter_list, \
                                ext=ext, **kwargs)
        self.only_last = False


beamer_slide_list = [remove_notes_filter, onlyslides_for_slides, onlynotes_for_slides]


class beamer_slides_md_filter_file(md_filter_file):
    def __init__(self, pathin=None, filter_list=beamer_slide_list, ext='_slides.md', \
                 only_last=False,  **kwargs):
        md_filter_file.__init__(self, pathin=pathin, filter_list=filter_list, \
                                ext=ext, **kwargs)
        self.only_last = only_last
        


html_filter_list = [process_picture_put_images, myfig_to_html_filter, \
                    remove_pauses_filter, \
                    remove_notes_filter, number_slides_for_handout]

## long-term: I need to add filtering for columns and possibly other things

class lecture_outline_to_html_ready_markdown(md_filter_file):
    """Convert a beamer-flavored markdown lecture outline file to a
    markdown file ready to be converted to html or a jupyer notebook."""
    def find_title(self):
        title_pat1 = "<!-- Lecture (.*)-->"
        inds = self.list.findallre(title_pat1)
        assert len(inds) > 0, "Did not find %s" % title_pat1
        assert len(inds) == 1, "Found more than one match for %s" % title_pat1
        match_line = self.list[inds[0]]
        q = re.search(title_pat1, match_line)
        self.title = "Lecture %s" % q.group(1).strip()
        return self.title


    def insert_title(self):
        """If there is a --- pair near the top of the file, insert the
        title after the second one."""
        dash_inds = self.list.findall('---')
        if dash_inds:
            assert dash_inds[0] < 5, "First set of dashes not within first 5 rows"
            # Do I ever not want to insert the title?
            # - maybe if I thought it was already in there?
            # - not worrying about that for now
            insert_title_ind = dash_inds[1] + 1
        else:
            insert_title_ind = 0
        self.list.insert(insert_title_ind, "")#blank line after title
        title_line = "# %s" % self.title
        self.list.insert(insert_title_ind, title_line)

        if insert_title_ind > 0:
            # add another blank line above the title
            self.list.insert(insert_title_ind, "")
            
        
    def __init__(self, pathin=None, filter_list=html_filter_list, ext='_for_html.md', \
                 only_last=False,  **kwargs):
        md_filter_file.__init__(self, pathin=pathin, filter_list=filter_list, \
                                ext=ext, **kwargs)
        self.only_last = only_last
        self.find_title()
        self.insert_title()
    
