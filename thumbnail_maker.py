import Image, os, glob, pdb

from IPython.Debugger import Pdb
from numpy import mod
import file_finder
reload(file_finder)
from file_finder import Search_for_images_in_folder, Image_Finder

import rwkos
reload(rwkos)

skipfolders = ['html','thumbnails','blog_size','resized', \
               '.comments','900by600','cache','screensize', \
               'exclude']

skipnames = ['index.html']

thumbheader = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<style type="text/css">
img {
border:2px;
margin:10px;
margin-bottom:2px;
border-color: black;
border-style: solid;
}

img.h90{
height:90%;
} 
img.w95{
width:95%;
} 
</style>
<title>%TITLE%</title>
</head>
<body>
"""

tail = """</body>
</html>
"""

owntemplate = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<!single image:%FILENAME%>
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
  <title>%TITLE%</title>
<style type="text/css">
img {
border:2px;
margin:10px;
margin-bottom:2px;
}

img.h90{
height:90%;
} 
img.w95{
width:95%;
} 
</style>
</head>
<h3>%FILENAME%</h3>
<body>
<img src="../%FILENAME%" alt="%FILENAME%"   class="h90"><br>
<a href="../index.html">up</a>
</body>
</html>
"""


newowntemplate = """<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<!single image:%FILENAME%>
<html>
<head>
  <meta content="text/html; charset=ISO-8859-1"
 http-equiv="content-type">
  <title>%TITLE%</title>
<style type="text/css">  
img {
border:2px;
margin:10px;
margin-bottom:2px;
border-color: black;
border-style: solid;
}


img.h90{
height:90%;
} 
img.w95{
width:95%;
} 
</style>
</head>
<body>
<img src="../%SCREENSIZEFOLDER%/%FILENAME%" alt="%FILENAME%" class="h90"><br>
"""

#What if my Python picture database gui was just an HTML window (probably two) with the OnClick hyperlink event overriden?
#   -> might not look super cool
#   -> could be really effective
#   -> would maintain consistant feel from viewing and making captions and ratings and things


def inskipfolders(pathin):
   path, folder = os.path.split(pathin)
   return bool(folder in skipfolders)


def inskipnames(pathin):
   path, folder = os.path.split(pathin)
   return bool(folder in skipnames)
   
   
def pictsindir(folder, exts=['*.jpg']):
   """Find all the pictures in folder, not looking in subfolders, but
   checking for the upper and lower cases versions of exts."""
   #pdb.set_trace()
   picts = []
   for pat in exts:
      if pat[0] == '.':
         pat = '*'+pat
      curfiles = glob.glob(os.path.join(folder, pat.lower()))
      list2 = glob.glob(os.path.join(folder, pat.upper()))
      filt2 = [item for item in list2 if item not in curfiles]
      picts += curfiles
      picts += filt2
   return picts


def haspicts(pathin, exts=['*.jpg']):
   """Check to see if pathin or any of its subfolders contains any
   pictures by walking down the directory tree and calling pictsindir
   on each subfolder."""
   #note that glob.glob of '*'+os.sep+'*.JPG' could also work (you
   #would also need just '*.JPG' to get the top level ones
   hasany = False
   for root, dirs, files in os.walk(pathin):
      print('root='+str(root))
      curpicts = pictsindir(root, exts)
      if curpicts:
         hasany = True
         break
   return hasany


def _resize(pathin, size):
   """Resize using Image.thumbnail, which modifies the image in place
   and preserves the aspect ratio.  Image.ANTIALIAS is used."""
   img = Image.open(pathin)
   img.thumbnail(size, Image.ANTIALIAS)
   return img
   
      
