from krauss_misc import txt_mixin
import re, os
import bb_utils


img_pat = re.compile('<img src="(.*?)"')
width_pat = re.compile("width=(.*?)px")

class img(object):
    def __init__(self, relpath='', width=600, url=''):
        self.relpath = relpath
        self.url = url
        self.width = width
        

class img_src_replacer(txt_mixin.txt_file_with_list):
    def __init__(self, *args, **kwargs):
        txt_mixin.txt_file_with_list.__init__(self, *args, **kwargs)
        self.csv_path = "img_paths.csv"
        self._find_csv()
        
        
    def find_img_paths(self):
        img_inds = self.list.findall("<img src=")
        img_relpaths = []
        for ind in img_inds:
            curline = self.list[ind]
            print("curline: %s" % curline)
            if curline.find('\\"') > -1:
                curline = curline.replace('\\"','"')
                print(curline)
            q = img_pat.search(curline)
            if q is None:
                print("problem line: %s" % curline)
            else:
                print("q.group(1) = %s" % q.group(1))
                img_relpaths.append(q.group(1))
        self.img_relpaths = img_relpaths



    def find_relpath_for_google_id(self, id_in):
        for img in self.imgs:
            if img.url.find(id_in) > -1:
                return img.relpath


    def _find_csv(self):
        if os.path.exists(self.csv_path):
            self.csv_found = True
            self._load_csv()
        else:
            self.csv_found = False
            self.csv = None
            self.imgs = []


    def _load_csv(self):
        self.csv = txt_mixin.delimited_txt_file(self.csv_path, delim=',')
        self.imgs = []
        ent0 = self.csv.array[0,0]
        if ent0 == "relpath":
            self.csv.array = self.csv.array[1:,:]
        for row in self.csv.array:
            cur_img = img(row[0],row[1],row[2])
            self.imgs.append(cur_img)
            


    def find_relpath_in_imgs(self, relpath):
        found_img = None
        for cur_img in self.imgs:
            if cur_img.relpath == relpath:
                return cur_img
            
    
    def sort_replaths(self):
        """img_relpaths that are found in the csv file and have a url
        need to be replaced.  img_relpaths not found in the csv file
        need to be appended."""
        found_relpaths = []
        missing_relpaths = []
        for relpath in self.img_relpaths:
            if self.find_relpath_in_imgs(relpath) is not None:
                found_relpaths.append(relpath)
            else:
                missing_relpaths.append(relpath)
        self.missing_relpaths = missing_relpaths
        self.found_relpaths = found_relpaths


    def create_new_csv(self):
        if not os.path.exists(self.csv_path):
            f = open(self.csv_path, 'w')
            f.write("relpath,width(px),url,beamer_width,pdf_doc_width\n")
            f.close()


    def save_csv(self):
        if len(self.missing_relpaths) == 0:
            #do nothing, exit
            return
        if not self.csv_found:
            self.create_new_csv()
        f = open(self.csv_path, 'a')#append
        for relpath in self.missing_relpaths:
            curline = "%s,600,,,\n" % relpath
            f.write(curline)
        f.close()


    def process_one_img(self, img_in):
        img_search = '<img src=.*%s' % img_in.relpath
        url_out = bb_utils.gdrive_url_builder(img_in.url)
        src_replace = url_out
        print("img_search = %s" % img_search)
        inds = self.list.findallre(img_search, match=0)
        print("inds = %s" % inds)
        for ind in inds:
            line_in = self.list[ind]
            print("line_in = %s" % line_in)
            line_out = line_in.replace(img_in.relpath, src_replace)
            widthstr = "width=%spx" % img_in.width
            line_out = width_pat.sub(widthstr,line_out)
            print("line_out = %s" % line_out)
            self.list[ind] = line_out
            


    def replace_img_urls(self):
        for cur_img in self.imgs:
            if cur_img.url:
                self.process_one_img(cur_img)


    def replace_one_gdrive_url_with_relpath(self, img_in):
        gdrive_search = '<img src=\\"%s' % bb_utils.gdrive_url_builder(img_in.url)
        relpath_out = '<img src=\\"%s' % img_in.relpath
        print("gdrive_search = %s" % gdrive_search)
        inds = self.list.findall(gdrive_search)
        print("inds = %s" % inds)
        for ind in inds:
            line_in = self.list[ind]
            print("line_in = %s" % line_in)
            line_out = line_in.replace(gdrive_search, relpath_out)
            print("line_out = %s" % line_out)
            self.list[ind] = line_out

        
    def replace_gdrive_urls(self):
        """This is essentially going backwards from what this code was
        originally designed to do.  Given a jupyter notebook or
        markdown file containing google drive links, find the relative
        paths so that I can generate a pdf using md_to_pdf.py"""
        for cur_img in self.imgs:
            if cur_img.url:
                self.replace_one_gdrive_url_with_relpath(cur_img)


    def save(self):
        # overwrite the input file (what could do wrong?)
        txt_mixin.txt_file_with_list.save(self,self.pathin)

        
    def main(self, replace_urls=True):
        self.find_img_paths()
        self.sort_replaths()
        self.save_csv()
        if replace_urls:
            self.replace_img_urls()
