import glob, os, shutil, re, copy
from krauss_misc import txt_mixin, rwkos


root_345 = os.path.expanduser("~/Documents/Work_vault_ios/345_prep")

prep_root_345 = os.path.expanduser("~/Documents/Work_vault_ios/345_prep/class_prep_345")
images_root_345 = os.path.expanduser("~/Documents/Work_vault_ios/345_prep/345_images")
hw_obs_root_345 = os.path.expanduser("~/Documents/Work_vault_ios/345_prep/homework_345")
vault_root = os.path.expanduser("~/Documents/Work_vault_ios")

p_width = re.compile(":fw:(.*)")
p_height = re.compile(":fh:(.*)")
p_img = re.compile(r"!\[\[(.*)]\]")


class obsidian_markdown_finder(object):
    def __init__(self, pattern, root=root_345):
        self.pattern = pattern
        self.root = root


    def find(self):
        self.matches = rwkos.find_in_top_and_all_sub_dirs(self.root, \
                                                        self.pattern)
        return self.matches


class obsidian_markdown_processor(object):
    def build_pat(self):
        self.pat = r"[Cc]lass[ _0]*%i.*\.md" % self.classnum
        self.p = re.compile(self.pat)



    def __init__(self, classnum, dstfolder=None, \
                 prep_root=None, images_root=None):
        self.classnum = classnum
        self.dstfolder = dstfolder
        self.prep_root = prep_root
        self.images_root = images_root
        self.build_pat()


    def build_glob_list(self):
        glob1 = "class*%i*.md" % self.classnum
        glob2 = "Class*%i*.md" % self.classnum
        self.glob_list = [glob1, glob2]


    def find_all_glob_matches(self):
        if not hasattr(self, "glob_list"):
            self.build_glob_list()

        all_matches = []

        for glob_pat in self.glob_list:
            curmatches = rwkos.Find_in_top_and_sub_dirs(self.prep_root, \
                                        glob_pat)
            all_matches.extend(curmatches)

        return all_matches



    def find_obsidian_markdown(self):
        ## Verify that this works if I create folders for various topics:
        ## 345_prep/bode/class 6 - intro to Bode.md
        all_glob = self.find_all_glob_matches()
        keep_list = [item for item in all_glob if self.p.search(item)]
        if len(keep_list) == 0:
            raise ValueError("did not find a match for %s" % self.pat)
        elif len(keep_list) > 1:
            raise ValueError("found more than match for %s:\n%s" % \
                    (pat, keep_list))
        else:
            self.obsidian_path = keep_list[0]
            return self.obsidian_path


    def load_obsidian_md(self):
        self.txt_file = txt_mixin.txt_file_with_list(self.obsidian_path)
        self.out_list = copy.copy(self.txt_file.list)


    def find_image_lines(self):
        """find images that match ![[filename]]

        It is assumed that these images are on a single line and are the only
        thing on the line"""
        self.image_inds = self.txt_file.list.findallre(r"!\[\[.*\]\]")


    def find_one_image(self, img_fn):
        ## There seems to be a problem here in that I have allowed
        ## a list of image roots and that isn't being handled well.
        print("self.images_root = %s" % self.images_root)
        print("img_fn = %s" % img_fn)
        matches = rwkos.find_in_top_and_all_sub_dirs(self.images_root,img_fn)
        if len(matches) == 0:
            ## need backup plan
            abspath = os.path.join(vault_root, img_fn)
            if os.path.exists(abspath):
                # also check for pdf version
                pne, ext = os.path.splitext(abspath)
                pdf_path = pne + '.pdf'
                if os.path.exists(pdf_path):
                    return pdf_path
                else:
                    return abspath
        assert len(matches) > 0, "did not find a match for %s in %s" % \
                (img_fn, self.images_root)
        match0 = matches[0]
        fno, ext = os.path.splitext(match0)
        if ext.lower() != '.pdf':
            # see if pdf version exists
            pdf_path = fno + '.pdf'
            if os.path.exists(pdf_path):
                match0 = pdf_path

        return match0


    def check_for_fw_or_fh(self, ind):
        # check a few lines above or below for :fw:#.##
        myrange = [-5,-4,-3,-2, -1, 1,2,3,4,5]
        N = len(self.out_list)
        found = False
        for offset in myrange:
            if ind+offset >= N:
                break
            curline = self.out_list[ind+offset]
            if curline:
                curline = curline.strip()
                if curline.find(":fw:") == 0:
                    found = True
                    q = p_width.search(curline)
                    wstr = q.group(1)
                    try:
                        wfloat = float(wstr)
                        out_str = "%0.4g\\textwidth" % wfloat
                    except:
                        out_str = wstr
                elif curline.find(":fh:") == 0:
                    found = True
                    q = p_height.search(curline)
                    hstr = q.group(1)
                    try:
                        hfloat = float(hstr)
                        out_str = "%0.4g\\textheight" % hfloat
                    except:
                        out_str = hstr
                        
                if found:
                    self.out_list[ind+offset] = ''
                    return out_str
    
            # return None if we get to this point
            
                    
    
    
    def copy_images(self):
        if not hasattr(self, "image_inds"):
            self.find_image_lines()
        p = re.compile(r"!\[\[(.*)]\]")
        fig_folder = os.path.join(self.dstfolder, 'figs')
        if len(self.image_inds) > 0:
            rwkos.make_dir(fig_folder)
        for ind in self.image_inds:
            curline = self.txt_file.list[ind]
            q = p.search(curline)
            img_fn = q.group(1)
            if "|" in img_fn:
                img_fn, px = img_fn.split("|",1)
            src_path = self.find_one_image(img_fn)
            rest, filename = os.path.split(src_path)
            dst_path = os.path.join(fig_folder, filename)
            shutil.copyfile(src_path, dst_path)
            relpath = os.path.join("figs", filename)
            size_str = self.check_for_fw_or_fh(ind)
            if size_str is None:
                outline = "\\myvfig{0.8\\textheight}{%s}" % relpath
            elif "height" in size_str:
                outline = "\\myvfig{%s}{%s}" % (size_str, relpath)
            elif "width" in size_str:
                outline = "\\myfig{%s}{%s}" % (size_str, relpath)
            else:
                print("something is wrong with size_stt: %s" % size_str)
                outline = "\\myvfig{0.8\\textheight}{%s}" % relpath

            self.out_list[ind] = outline


    def clean_size_strs(self):
        # every line that starts with :fv: or :fh: is replaces
        # with a blank line
        pass


    def save(self):
        """overwrite the slides md file in the class folder without backing it
        up or checking

        - don't edit that file anymore
            - do all editing in Obsidian
        """
        # find slides md file
        pat = "class_%0.2i_*_slides.md" % self.classnum
        fullpath = os.path.join(self.dstfolder, pat)
        slides_md_path = rwkos.find_one_glob(fullpath)
        txt_mixin.dump(slides_md_path, self.out_list)
                                
            