def _resize_older_slower(image, maxSize, method = 3):
   """ im = maxSize(im, (maxSizeX, maxSizeY), method = Image.BICUBIC)

   Resizes a PIL image to a maximum size specified while maintaining
   the aspect ratio of the image.  Similar to Image.thumbnail(), but
   allows usage of different resizing methods and does NOT modify the
   image in place."""

   imAspect = float(image.size[0])/float(image.size[1])
   outAspect = float(maxSize[0])/float(maxSize[1])

   if imAspect >= outAspect:
       #set to maxWidth x maxWidth/imAspect
       return image.resize((maxSize[0], int((float(maxSize[0])/imAspect) +
0.5)), method)
   else:
       #set to maxHeight*imAspect x maxHeight
       return image.resize((int((float(maxSize[1])*imAspect) + 0.5),
maxSize[1]), method)


class Thumbnail:
   def __init__(self, pathin, thumbdir='thumbnails', \
                size=[300,200], quality=85, outext='.jpg'):
      infolder, filename = os.path.split(pathin)
      self.pathin = pathin
      self.filename = filename
      self.mainfolder = infolder
      outfolder = os.path.join(infolder, thumbdir)
      self.thumbfolder = outfolder
      outpath = os.path.join(outfolder, filename)
      pne, oldext = os.path.splitext(outpath)
      outpath = pne+outext
      self.thumbpath = outpath
      self.size = size
      self.quality = quality

      
   def MakeThumbfolder(self):
      folderexists = os.path.exists(self.thumbfolder)
      if not folderexists:
         os.mkdir(self.thumbfolder)
      return not folderexists


   def Exists(self):
      return os.path.exists(self.thumbpath)
         

   def Resize(self):
      """Resize using Image.thumbnail, which modifies the image in
      place and preserves the aspect ratio.  Image.ANTIALIAS is used."""
      self.img = Image.open(self.pathin)
      print('In thumbnail_maker.py, Thumbnail.Resize,')
      print('self.size='+str(self.size))
      self.img.thumbnail(self.size, Image.ANTIALIAS)
      return self.img


   def Save(self):
      if not hasattr(self, 'img'):
         self.Resize()
      self.MakeThumbfolder()
      self.img.save(self.thumbpath, quality=self.quality)


   def ResizeAndSave(self, force=False, verbosity=1, ifnewer=True):
      skip = False
      if self.Exists():
         if force:
            skip = False
         elif ifnewer:
            #update the thumbpath if the main image is newer
            thumb_mtime = os.path.getmtime(self.thumbpath)
            main_mtime = os.path.getmtime(self.pathin)
            if main_mtime > thumb_mtime:
               print('updating thumbnail: %s' % self.pathin)
               skip = False
            else:
               skip = True
         else:
            skip = True
               
      if skip:
         if verbosity > 0:
            print('skipping: '+self.pathin)
         #do nothing
         return
      self.Resize()
      self.Save()
      return self.img
      

class CacheImage(Thumbnail):
   """This class is for creating a caching screen sized images
   (assumed 900 by 600) for displaying 'fullsize' on the screen.
   These pictures should show nicely on the screen, while being much
   smaller than actual 8-10 megapixel images, thereby reducing network
   transmission time.

   For now, only the default size and thumbdir name are different."""
   def __init__(self, pathin, thumbdir='900by600', \
                size=[900,600], quality=90):
      Thumbnail.__init__(self, pathin, thumbdir=thumbdir, \
                         size=size, quality=quality)


class DVDImage(Thumbnail):
   """This class is for creating images for DVD slideshows
   (assumed 720 by 480)"""

   def __init__(self, pathin, thumbdir='DVD_size', \
                size=[720,480], quality=95):
      Thumbnail.__init__(self, pathin, thumbdir=thumbdir, \
                         size=size, quality=quality)

def resize_one(pathin, size=[300,200], thumbdir='thumbnails', force=False, verbose=0):
    """Resize image whose path is pathin to the size size, preserving
    the aspect ratio.  Save the resized image in the folder whose
    relative path is thumbdir.  If force is False, do not recreate the
    resized image if it already exists."""
    mythumb = Thumbnail(pathin, thumbdir)
    mythumb.MakeThumbfolder()
    if force or (not mythumb.Exists()):
       if verbose > 0:
          print('creating thumbnail for:'+outpath)
       #scaled = _resize(pathin, size)
       #scaled.save(outpath, qualtiy=85)
       mythumb.ResizeAndSave()
    

