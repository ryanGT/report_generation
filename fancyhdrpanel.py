import wx

import os, cPickle, pdb

#import pytex
import pytexpanel
import pytexutils

savesettingsname = 'fancyhdrsettings.pkl'


class FancyHdrPanel(pytexpanel.PyTexPanel):
    def __init__(self, parent, dircontrol=None):#(self, parent, *args, dircontrol=None, **kwds):
        # begin wxGlade: rwksinglefilechooser.__init__
        pytexpanel.PyTexPanel.__init__(self, parent, dircontrol=dircontrol)
        
        mysizer = wx.FlexGridSizer(4, 3, 0, 0)
        mysizer.AddGrowableCol(0)
        mysizer.AddGrowableCol(1)
        mysizer.AddGrowableCol(2)


        self.leftheadtitle = wx.StaticText(self, -1, "Left Header")
        self.lefthead = wx.TextCtrl(self, -1, "", size=(100, -1))
        self.centerheadtitle = wx.StaticText(self, -1, "Center Header")
        self.centerhead = wx.TextCtrl(self, -1, "", size=(30, -1))
        self.rightheadtitle = wx.StaticText(self, -1, "Right Header")
        self.righthead = wx.TextCtrl(self, -1, "", size=(30, -1))
        

        self.leftfoottitle = wx.StaticText(self, -1, "Left Footer")
        self.leftfoot = wx.TextCtrl(self, -1, "", size=(30, -1))
        self.centerfoottitle = wx.StaticText(self, -1, "Center Footer")
        self.centerfoot = wx.TextCtrl(self, -1, "", size=(30, -1))
        self.rightfoottitle = wx.StaticText(self, -1, "Right Footer")
        self.rightfoot = wx.TextCtrl(self, -1, "", size=(30, -1))


        txtboxopts = wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND
        border = 10
        
        mysizer.AddMany([#row 0
                         (self.leftheadtitle, 0, wx.TOP|wx.LEFT, border),
                         (self.centerheadtitle, 0, wx.TOP|wx.LEFT, border),
                         (self.rightheadtitle, 0, wx.TOP|wx.LEFT, border),
                         #row 1
                         (self.lefthead, 0, txtboxopts, border),
                         (self.centerhead, 0, txtboxopts, border),
                         (self.righthead, 0, txtboxopts, border),
                         #row 2
                         (self.leftfoottitle, 0, wx.TOP|wx.LEFT, border),
                         (self.centerfoottitle, 0, wx.TOP|wx.LEFT, border),
                         (self.rightfoottitle, 0, wx.TOP|wx.LEFT, border),
                         #row 3
                         (self.leftfoot, 0, txtboxopts, border),
                         (self.centerfoot, 0, txtboxopts, border),
                         (self.rightfoot, 0, txtboxopts, border),
                        ])


        self.GetMainDir()
        self.settingspath = os.path.join(self.maindir, savesettingsname)
        if not os.path.exists(self.settingspath):
            if not self.maindir:
                searchdir = os.getcwd()
            else:
                searchdir = self.maindir
            mypath = pytexutils.FindWalkingUp(savesettingsname, searchdir)
            if mypath:
                self.loadsettingspath = mypath
        #print('pyppanel.maindir='+self.maindir)


        savekeys = ['lhead', 'chead','rhead','lfoot','cfoot','rfoot']
        textctrls = [self.lefthead, self.centerhead, self.righthead, self.leftfoot, self.centerfoot, self. rightfoot]
        getmethods = [item.GetValue for item in textctrls]
        setmethods = [item.SetValue for item in textctrls]
        self.savedict = dict(zip(savekeys, getmethods))
        self.loaddict = dict(zip(savekeys, setmethods))


        self.SetSizer(mysizer)
        #mainsizer.Fit(self)
        self.Layout()


    def GetHeaderList(self):
        headctrls = [self.lefthead, self.centerhead, self.righthead]
        return [item.GetValue() for item in headctrls]


    def GetFooterList(self):
        footctrls = [self.leftfoot, self.centerfoot, self. rightfoot]
        return [item.GetValue() for item in footctrls]


    def GetLatexLines(self):
        outlist = []
        headerlist = self.GetHeaderList()
        footerlist = self.GetFooterList()
        if (not headerlist) and (not footerlist):
            return []
        out = outlist.append
        out('\\pagestyle{fancy}')
        out('\\lhead{%s}'%headerlist[0])
        out('\\chead{%s}'%headerlist[1])
        out('\\rhead{%s}'%headerlist[2])
        out('\\lfoot{%s}'%footerlist[0])
        out('\\cfoot{%s}'%footerlist[1])
        out('\\rfoot{%s}'%footerlist[2])
        return outlist

