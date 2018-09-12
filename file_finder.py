import os, glob, time, pdb
import rwkos

def dont_fitler_me(pathin, skipnames):
    ## junk, test = os.path.split(pathin)
    ## if test == 'fix_underlines.py':
    ##     pdb.set_trace()
        
    if pathin in skipnames:
        #fitler first for fullpaths
        return False
    #check for filename only matches
    folder, filename = os.path.split(pathin)
    return bool(filename not in skipnames)

def find_folder_contents(pathin):
    all_contents = os.listdir(pathin)
    fullpaths = [os.path.join(pathin, item) for item in all_contents]
    return fullpaths


def find_all_files_in_folder(pathin):
    fullpaths = find_folder_contents(pathin)
    files_only = [item for item in fullpaths if os.path.isfile(item)]
    return files_only


def find_subfolders(pathin):
    fullpaths = find_folder_contents(pathin)
    dirs_only = [item for item in fullpaths if os.path.isdir(item)]
    return dirs_only

    

def clean_extlist(extlist):
    extsout = []
    for ext in extlist:
        if ext[0] == '*':
            ext = ext[1:]
        if ext.find('.') != 0:
            ext = '.'+ext
        extsout.append(ext.lower())
    return extsout


def search_for_files_in_folder(pathin, extlist):
    filelist = []
    for ext in extlist:
        if ext.find('.') == -1:
            ext = '.'+ext
        pat1 = os.path.join(pathin, '*'+ext.lower())
        pat2 = os.path.join(pathin, '*'+ext.upper())
        list1 = glob.glob(pat1)
        list2 = glob.glob(pat2)
        filt2 = [item for item in list2 if item not in list1]
        filelist.extend(list1+filt2)
    return filelist


def search_for_files_in_folder_v2(pathin, extlist=None, skiplist=[]):
    if type(extlist) == str:
        extlist = [extlist]
    temp_files = find_all_files_in_folder(pathin)
    if pathin[-1] == '/':
        pathin = pathin[0:-1]
    ## if pathin == '/home/ryan/siue/classes/454/2012/lectures/05_22_12':
    ##     #pdb.set_trace()
    ##     print('')
    ##     print('------------------------')
    ##     print('pathin = ' + pathin)
    ##     print('in search_for_files_in_folder_v2, skiplist=' + str(skiplist))
        
    all_files = [item for item in temp_files if \
                 dont_fitler_me(item, skiplist)]

        
    if not extlist:
        all_files.sort()
        return all_files
    filelist = []
    extlist = clean_extlist(extlist)
    for curfile in all_files:
        fno, ext = os.path.splitext(curfile)
        if ext.lower() in extlist:
            filelist.append(curfile)

    ## if pathin == '/home/ryan/siue/classes/454/2012/lectures/05_22_12':
    ##     #pdb.set_trace()
    ##     print('+++++')
    ##     print('extlist = ' + str(extlist))
    ##     print('filelist = ')
    ##     for item in filelist:
    ##         print(str(item))
    ##     print('+++++')
        
    return filelist

def search_for_pat_in_folder(pat, pathin, extlist=None, skiplist=[]):
    all_files = search_for_files_in_folder_v2(pathin, extlist=extlist, skiplist=skiplist)
    matching_items = [item for item in all_files if item.find(pat) > -1]
    return matching_items


def Search_for_images_in_folder(pathin, extlist=['.jpg','.jpeg'], \
                                skiplist=[]):
    image_list = search_for_files_in_folder_v2(pathin, extlist, \
                                               skiplist=skiplist)
    image_list.sort()
    return image_list



