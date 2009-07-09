import wx

import os, cPickle, pdb

import pytex
import pytexpanel
reload(pytexpanel)

import relpath
import rwkos


BROWSEBUTTON=wx.NewEventType()
#from rwkSingleFileChooser_v2 import rwkSingleFileChooser


class LatexOptionsPanel(pytexpanel.PyTexPanel):
    def __init__(self, parent, hasfancyhdr=False):
        #kwds = {"style":wx.TAB_TRAVERSAL}
        #wx.Panel.__init__(self, parent, **kwds)
        pytexpanel.PyTexPanel.__init__(self, parent)
        #moreoptionsbox = wx.BoxSizer(wx.HORIZONTAL)
        if hasfancyhdr:
            nc = 4
        else:
            nc = 3
        moreoptionsbox = wx.FlexGridSizer(1, nc, 0, 0)  # rows, cols, hgap, vgap
        self.dvi = wx.CheckBox(self, -1, "dvi")
        self.dvi.SetValue(False)
        self.kpdf = wx.CheckBox(self, -1, "kpdf")
        self.kpdf.SetValue(True)
        self.openout = wx.CheckBox(self, -1, "Auto Open Output")
        self.openout.SetValue(False)
        moreoptionsbox.AddMany([(self.dvi, 1, wx.ALL,5),
                                (self.kpdf, 1, wx.ALL,5),#|wx.ALIGN_CENTER_HORIZONTAL,5),
                                (self.openout, 1, wx.ALL,5),
                                ])
        if hasfancyhdr:
            self.usefancyhdr = wx.CheckBox(self, -1, "Use fancyhdr")
            self.usefancyhdr.SetValue(True)
            moreoptionsbox.Add(self.usefancyhdr, 1, wx.ALL,5)
        self.SetSizer(moreoptionsbox)
        #mainsizer.Fit(self)
        self.Layout()



class LatexOptionsPanel2(pytexpanel.PyTexPanel):
    def __init__(self, parent):
        pytexpanel.PyTexPanel.__init__(self, parent)
        self.parent = parent
        self.RunLatex = wx.CheckBox(self, -1, "Run LaTeX")
        self.RunLatex.SetValue(True)

        self.usefancyhdr = wx.CheckBox(self, -1, "Use fancyhdr")
        self.usefancyhdr.SetValue(True)


        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.AddMany([(self.RunLatex, 0, wx.ALL, 5),
                      (self.usefancyhdr, 0, wx.ALL, 5),
                      ])
        
        self.latexoptions = LatexOptionsPanel(self)

        mysizer = wx.FlexGridSizer(2, 1, 0, 0)
        mysizer.Add(box2, 1, wx.ALL, 5)
        mysizer.Add(self.latexoptions, 1, wx.ALL, 5)

        self.SetSizer(mysizer)
        self.Layout()
        

    def GetSettings(self):
        optdict = {}
        methodlist = [self.RunLatex.GetValue, self.usefancyhdr.GetValue, \
                      self.latexoptions.dvi.GetValue, \
                      self.latexoptions.kpdf.GetValue]
        keys = ['runlatex', 'usefancyhdr', 'dvi', 'kpdf']
        for curkey, curmethod in zip(keys, methodlist):
            optdict[curkey] = curmethod()
        return optdict


    def SetSettings(self, optdict):
        methodlist = [self.RunLatex.SetValue, self.usefancyhdr.SetValue, \
                      self.latexoptions.dvi.SetValue, \
                      self.latexoptions.kpdf.SetValue]
        keys = ['runlatex', 'usefancyhdr', 'dvi', 'kpdf']
        for curkey, curmethod in zip(keys, methodlist):
            if optdict.has_key(curkey):
                curmethod(optdict[curkey])
        
        
            


