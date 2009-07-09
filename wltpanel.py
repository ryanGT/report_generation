import wx

import os, cPickle, pdb

import pytexpanel
#import texpy
#import pytex
import texmaxima
import latexpanel
import replacelist
import pytexutils

import wxmlit
#import textfiles
#reload(textfiles)
#import textfiles.maximalist
#reload(textfiles.maximalist)
#import textfiles.latexlist
#reload(textfiles.latexlist)
#from textfiles.latexlist import RunLatex


BROWSEBUTTON=wx.NewEventType()
import reusablepanels
from reusablepanels.rwkSingleFileChooser_v2 import rwkSingleFileChooser
from reusablepanels.rwkdirchooserpanel import rwkdirchooserpanel

savesettingsname = 'wltpanelsettings.pkl'

class WLTPanel(pytexpanel.PyTexPanel):
    def __init__(self, parent, dircontrol=None, fancyhdrpanel=None):
        # begin wxGlade: rwksinglefilechooser.__init__
        pytexpanel.PyTexPanel.__init__(self, parent, dircontrol=dircontrol, fancyhdrpanel=None)
        
        #self.filechooser = rwkSingleFileChooser(self)
        self.filechooser = pytexpanel.PyTexChooserPanel(self, dircontrol=dircontrol, postmethods=[])#self.LoadTexFile])
        self.filechooser.SetFilter("WLT Files (*.wlt)|*.wlt|All Files (*.*)|*.*")
        self.filechooser.SetLabel('Maxima Input File')
        self.fancyhdrpanel = fancyhdrpanel

        mysizer = wx.FlexGridSizer(10, 1, 0, 0)
        mysizer.AddGrowableCol(0)


        self.latexopts = latexpanel.LatexOptionsPanel2(self)

        self.runbutton = wx.Button(self, -1, "Run")

        self.OutputChooser = pytexpanel.PyTexChooserPanel(self, dircontrol=dircontrol, postmethods=[])
        self.OutputChooser.SetLabel('LaTeX Output File')


        translations_label = wx.StaticText(self, -1, "Translators", (-1,30))

        # WXM -> WLT translator
        self.wxmchooser = pytexpanel.PyTexChooserPanel(self, dircontrol=dircontrol, postmethods=[])#self.LoadTexFile])
        self.wxmchooser.SetFilter("WXM Files (*.wxm)|*.wxm|All Files (*.*)|*.*")
        self.wxmchooser.SetLabel('WXM Input File')
        self.wxmtowltbutton = wx.Button(self, -1, "wxm -> wlt")

        # WLT -> texmaxima translator
        self.wltchooser = pytexpanel.PyTexChooserPanel(self, dircontrol=dircontrol, postmethods=[])#self.LoadTexFile])
        self.wltchooser.SetFilter("WLT Files (*.wlt)|*.wlt|All Files (*.*)|*.*")
        self.wltchooser.SetLabel('WLT Input File')
        self.wlttotexmaximabutton = wx.Button(self, -1, "wlt -> texmaxima")

        # Texmaxima output
        self.texmaximaoutput = pytexpanel.PyTexChooserPanel(self, dircontrol=dircontrol, postmethods=[])#self.LoadTexFile])
        self.texmaximaoutput.SetLabel('Texmaxima Output')
        self.texmaximaoutput.SetFilter("tex Files (*.tex)|*.tex|All Files (*.*)|*.*")
        
        
        #row 0
        mysizer.Add(self.filechooser, 1, wx.EXPAND|wx.ALL, 0)
        #row 1
        mysizer.Add(self.latexopts, 1, wx.EXPAND|wx.ALL, 0)
        #row 2
        mysizer.Add(self.runbutton, 1, wx.ALL|wx.ALIGN_RIGHT, 5)
        #row 3
        mysizer.Add(self.OutputChooser, 1, wx.EXPAND|wx.ALL, 0)
        #row 4
        mysizer.Add(translations_label, 1, wx.ALL, 5)
        #row 5
        mysizer.Add(self.wxmchooser, 1, wx.ALL|wx.EXPAND, 0)
        #row 6
        mysizer.Add(self.wxmtowltbutton, 1, wx.ALL|wx.ALIGN_RIGHT, 5)
        #row 7
        mysizer.Add(self.wltchooser, 1, wx.ALL|wx.EXPAND, 0)
        #row 8
        mysizer.Add(self.wlttotexmaximabutton, 1, wx.ALL|wx.ALIGN_RIGHT, 5)
        #row 9
        mysizer.Add(self.texmaximaoutput, 1, wx.ALL|wx.EXPAND, 0)


        ##################
        #
        #  Saving settings
        #
        ##################
        self.GetMainDir()
        self.settingspath = os.path.join(self.maindir, savesettingsname)

        savekeys = ['path', 'latexdict', 'outputpath']
        getmethods = [self.filechooser.GetPath, self.latexopts.GetSettings, self.OutputChooser.GetPath]
        setmethods = [self.filechooser.SetPath, self.latexopts.SetSettings, self.OutputChooser.SetPath]
        self.savedict = dict(zip(savekeys, getmethods))
        self.loaddict = dict(zip(savekeys, setmethods))


        ##################
        #
        #  Bind Events
        #
        ##################
        self.Bind(wx.EVT_BUTTON, self.EvtRunButton, self.runbutton)
        self.Bind(wx.EVT_BUTTON, self.EvtWXMtoWLTButton, self.wxmtowltbutton)
        self.Bind(wx.EVT_BUTTON, self.EvtWLTtoTexmaxima, self.wlttotexmaximabutton)

        #self.mylabel.Hide()

        self.SetSizer(mysizer)
        #mainsizer.Fit(self)
        self.Layout()


    def EvtWXMtoWLTButton(self, event):
        wxmpath = self.wxmchooser.GetPath()
        wxmfile = wxmlit.wxmFile(wxmpath)
        wltfile = wxmfile.ToWLT()
        self.wltchooser.SetPath(wltfile.pathin)


    def EvtWLTtoTexmaxima(self, event):
        wltpath = self.wltchooser.GetPath()
        wlttrans = texmaxima.WLTTranslator(wltpath)
        wlttrans.Read()
        latexlist = wlttrans.Translate()#a pure Python list
        pno, ext = os.path.splitext(wltpath)
        texpath = pno+'.tex'
        pytexutils.writefile(texpath, latexlist)
        self.texmaximaoutput.SetPath(texpath)
        

    def EvtRunButton(self, event):
        #get the path to the starting wlt file
        wltpath = self.filechooser.GetPath()
        
        #convert to wxm and save
        wltfile = wxmlit.wxmLitFile(wltpath)
        wxmfile = wltfile.ToWXM()

        #wxm to LaTeX in (this is not a legitimate tex file - it includes \maxima{...} and similar environments
        wxmpath = wxmfile.pathin
        fno,ext = os.path.splitext(wxmpath)
        texpath = fno+'.tex'

        print('wxmpath='+wxmpath)
        print('texpath='+texpath)

        wlttrans = texmaxima.WLTTranslator(wltpath)
        wlttrans.Read()
        latexlist = wlttrans.Translate()#a pure Python list
        pytexutils.writefile(texpath, latexlist)

        findlist = []
        self.replacelist = replacelist.ReplaceList()
        self.replacelist.ReadFRFile()

        optdict = self.latexopts.GetSettings()
        
        if optdict['usefancyhdr'] and (self.fancyhdrpanel is not None):
            headerlines = self.fancyhdrpanel.GetLatexLines()
            print('\n'*3)
            print('fancyhdrpanel lines:')
            for line in headerlines:
                print line
            print('\n'*3)

            
        inpath = texpath
        pno, ext = os.path.splitext(inpath)
        outpath2 = pno+'_out.tex'
        self.texmaxima = texmaxima.TexMaximaFile(inpath)
        self.texmaxima.RunMaxima()
        self.texmaxima.SubstituteLatex(echo=0, replacelist=self.replacelist)
        self.texmaxima.AddHeader()

        if optdict['usefancyhdr'] and (self.fancyhdrpanel is not None):
            headerlines = self.fancyhdrpanel.GetLatexLines()
            print('\n'*3)
            print('fancyhdrpanel lines:')
            for line in headerlines:
                print line
            print('\n'*3)
            self.texmaxima.HeaderInsert(headerlines)
            
        self.texmaxima.SaveLatex(filename=outpath2)
        maxfindlist = self.texmaxima.FindReplacePats()
        findlist.extend(maxfindlist)

        self.replacelist.AppendFRFile(findlist)

        
        if optdict['runlatex']:
            outputpath3 = pytexutils.RunLatex(outpath2, sourcespecials=True, log=None, **optdict)
            self.OutputChooser.SetPath(outputpath3)
        else:
            self.OutputChooser.SetPath(outpath2)

        