def HTML_one_thumb(filename, htmldir='html', thumbdir='thumbnails'):
    temp = """
        <TD>
        <a href="%HTMLPATH%">
        <img src="%THUMBPATH%"><br>
        %FILENAME%
        </a>
        </TD>"""
    fno, ext = os.path.splitext(filename)
    htmlpath = os.path.join(htmldir, fno+'.html')
    thumbpath = os.path.join(thumbdir, fno+'.jpg')
##     if not os.path.exists(thumbpath):
##        thumbpath = os.path.join(thumbdir, fno+'.JPG')
    outstr = temp.replace('%HTMLPATH%', htmlpath)
    outstr = outstr.replace('%THUMBPATH%', thumbpath)
    outstr = outstr.replace('%FILENAME%', filename)
    return outstr


class HTMLImage:
   def __init__(self, pathin, prevfile=None, nextfile=None, \
                screensizedir='screensize'):
      self.jpegpath = pathin
      self.pathin = pathin
      self.folder, self.jpegname = os.path.split(self.jpegpath)
      self.fno, ext = os.path.splitext(self.jpegname)
      self.prevfile = prevfile
      self.nextfile = nextfile
      self.screensizedir = screensizedir
      

   def GenerateThumbnail(self, size=[300,200], force=False, **kwargs):
      resize_one(self.jpegpath, size=size, force=force, **kwargs)


   def Save_HTML(self):
      #print('writing '+self.htmlpath)
      f = open(self.htmlpath, 'w')
      f.write(self.html_str)
      f.close()


   def GenerateOwnHTML(self, folder='html', **kwargs):
      #need next and previous links
      self.htmlfolder = os.path.join(self.folder,folder)
      if not os.path.exists(self.htmlfolder):
         os.mkdir(self.htmlfolder)
      self.htmlname = self.fno+'.html'
      self.htmlpath = os.path.join(self.htmlfolder, self.htmlname)
      myhtml = owntemplate
      myhtml = myhtml.replace('%FILENAME%', self.jpegname)
      myhtml = myhtml.replace('%TITLE%', self.jpegname)
      #print('writing '+self.htmlpath)
      self.html_str = myhtml

      
      
   def GenerateHTML(self, **kwargs):
      htmlstr = HTML_one_thumb(self.jpegname, **kwargs)
      return htmlstr

                             

