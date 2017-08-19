import os, txt_mixin, lecture_folders_gvsu, rwkos

class markdown_file(txt_mixin.txt_file_with_list):
    def out(self, line):
        self.list.append(line)


    def out_list(self, listin):
        for line in listin:
            self.out(line)

        
    def _init_list(self, title=None, author=None):
        self.out('---')
        
        if title:
            self.out('title = "%s"' % title)
        if author:
            self.out('author = "%s"' % author)

        self.out("geometry: margin=1in")
        self.out("output: pdf_document")
        self.out('---')
        self.out('')

        
    def __init__(self, pathin=None, title=None, author=None):
        txt_mixin.txt_file_with_list.__init__(self, pathin=pathin)
        self._init_list(title=title, author=author)
        

class md_lecture_file(markdown_file):
    def __init__(self, title, lecture_num):
        """Note that title in a markdown file is handled a little
        weirdly and takes up too much space, so I will not typically
        use the official title or author spots"""
        markdown_file.__init__(self)
        self.title = title
        self.lecture_num = lecture_num


class md_lecture_file_345(md_lecture_file):
    def build_lecture_path(self):
        self.lecture_folder = lecture_folders_gvsu.build_lecture_path(self.root, \
                                                                      self.title, \
                                                                      self.lecture_num)

    def __init__(self, title, lecture_num):
        md_lecture_file.__init__(self, title, lecture_num)
        self.root = "/Users/kraussry/Google Drive/Teaching/345/lectures"



    def save(self, overwrite=False):
        fn = self.build_filename()
        self.build_lecture_path()
        pathout = os.path.join(self.lecture_folder, fn)
        if overwrite or (not os.path.exists(pathout)):
            txt_mixin.txt_file_with_list.save(self, pathout)
        

    def main(self):
        self.add_title()

        
class md_outline(markdown_file):
    def add_title(self):
        title_line1 = "# Outline: Lecture %s" % self.lecture_num
        title_line2 = "# " + self.title
        self.out_list([title_line1, '', title_line2])
        
        self.out('')


    def build_filename(self):
        clean_title = rwkos.clean_fno_or_folder(self.title)
        fn = 'outline_lect_%s_%s.md' % (self.lecture_num, clean_title)
        self.fn = fn
        return fn

class md_outline_345(md_outline,md_lecture_file_345):
    pass


class md_detailed_notes(markdown_file):
    def add_title(self):
        title_line1 = "# Lecture %s - Detailed Notes" % self.lecture_num
        title_line2 = "# " + self.title
        self.out_list([title_line1, '', title_line2])

        self.out('')


    def build_filename(self):
        clean_title = rwkos.clean_fno_or_folder(self.title)
        fn = 'detailed_notes_lect_%s_%s.md' % (self.lecture_num, clean_title)
        self.fn = fn
        return fn


class md_detailed_notes_345(md_detailed_notes,md_lecture_file_345):
    pass



class md_post_lecture_notes(markdown_file):
    def add_title(self):
        title_line1 = "# Post Lecture Notes - Lecture %s" % self.lecture_num
        title_line2 = "# " + self.title
        self.out_list([title_line1, '', title_line2])

        self.out('')


    def build_filename(self):
        clean_title = rwkos.clean_fno_or_folder(self.title)
        fn = 'post_lecture_notes_lect_%s_%s.md' % (self.lecture_num, clean_title)
        self.fn = fn
        return fn


class md_post_lecture_notes_345(md_post_lecture_notes,md_lecture_file_345):
    pass