class obsidian_345_processor(obsidian_markdown_processor):
    def __init__(self, classnum, dstfolder):
        obsidian_markdown_processor.__init__(self, classnum, dstfolder, \
                prep_root=prep_root_345, images_root=images_root_345)


class obsidian_345_hw_processor(obsidian_markdown_processor):
    def __init__(self, hwnum, dstfolder):
        obsidian_markdown_processor.__init__(self, hwnum, dstfolder, \
                prep_root=hw_obs_root_345, images_root=images_root_345)


    def build_glob_list(self):
        glob1 = "HW*%i*.md" % self.classnum
        glob2 = "hw*%i*.md" % self.classnum
        self.glob_list = [glob1, glob2]


    def build_pat(self):
        self.pat = r"HW[ _0]*%i.*\.md" % self.classnum
        self.p = re.compile(self.pat)



#\myfigcap{0.45\textwidth}{figs/mac_USB_latency_hist.pdf}{Latency
#histogram for the USB serial approach with a laptop
#\label{fig:machist}}


class obsidian_image_handler(obsidian_markdown_processor):
    """Given a markdown file from obsidian with ![imagefile], 
        - find the images
        - copy them to a subfolder
        - replace the text with \\myfig{}{} or something.

        Note: this class handles a list of image roots, where the main
        base class does not."""
    def __init__(self, md_path, dstfolder=None, \
                 prep_root=None, img_root_list=[], \
                 default_img_size='4.5in'):
        self.md_path = md_path
        self.dstfolder = dstfolder
        self.prep_root = prep_root
        self.img_root_list = img_root_list
        self.default_img_size = default_img_size
        self.txt_file = txt_mixin.txt_file_with_list(self.md_path)
        self.out_list = copy.copy(self.txt_file.list)


    def load_obsidian_md(self):
        self.txt_file = txt_mixin.txt_file_with_list(self.md_path)
        self.out_list = copy.copy(self.txt_file.list)


    def find_one_image(self, img_fn):
        found = False
        print("img_root_list: %s" % self.img_root_list)
        for img_root in self.img_root_list:
            print("img_root: %s" % img_root)
            print("img_fn: %s" % img_fn)
            matches = rwkos.find_in_top_and_all_sub_dirs(img_root,img_fn)
            if len(matches) >0:
                found = True
                break

        if found:
            match0 = matches[0]
            fno, ext = os.path.splitext(match0)
            if ext.lower() != '.pdf':
                # see if pdf version exists
                pdf_path = fno + '.pdf'
                if os.path.exists(pdf_path):
                    match0 = pdf_path

            return match0
        
        else:
            raise ValueError("did not find a match for %s" % img_fn)


    def build_out(self, relpath, ind):
        size_str = self.check_for_fw_or_fh(ind)
        if size_str is None:
            size_str = self.default_img_size

        caption_check = self.find_caption_start(ind)

        if caption_check is not None:
            caption = self.find_caption_and_label(ind)
            outline = "\\myfigcap{%s}{%s}{%s}" % \
                        (size_str, relpath, caption)
        else:
            outline = "\\myfig{%s}{%s}" % (size_str, relpath)

        return outline


    def replace_img_md_code(self, relpath, ind):
        outline = self.build_out(relpath, ind)
        self.out_list[ind] = outline


    def find_caption_start(self, ind):
        N = len(self.out_list)

        found = False
        for offset in range(5):
            if ind+offset >= N:
                break
            curline = self.out_list[ind+offset]
            if curline:
                curline = curline.strip()
                if curline.find("caption:") == 0:
                    return ind+offset


    def find_caption_end(self, ind):
        # search for a blank line or a line that starts with
        # label:
        N = len(self.out_list)

        found = False
        for offset in range(20):
            curind = ind+offset
            if curind >= N:
                break
            curline = self.out_list[curind]
            if not curline:
                return curind
            elif curline:
                curline = curline.strip()
                if len(curline) == 0:
                    return curind
                if curline.find("label:") == 0:
                    return curind



    def find_label(self, ind):
        N = len(self.out_list)

        found = False
        for offset in range(5):
            if ind+offset >= N:
                break
            curline = self.out_list[ind+offset]
            if curline:
                curline = curline.strip()
                if curline.find("label:") == 0:
                    return ind+offset


    def find_caption_and_label(self, ind):
        # check a few lines below for caption:
        # - never put the caption above the figure
        #     - that's just wrong
        # - label is below caption if it exists
        capstart = self.find_caption_start(ind)
        capend = self.find_caption_end(capstart)
        label_ind = self.find_label(capend-1)
        # what if capend is None because it ends at the
        # end of the file?
        caption = "\n".join(self.out_list[capstart:capend])
        # get rid of "caption:" from the front by splitting
        # at the first colon
        rest, caption = caption.split(":",1)
        caption = caption.strip()
        if label_ind:
            label_line = self.out_list[label_ind]
            rest, label = label_line.split(":",1)
            label = label.strip()
        else:
            label = None

        if label is not None:
            caption += "\\label{%s}" % label
            self.out_list[label_ind] = ""


        for i in range(capstart, capend):
            self.out_list[i] = ''

        return caption



    def copy_images(self):
        # assuming the images have already been found, 
        # copy them to the destination figs folder
        if not hasattr(self, "image_inds"):
            self.find_image_lines()
        #p = re.compile(r"!\[\[(.*)]\]")
        fig_folder = os.path.join(self.dstfolder, 'figs')
        if len(self.image_inds) > 0:
            rwkos.make_dir(fig_folder)
        for ind in self.image_inds:
            curline = self.txt_file.list[ind]
            q = p_img.search(curline)
            img_fn = q.group(1)
            if "|" in img_fn:
                img_fn, px = img_fn.split("|",1)
            src_path = self.find_one_image(img_fn)
            rest, filename = os.path.split(src_path)
            dst_path = os.path.join(fig_folder, filename)
            shutil.copyfile(src_path, dst_path)
            relpath = os.path.join("figs", filename)
            self.replace_img_md_code(relpath, ind)


    def save(self, overwrite=False):
        if overwrite:
            outpath = self.md_path
        else:
            fno, ext = os.path.splitext(self.md_path)
            outpath = fno + '_out.md'
        txt_mixin.dump(outpath, self.out_list)
    


    def main(self, overwrite=False):
        self.load_obsidian_md()
        self.find_image_lines()
        self.copy_images()
        self.save(overwrite=overwrite)
        



