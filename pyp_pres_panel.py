import wx

import os, cPickle, pdb, subprocess

import persistent_panel

from rwkSingleFileChooser_v2 import rwkSingleFileChooser

import pyp_converter, rwkos

def_values = {'author':'Ryan Krauss','title':'My Title', \
              'theme':'siue_Cambridge'}

themes = ['ryan_Warsaw', \
          'siue_Cambridge', \
          'AnnArbor', \
          'Antibes', \
          'Bergen', \
          'Berkeley', \
          'Berlin', \
          'Boadilla', \
          'CambridgeUS', \
          'Copenhagen', \
          'Darmstadt', \
          'Dresden', \
          'Frankfurt', \
          'Goettingen', \
          'Hannover', \
          'Ilmenau', \
          'JuanLesPins', \
          'Luebeck', \
          'Madrid', \
          'Malmoe', \
          'Marburg', \
          'Montpellier', \
          'PaloAlto', \
          'Pittsburgh', \
          'Rochester', \
          'Singapore', \
          'Szeged', \
          'Warsaw']

go_button_id = wx.NewId()
launch_pdf_id = wx.NewId()

import rwkos


class main_panel(persistent_panel.Persistent_Panel):
    def __init__(self, parent, *args, **kwds):
        persistent_panel.Persistent_Panel.__init__(self, parent, \
                                                   *args, **kwds)
        self.maindir = os.getcwd()

        self.filechooser = rwkSingleFileChooser(self)
        self.filechooser.filter = "PYP File (*.pyp)|*.pyp|All Files (*.*)|*.*"
        self.author_label = wx.StaticText(self, -1, "Author")
        self.author_box = wx.TextCtrl(self, -1, "")
        self.title_label = wx.StaticText(self, -1, "Title")
        self.title_box = wx.TextCtrl(self, -1, "")
        self.theme_label = wx.StaticText(self, -1, "Beamer Theme")
        self.theme_box = wx.ComboBox(self, -1, choices=themes)
        self.draft_label = wx.StaticText(self, -1, "Draft")
        self.draft_check = wx.CheckBox(self, -1)
        self.go_button = wx.Button(self, go_button_id, "Go")
        self.pdf_button = wx.Button(self, launch_pdf_id, "Open PDF")


        self.only_one_label = wx.StaticText(self, -1, "Only One Slide")
        self.only_one_check = wx.CheckBox(self, -1)

        self.slide_num_label = wx.StaticText(self, -1, "Slide Number")
        self.slide_num_box = wx.TextCtrl(self, -1, "-1")

        only_one_sizer = wx.GridSizer(2,2)

        TLR = wx.TOP|wx.LEFT|wx.RIGHT
        BLR = wx.BOTTOM|wx.LEFT|wx.RIGHT
        
        only_one_sizer.Add(self.only_one_label, 0, TLR, 5)
        only_one_sizer.Add(self.slide_num_label, 0, TLR, 5)
        only_one_sizer.Add(self.only_one_check, 0, BLR, 5)
        only_one_sizer.Add(self.slide_num_box, 0, BLR, 5)
        

        self.Bind(wx.EVT_BUTTON, self.On_Go_Button, self.go_button)
        self.Bind(wx.EVT_BUTTON, self.Launch_PDF, self.pdf_button)
        # Use a sizer to layout the controls, stacked vertically and with
        # a 10 pixel border around each

        ##################
        #
        #  Saving settings
        #
        ##################
        savesettingsname = 'pyp_pres_panel_settings.pkl'
        self.settingspath = os.path.join(self.maindir, savesettingsname)
        savekeys = ['path','author','title','theme','draft',\
                    'onlyone','slidenum']
        getmethods = [self.filechooser.GetPath, \
                      self.author_box.GetValue, \
                      self.title_box.GetValue, \
                      self.theme_box.GetValue,\
                      self.draft_check.GetValue,
                      self.only_one_check.GetValue, \
                      self.slide_num_box.GetValue]

        setmethods = [self.filechooser.SetPath, \
                      self.author_box.SetValue, \
                      self.title_box.SetValue, \
                      self.theme_box.SetValue, \
                      self.draft_check.SetValue, \
                      self.only_one_check.SetValue, \
                      self.slide_num_box.SetValue]
        
        self.savedict = dict(zip(savekeys, getmethods))
        self.loaddict = dict(zip(savekeys, setmethods))

        self.LoadSettings(defaults=def_values)

        self.Initialize()
        
        #sizer and layout
        grid_sizer = wx.FlexGridSizer(11, 1, 0, 0)        
        grid_sizer.Add(self.filechooser, 0, wx.ALL|wx.EXPAND, 5)
        grid_sizer.Add(self.author_label, 0, wx.TOP|wx.LEFT|wx.RIGHT, 5)
        grid_sizer.Add(self.author_box, 0, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        grid_sizer.Add(self.title_label, 0, wx.TOP|wx.LEFT|wx.RIGHT, 5)
        grid_sizer.Add(self.title_box, 0, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        grid_sizer.Add(self.theme_label, 0, wx.TOP|wx.LEFT|wx.RIGHT, 5)
        grid_sizer.Add(self.theme_box, 0, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)
        grid_sizer.Add(self.draft_label, 0, wx.TOP|wx.LEFT|wx.RIGHT, 5)
        grid_sizer.Add(self.draft_check, 0, wx.BOTTOM|wx.LEFT|wx.RIGHT|wx.EXPAND, 5)

        grid_sizer.Add(only_one_sizer, 0, wx.ALL, 5)
        grid_sizer.Add(self.go_button, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        grid_sizer.Add(self.pdf_button, 0, wx.ALL|wx.ALIGN_RIGHT, 5)
        grid_sizer.AddGrowableCol(0)
        self.SetSizer(grid_sizer)
        self.Layout()


    def Initialize(self):
        self.Build_PDF_Path()


    def Build_PDF_Path(self):
        path = self.Get_Path()
        if path:
            p_no_e, ext = os.path.splitext(path)
            self.pdfpath = p_no_e+'.pdf'
            

    def Get_Draft(self):
        return self.draft_check.GetValue()


    def Get_Author(self):
        return self.author_box.GetValue()
    

    def Get_Title(self):
        return self.title_box.GetValue()


    def Get_Theme(self):
        return self.theme_box.GetValue()


    def Get_Path(self):
        return self.filechooser.GetPath()


    def Get_Only_One_Ind(self):
        if self.only_one_check.GetValue():
            myind = int(self.slide_num_box.GetValue())
            return [myind]
        else:
            return None
        

    def Launch_PDF(self, event=0):
        self.Build_PDF_Path()
        path = rwkos.FindFullPath(self.pdfpath)
        if rwkos.amiLinux():
            pdfcmd = 'kpdf %s &'
            cmd = pdfcmd % path
            print(cmd)
            os.system(cmd)
        else:
            pdfcmd = 'AcroRd32.exe %s'
            cmd = pdfcmd % path
            print(cmd)
            subprocess.Popen(cmd)
        

    
    def On_Go_Button(self, event):
        draft = self.Get_Draft()
        theme = self.Get_Theme()
        title = self.Get_Title()
        author = self.Get_Author()
        path = self.Get_Path()
        self.Build_PDF_Path()

        slidenums = self.Get_Only_One_Ind()
        
        path = rwkos.FindFullPath(path)
        print('path='+path)
        
        my_pres = pyp_converter.Beamer_pres(path, draft=draft, author=author, \
                                            title=title, theme=theme)
        my_pres.to_latex(slidenums=slidenums)
        my_pres.save()
        #if options.runlatex:
        my_pres.run_latex()
        pathout = my_pres.pathout
        
        



class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title,
                          pos=(150, 150), size=(650, 500))
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

        self.panel = main_panel(self)


    def OnTimeToClose(self, event):
        print('got OnTimeToClose event')
        self.panel.SaveSettings()
        self.Close()




class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "PYP Presentation Generator")
        self.SetTopWindow(frame)

        #print "Print statements go to this stdout window by default."

        frame.Show(True)
        return True


if __name__ == "__main__":
    app = MyApp(redirect=False)
    app.MainLoop()
