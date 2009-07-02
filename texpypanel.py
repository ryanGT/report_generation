import wx

import os, cPickle, pdb

import pytexpanel
import texpy
import pytex
import texmaxima
import latexpanel
import replacelist

BROWSEBUTTON=wx.NewEventType()
import reusablepanels
from reusablepanels.rwkSingleFileChooser_v2 import rwkSingleFileChooser
from reusablepanels.rwkdirchooserpanel import rwkdirchooserpanel

savesettingsname = 'texpypanelsettings.pkl'

class TexPyPanel(pytexpanel.PyTexPanel):
    def _PathExists(self):
        self.path = self.filechooser.GetPath()
        if self.path:
            if os.path.exists(self.path):
                return True
        return False
    

    def ScanFile(self):
        if hasattr(self, 'texpy'):
            if self.texpy.HasPython():
                self.runpython.Enable()
                self.runpython.SetValue(True)
        if hasattr(self, 'texmaxima'):
            if self.texmaxima.HasMaxima():
                self.runmaxima.Enable()
                self.runmaxima.SetValue(True)


    def LoadTexFile(self):
        #print('In LoadTexFile')
        self.LoadTexPyFile()
        self.LoadTexMaximaFile()

        
    def LoadTexPyFile(self, pathin=None):
        if pathin is None:
            if self._PathExists():
                self.texpy = texpy.TexPyFile(self.path)
                self.ScanFile()
        else:
            self.texpy = texpy.TexPyFile(pathin)
            self.ScanFile()


    def LoadTexMaximaFile(self, pathin=None):
        if pathin is None:
            if self._PathExists():
                self.texmaxima = texmaxima.TexMaximaFile(self.path)
                self.ScanFile()
        else:
            self.texmaxima = texmaxima.TexMaximaFile(pathin)
            self.ScanFile()

            
    def __init__(self, parent, dircontrol=None, fancyhdrpanel=None):#(self, parent, *args, dircontrol=None, **kwds):
        # begin wxGlade: rwksinglefilechooser.__init__
        pytexpanel.PyTexPanel.__init__(self, parent, dircontrol=dircontrol)
        self.fancyhdrpanel = fancyhdrpanel
        #self.filechooser = rwkSingleFileChooser(self)
        self.filechooser = pytexpanel.PyTexChooserPanel(self, dircontrol=dircontrol, postmethods=[self.LoadTexFile])
        self.filechooser.SetFilter("Tex Files (*.tex)|*.tex|All Files (*.*)|*.*")

        self.runpython = wx.CheckBox(self, -1, "Run Python")
        self.eqnstar = wx.CheckBox(self, -1, "Star Equations")
        self.runmaxima = wx.CheckBox(self, -1, "Run Maxima")
        self.savenh = wx.CheckBox(self, -1, "Save No Header Version")
        self.answer = wx.CheckBox(self, -1, "Include Answers")
        self.usefancyhdr = wx.CheckBox(self, -1, "Use fancyhdr")
        self.echo = wx.CheckBox(self, -1, "echo Python")
        self.runpython.SetValue(False)
        self.runmaxima.SetValue(False)
        self.eqnstar.SetValue(False)
        self.savenh.SetValue(False)
        self.usefancyhdr.SetValue(True)
        
        mysizer = wx.FlexGridSizer(8, 1, 0, 0)
        mysizer.AddGrowableCol(0)

        othersizer = wx.FlexGridSizer(2, 4, 0, 0)

        #row 0
        othersizer.Add(self.runpython, 1, wx.ALL, 5)
        othersizer.Add(self.answer, 1, wx.ALL, 5)
        othersizer.Add(self.usefancyhdr, 1, wx.ALL, 5)
        othersizer.Add(self.eqnstar, 1, wx.ALL, 5)
        #row 1
        othersizer.Add(self.runmaxima, 1, wx.ALL, 5)
        othersizer.Add(self.savenh, 1, wx.ALL, 5)
        othersizer.Add(self.echo, 1, wx.ALL, 5)


        self.runpython.Disable()
        self.runmaxima.Disable()


        #Run Buttons
        self.runbutton = wx.Button(self, -1, "Run")
        self.wltbutton = wx.Button(self, -1, "Export Maxima")
        self.pyexportbutton = wx.Button(self, -1, 'Export Python')
        self.runallbutton = wx.Button(self, -1, "Run All")
        self.Bind(wx.EVT_BUTTON, self.RunPyMax, self.runbutton)
        self.Bind(wx.EVT_BUTTON, self.RunAll, self.runallbutton)
        self.Bind(wx.EVT_BUTTON, self.ExportMaxima, self.wltbutton)
        self.Bind(wx.EVT_BUTTON, self.ExportPython, self.pyexportbutton)

        self.LatexPanel = latexpanel.LatexPanel(self, dircontrol=self.dircontrol, fancyhdrpanel=None)#this is probably not the place for this.  It is too late in the process.  This panel just runs LaTeX on an already existing file#fancyhdrpanel=self.fancyhdrpanel
        self.GetMainDir()
        #print('self.maindir='+self.maindir)

        self.settingspath = os.path.join(self.maindir, savesettingsname)

        savekeys = ['path','latexdict','savenh','answer','usefancyhdr','echo','eqnstar']
        getmethods = [self.filechooser.GetPath, self.LatexPanel.GetSettings, self.savenh.GetValue, self.answer.GetValue, self.usefancyhdr.GetValue, self.echo.GetValue, self.eqnstar.GetValue]
        setmethods = [self.filechooser.SetPath, self.LatexPanel.SetSettings, self.savenh.SetValue, self.answer.SetValue, self.usefancyhdr.SetValue, self.echo.SetValue, self.eqnstar.SetValue]
        self.postloadmethods = [self.LoadTexFile]
        self.savedict = dict(zip(savekeys, getmethods))
        self.loaddict = dict(zip(savekeys, setmethods))


        self.mylabel = wx.StaticText(self, -1, "")

        #row 0
        mysizer.Add(self.filechooser, 1, wx.EXPAND|wx.ALL, 0)
        #row 1
        mysizer.Add(othersizer, 1, wx.ALL, 5)
        #row 2
        mysizer.Add(self.wltbutton, 1, wx.ALL|wx.ALIGN_LEFT, 5)
        #row 3
        mysizer.Add(self.pyexportbutton, 1, wx.ALL|wx.ALIGN_LEFT, 5)
        #row 4
        mysizer.Add(self.runbutton, 1, wx.ALL|wx.ALIGN_RIGHT, 5)
        #row 5
        mysizer.Add(self.LatexPanel, 1, wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
        #row 6
        mysizer.Add(self.mylabel, 1, wx.ALL, 5)
        #row 7
        mysizer.Add(self.runallbutton, 1, wx.ALL|wx.ALIGN_RIGHT, 5)


        #self.mylabel.Hide()

        self.SetSizer(mysizer)
        #mainsizer.Fit(self)
        self.Layout()


    def ExportMaxima(self, evt):
        self.texmaxima.ToWLT()


    def ExportPython(self,evt):
        self.texpy = texpy.TexPyFile(self.path)
        self.texpy.ExportPython()
        

    def RunPyMax(self, evt):
        #####################
        # need checkboxes:
        #####################
        dvi = False
        #echos (2?)
        #####################
        answer = self.answer.GetValue()
        print('In RunPyMax, answer='+str(answer))
        runpy = self.runpython.GetValue()
        star = self.eqnstar.GetValue()
        runmax = self.runmaxima.GetValue()
        echo = self.echo.GetValue()
        if not self._PathExists():
            return
        inpath = self.path
        pno, ext = os.path.splitext(inpath)
        outpath = pno+'_temp.tex'
        outpath2 = pno+'_out.tex'
        savenh = self.savenh.GetValue()
        findlist = []
        #pdb.set_trace()
        self.replacelist = replacelist.ReplaceList()
        self.replacelist.ReadFRFile()
        if runpy:
            if not runmax:
                outpath = outpath2
            self.texpy = texpy.TexPyFile(inpath)
            self.texpy.Execute(answer=answer, \
                               replacelist=self.replacelist, \
                               echo=echo, star=star)
            if not runmax:
                self.texpy.AddHeader()
            self.texpy.SaveLatex(filename=outpath)
            findlist.extend(self.texpy.FindLHSs())
            inpath = outpath
            if (not runmax) and savenh:
                self.texpy.SaveNH(filename=outpath)
        if runmax:
            self.texmaxima = texmaxima.TexMaximaFile(inpath, \
                                                     answer=answer)
            self.texmaxima.RunMaxima()
            #pdb.set_trace()#<-- problem with replacement on a second time through
            self.texmaxima.SubstituteLatex(echo=0, \
                                           replacelist=self.replacelist, \
                                           answer=answer)
            self.texmaxima.AddHeader()
            self.texmaxima.SaveLatex(filename=outpath2)
            #pdb.set_trace()
            maxfindlist = self.texmaxima.FindReplacePats()
            findlist.extend(maxfindlist)
            if savenh:
                self.texmaxima.SaveNH(filename=outpath2)
        usefancyhdr = self.usefancyhdr.GetValue()
        headerlines = []
        if usefancyhdr and (self.fancyhdrpanel is not None) and (runmax or runpy):
            headerlines = self.fancyhdrpanel.GetLatexLines()
            #print('\n'*3)
            #print('fancyhdrpanel lines:')
            #for line in headerlines:
            #    print line
            #print('\n'*3)
            if runmax:
                mylastfile = self.texmaxima
            else:
                mylastfile = self.texpy
            mylastfile.HeaderInsert(headerlines)
            mylastfile.SaveLatex(filename=outpath2)
        if runmax or runpy:
            self.LatexPanel.SetLatexPath(outpath2)
        self.replacelist.AppendFRFile(findlist)
        #pytex.writefile('frpatterns.txt', findlist)
            
            

    def RunAll(self, evt):
        self.RunPyMax(evt)
        self.LatexPanel.RunLatex(evt)



