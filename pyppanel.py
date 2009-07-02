import wx

import os, cPickle, pdb

import pytexpanel
import texpy
import pytex
import texmaxima
import latexpanel
import replacelist

import pydocument
import rwkmisc
from pytexutils import RunLatex

import pypembeddingpanel

#import textfiles
#reload(textfiles)
#import textfiles.latexlist
#reload(textfiles.latexlist)

import pypres
#reload(pypres)

BROWSEBUTTON=wx.NewEventType()
import reusablepanels
from reusablepanels.rwkSingleFileChooser_v2 import rwkSingleFileChooser
from reusablepanels.rwkdirchooserpanel import rwkdirchooserpanel

savesettingsname = 'pyppanelsettings.pkl'

class PYPPanel(pytexpanel.PyTexPanel):
    def __init__(self, parent, dircontrol=None, fancyhdrpanel=None):
        # begin wxGlade: rwksinglefilechooser.__init__
        pytexpanel.PyTexPanel.__init__(self, parent, dircontrol=dircontrol, fancyhdrpanel=fancyhdrpanel)
        
        #self.filechooser = rwkSingleFileChooser(self)
        self.embeddingpanel = pypembeddingpanel.PYPEmbeddingPanel(self)
        self.filechooser = pytexpanel.PyTexChooserPanel(self, dircontrol=dircontrol, postmethods=[self.embeddingpanel.ScanFile])
        self.filechooser.SetFilter("PYP Files (*.pyp)|*.pyp|All Files (*.*)|*.*")
        self.filechooser.SetLabel('PYP Input File')

        self.embeddingpanel.filechooser = self.filechooser
        
        mysizer = wx.FlexGridSizer(7, 1, 0, 0)
        mysizer.AddGrowableCol(0)


        #Output Options
        outopts = ['Outline', 'Document', 'Lab Procedure', 'Presentation']
        self.OutputOptions = wx.RadioBox(self, -1, "Output Options", choices=outopts, majorDimension=0, style=wx.RA_SPECIFY_ROWS)

        
        #########################
        #
        #   Lab info sizer
        #
        #########################
        sizer2 = wx.FlexGridSizer(2, 2, 0, 0)  # rows, cols, hgap, vgap
        self.label_lab_num = wx.StaticText(self, -1, "Lab #")
        self.label_title = wx.StaticText(self, -1, "Title")
        self.lab_num = wx.TextCtrl(self, -1, "", size=(30, -1))
        self.title = wx.TextCtrl(self, -1, "", size=(300, -1))
        sizer2.AddMany([(self.label_lab_num, 0, wx.TOP|wx.LEFT|wx.ALIGN_BOTTOM, 5),
                        (self.label_title, 0, wx.TOP|wx.LEFT|wx.ALIGN_BOTTOM, 5),
                        (self.lab_num, 0, wx.BOTTOM|wx.LEFT|wx.ALIGN_TOP, 5),
                        (self.title, 0, wx.BOTTOM|wx.LEFT|wx.ALIGN_TOP, 5),
                        ])
        #########################
        middlebox = wx.BoxSizer(wx.HORIZONTAL)
        middlebox.AddMany([(self.OutputOptions, 0, wx.ALL, 5),
                           (sizer2, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL, 5),
                           ])


        self.HideBody = wx.CheckBox(self, -1, "Hide Body")#, (65, 60), (150, 20), wx.NO_BORDER)
        self.HideBody.SetValue(False)
        
        self.RunLatex = wx.CheckBox(self, -1, "Run LaTeX")
        self.RunLatex.SetValue(True)

        self.usefancyhdr = wx.CheckBox(self, -1, "Use fancyhdr")
        self.usefancyhdr.SetValue(True)


        box2 = wx.BoxSizer(wx.HORIZONTAL)
        box2.AddMany([(self.RunLatex, 0, wx.ALL, 5),
                      (self.usefancyhdr, 0, wx.ALL, 5),
                      ])
        
        
        self.latexoptions = latexpanel.LatexOptionsPanel(self)
        self.RunButton = wx.Button(self, -1, "Run")
        
        lowersizer = wx.FlexGridSizer(1, 2, 0, 0)#wx.BoxSizer(wx.HORIZONTAL)
        lowersizer.AddMany([(self.latexoptions, 0, wx.ALL, 0),
                          (self.RunButton, 0, wx.ALL|wx.ALIGN_RIGHT, 5),
                         ])
        lowersizer.AddGrowableCol(1)

        self.OutputChooser = pytexpanel.PyTexChooserPanel(self, dircontrol=dircontrol, postmethods=[])
        self.OutputChooser.SetLabel('LaTeX Output File')

        
        #row 0
        mysizer.Add(self.filechooser, 1, wx.EXPAND|wx.ALL, 0)
        mysizer.Add(self.embeddingpanel, 1, wx.EXPAND|wx.ALL, 0)
        mysizer.Add(middlebox, 1, wx.ALL|wx.ALIGN_LEFT, 5)
        mysizer.Add(self.HideBody, 0, wx.ALL, 5)
        mysizer.Add(box2, 0, wx.ALL, 0)
        mysizer.Add(lowersizer, 0, wx.ALL|wx.EXPAND, 0)
        mysizer.Add(self.OutputChooser, 0, wx.ALL|wx.EXPAND, 0)

        self.GetMainDir()
        self.settingspath = os.path.join(self.maindir, savesettingsname)
        #print('pyppanel.maindir='+self.maindir)


        ##################
        #
        #  Saving settings
        #
        ##################
        savekeys = ['path', 'outputpath','outputoption','dvi','runlatex','kpdf','fancyhdr','title']
        getmethods = [self.filechooser.GetPath, self.OutputChooser.GetPath, \
                      self.OutputOptions.GetSelection, self.latexoptions.dvi.GetValue, \
                      self.RunLatex.GetValue, self.latexoptions.kpdf.GetValue, \
                      self.usefancyhdr.GetValue, self.title.GetValue]
        setmethods = [self.filechooser.SetPath, self.OutputChooser.SetPath, \
                      self.OutputOptions.SetSelection, self.latexoptions.dvi.SetValue, \
                      self.RunLatex.SetValue, self.latexoptions.kpdf.SetValue, \
                      self.usefancyhdr.SetValue, self.title.SetValue]
        self.savedict = dict(zip(savekeys, getmethods))
        self.loaddict = dict(zip(savekeys, setmethods))


        ##################
        #
        #  Bind Events
        #
        ##################
        self.Bind(wx.EVT_BUTTON, self.EvtRunButton, self.RunButton)
        self.SetSizer(mysizer)
        #mainsizer.Fit(self)
        self.Layout()



    def SaveSettings(self):
        pytexpanel.PyTexPanel.SaveSettings(self)
        self.embeddingpanel.SaveSettings()


        
    def LoadSettings(self):
        pytexpanel.PyTexPanel.LoadSettings(self)
        self.embeddingpanel.LoadSettings()



    def EvtRunButton(self, event): # wxGlade: MyFrame.<event_handler>
        #fig{width:3.0in|RC_circuit.eps}
        runpython = self.embeddingpanel.runpython.GetValue()
        mypath = self.filechooser.GetPath()
        dvi = self.latexoptions.dvi.GetValue()
        pdf = not dvi
        if runpython:
            mytexpy = texpy.TexPYPFile(mypath)
            ans = self.embeddingpanel.answer.GetValue()
            mytexpy.Execute(answer=ans, pdf=pdf, handout=False)
            fno, ext = os.path.splitext(mypath)
            outpath = mytexpy.SavePYP()
            mypath = outpath
            
        runlatex = self.RunLatex.GetValue()
        nobody = self.HideBody.GetValue()
        output = self.OutputOptions.GetSelection()
        usefancyhdr = self.usefancyhdr.GetValue()
        headerlines = []
        if usefancyhdr and (self.fancyhdrpanel is not None):
            headerlines = self.fancyhdrpanel.GetLatexLines()
            print('\n'*3)
            print('fancyhdrpanel lines:')
            for line in headerlines:
                print line
            print('\n'*3)
        rwkmisc.PrintToScreen(['runlatex','dvi','nobody','mypath','output'],locals())
        outfile = ''
        if output == 0:
            outfile = pydocument.OutlineToLatexOutline(mypath, runlatex=runlatex, \
                                                       dvi=dvi, nobody=nobody, headerinsert=headerlines)
        elif output == 1:
            myoutline = pydocument.Document()
            myoutline.ReadFile(mypath)
            myoutline.FindNestLevels(nobody=nobody)
            myoutline.ToLatex()
            fno, ext = os.path.splitext(mypath)
            outname = fno+'_out.tex'
            myoutline.ToFile(outname)
            if runlatex:
                outfile = RunLatex(outname, dvi=dvi)
                #outfolder, outfile = os.path.split(outpath)
                print('outname='+outfile)

        elif output == 2:
            lab_num = self.lab_num.GetValue()
            title = self.title.GetValue()
            if not title:
                print("You must specify the Title before \n compiling a Lab Procedure.")
                return
            if lab_num:
                lab_num = int(lab_num)
            else:
                lab_num = None
            print('lab_num='+str(lab_num))
            outfile = pydocument.LabOutlineToLatex(mypath, lab_num, title, runlatex=runlatex, dvi=dvi)
        elif output == 3:
            print('yeah, 3!')
            print('mypath='+str(mypath))
            #pdb.set_trace()
            mypres = pypres.Presentation(filename=mypath)
            mypres.Initialize()
            mytitle = self.title.GetValue()
            if not mytitle:
                mytitle = 'My Title'
            mypres.ToLatex(title=mytitle)
            outfile = mypres.filename
            if runlatex:
                outfile = mypres.RunLatex(dvi=dvi)
        self.OutputChooser.SetPath(outfile)
        return outfile
