import wx

import os, cPickle, pdb, subprocess

import relpath
import rwkos

BROWSEBUTTON=wx.NewEventType()
import reusablepanels
from reusablepanels.rwkSingleFileChooser_v2 import rwkSingleFileChooser
from reusablepanels.rwkdirchooserpanel import rwkdirchooserpanel

from pytexutils import OpenOutput

def openemacs(pathin):
    if not pathin:
        return
    if os.path.exists(pathin):
        if rwkos.amiLinux():
            cmd='emacs '+pathin+' &'
            os.system(cmd)
        else:
            cmd='emacsclientw '+pathin
            subprocess.Popen(cmd)
        print cmd
        

class PyTexPanel(wx.Panel):
    """This is sort of an abstract class for all panels on pytexgui to
    derive from.  I hope to create panels that can be used in other
    things while also making a nice gui for my current application.
    The primary feature for now is the dircontrol control which allows
    each panel to be passed the control for setting the main directory
    of the gui.

    Note that all derived classes must define self.settingspath,
    self.savedict, and self.loaddict so that SaveSettings and
    LoadSettings will work correctly.  self.settingspath is a string
    containing the path to the settings pickle file.  self.savedict
    and self.loaddict are dictionaries whose keys are the keys of the
    dictionary in the pickled settings file.  The values are the
    methods for getting or setting the widget values.
    
    self.postloadmethods is a list of methods that will
    be called after self.LoadSettings."""
    def __init__(self, parent, dircontrol=None, fancyhdrpanel=None):#(self, parent, *args, dircontrol=None, **kwds):
        kwds = {"style":wx.TAB_TRAVERSAL}
        wx.Panel.__init__(self, parent, **kwds)
        self.parent = parent
        self.dircontrol = dircontrol
        self.savedict = {}
        self.loaddict = {}
        self.postloadmethods = []
        self.fancyhdrpanel = fancyhdrpanel


    def GetMainDir(self):
        if self.dircontrol is not None:
            self.maindir = self.dircontrol.GetDir()
        else:
            self.maindir = ''
        return self.maindir


    def GetSettings(self):
        """Retreive the settings associated with the panel as a
        dictionary.  This method is called by
        self.SaveSettings, and could also be called by a parent's
        SaveSettings method."""
        mydict = {}
        for key, method in self.savedict.iteritems():
            curval = method()
            mydict[key] = curval
        return mydict


    def SetSettings(self, mydict):
        """Set the settings associated with the panel, based on the
        dictionary mydict.  This method is called by
        self.LoadSettings, and could also be called by a parent's
        LoadSettings method."""
        for key, method in self.loaddict.iteritems():
            if mydict.has_key(key):
                method(mydict[key])
        for method in self.postloadmethods:
            method()


    def SaveSettings(self):
        mydict = self.GetSettings()
        mypkl = open(self.settingspath,'wb')
        #print('mydict='+str(mydict))
        cPickle.dump(mydict,mypkl)
        mypkl.close()
        #for key, val in mydict.iteritems():
        #    print str(key) + ':' + str(val)


    def LoadSettings(self): # wxGlade: MyFrame.<event_handler>
        mypkl = None
        if os.path.exists(self.settingspath):
            mypkl = open(self.settingspath,'rb')
        elif hasattr(self, 'loadsettingspath'):
            if os.path.exists(self.loadsettingspath):
                mypkl = open(self.loadsettingspath,'rb')
        if mypkl:
            
            mydict = cPickle.load(mypkl)
            mypkl.close()
            #print('mydict='+str(mydict))
            self.SetSettings(mydict)
            

    def openfile(self, filechooser, kpdf=True):
        mypath = filechooser.GetPath()
        #print('mypath='+mypath)
        pno, ext= os.path.splitext(mypath)
        if (ext == '.dvi') or (ext == '.pdf'):
            OpenOutput(mypath, kpdf=kpdf)
        else:
            openemacs(mypath)




