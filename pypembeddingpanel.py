import wx

import os, cPickle, pdb

import pytexpanel
import texpy
import pytex
import texmaxima
import latexpanel
import replacelist
import texpypanel

savesettingsname = 'pypembeddingsettings.pkl'

class PYPEmbeddingPanel(texpypanel.TexPyPanel):
    def __init__(self, parent, dircontrol=None, filechooser=None):
        #kwds = {"style":wx.TAB_TRAVERSAL}
        #wx.Panel.__init__(self, parent, **kwds)
        #texpypanel.TexPyPanel.__init__(self, parent)
        pytexpanel.PyTexPanel.__init__(self, parent, dircontrol=dircontrol)
        #moreoptionsbox = wx.BoxSizer(wx.HORIZONTAL)
        moreoptionsbox = wx.FlexGridSizer(2, 2, 0, 0)  # rows, cols, hgap, vgap
        self.runpython = wx.CheckBox(self, -1, "Run Python")
        self.runmaxima = wx.CheckBox(self, -1, "Run Maxima")
        self.savenh = wx.CheckBox(self, -1, "Save No Header Version")
        self.answer = wx.CheckBox(self, -1, "Include Answers")

        self.filechooser = filechooser

        self.runpython.SetValue(False)
        self.runmaxima.SetValue(False)
        self.savenh.SetValue(False)
        
        self.runpython.Disable()
        self.runmaxima.Disable()
        
        moreoptionsbox.AddMany([(self.runpython, 1, wx.ALL,5),
                                (self.savenh, 1, wx.ALL,5),#|wx.ALIGN_CENTER_HORIZONTAL,5),
                                (self.runmaxima, 1, wx.ALL,5),
                                (self.answer, 1, wx.ALL,5),
                                ])


        ##################
        #
        #  Saving Settings
        #
        ##################
        self.GetMainDir()
        self.settingspath = os.path.join(self.maindir, savesettingsname)

        
        savekeys = ['pythonenabled','runpython','maximaenabled','runmaxima','savenh', 'answer']
        getmethods = [self.runpython.IsEnabled, self.runpython.GetValue, self.runmaxima.IsEnabled, self.runmaxima.GetValue, self.savenh.GetValue, self.answer.GetValue]
        setmethods = [self.runpython.Enable, self.runpython.SetValue, self.runmaxima.Enable, self.runmaxima.SetValue, self.savenh.SetValue, self.answer.SetValue]
        self.savedict = dict(zip(savekeys, getmethods))
        self.loaddict = dict(zip(savekeys, setmethods))

        
        self.SetSizer(moreoptionsbox)
        #mainsizer.Fit(self)
        self.Layout()


    def ScanFile(self):
        if self.filechooser is not None:
            mypath = self.filechooser.GetPath()
            mytexpy = texpy.TexPYPFile(mypath)
            if mytexpy.HasPython():
                self.runpython.Enable()
                self.runpython.SetValue(True)
        #texpypanel.TexPyPanel.ScanFile(self)
