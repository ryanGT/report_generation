#!/usr/bin/python
import pyfind, pytexutils, pyp_to_rst
import relpath
import os, copy, pdb, re, shutil
import rwkos

import txt_mixin

from IPython.core.debugger import Pdb

reload(pyp_to_rst)

import restify

#htmlpaths = pyfind.findall(root1, '*.html')
#relpaths = [relpath.relpath(item, root1) for item in htmlpaths]

skipfolders = ['ui','figs','pics']
ws = ' '*4


link_dec = pyp_to_rst.link_decorator2()


def inskipfolders(pathin, sfolders=None):
   path, folder = os.path.split(pathin)
   if sfolders is None:
      sfolders = skipfolders
   return bool(folder in sfolders)


def infolder(pathin, folder):
    path, item = os.path.split(pathin)
    return path == folder


def find_sub_dirs(pathin, sfolders=None):
    everything = os.listdir(pathin)
    full_paths_to_everything = [os.path.join(pathin, item) \
                                for item in everything]
    all_dirs = [item for item in full_paths_to_everything \
                if os.path.isdir(item)]
    subfolders = [item for item in all_dirs \
                  if not inskipfolders(item, sfolders=sfolders)]
    return subfolders


def rel_list(listin, basepath):
    listout = [relpath.relpath(item, basepath) \
               for item in listin]
    return listout


class subfolder_abstract(object):
    """This is a sort of abstract class for subfolder and main_index
    to both use."""
    def find_subfolders(self):
        print('in find_subfolders, self.skipfolders='+str(self.skipfolders))
        self.subfolders = find_sub_dirs(self.abspath, self.skipfolders)
        self.subfolders.sort()
        self.subfolders_rel = rel_list(self.subfolders, self.abspath)
        self.folders = [self.subclass(item, self.basepath, self.rel_link_paths, \
                                      index_name=self.index_name,
                                      subclass=self.subclass,
                                      myskips=self.myskips) \
                        for item in self.subfolders]


    def __init__(self, index_name = 'index.html', title=None, \
                 subclass=None, myskips=[], level=0):
        self.level = level
        self.index_name = index_name
        self.title = title
        self.subclass = subclass
        self.toplinks = [item for item in self.rel_link_paths \
                         if infolder(item, self.relpath)]
        self.toplinks =[item for item in self.toplinks \
                        if item not in skip_files]
        self.myskips = myskips
        self.skipfolders = skipfolders + myskips
        self.find_subfolders()


    def copy_tree(self, newbase):
       newfolder = os.path.join(newbase, self.relpath)
       if not os.path.exists(newfolder):
          os.mkdir(newfolder)
       for item in self.toplinks:
          src = os.path.join(self.basepath, item)
          dst = os.path.join(newbase, item)
          if not os.path.exists(dst):
             shutil.copy2(src, dst)
       for folder in self.folders:
          folder.copy_tree(newbase)




class subfolder(subfolder_abstract):
    def __init__(self, abspath, basepath, rel_link_paths, level=1, \
                 index_name='index.html', subclass=None, title=None,
                 myskips=[]):
        self.abspath = abspath
        rest, self.name = os.path.split(self.abspath)
        self.basepath = basepath
        if subclass is None:
           subclass = subfolder
        self.relpath = relpath.relpath(abspath, basepath)
        self.rel_link_paths = rel_link_paths
        self.mylinks = [item for item in self.rel_link_paths \
                        if item.find(self.relpath+os.sep) == 0]

        subfolder_abstract.__init__(self, index_name=index_name, \
                                    title=title, subclass=subclass, \
                                    myskips=myskips, level=level)
        self.topnavlinks = [relpath.relpath(item, self.relpath) for item in self.toplinks]#used for sidebar navigation in Krauss blog


    def has_link(self):
        if self.mylinks or self.toplinks:
            return True
        for item in self.folders:
            if item.has_link():
                return True
        return False


    def rst_toplinks(self):
       listout = []
       for link in self.toplinks:
          junk, nameonly = os.path.split(link)
          if not rwkos.amiLinux():
             link = link.replace('\\','/')
          curline = self.level*ws+'- `%s <%s>`_'% (nameonly, link)
          listout.append(curline)
       return listout


    def to_rst(self):
       if not self.has_link():
          return []
       listout = []
       if self.level==1:
          l2_dec = pyp_to_rst.rst_section_level_2()
          listout.extend(l2_dec(self.name))
       else:
          line1 = (self.level-1)*ws+'- '+self.name
          listout.append(line1)
       listout.extend(self.rst_toplinks())
       listout.append('')
       for folder in self.folders:
          listout.extend(folder.to_rst())
          listout.append('')
       return listout

