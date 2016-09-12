import txt_mixin
#reload(txt_mixin)

class rst_replacer(txt_mixin.txt_file_with_list):
    """Note that this is really working on the tex file output by
    rst2latex"""
    def figure_placement_replacer(self, filename, oldstr='htbp', \
                                  newstr='htbp!'):
        pat1 = 'includegraphics.*{.*' + filename + '.*}'
        pat2 = 'begin{figure}\[%s\]' % oldstr
        repstr = 'begin{figure}[%s]' % newstr
        self.replace_before(pat1, pat2, repstr)


    def figure_placement_replacer_no_old(self, filename, \
                                         newstr='htbp!', \
                                         max_N=10):
        pat1 = 'includegraphics.*{.*' + filename + '.*}'
        oldline = '\\begin{figure}'
        newline = '\\begin{figure}[%s]' % newstr
        self.replace_line_before(pat1, oldline, newline)
        #self.replace_before(pat1, pat2, repstr)
        
