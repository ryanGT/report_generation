import txt_mixin, re

#from IPython.core.debugger import Pdb

class rst_file(txt_mixin.txt_file_with_list):
    def filter_dec(self, ind, dec='==='):
        dec_line = self.list[ind+1]
        if dec_line.find(dec) > -1:
            return True
        else:
            return False

    def find_title(self, pat='^=+$'):
        """I am 95% certain the title has to come first, so I am
        searching for two inds at the beginning that should be two
        lines apart."""
        inds = self.findallre(pat)
        # the first two inds should have the title in between them and be
        # one line apart:
        assert inds[1] == inds[0] + 2, "overline/underline problem"
        self.title_ind = inds[0] + 1
        self.title = self.list[self.title_ind]
        return self.title
    

    def find_subtitle(self, pat='^~+$'):
        """There should be only one match for the subtitle decorator"""
        inds = self.findallre(pat)
        assert len(inds) < 2, "bad pattern, mulitple matches for subtitle decorator"
        if len(inds) == 0:
            self.subtitle = None
            self.subtitle_ind = None
        else:
            self.subtitle_ind = inds[0] - 1
            self.subtitle = self.list[self.subtitle_ind]
            return self.subtitle
        

    def find_header(self, pat='^=+$'):
        """This code is based on the assumption that the document
        title uses equal signs for over and under lining and that the
        subtitle uses ~ underlining if a subtitle is present.  The
        header ends just before the first section title.  The first
        section title follows title and subtitle (if subtitle is
        present).  If subtitle is present, it must follow title
        (docutils requires this)."""
        if not hasattr(self, 'title_ind'):
            self.find_title()
        if not hasattr(self, 'subtitle_ind'):
            self.find_subtitle()
        inds = self.findallre(pat)

        # find the first section after title or subtitle
        if self.subtitle_ind is not None:
            min_ind = self.subtitle_ind + 1
        else:
            min_ind = self.title_ind + 1

        while inds[0] < min_ind:
            inds.pop(0)

        self.header_end = inds[0] - 1
        self.header = self.list[0:self.header_end]
        return self.header

    def get_body(self):
        if not hasattr(self, 'header_end'):
            self.find_header()
        self.body = self.list[self.header_end:]
        return self.body
        
        
    def find_section_inds(self, title, dec='==='):
        """Find all instances of title in self.list, then filter so
        that only thos followed by a line starting with dec are left.
        Assert that there is only one index left.  Add 2 to this value
        (for the title and the dec), and call this the starting index
        for the section.  Go to next instance of dec, back up one line
        and call that the end of the section.  If a second instance of
        dec is not found, go to the end of self.list"""
        all_start_inds = self.list.findall(title)
        assert len(all_start_inds) > 0, "Did not find " + str(title) +  \
               " in self.list."
        title_inds = filter(self.filter_dec, all_start_inds)
        assert len(title_inds) > 0, "Did not find any section titles for " + \
               str(title) + " followed by a decorator line starting with " + \
               dec
        assert len(title_inds) == 1, "Found more than one section with the " + \
               "title " + str(title)
        start_ind = title_inds[0] + 2
        end_ind = self.list.find(dec, start_ind=start_ind)
        if end_ind is not None:
            end_ind -= 1#back up from dec line to title line of next
                        #section
        return start_ind, end_ind


    def get_section_contents(self, title, dec='==='):
        try:
            start_ind, end_ind = self.find_section_inds(title, dec=dec)
            return self.list[start_ind:end_ind]
        except AssertionError:
            return None




    def replace_section(self, title, new_list, dec='===', force=False):
        """Replace the content of a section with title title with
        new_list.

        force overrides the test for the contents of the section being
        empty in the original file."""
        #Do I want to make this check that the current contents of the
        #section are empty?
        old_contents = self.get_section_contents(title, dec=dec)
        if old_contents is None:
            print('Cannot find section with title %s. Doing nothing.' % title) 
            return
        filt_old = filter(None, old_contents)
        if not force:
            if len(filt_old) > 0:
                print("Contents of old section " + title + " were not empty.  Doing nothing.")
                return
        if new_list[-1] != '':
            new_list.append('')
        start_ind, end_ind = self.find_section_inds(title, dec=dec)
        self.list[start_ind:end_ind] = new_list