class HTMLImage2(HTMLImage):
   def __init__(self, pathin, screensizedir='screensize', ext='.jpg', \
                prevfile=None, nextfile=None, htmlfolder='html'):
      pne, oldext = os.path.splitext(pathin)
      self.rawpath = pathin
      junk, self.rawname = os.path.split(pathin)
      pathjpg = pne+ext
      HTMLImage.__init__(self, pathjpg, prevfile, nextfile)
      self.screensizedir = screensizedir 
      self.htmlfolder = htmlfolder


   def _wrap_TD(self, item, align=None, width=None):
      start_str = '<TD'
      if align:
         start_str += ' align=%s' % align
      if width:
         start_str += ' width=%s' % width
      start_str += '>'
      return start_str +' %s </TD>' % item


   def _to_html_path(self, linkpath):
      """Assuming linkpath is the path to the fullsize png or jpg,
      make it the relative path to the html file."""
      folderpath, filename = os.path.split(linkpath)
      onelevelup, foldername = os.path.split(folderpath)
      if foldername != self.htmlfolder:
         foldername = os.path.join(foldername, self.htmlfolder)
      htmlfolder = os.path.join(onelevelup, foldername)
      fne, ext = os.path.splitext(filename)
      htmlfilename = fne+'.html'
      #pathout = os.path.join(htmlfolder, htmlfilename)
      pathout = htmlfilename
      return pathout
   

   def _wrap_link(self, linkpath, text, **kwargs):
      htmlpath = self._to_html_path(linkpath)
      return self._wrap_TD('<a href="%s">%s</a>' % (htmlpath, text), \
                           **kwargs)


   def _gen_bottom_nav_table(self):
      navlist = ["<TABLE width=875>", "<TR align=center>"]
      mywidth = '25%'
      if self.prevfile:
         navlist.append(self._wrap_link(self.prevfile, 'previous', \
                                        align='LEFT', width=mywidth))
      else:
         navlist.append(self._wrap_TD(""))
      navlist.append(self._wrap_TD('<a href="../index.html">up</a>', \
                                   align="CENTER", width=mywidth))
      navlist.append(self._wrap_TD('<a href="../%s">fullsize</a>' % \
                                   self.rawname, \
                                   align="CENTER", width=mywidth))
      if self.nextfile:
         navlist.append(self._wrap_link(self.nextfile, 'next', \
                                        align='RIGHT', width=mywidth))
      else:
         navlist.append(self._wrap_TD(""))
      
      navlist.append('</TR>')
      navlist.append('</TABLE>')
      navstr = '\n'.join(navlist)
      self.navlist = navlist
      return navstr
      

      
   def GenerateOwnHTML(self, folder='html', **kwargs):
      #need next and previous links
      self.htmlfolder = os.path.join(self.folder,folder)
      if not os.path.exists(self.htmlfolder):
         os.mkdir(self.htmlfolder)
      self.htmlname = self.fno+'.html'
      self.htmlpath = os.path.join(self.htmlfolder, self.htmlname)
      myhtml = newowntemplate
      myhtml = myhtml.replace('%FILENAME%', self.jpegname)
      myhtml = myhtml.replace('%TITLE%', self.jpegname)
      myhtml = myhtml.replace('%SCREENSIZEFOLDER%',
                              self.screensizedir)
      navstr = self._gen_bottom_nav_table()
      myhtml += '\n'
      myhtml += navstr
      myhtml += '\n'      
      myhtml += tail
      self.html_str = myhtml


class css_line_delete_mixin:
   def delete_list_from_str(self, css_string, delete_list=None):
      if delete_list is None:
         delete_list = ['border-color: black;','border-style: solid;']
      for item in delete_list:
         css_string = css_string.replace(item+'\n', '')
      return css_string
   

class HTMLImage3(HTMLImage2, css_line_delete_mixin):
   def GenerateOwnHTML(self, folder='html', **kwargs):
      HTMLImage2.GenerateOwnHTML(self, folder=folder, **kwargs)
      self.html_str = self.delete_list_from_str(self.html_str)

      

def FilenamesFromListofPaths(listin):
   listout = [os.path.split(item)[1] for item in listin]
   return listout
       

#######################
#
#  Use Image_Finder to make a CacheImageCreator
#
#######################

jpgextlist = ['.jpg','.jpeg']
myskipdirs=['.comments','thumbnails','900by600',\
            'screensize','exclude']

class ImageResizerDir(Image_Finder):
   """A class that finds all the JPG's in the directory and its
   children and resizes them, creating either thumbnails or
   cacheimages (900by600)."""
   def __init__(self, folderpath, resizeclass=Thumbnail, \
                resizefolder='thumbnails', size=[300,200], \
                extlist=jpgextlist, skipdirs=myskipdirs):
      Image_Finder.__init__(self, folderpath, extlist=extlist, \
                            skipdirs=skipdirs)
      self.folder = folderpath
      self.resizeclass = resizeclass
      self.resizefolder = resizefolder
      self.size = size
      self.kwargs = {'size':self.size,'thumbdir':self.resizefolder}


   def ResizeTopDir(self, verbosity=1):
      self.Find_Images()
      self.images = [self.resizeclass(item, **self.kwargs) \
                     for item in self.imagepaths]
      for item in self.images:
         if verbosity > 0:
            print('resizing: '+item.pathin)
         item.ResizeAndSave()


   def ResizeAll(self, verbosity=1):
      self.Find_All_Images()
      self.allimages = [self.resizeclass(item, **self.kwargs) \
                        for item in self.allimagepaths]
      for item in self.allimages:
         if verbosity > 0:
            print('resizing: '+item.pathin)
         item.ResizeAndSave()
         item.img = None


   def FilterExisting(self):
      self.Find_Images()
      self.resizepath = os.path.join(self.folder, self.resizefolder)
      existing = Search_for_images_in_folder(self.resizepath)
      allnames = [os.path.split(item)[1] for item in self.imagepaths]
      existingnames = [os.path.split(item)[1] for item in existing]
      self.newjpegnames = [item for item in allnames if item not in existingnames]
      self.newjpegs = [os.path.join(self.folder, item) for item in self.newjpegnames]
      return self.newjpegs


   def ResizeNew(self, verbosity=1):
      if not hasattr(self, 'newjpegs'):
         self.FilterExisting()
      self.newimages = [self.resizeclass(item, **self.kwargs) for item in self.newjpegs]
      for item in self.newimages:
         if verbosity > 0:
            print('resizing: '+item.pathin)
         item.ResizeAndSave()

      