class obsidian_technical_paper(obsidian_image_handler):#,obsidian_markdown_processor):
    def __init__(self, md_path, dstfolder=None, \
                 prep_root=None, img_root_list=[]):
        self.md_path = md_path
        self.dstfolder = dstfolder
        self.prep_root = prep_root
        self.img_root_list = img_root_list
        self.txt_file = txt_mixin.txt_file_with_list(self.md_path)
        self.out_list = copy.copy(self.txt_file.list)


    


    def find_caption_start(self, ind):
        N = len(self.out_list)

        found = False
        for offset in range(5):
            if ind+offset >= N:
                break
            curline = self.out_list[ind+offset]
            if curline:
                curline = curline.strip()
                if curline.find("caption:") == 0:
                    return ind+offset


    def find_caption_end(self, ind):
        # search for a blank line or a line that starts with
        # label:
        N = len(self.out_list)

        found = False
        for offset in range(20):
            curind = ind+offset
            if curind >= N:
                break
            curline = self.out_list[curind]
            if not curline:
                return curind
            elif curline:
                curline = curline.strip()
                if len(curline) == 0:
                    return curind
                if curline.find("label:") == 0:
                    return curind



    def find_label(self, ind):
        N = len(self.out_list)

        found = False
        for offset in range(5):
            if ind+offset >= N:
                break
            curline = self.out_list[ind+offset]
            if curline:
                curline = curline.strip()
                if curline.find("label:") == 0:
                    return ind+offset


    def find_caption_and_label(self, ind):
        # check a few lines below for caption:
        # - never put the caption above the figure
        #     - that's just wrong
        # - label is below caption if it exists
        capstart = self.find_caption_start(ind)
        capend = self.find_caption_end(capstart)
        label_ind = self.find_label(capend-1)
        # what if capend is None because it ends at the
        # end of the file?
        caption = "\n".join(self.out_list[capstart:capend])
        # get rid of "caption:" from the front by splitting
        # at the first colon
        rest, caption = caption.split(":",1)
        caption = caption.strip()
        if label_ind:
            label_line = self.out_list[label_ind]
            rest, label = label_line.split(":",1)
            label = label.strip()
        else:
            label = None

        if label is not None:
            caption += "\\label{%s}" % label
            self.out_list[label_ind] = ""


        for i in range(capstart, capend):
            self.out_list[i] = ''

        return caption


    
    def copy_images(self):
        # assumptions:
        # - there is no such thing as a figure without a caption
        # - labels are optional but recommended
        if not hasattr(self, "image_inds"):
            self.find_image_lines()
        p = re.compile(r"!\[\[(.*)]\]")
        fig_folder = os.path.join(self.dstfolder, 'figs')
        if len(self.image_inds) > 0:
            rwkos.make_dir(fig_folder)
        for ind in self.image_inds:
            curline = self.txt_file.list[ind]
            q = p.search(curline)
            img_fn = q.group(1)
            if "|" in img_fn:
                img_fn, px = img_fn.split("|",1)
            src_path = self.find_one_image(img_fn)
            rest, filename = os.path.split(src_path)
            dst_path = os.path.join(fig_folder, filename)
            shutil.copyfile(src_path, dst_path)
            relpath = os.path.join("figs", filename)
            size_str = self.check_for_fw_or_fh(ind)
            caption = self.find_caption_and_label(ind)
            if size_str is None:
                outline = "\\myfigcap{0.45\\textwidth}{%s}{%s}" % \
                        (relpath, caption)
            else:
                outline = "\\myfigcap{%s}{%s}{%s}" % \
                        (size_str, relpath, caption)

            self.out_list[ind] = outline


    def save(self):
        """overwrite the slides md file in the class folder without backing it
        up or checking

        - don't edit that file anymore
            - do all editing in Obsidian
        """
        # find slides md file
        txt_mixin.dump(self.md_path, self.out_list)
                                
 