class File_Finder(object):
    def __init__(self, folderpath, extlist=None, \
                 skipdirs=['.comments'], skiplist=[], \
                 skipextlist=None):
       self.folder = folderpath
       if extlist:
           self.extlist = clean_extlist(extlist)
       else:
           self.extlist = extlist
       self.skipdirs = skipdirs
       self.skiplist = skiplist
       self.skipextlist = skipextlist


    def Find_All_Folders(self):
       self.all_folders = rwkos.FindAllSubFolders(self.folder, \
                                                  skipdirs=self.skipdirs)


    def Find_All_Files(self):
       if not hasattr(self, 'all_folders'):
          self.Find_All_Folders()
       self.all_files = []
       for folder in self.all_folders:
           curfiles = search_for_files_in_folder_v2(folder, self.extlist, \
                                                    skiplist=self.skiplist)
           self.all_files.extend(curfiles)
       return self.all_files


    def myext_filter(self, filepath):
        rest, ext = os.path.splitext(filepath)
        return bool(ext not in self.skipextlist)


    def filter_exts(self):
        if self.skipextlist is None:
            filt_files = self.all_files
        else:
            filt_files = filter(self.myext_filter, self.all_files)
        self.filt_files = filt_files
        return self.filt_files
    

    def Find_Top_Level_Files(self, extlist=None):
       if extlist is None:
           extlist = self.extlist
       self.top_level_files = search_for_files_in_folder_v2(self.folder, \
                                                            extlist, \
                                                            skiplist=self.skiplist)
       return self.top_level_files


    def Find_Files_in_One_Subfolder(self, relpath, \
                                    extlist=None, skiplist=[]):
        if extlist is None:
            extlist = self.extlist
        folderpath = os.path.join(self.folder, relpath)
        files = search_for_files_in_folder_v2(folderpath, \
                                              extlist, \
                                              skiplist=skiplist)
        return files
       


class Glob_File_Finder(File_Finder):
    def __init__(self, folderpath, glob_pat='*.rst', \
                 skipdirs=['.comments'], skiplist=[], \
                 skipextlist=None):
        self.folder = folderpath
        self.glob_pat = glob_pat
        self.skipdirs = skipdirs
        self.skiplist = skiplist
        self.skipextlist = skipextlist


    def Find_All_Files(self):
        if not hasattr(self, 'all_folders'):
            self.Find_All_Folders()
            
        self.all_files = []
    
        for folder in self.all_folders:
            print('folder = ' + folder)
            cur_pat = os.path.join(folder, self.glob_pat)
            print('cur_pat = ' + cur_pat)
            curfiles = glob.glob(cur_pat)
            self.all_files.extend(curfiles)


class course_website_archiver(File_Finder):
    """This is a class for finding all the files needed to create a
    read-only archive of a course website.  .xcf and other files along
    with the exclude directories are filtered out (other than xcf, all
    the other extensions are tex/rst related)."""
    def __init__(self, folderpath, extlist=None, \
                 skipdirs=['exclude'], skiplist=[], \
                 skipextlist=['.xcf','.log','.aux','.out',\
                              '.nav','.snm','.vrb','.toc']):
        File_Finder.__init__(self, folderpath, extlist=extlist, \
                             skipdirs=skipdirs, skiplist=skiplist,
                             skipextlist=skipextlist)
        

## class course_website_archiver2(File_Finder):
##     def __init__(self, folderpath, extlist=None, \
##                  skipdirs=['exclude'], skiplist=[], \
##                  skipextlist=['.xcf','.log','.aux','.out',\
##                               '.nav','.snm','.vrb','.toc', \
##                               '.avi']):
##         File_Finder.__init__(self, folderpath, extlist=extlist, \
##                              skipdirs=skipdirs, skiplist=skiplist,
##                              skipextlist=skipextlist)
        
    
multi_media_exts = ['jpg','jpeg','avi','mov','mpeg','mpg', \
                    'gif','xcf','png','nef','cr2','mp4']#cr2 is the Cannon raw ext


class Multi_Media_Finder(File_Finder):
    def __init__(self, folderpath, extlist=multi_media_exts, \
                 skipdirs=['.comments']):
        File_Finder.__init__(self, folderpath, extlist=extlist, \
                             skipdirs=skipdirs)