class ImageResizer900by600(ImageResizerDir):
   def __init__(self, topdir, resizeclass=CacheImage, \
                resizefolder='900by600', size=[900,600], \
                extlist=jpgextlist):
      ImageResizerDir.__init__(self, topdir, resizeclass=resizeclass, \
                               resizefolder=resizefolder, size=size, \
                               extlist=extlist)


class ImageResizerDVD(ImageResizerDir):
   def __init__(self, topdir, resizeclass=DVDImage, \
                resizefolder='DVD_size', size=[720,480], \
                extlist=jpgextlist):
      ImageResizerDir.__init__(self, topdir, resizeclass=resizeclass, \
                               resizefolder=resizefolder, size=size, \
                               extlist=extlist)

   

class ThumbNailPage(Image_Finder):
   def __init__(self, folder, title=None, body=None, \
                htmldir='html', thumbdir='thumbnails', \
                extlist=jpgextlist, contentlist=[], \
                HTMLclass=HTMLImage, skipdirs=myskipdirs, \
                screensizedir='screensize', \
                bodyin=[]):
      Image_Finder.__init__(self, folder, extlist=extlist, \
                            skipdirs=skipdirs)
      self.folder = folder
      self.header = thumbheader.replace('%TITLE%', str(title))
      self.extlist = extlist
      self.body = bodyin
      self.contentlist = contentlist
      #print('bodyin = '+str(bodyin))
      self.htmldir = htmldir
      self.thumbdir = thumbdir
      if title:
         self.body.insert(0,'<h1>'+title+'</h1>')
      if body:
         self.body.append(body+'<br>')
      self.tail = tail
      self.HTMLclass = HTMLclass
      self.screensizedir = screensizedir


   def FindImages(self):
       self.Find_Images()#self.imagepaths is set by self.Find_Images
       N = len(self.imagepaths)
       self.images = []
       for i in range(N):
          if i == 0:
             prevfile = None
          else:
             prevfile = self.imagepaths[i-1]
          if i < N-1:
             nextfile = self.imagepaths[i+1]
          else:
             nextfile = None
          curpath = self.imagepaths[i]
          curimage = self.HTMLclass(curpath, prevfile=prevfile, \
                                    nextfile=nextfile, \
                                    screensizedir=self.screensizedir)
          self.images.append(curimage)
       return self.imagepaths


   def GenerateThumbnails(self, size=[300,200], **kwargs):
       if not hasattr(self, 'images'):
          self.FindImages()
       for image in self.images:
          image.GenerateThumbnail(size=size, **kwargs)


   def GenerateHTMLs(self, **kwargs):
       if not hasattr(self, 'images'):
          self.FindImages()
       for image in self.images:
          image.GenerateOwnHTML(**kwargs)
          image.Save_HTML()
      

   def AddThumbNailTable(self, **kwargs):
       if not hasattr(self, 'images'):
          self.FindImages()
       if not self.images:
          return None
       self.table=['<TABLE>']
       out = self.table.append
       extd = self.table.extend
       n = 2#number of images per row
       for i, image in enumerate(self.images):
          if mod(i, n) == 0:
             out('<TR align=center>')
          elif mod(i,n)-1 == n:
             out('</TR>')
          out(image.GenerateHTML(**kwargs))
       out('</TABLE>')
       self.body.extend(self.table)


   def Add_bottom_link(self, br=True):
      if br:
         self.body.append('<br>')
      self.body.append('<a href="../index.html">up</a>')


   def _build_body_str(self):
      self.bodystr = '\n'.join(self.body)
      outstr = self.header + self.bodystr + self.tail
      self.full_bodystr = outstr
      return self.full_bodystr
      
      
   def ToFile(self, name='index.html'):
      outstr = self._build_body_str()
      outpath = os.path.join(self.folder,name)
      f = open(outpath, 'w')
      f.write(outstr)
      f.close()


