#!/usr/bin/env python

import wx

#from scipy import *

import os, cPickle, pdb, sys

import reusablepanels
from reusablepanels.rwkSingleFileChooser_v2 import rwkSingleFileChooser
from reusablepanels.rwkdirchooserpanel import rwkdirchooserpanel

#import pydocument
#reload(pydocument)

#import pypres
#reload(pypres)

import rwkmisc
#reload(rwkmisc)

import rwkos
#reload(rwkos)

import texpypanel
import latexpanel
import pyppanel
import fancyhdrpanel
import wltpanel

settingsname = 'pytexguisettings.pkl'

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title,
                          pos=(150, 150), size=(650, 725))
        # Create the menubar
        menuBar = wx.MenuBar()

        # and a menu 
        menu = wx.Menu()

        # add an item to the menu, using \tKeyName automatically
        # creates an accelerator, the third param is some help text
        # that will show up in the statusbar
        menu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Exit the application")

        # bind the menu event to an event handler
        self.Bind(wx.EVT_MENU, self.OnTimeToClose, id=wx.ID_EXIT)

        # and put the menu on the menubar
        menuBar.Append(menu, "&File")
        self.SetMenuBar(menuBar)


        #create top level controls (i.e. those not on a notebook page)
        #create the main directory chooser
        self.topdirchooser = rwkdirchooserpanel(self, -1)
        #and the main exit button
        self.exitbutton = wx.Button(self, -1, "Exit")

        
        #create the notebook
        self.notebook = wx.Notebook(self, -1, style=0)

        #notebook panes
        self.fancyhdrpane = fancyhdrpanel.FancyHdrPanel(self.notebook, dircontrol=self.topdirchooser)
        self.texpypane = texpypanel.TexPyPanel(self.notebook, dircontrol=self.topdirchooser, fancyhdrpanel=self.fancyhdrpane)
        self.purelatexpane = latexpanel.LatexPanel(self.notebook, dircontrol=self.topdirchooser, settingsname='purelatexsettings.pkl')
        self.pyppane = pyppanel.PYPPanel(self.notebook, dircontrol=self.topdirchooser, fancyhdrpanel=self.fancyhdrpane)
        self.wltpane = wltpanel.WLTPanel(self.notebook, dircontrol=self.topdirchooser, fancyhdrpanel=self.fancyhdrpane)
        
        
        #create the sizer for the first pane
        grid_sizer = wx.FlexGridSizer(2, 1, 0, 0)

        #create widgets for pane one
        #self.panel = wx.Panel(self)
        #self.label_4 = wx.StaticText(self.notebook_pane_1, -1, "label_4")
        #self.button_1 = wx.Button(self.notebook_pane_1, -1, "button_1")

        #add the widgets to pane one's sizer
        #grid_sizer.Add(self.label_4, 0, 0, 0)
        #grid_sizer.Add(self.button_1, 0, 0, 0)

        #self.notebook_pane_1.SetSizer(grid_sizer)

        grid_sizer.AddGrowableCol(0)
        grid_sizer.AddGrowableRow(0)
        #Add pane one to the notebook
        self.notebook.AddPage(self.texpypane, "TexPy/TexMaxima")
        self.notebook.AddPage(self.pyppane, "PYP")
        self.notebook.AddPage(self.purelatexpane, "Pure LaTeX")
        self.notebook.AddPage(self.fancyhdrpane, "fancyhdr")
        self.notebook.AddPage(self.wltpane, "WLT")
        #create the sizer for the main frame
        mainsizer = wx.FlexGridSizer(3, 1, 0, 0)
        mainsizer.AddGrowableCol(0)
        mainsizer.AddGrowableRow(1)
        
        #add the controls to the main sizer
        mainsizer.Add(self.topdirchooser, 1, wx.EXPAND|wx.ALL, 5)
        mainsizer.Add(self.notebook, 1, wx.EXPAND, 5)
        mainsizer.Add(self.exitbutton, 1, wx.ALL|wx.ALIGN_RIGHT, 5)

        self.Bind(wx.EVT_BUTTON, self.OnTimeToClose, self.exitbutton)


        self.startdir = os.getcwd()
        self.settingspath = os.path.join(self.startdir, settingsname)

        if self.startdir not in sys.path:
            sys.path.insert(0, self.startdir)
        
        self.SetSizer(mainsizer)
        self.savepanellist = [self.texpypane, self.purelatexpane, self.pyppane, self.fancyhdrpane, self.wltpane]
        #mainsizer.Fit(self)
        self.Layout()
        self.LoadSettings()


    def SaveSettings(self): # wxGlade: MyFrame.<event_handler>
        mydict = {}
#        for key, chooser in zip(self.pathlist, self.filechoosers):
#            curpath = chooser.GetPath()
#            mydict[key] = curpath
#        wlt = self.wltcheckbox.GetValue()
        topdir = self.topdirchooser.GetPath()
        mydict['topdir'] = topdir
        nbind = self.notebook.GetSelection()
        mydict['nbind'] = nbind
        mypkl = open(self.settingspath,'wb')
        #print('mydict='+str(mydict))
        cPickle.dump(mydict,mypkl)
        mypkl.close()
        #for key, val in mydict.iteritems():
        #    print str(key) + ':' + str(val)
        for panel in self.savepanellist:
            panel.SaveSettings()


    def LoadSettings(self): # wxGlade: MyFrame.<event_handler>
        if os.path.exists(self.settingspath):
            mypkl = open(self.settingspath,'rb')
            mydict = cPickle.load(mypkl)
            mypkl.close()
            #print('mydict='+str(mydict))
            if mydict.has_key('topdir'):
                self.topdirchooser.SetPath(mydict['topdir'])
            if mydict.has_key('nbind'):
                self.notebook.SetSelection(mydict['nbind'])
        else:
            self.topdirchooser.SetPath(os.getcwd())
        for panel in self.savepanellist:
            panel.LoadSettings()


    def OnTimeToClose(self, evt):
        """Event handler for the button click."""
        self.SaveSettings()
        self.Close()


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "PyTex Office Suite")
        self.SetTopWindow(frame)

        #print "Print statements go to this stdout window by default."

        frame.Show(True)
        return True
        

if __name__ == "__main__":
    app = MyApp(redirect=False)
    app.MainLoop()