movie_exts = ['mov','avi','mpeg','mpg','mp4']


class Movie_Finder(File_Finder):
    def __init__(self, folderpath, extlist=movie_exts, \
                 skipdirs=['.comments']):
        File_Finder.__init__(self, folderpath, extlist=extlist, \
                             skipdirs=skipdirs)


def is_thumb_dir(pathin):
    rest, folder = os.path.split(pathin)
    if folder.find('thumbnails') > -1:
        return True
    else:
        return False

    
class Image_Finder(File_Finder):
    def __init__(self, folderpath, extlist=['.jpg', '.jpeg'], \
                 skipdirs=['.comments','thumbnails',\
                           '900by600','screensize'], \
                 skiplist=[]):
        File_Finder.__init__(self, folderpath, extlist=extlist, \
                             skipdirs=skipdirs, skiplist=skiplist)
        

    
    def Find_Images(self):
       self.imagepaths = Search_for_images_in_folder(self.folder, \
                                                     extlist=self.extlist, \
                                                     skiplist=self.skiplist)
       return self.imagepaths


    def Find_Images_mathcing_pat(self, pat):
       if not hasattr(self, 'allimagepaths') or self.allimagepaths==[]:
           self.Find_All_Images()
       matching_items = [item for item in self.allimagepaths if item.find(pat) > -1]
       self.matching_images = matching_items
       return self.matching_images

       

    def FindAllPictureFolders(self):
       self.allfolders = rwkos.FindAllPictureFolders(self.folder, \
                                                     skipdirs=self.skipdirs)


    def Find_All_Images(self):
       if not hasattr(self, 'allfolders'):
          self.FindAllPictureFolders()
       self.allimagepaths = []
       for folder in self.allfolders:
          #if folder == '/home/ryan/siue/classes/mechatronics/2009/lectures/08_26_09':
          #     pdb.set_trace()
          curimages = Search_for_images_in_folder(folder, \
                                                  extlist=self.extlist, \
                                                  skiplist=self.skiplist)
          self.allimagepaths.extend(curimages)
       return self.allimagepaths


    def FindThumbs(self, thumbfolder='thumbnails'):
       self.thumbs = Search_for_images_in_folder(os.path.join(self.folder, thumbfolder))
       return self.thumbs


    def FindScreenSize(self, folder='900by600'):
       self.screensize = Search_for_images_in_folder(os.path.join(self.folder, thumbfolder))
       return self.screensize


    def FindOrphans(self, subfolder='thumbnails'):
       self.Find_Images()
       self.imagenames = FilenamesFromListofPaths(self.imagepaths)
       subfolderpath = os.path.join(self.folder, subfolder)
       subpaths = Search_for_images_in_folder(subfolderpath)
       subnames = FilenamesFromListofPaths(subpaths)
       orphannames = [item for item in subnames if item not in self.imagenames]
       orphans = [os.path.join(subfolderpath, item) for item in orphannames]
       return orphans


    def DeleteOrphans(self, subfolder='thumbnails'):
       orphans = self.FindOrphans(subfolder=subfolder)
       for item in orphans:
          os.remove(item)


    def Find_All_Thumb_Folders(self):
        self.Find_All_Folders()
        self.all_thumb_folders = filter(is_thumb_dir, self.all_folders)
        return self.all_thumb_folders


    def Find_All_Thumbnails(self):
        self.Find_All_Thumb_Folders()
        self.thumb_list = []
        for folder in self.all_thumb_folders:
            cur_list = Search_for_images_in_folder(folder)
            self.thumb_list.extend(cur_list)
        return self.thumb_list
    
            

class PNG_Finder(Image_Finder):
    def __init__(self, folderpath, extlist=['.png'], \
                 skipdirs=['.comments','thumbnails','900by600','screensize']):
        Image_Finder.__init__(self, folderpath, extlist=extlist, \
                              skipdirs=skipdirs)
