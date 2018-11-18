import txt_mixin, copy, os



def remove_columns_filter(listin):
    for i in range(10000):
        ind = listin.findnext('\\column')
        if ind:
            listin.pop(ind)
        else:
            break
    return listin



def remove_subsection_filter(listin, section_name, level_str='#'):
    """Remove everything from # section_name to the next #.  Since
       level_str is not forced to match the start of a line, it would
       match any line that contained # section_name.  Set level_str to
       "##" to force a second level subsection.
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
       "##" to force a second level subsection.
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
        
