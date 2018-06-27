import txt_mixin
from IPython.core.debugger import Pdb
import os, copy
import basic_file_ops
import re

web_folder_mount_point = "/Volumes/facweb-private/KRAUSSRY/"
www_mount_point = "http://www4.gvsu.edu/kraussry/"

folder_p = re.compile('/lecture_folders/(.*)')
md_image_p = re.compile(r'!\[\]\((.*?)\)')

# do I need separate classes for notebooks and notebook files?
#     - a notebook is one thing represented by a dictionary
#     - a notebook file is an ipynb file that contains the text
#       to create a notebook
#     - where would reading and writing notebooks go?
#     - what are my use cases?
#          - I will probably want to do md --> ipynb at some point
#                - what will this require?
#                - generating a dictionary
#                - dumping the dictionary to a file

## The docutils approach
## - it seems wise at this point to follow the docutils approach and
##   have separate reader and writer classes
## - is this overkill

class notebook(object):
    def process_cells(self):
        """This method exists as a hook for sub-classess to overwrite and
           populate."""
        pass

    
    def __init__(self, dictin, folder=''):
        self.dict = copy.copy(dictin)
        self.folder = folder


class notebook_to_web_processor(notebook):
    """A sub-class of notebook that is for generating web friendly
       notebooks to share with my students.

       For now, this means the notebook images have been moved to my
       gvsu website.
    """
    def resize_image(self, relpath):
        # - first resize and stuff (no pad for now)
        # - then copy to mounted folder if online
        # - if the image name contains trimmed or padded I will leave it alone
        skip_list = ['trimmed','padded']
        for item in skip_list:
            if item in relpath:
                # skip
                return relpath
        
        cmd3 = 'resize_and_pad_image_for_jupyter_slides.py --no-pad --width %i --height %i %s' % \
               (self.W,self.H,relpath)
        #print(cmd3)
        os.system(cmd3)
        pne, ext = os.path.splitext(relpath)
        resized_png_name = pne + '_cropped_resized.png'
        return resized_png_name


    def copy_resized_image_to_web(self, resized_relpath):
        src = resized_relpath
        junk, dst_name = os.path.split(resized_relpath)
        dst = os.path.join(self.mount_dir, dst_name)
        if self.online:
            shutil.copyfile(src, dst)

        return dst


    def get_www_path(self, dst):
        www_path = dst.replace(web_folder_mount_point, www_mount_point)
        return www_path
    
        
    def find_and_process_images(self, cell):
        # <img src="http://www4.gvsu.edu/kraussry/445_lectures/lecture_11/fig_3_15_eqn_3_3_cropped_padded.png" alt="drawing" style="width: 800px;"/>
        #
        # - How do I separte finding and processing images if the text is buried inside
        #   of the source list of certain cells that happen to be markdown?
        # - How do I generalize this so that I can do other things to cells later?
        #
        # --> I could have a "process_cells" method that provides hooks for other things I
        #     later want to do.

        # ?How do I want this to work while offline?
        if cell_in["cell_type"] != 'markdown':
            return
        else:
            src_out = []
            for line in cell_in["source"]:
                line_out = line
                if '![](' in line:
                    # process one image here
                    q = md_image_p.search(line)
                    relpath = q.group(1)
                    resized_relpath = self.resize_and_copy_image_to_web(relpath)
                    dst = self.copy_resized_image_to_web(resized_relpath)
                    www_path = self.get_www_path(dst)
                    # insert new text into source, replacing ![]()
                    # - do I use re or some other approach?
                    #    - re seems like the only real option
                    
                    
                    
    def process_cells(self):
        for cell in self.dict.cells:
            # add other "hook" functions that process one cell in
            # preparing it for the web notebook
            self.find_and_process_images(cell)


    def get_lecture_folder(self):
        # grab folder path after /lecture_folders/:
        out1 = folder_p.search(self.folder).group(1)
        # grab the first folder after lecture_folders:
        self.lecture_folder = out1.split(os.path.sep)[0]
        return self.lecture_folder


    def build_mount_path(self):
        if not hasattr(self, 'lecture_folder'):
            self.get_lecture_folder()
        temp = os.path.join(web_folder_mount_point, self.class_folder)
        #temp2 = os.path.join(temp, 'lecture_folders')#<-- do I really do this?, I don't think so
        self.mount_dir = os.path.join(temp, self.lecture_folder)
        self.www_mount_dir = self.mount_dir.replace(web_folder_mount_point, www_mount_point)


    def create_mount_folder(self):
        if self.online:
            if not os.path.exists(self.mount_dir):
                os.makedir(self.mount_dir)
                

    def check_if_online(self):
        if os.path.exists(web_folder_mount_point):
            self.online = True
        else:
            self.online = False
            print('web folder not mounted, going to offline mode')


    def __init__(self, *args, class_folder='445_lectures', **kwargs):
        notebook.__init__(self, *args, **kwargs)
        self.check_if_online()
        self.class_folder = class_folder
        self.get_lecture_folder()
        self.build_mount_path()
        self.create_mount_folder()
        
        

        

class notebook_parser(object):
    """This class exists to take a file path and generate the corresponding
       dictionary, which will then be passed to a notebook instance."""
    def __init__(self, pathin):
        self.pathin = pathin
        folder, filename = os.path.split(pathin)
        absfolder = os.path.abspath(folder)
        self.absfolder = absfolder
        self.folder = folder



    def read(self):
        f = open(self.pathin,'r')
        strin = f.read()
        f.close()
        self.str = strin


    def clean_string(self):
        if not hasattr(self, 'raw_str'):
            self.raw_str = copy.copy(self.str)
            
        findrepdict = {'null':'\"null\"', \
                       'true':'True', \
                       'false':'False'}
        
        for fnd, rpl in findrepdict.items():
            self.str = self.str.replace(fnd, rpl)

        return self.str

        
    def parse(self):
        if not hasattr(self, 'str'):
            self.read()
        self.clean_string()
        self.dict = eval(self.str)
        
        return self.dict