class LatexPanel(pytexpanel.PyTexPanel):
    def GetLatexPath(self):
        return self.LatexFileChooser.GetPath()


    def SetLatexPath(self, pathin):
        self.LatexFileChooser.SetPath(pathin)


    def GetOutputPath(self):
        return self.OutputChooser.GetPath()

        
    def SetOutputPath(self, pathin):
        self.OutputChooser.SetPath(pathin)

        
    def __init__(self, parent, dircontrol=None, settingsname='latexpanelsettings.pkl', fancyhdrpanel=None):
        pytexpanel.PyTexPanel.__init__(self, parent, dircontrol=dircontrol)
        self.LatexFileChooser = pytexpanel.PyTexFileChooser(self, postmethods=[])
        self.LatexFileChooser.SetLabel('LaTeX Input File')
        self.LatexFileChooser.filter = "TeX Files (*.tex)|*.tex|All Files (*.*)|*.*"
        self.LatexOpenButton = wx.Button(self, -1, "Open")
        sizer = wx.FlexGridSizer(3, 2, 0, 0)  # rows, cols, hgap, vgap
        self.RunLatexButton = wx.Button(self, -1, "Run LaTeX")
        self.OptionsPanel = LatexOptionsPanel(self, hasfancyhdr=False)#don't do this, I think hasfancyhdr is a bad idea, it is too late in the process
        self.OutputChooser = pytexpanel.PyTexFileChooser(self, postmethods=[])
        self.OutputChooser.SetLabel('LaTeX Output File')
        self.OutputChooser.filter = "dvi files (*.dvi)|*.dvi|pdf files (*.pdf)|*.pdf|All Files (*.*)|*.*"
        self.OpenOutputButton = wx.Button(self, -1, "Open Output")
        sizer.AddMany([#row 0
                       (self.LatexFileChooser, 0, wx.BOTTOM|wx.EXPAND|wx.TOP, 5),
                       (self.LatexOpenButton, 0, wx.ALL|wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT, 5),
                       #row 1
                       (self.OptionsPanel, 0, wx.ALL|wx.ALIGN_BOTTOM, 5),
                       (self.RunLatexButton, 0,  wx.ALL|wx.ALIGN_RIGHT, 5),
                       #row 2
                       (self.OutputChooser, 0, wx.BOTTOM|wx.EXPAND|wx.TOP, 5),
                       (self.OpenOutputButton, 0, wx.ALL|wx.ALIGN_BOTTOM|wx.ALIGN_RIGHT, 5),
                       ])
        sizer.AddGrowableCol(0)

        self.fancyhdrpanel = fancyhdrpanel
##         if fancyhdrpanel is None:
##             self.OptionsPanel.usefancyhdr.SetValue(False)
##             self.OptionsPanel.usefancyhdr.Disable()
        


        self.Bind(wx.EVT_BUTTON, self.RunLatex, self.RunLatexButton)
        self.Bind(wx.EVT_BUTTON, self.OpenLatex, self.LatexOpenButton)
        self.Bind(wx.EVT_BUTTON, self.OpenOutput, self.OpenOutputButton)

        self.GetMainDir()
        print('self.maindir='+self.maindir)
        self.settingspath = os.path.join(self.maindir, settingsname)
        
        savekeys = ['latexin','latexout','dvi','autoopen']
        getmethods = [self.GetLatexPath, self.GetOutputPath, self.OptionsPanel.dvi.GetValue, self.OptionsPanel.openout.GetValue]
        setmethods = [self.SetLatexPath, self.SetOutputPath, self.OptionsPanel.dvi.SetValue, self.OptionsPanel.openout.SetValue]
        self.savedict = dict(zip(savekeys, getmethods))
        self.loaddict = dict(zip(savekeys, setmethods))
        
        self.SetSizer(sizer)
        #mainsizer.Fit(self)
        self.Layout()


    def OpenOutput(self, evt):
        kpdf = self.OptionsPanel.kpdf.GetValue()
        if rwkos.amiLinux():
            if kpdf:
                cmds={'.dvi':'kdvi %s','.pdf':'kpdf %s'}
            else:
                cmds={'.dvi':'kdvi %s','.pdf':'acroread %s'}
        else:
            cmds={'.dvi':'yap -1 %s','.pdf':'AcroRd32 %s'}
        outname = self.GetOutputPath()
        print 'outname='+str(outname)
        if not outname:
            print "No outname, exitting."
            return
        outpath_noext, ext = os.path.splitext(outname)
        mycmd=cmds[ext]% outname
#        print('mycmd='+mycmd)
#        subprocess.Popen(cmds[ext]% outname)
        if rwkos.amiLinux():
            os.system(mycmd + ' &')
            print('mycmd='+mycmd)
        else:
            subprocess.Popen(mycmd)


    def RunLatex(self, evt):
        dvi = self.OptionsPanel.dvi.GetValue()
        openviewer = self.OptionsPanel.openout.GetValue()
        filepath = self.LatexFileChooser.GetPath()
        outputpath = pytex.RunLatex(filepath, dvi=dvi, openviewer=openviewer, sourcespecials=True, log=None)
        print('outputpath = '+outputpath)
        self.SetOutputPath(outputpath)
        autoopen = self.OptionsPanel.openout.GetValue()
        if autoopen:
            self.OpenOutput(0)


    def OpenLatex(self, evt):
        self.openfile(self.LatexFileChooser)