skip_files = ['index.html','myrst2s5.py']

def skip_filter(pathin):
   folder, name = os.path.split(pathin)
   return name not in skip_files


class rst_saver_mixin(object):
   def get_main_dir(self):
       if hasattr(self, 'main_dir'):
          my_dir = self.main_dir
       elif hasattr(self, 'abspath'):
          my_dir = self.abspath
       return my_dir


   def save_rst(self):
       if not hasattr(self, 'rst'):
          self.to_rst()
       fno, ext = os.path.splitext(self.index_name)
       self.rst_name = fno+'.rst'
       my_dir = self.get_main_dir()
       self.rst_path = os.path.join(my_dir, self.rst_name)
       pytexutils.writefile(self.rst_path, self.rst)


   def rst2html(self):
      my_dir = self.get_main_dir()
      fno, ext = os.path.splitext(self.index_name)
      rst_name = fno+'.rst'
      rst_path = os.path.join(my_dir, rst_name)
      html_path = os.path.join(my_dir, self.index_name)
      if os.path.exists(rst_path):
         curdir = os.getcwd()
         print('curdir='+curdir)
         try:
            if rwkos.amiLinux():
               basecmd = 'rst2html'
            else:
               basecmd = 'python C:\\Python25\\Scripts\\rst2html.py'
            cmd = basecmd+' %s %s' % (rst_name, self.index_name)
            #print(cmd)
            print('switching to '+my_dir)
            os.chdir(my_dir)
            os.system(cmd)
         finally:
            print('switching back to '+curdir)
            os.chdir(curdir)



#-----------------------------------------
class main_index(subfolder, rst_saver_mixin):
    def __init__(self, main_dir, pats=['*.html','*.pdf'], \
                 index_name = 'index.html', title=None, header=[], \
                 subclass=subfolder, myskips=[]):
        self.main_dir = main_dir
        self.basepath = main_dir
        self.abspath = main_dir
        self.relpath = ''
        self.pats = pats
        self.header = header
        self.full_link_paths = []
        for pat in self.pats:
            curpaths = pyfind.findall(self.main_dir, pat)
            self.full_link_paths.extend(curpaths)
        self.full_link_paths.sort()#need to filter myrst2s5.py
        all_links = copy.copy(self.full_link_paths)
        self.full_link_paths = filter(skip_filter, all_links)
        self.rel_link_paths = [relpath.relpath(item, self.main_dir) \
                               for item in self.full_link_paths]
        subfolder_abstract.__init__(self, index_name=index_name, \
                                    title=title, subclass=subclass, \
                                    myskips=myskips, level=0)



    def to_rst(self):
       listout = []
       if self.title:
          title_dec = pyp_to_rst.rst_section_level_1()
          listout.extend(title_dec(self.title))
       if self.toplinks:
          listout.extend(self.rst_toplinks())
          listout.append('')
       for folder in self.folders:
          listout.extend(folder.to_rst())
          listout.append('')
       self.rst = listout


    def rst_to_html(self):
       if not hasattr(self, 'rst_path'):
          self.save_rst()
       curdir = os.getcwd()
       print('curdir='+curdir)
       if rwkos.amiLinux():
          basecmd = 'rst2html'
       else:
          basecmd = 'python C:\\Python25\\Scripts\\rst2html.py'
       cmd = basecmd+' %s %s' % (self.rst_name, self.index_name)
       print(cmd)
       if self.main_dir:
          print('switching to '+self.main_dir)
          os.chdir(self.main_dir)
       os.system(cmd)
       if curdir:
          print('switching back to '+curdir)
          os.chdir(curdir)




