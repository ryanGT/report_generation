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
            

    def save(self):
        fno, old_ext = os.path.splitext(self.pathin)
        self.pathout = fno + self.ext
        txt_mixin.txt_file_with_list.save(self, self.pathout)







notes_list = [beamer_to_notes_filter, onlyslides_for_notes, onlynotes_for_notes]


class notes_md_filter_file(md_filter_file):
    def __init__(self, pathin=None, filter_list=notes_list, ext='_notes.md', **kwargs):
        md_filter_file.__init__(self, pathin=pathin, filter_list=filter_list, \
                                ext=ext, **kwargs)
        


beamer_slide_list = [remove_notes_filter, onlyslides_for_slides, onlynotes_for_slides]


class beamer_slides_md_filter_file(md_filter_file):
    def __init__(self, pathin=None, filter_list=beamer_slide_list, ext='_slides.md', **kwargs):
        md_filter_file.__init__(self, pathin=pathin, filter_list=filter_list, \
                                ext=ext, **kwargs)