class PyTexFileChooser(rwkSingleFileChooser):
    def __init__(self, parent, postmethods=[]):
        """postmethods is a list of methods to be called after a
        successful file choice.

        parent must have a GetMainDir method."""
        rwkSingleFileChooser.__init__(self, parent)
        self.postmethods = postmethods
        
    def OnBrowseButton(self,e):
        self._FindMainDir()
        #--------------------------------------------------
        # wxLogMessage("dirchooser Browse Button Pushed")
        #--------------------------------------------------  
        dlg = wx.FileDialog(self,self.message,self.defaultdir,"", self.filter, self.style)
        success=dlg.ShowModal()
        if success== wx.ID_OK:
            path=dlg.GetPath()
            self.path = path
            if self.defaultdir:
                self.relpath = relpath.relpath(path, self.defaultdir)
            else:
                self.relpath = self.path
            self.DirectoryTextBox.SetValue(self.relpath)
            for method in self.postmethods:
                method()
        dlg.Destroy()
        return success

            
    def _FindMainDir(self):
        maindir = self.parent.GetMainDir()
        #print('maindir='+maindir)
        self.defaultdir = maindir
        return maindir


    def _FindRelPath(self, abspath):
        maindir = self._FindMainDir()
        #print('self.defaultdir='+self.defaultdir)
        #print('abspath='+abspath)
        #print('maindir='+maindir)
        #pdb.set_trace()
        abspath = rwkos.FindFullPath(abspath)#this might break some stuff
        maindir = rwkos.FindFullPath(maindir)
        if not maindir:
            self.relpath = abspath
        #elif os.path.samefile(abspath, maindir):
        elif abspath == maindir:
            self.relpath = ''
        else:
            self.relpath = relpath.relpath(abspath, maindir)
        return self.relpath
    

    def GetPath(self):
        relpath = self.DirectoryTextBox.GetValue()
        if not relpath:
            return ''
        maindir = self.parent.GetMainDir()
        if maindir:
            abspath = os.path.join(maindir, relpath)
        else:
            abspath = relpath
        return abspath


    def GetDir(self):
        return self.GetPath()


    def SetDir(self, dir):
        if dir:
            #print('dir='+dir)
            relpath = self._FindRelPath(dir)
            self.DirectoryTextBox.SetValue(relpath)
        

    def SetPath(self,path):
        self.SetDir(path)

    


class PyTexChooserPanel(PyTexPanel):
    def __init__(self, parent, dircontrol=None, settingsname='pytexchoosersettings.pkl', postmethods=[]):
        PyTexPanel.__init__(self, parent, dircontrol=dircontrol)
        self.FileChooser = PyTexFileChooser(self, postmethods=postmethods)
        self.OpenButton = wx.Button(self, -1, "Open")
        sizer = wx.FlexGridSizer(1, 2, 0, 0)  # rows, cols, hgap, vgap
        sizer.AddMany([#row 0
                       (self.FileChooser, 0, wx.BOTTOM|wx.EXPAND|wx.TOP, 5),
                       (self.OpenButton, 0, wx.ALL|wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT, 5),
                       ])
        sizer.AddGrowableCol(0)

        self.Bind(wx.EVT_BUTTON, self.OpenFile, self.OpenButton)

        self.GetMainDir()
        self.settingspath = os.path.join(self.maindir, settingsname)
        
        savekeys = ['path']
        getmethods = [self.FileChooser.GetPath]
        setmethods = [self.FileChooser.SetPath]
        self.savedict = dict(zip(savekeys, getmethods))
        self.loaddict = dict(zip(savekeys, setmethods))
        
        self.SetSizer(sizer)
        #mainsizer.Fit(self)
        self.Layout()


    def GetPath(self):
        return self.FileChooser.GetPath()


    def SetPath(self, pathin):
        return self.FileChooser.SetPath(pathin)


    def SetFilter(self, filtstr):
        self.FileChooser.filter = filtstr


    def OpenFile(self, evt):
        self.openfile(self.FileChooser)


    def SetLabel(self, newlabel):
        self.FileChooser.SetLabel(newlabel)