class DirectoryPage(ThumbNailPage):
   def FindSubFolders(self):
      pat = os.path.join(self.folder,'*')
      everything = glob.glob(pat)
      subfolders = [item for item in everything if os.path.isdir(item)]
      filtfolders = [item for item in subfolders if \
                     haspicts(item)]
      otherfolders = [item for item in subfolders if \
                      haspicts(item, self.contentlist)]
      new_other = [item for item in otherfolders if item not in filtfolders]
      filtfolders += new_other
      filt2 = [item for item in filtfolders if not inskipfolders(item)]
      self.filtfoldersabs = filt2
      self.filtfolders = []
      for item in self.filtfoldersabs:
         junk, curfolder = os.path.split(item)
         self.filtfolders.append(curfolder)
      self.filtfolders.sort()


   def AddSubFolderLinks(self):
      if not hasattr(self, 'filtfolders'):
         self.FindSubFolders()
      out = self.body.append
      if self.filtfolders:
         out('<h2>Folders:</h2>')
         out('<ul>')
         for item in self.filtfolders:
            self.body.append('<li> <a href=%s/index.html>%s</a></li>'%(item,item))
         out('</ul>')
      return self.body


   def FullCreate(self):
      self.FindSubFolders()
      self.AddSubFolderLinks()
      self.FindImages()
      self.GenerateThumbnails()
      self.GenerateHTMLs()
      self.AddThumbNailTable()
      self.ToFile()


   def Find_Other_Top_Level_Files(self, extlist):
      rawpaths = self.Find_Top_Level_Files(extlist=extlist)
      self.otherpaths = [item for item in rawpaths if not inskipnames(item)]
      self.othernames = []
      for item in self.otherpaths:
         junk, filename = os.path.split(item)
         #print('filename = '+filename)
         self.othernames.append(filename)
      #print('othernames = '+str(self.othernames))
      return self.othernames


   def Add_Other_Links(self, extlist, sectiontitle):
      """Find other files (not images - probably python, html, and
      pdf) in the top level dir and create links under the heading
      sectiontitle."""
      namelist = self.Find_Other_Top_Level_Files(extlist)
      if namelist:
         self.body.append('<h2>%s</h2>' % sectiontitle)
         self.body.append('<ul>')
         for item in namelist:
            self.body.append('<li> <a href=%s>%s</a></li>'%(item,item))
         self.body.append('</ul>')
      return self.body
      
   

   def Create_Most(self, bl=True):
      self.FindSubFolders()
      if bl:
         self.Add_bottom_link(br=False)
      self.AddSubFolderLinks()
      self.FindImages()      
      self.GenerateHTMLs()
      self.AddThumbNailTable()
      self.Add_Other_Links(['.py'], "Python Files:")
      self.Add_Other_Links(['.m'], "Matlab Files:")      
      self.Add_Other_Links(['.pdf'], "PDF Files:")
      self.Add_Other_Links(['.html'], "HTML Files:")
      if bl:
         self.Add_bottom_link()
      self.ToFile()


class DirectoryPage3(DirectoryPage, css_line_delete_mixin):
   def ToFile(self, name='index.html'):
      outstr = self._build_body_str()
      outstr = self.delete_list_from_str(outstr, delete_list=None)
      outpath = os.path.join(self.folder,name)
      f = open(outpath, 'w')
      f.write(outstr)
      f.close()
      
   