class rst_subfolder(subfolder, rst_saver_mixin):
   def rst_one_link(self, link, name=None):
      if name is None:
         junk, name = os.path.split(link)
      if not rwkos.amiLinux():
             link = link.replace('\\','/')
      #curline = self.level*ws+'- `%s <%s>`_'% (name, link)
      curline = '- `%s <%s>`_'% (name, link)
      return curline


   def rst_link_one_folder(self, folder):
      abspath = folder.abspath
      index_path = os.path.join(abspath, 'index.html')
      rel_index_path = relpath.relpath(index_path, self.get_main_dir())
      folder_path, folder_name = os.path.split(abspath)
      return self.rst_one_link(rel_index_path, folder_name)


   def rst_folders(self):
      self.rst = []
      title_dec = pyp_to_rst.rst_section_level_1()
      if not self.title:
         self.title = self.name
      self.rst.extend(title_dec(self.title))

      for folder in self.filtered_folders:
         folder.to_rst()
         self.rst.append(self.rst_link_one_folder(folder))
      return self.rst


   def filter_subs(self):
      self.filtered_folders = [item for item in self.folders \
                               if item.has_link()]


   def to_rst(self, *args, **kwargs):
      self.filter_subs()
      if len(self.toplinks) == 1:
         mylink = self.toplinks[0]
         folder, filename = os.path.split(mylink)
         in_path = os.path.join(self.abspath, filename)
         out_path = os.path.join(self.abspath, self.index_name)
         shutil.copy2(in_path, out_path)
      elif len(self.toplinks) > 1:
         raise StandardError, \
               "Found a folder with more than one index file:" + \
               str(self.toplinks)
      else:
         self.rst_folders()
         self.save_rst()


   def rst2html(self):
      rst_saver_mixin.rst2html(self)
      for folder in self.filtered_folders:
         folder.rst2html()


class rst_main_index(rst_subfolder, main_index):
   """This class exists to help me make a website out of a directory
   with greater flexibility than main_index.  The main idea is that
   index_*.rst files will be put in directories that I want to show
   up.  Those files will be created by hand so that only the things I
   want in the website show up.

   This main class will search for all the index_*.rst files in the
   subfolders and create a web site tree that ultimately links to
   those files."""
   def __init__(self, main_dir, pats=['index_*.rst'], \
                index_name = 'index.html', title=None, \
                header=[], subclass=rst_subfolder):
       main_index.__init__(self, main_dir, pats=pats, index_name=index_name, \
                           title=title, header=header, subclass=subclass)




months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug',\
          'Sep','Oct','Nov','Dec']


day_pat = '[A-z]*_(\\d+)_\\d+.html'
day_re = re.compile(day_pat)


def dict_to_rst(dictin, prestr=''):
   keys = dictin.keys()
   keys.sort()
   rst_list = []
   for key in keys:
      target = dictin[key]
      cur_rst = link_dec(target, key)
      rst_list.append(prestr+cur_rst)
   return rst_list


def rst_to_html_list(listin, clean=True):
   str_in = '\n'.join(listin)
   str_out = restify.reSTify_part(str_in)
   listout = str_out.split('\n')
   if clean:
      listout = [item.rstrip() for item in listout]
   return listout


class blog_day(txt_mixin.txt_file_with_list):
   def replace_navbar(self, link_list, save=True):
      start = '<div id="sidebar">'
      end = '</div>'
      inds = self.findall(start)
      startind = inds[0]
      stopind = self.findnext(end, startind+1)+1
      listout = [start]+link_list+[end]
      self.list[startind:stopind] = listout
      self.writefile(self.pathin)


class blog_month(subfolder):
    def __init__(self, abspath, basepath, rel_link_paths, parent=None, level=2):
       subfolder.__init__(self, abspath, basepath, rel_link_paths, level=level)
       self.parent = parent
       self.day_rel_paths = self.mylinks
       self.day_abs_paths = [os.path.join(self.basepath, item) for item in self.day_rel_paths]
       self.days = [blog_day(item) for item in self.day_abs_paths]
       self.day_links = self.topnavlinks
       self.days.sort()
       self.first_day = self.day_rel_paths[0]
       day_keys = []
       for link in self.day_links:
          q = day_re.search(link)
          if q:
             day_keys.append(q.group(1))
          else:
             key, ext = os.path.splitext(link)
             day_keys.append(key)
       self.day_dict = dict(zip(day_keys, self.day_links))


    def dict_to_rst(self):
       self.rst_links = dict_to_rst(self.day_dict, prestr='- ')


    def gen_nav(self, firstdays_dict):
       navlist = []
       self.dict_to_rst()
       for month in months:
          if firstdays_dict.has_key(month):
             month_link = firstdays_dict[month]
             month_rel_link = relpath.relpath(month_link, self.relpath)
             month_rel_link = month_rel_link.replace('\\','/')
             navlist.append(link_dec(month_rel_link, month))
             navlist.append('')
             if month == self.name:
                navlist.append('')
                navlist.extend(self.rst_links)
                navlist.append('')
       self.navlist = rst_to_html_list(navlist)
       return self.navlist


    def replace_nav(self):
       if not hasattr(self, 'navlist'):
          if self.parent:
             self.gen_nav(self.parent.firstdays_dict)
          else:
             raise StandardError, 'You cannot call replace_nav until after you call gen_nav'
       for day in self.days:
          day.replace_navbar(self.navlist)



