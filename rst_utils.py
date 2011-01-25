import txt_mixin

from IPython.Debugger import Pdb

class rst_file(txt_mixin.txt_file_with_list):
    def filter_dec(self, ind, dec='==='):
        dec_line = self.list[ind+1]
        if dec_line.find(dec) > -1:
            return True
        else:
            return False
        
                   
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
        filt_old = filter(None, old_contents)
        if not force:
            if len(filt_old) > 0:
                print("Contents of old section " + title + " were not empty.  Doing nothing.")
                return
        if new_list[-1] != '':
            new_list.append('')
        start_ind, end_ind = self.find_section_inds(title, dec=dec)
        self.list[start_ind:end_ind] = new_list
        

            