class MainPageMaker:
   def __init__(self, folder, title=None, body=None, \
                htmldir='html', thumbdir='thumbnails'):
      self.mainfolder = folder


   def Create(self):
      mainpage = DirectoryPage(self.mainfolder)
      mainpage.FullCreate()
      for root, dirs, files in os.walk(self.mainfolder):
         if (not inskipfolders(root)) and (haspicts(root)):
            print('root='+root)
            #Pdb().set_trace()
            curpage = DirectoryPage(root)
            curpage.FullCreate()
            
      
class MainPageMaker2:
   """This class will be similar to MainPageMaker but will do a couple
   of things differently:

   1. The image types will be able to be specified so that .png can be
   used instead of or in addition to .jpg and .jpeg.

   2. The html for individual images will be improved:

       - When a thumbnail is clicked, it will open a page showing a
         screensize rather than the fullsize one (should improve speed)

       - The individual html pages with have forward and backward links
         as well as links to the fullsize images."""
   def __init__(self, folder, title=None, body=None, \
                htmldir='html', thumbdir='thumbnails', \
                screensizedir='screensize', \
                extlist=['.html','.py','.pdf','.m'], \
                imageextlist=['.png', '.jpg', '.jpeg'], \
                screensizesize=(875,700), \
                thumbsize=(400, 300), \
                HTMLclass=HTMLImage2, \
                DirectoryPageclass=DirectoryPage):
      self.title = title
      self.mainfolder = folder
      self.screensizesize = screensizesize
      self.screensizedir = screensizedir
      self.extlist = extlist
      self.imageextlist = imageextlist
      self.HTMLclass = HTMLclass
      self.DirectoryPageclass = DirectoryPageclass
      self.Screen_Size_Maker = ImageResizer900by600(folder, \
                                                    resizefolder=screensizedir,\
                                                    size=screensizesize, \
                                                    extlist=imageextlist)
      self.Thumbnail_Maker = ImageResizerDir(folder, \
                                             resizefolder=thumbdir,\
                                             size=thumbsize, \
                                             extlist=imageextlist)

   def Go(self, toplevel_html_list=[]):
      self.Screen_Size_Maker.ResizeAll()
      self.Thumbnail_Maker.ResizeAll()
      self.mainpage = self.DirectoryPageclass(self.mainfolder, \
                                              extlist=self.imageextlist, \
                                              contentlist=self.extlist, \
                                              HTMLclass=self.HTMLclass, \
                                              title = self.title, \
                                              screensizedir=self.screensizedir)
      for root, dirs, files in os.walk(self.mainfolder):
         if (not inskipfolders(root)) and (haspicts(root, self.extlist)):
            print('root='+root)
            #print('mainfolder='+self.mainfolder)
            toplevel = (root == self.mainfolder)
            if toplevel:
               bodyin = toplevel_html_list
               title = self.title
            else:
               bodyin = []
               junk, foldername = os.path.split(root)
               if self.title:
                  title = self.title+': '+foldername
               else:
                  title = foldername
            #print('bodyin = '+str(bodyin))
            curpage = self.DirectoryPageclass(root, \
                                              extlist=self.imageextlist, \
                                              HTMLclass=self.HTMLclass, \
                                              contentlist=self.extlist, \
                                              bodyin=bodyin, \
                                              title = title, \
                                              screensizedir=self.screensizedir)
            curpage.Create_Most(bl=(not toplevel))

      
if __name__ == '__main__':
   #testpath = '/mnt/personal/pictures/Joshua_Ryan/2009/June_2009/Bowman_visit/'
   testpath = '/mnt/personal/pictures/Joshua_Ryan/2009/June_2009/'   
   #myresizer = ImageResizer900by600(testpath)
   #myresizer.ResizeAll()
   mp = MainPageMaker2(testpath, screensizedir='900by600', \
                       screensizesize=[900,600], \
                       HTMLclass=HTMLImage3, \
                       DirectoryPageclass=DirectoryPage3, \
                       )
   mp.Go()
   