class blog_year(subfolder):
    def __init__(self, abspath, basepath, rel_link_paths, level=1):
       subfolder.__init__(self, abspath, basepath, rel_link_paths, level=level)
       self.months = [blog_month(item, self.basepath, self.rel_link_paths, \
                                 level=self.level+1, parent=self) \
                        for item in self.subfolders]

       self.month_links = [relpath.relpath(item, self.abspath) for item in self.subfolders]
       self.first_day_links = [item.first_day for item in self.months]
       keys = [item.name for item in self.months]
       vals = [item.first_day for item in self.months]
       self.firstdays_dict = dict(zip(keys, vals))


    def replace_nav(self):
       for month in self.months:
          month.replace_nav()




class blog_nav_index(main_index):
    def __init__(self, main_dir, pats=['*.html','*.pdf'], index_name = 'index.html', title=None, header=[]):
       main_index.__init__(self, main_dir, pats=pats, index_name=index_name, \
                           title=title, header=header)
       self.years = [blog_year(item, self.main_dir, self.rel_link_paths) \
                        for item in self.subfolders]

    def replace_nav(self):
       for year in self.years:
          year.replace_nav()


def copy_for_ken():
   myskips = ['uncropped','hibbeler_solutions','hibbeler']
   mypath = '/home/ryan/siue/classes/AdvDynamics/2007/'
   my_index = main_index(mypath, title='ME 530 Advanced Dynamics 2007',
                         pats=['*.pdf'], myskips=myskips)
   newbase = '/home/ryan/for_ken/'
   nb1 = os.path.join(newbase, '2007')

   mypath2 = '/home/ryan/siue/classes/AdvDynamics/2008/'
   my_index2 = main_index(mypath2, title='ME 530 Advanced Dynamics 2008',
                         pats=['*.pdf'], myskips=myskips)
   nb2 = os.path.join(newbase, '2008')
   my_index.copy_tree(nb1)
   my_index2.copy_tree(nb2)
   return my_index, my_index2


def create_for_ken():
    myskips = ['uncropped','hibbeler_solutions','hibbeler']
    newbase = '/home/ryan/for_ken/'
    nb1 = os.path.join(newbase, '2007')
    nb2 = os.path.join(newbase, '2008')
    my_index = main_index(nb1, title='ME 530 Advanced Dynamics 2007',
                          pats=['*.pdf'], myskips=myskips)
    my_index2 = main_index(nb2, title='ME 530 Advanced Dynamics 2008',
                         pats=['*.pdf'], myskips=myskips)
    my_index.rst_to_html()
    my_index2.rst_to_html()


if __name__ == '__main__':
    roots = ['/home/ryan/siue/classes/482/lectures', \
             '/home/ryan/siue/classes/484/lectures', \
             '/home/ryan/siue/classes/mechatronics/2008/lectures/', \
             '/home/ryan/siue/classes/Mobile_Robotics/2008/in_class_project/']
    titles = ['ME 482 - Mechanical Engineering Design I', \
              'ME 482 - Mechanical Engineering Design II', \
              'ME 458 - Mechatronics', \
              'Mobile Robotics']

    mypats = ['*.html','*.pdf','*.py']
    for root, title in zip(roots, titles):
       cur_root = rwkos.FindFullPath(root)
       my_index = main_index(cur_root, title=title, pats=mypats)
       my_index.rst_to_html()



