#!/usr/bin/env python

import wx

#from scipy import *

import os, cPickle, pdb, sys, re
import time
import rwkmisc
#reload(rwkmisc)

if len(sys.argv) > 1:
    headless = int(sys.argv[1])
else:
    headless = 0

if headless:
    frame_size = (400, 200)
    text_ctrl_size = (380, 50)
    sizer_rows = 2
else:
    frame_size = (900, 250)
    text_ctrl_size = (850, 50)
    sizer_rows = 3
    
import rwkos
#reload(rwkos)

#from PIL import Image

import latex_dvi_png

keyMap = {}

import os, copy

import rwkos

cache_dir = latex_dvi_png.find_cache_dir()

from xdotool import send_xdotool_cmd, get_window_ids, \
     windows_with_str_in_title, GIMP_windows, \
     Untitled_windows, get_Untitled_GIMP, activate_window, \
     latex_eqn_preview_id, set_window_focus, read_window_id
    
def gen_keymap():
    keys = ("BACK", "TAB", "RETURN", "ESCAPE", "SPACE", "DELETE", "START",
        "LBUTTON", "RBUTTON", "CANCEL", "MBUTTON", "CLEAR", "PAUSE",
        "CAPITAL", "PRIOR", "NEXT", "END", "HOME", "LEFT", "UP", "RIGHT",
        "DOWN", "SELECT", "PRINT", "EXECUTE", "SNAPSHOT", "INSERT", "HELP",
        "NUMPAD0", "NUMPAD1", "NUMPAD2", "NUMPAD3", "NUMPAD4", "NUMPAD5",
        "NUMPAD6", "NUMPAD7", "NUMPAD8", "NUMPAD9", "MULTIPLY", "ADD",
        "SEPARATOR", "SUBTRACT", "DECIMAL", "DIVIDE", "F1", "F2", "F3", "F4",
        "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "F13", "F14",
        "F15", "F16", "F17", "F18", "F19", "F20", "F21", "F22", "F23", "F24",
        "NUMLOCK", "SCROLL", "PAGEUP", "PAGEDOWN", "NUMPAD_SPACE",
        "NUMPAD_TAB", "NUMPAD_ENTER", "NUMPAD_F1", "NUMPAD_F2", "NUMPAD_F3",
        "NUMPAD_F4", "NUMPAD_HOME", "NUMPAD_LEFT", "NUMPAD_UP",
        "NUMPAD_RIGHT", "NUMPAD_DOWN", "NUMPAD_PRIOR", "NUMPAD_PAGEUP",
        "NUMPAD_NEXT", "NUMPAD_PAGEDOWN", "NUMPAD_END", "NUMPAD_BEGIN",
        "NUMPAD_INSERT", "NUMPAD_DELETE", "NUMPAD_EQUAL", "NUMPAD_MULTIPLY",
        "NUMPAD_ADD", "NUMPAD_SEPARATOR", "NUMPAD_SUBTRACT", "NUMPAD_DECIMAL",
        "NUMPAD_DIVIDE")
    
    for i in keys:
        keyMap[getattr(wx, "WXK_"+i)] = i
    for i in ("SHIFT", "ALT", "CONTROL", "MENU"):
        keyMap[getattr(wx, "WXK_"+i)] = ''

def GetKeyPress(evt):
    keycode = evt.GetKeyCode()
    keyname = keyMap.get(keycode, None)
    modifiers = ""
    for mod, ch in ((evt.ControlDown(), 'Ctrl+'),
                    (evt.AltDown(),     'Alt+'),
                    (evt.ShiftDown(),   'Shift+'),
                    (evt.MetaDown(),    'Meta+')):
        if mod:
            modifiers += ch

    if keyname is None:
        if 27 < keycode < 256:
            keyname = chr(keycode)
        else:
            keyname = "(%s)unknown" % keycode
    return modifiers + keyname
    #return keyname

#settingsname = 'pytexguisettings.pkl'
## def Load_PIL_and_Resize(pathin, size):
##     img = Image.open(pathin)
##     #img2 = copy.deepcopy(img)#return fullsize copy along with resized
##     img.thumbnail(size, Image.CUBIC)#Image.ANTIALIAS)
##     return img#, img2

## def PIL_to_wx(img):
##     image = wx.EmptyImage(img.size[0],img.size[1])
##     image.SetData(img.convert("RGB").tostring())
##     return wx.BitmapFromImage(image)


class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, -1, title,
                          pos=(150, 500), size=frame_size)
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

        self.p_re = re.compile('\$\$(.*?)\$\$')
        #create top level controls (i.e. those not on a notebook page)
        #create the main directory chooser
        imageFile = os.path.join(cache_dir, 'temp_out1.png')
        if not os.path.exists(imageFile):
            pngpath = latex_dvi_png.eq_to_dvi_png('\v{x} = \\twobyone{1/3}{1}')
        mysize = self.GetSize()
        w, h = mysize
        #w = 500
        #h = 100
        #pil = Load_PIL_and_Resize(imageFile, [int(0.95*w), int(0.7*h)])
        #wxbmp = PIL_to_wx(pil)

        if not headless:
            png1 = wx.Image(imageFile, wx.BITMAP_TYPE_ANY)
            pw, ph = png1.GetSize()
            aspect_ratio = float(pw)/float(ph)
            new_w = 400
            new_h = 100
            png1.Rescale(int(new_w), int(new_h))
            wxbmp = png1.ConvertToBitmap()
            self.bmp = wx.StaticBitmap(self, -1, wxbmp, \
                                       (10 + wxbmp.GetWidth(), 5), \
                                       (wxbmp.GetWidth(), \
                                        wxbmp.GetHeight()))
        #change the size if headless
        self.text = wx.TextCtrl(self, -1, "", size=text_ctrl_size,
                                style = wx.TE_MULTILINE
                                |wx.WANTS_CHARS
                                #|wx.TE_CHARWRAP 
                                |wx.TE_WORDWRAP
                                #| wx.TE_RICH
                                #| wx.TE_RICH2
                                )
        myfont = wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.NORMAL, \
                         False, u'Nimbus Roman No 9')
        #self.bmp.SetSize([300, 100])
        self.text.SetFont(myfont)
        self.exitbutton = wx.Button(self, -1, "Exit")
        self.refresh_button = wx.Button(self, -1, "Refresh")
        self.eqn_button = wx.Button(self, -1, "Eqn. LaTeX")
        self.tex_button = wx.Button(self, -1, "LaTeX")

        buttonsizer = wx.FlexGridSizer(1, 4, 0, 0)
        buttonsizer.Add(self.tex_button, 1, wx.ALL, 5)
        buttonsizer.Add(self.eqn_button, 1, wx.ALL, 5)
        buttonsizer.Add(self.refresh_button, 1, wx.ALL, 5)
        buttonsizer.Add(self.exitbutton, 1, wx.ALL, 5)
        
        mainsizer = wx.FlexGridSizer(sizer_rows, 1, 0, 0)
        mainsizer.AddGrowableCol(0)
        mainsizer.AddGrowableRow(0)
        #add the controls to the main sizer
        if not headless:
            mainsizer.AddGrowableRow(1)
            mainsizer.Add(self.bmp, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5)
        mainsizer.Add(self.text, 1, wx.EXPAND|wx.ALL|wx.ALIGN_RIGHT, 5)
        mainsizer.Add(buttonsizer, 1, wx.ALL|wx.ALIGN_RIGHT, 5)

        self.Bind(wx.EVT_BUTTON, self.On_Tex_Button, self.tex_button)
        self.Bind(wx.EVT_BUTTON, self.On_Eqn_Tex_Button, \
                                 self.eqn_button)
        self.Bind(wx.EVT_BUTTON, self.On_Refresh_Button,\
                                 self.refresh_button)
        self.Bind(wx.EVT_BUTTON, self.OnTimeToClose, self.exitbutton)
        self.text.Bind(wx.EVT_KEY_DOWN, self.KeyPressed, self.text)


##         self.startdir = os.getcwd()
##         self.settingspath = os.path.join(self.startdir, settingsname)

##         if self.startdir not in sys.path:
##             sys.path.insert(0, self.startdir)
        
        self.SetSizer(mainsizer)
##         self.savepanellist = [self.texpypane, self.purelatexpane, self.pyppane, self.fancyhdrpane, self.wltpane]
        #mainsizer.Fit(self)
        self.Layout()
        if not headless:
            self.load_png(imageFile)
        self.text.SetFocus()
        self.my_id = None

    def _size_png(self, png):
        mysize = self.GetSize()
        w, h = mysize
        pw, ph = png.GetSize()
        aspect_ratio = float(pw)/float(ph)
        new_w = w*0.95
        new_h = new_w/aspect_ratio
        if new_h > 100:
            new_h = 100
            new_w = aspect_ratio*new_h
        png.Rescale(int(new_w), int(new_h))
        return png
        
    def load_png(self, pngpath):
        png1 = wx.Image(pngpath, wx.BITMAP_TYPE_ANY)
        self._size_png(png1)
        wxbmp = png1.ConvertToBitmap()
        self.bmp.SetBitmap(wxbmp)

    def clean_double_dollar_signs(self, text):
        return self.p_re.sub(r'\n\\begin{equation*}\n\1\n\end{equation*}\n', \
                             text)

    def _get_clean_text(self):
        raw_text = self.text.GetValue()
        print('raw_text = %s' % raw_text)
        text = raw_text.replace('\n' ,' ')
        text = self.clean_double_dollar_signs(text)
        return text
    
    def On_Tex_Button(self, evt):
        """Run LaTeX on the connents of the text control and show the
        result in the png viewer."""
        text = self._get_clean_text()
        pngpath = latex_dvi_png.latex_to_dvi_png(text)
        if not headless:
            self.load_png(pngpath)

    def On_Eqn_Tex_Button(self, evt):
        text = self._get_clean_text()        
        pngpath = latex_dvi_png.eq_to_dvi_png(text)
        if not headless:
            self.load_png(pngpath)

    def On_Refresh_Button(self, evt):
        print('in On_Refresh_Button')

    def KeyPressed(self, evt):
        keycode = evt.GetKeyCode()
        flist = [346]#seem to go in order 346 = f7
        if keycode==92 and (evt.ControlDown() or evt.AltDown()):
            #ctrl or alt \
            if evt.AltDown():
                print('AltDown = True')
                self.On_Tex_Button(evt)
            else:
                self.On_Eqn_Tex_Button(evt)
            GIMP_id = read_window_id()
            if self.my_id is None:
                self.my_id = latex_eqn_preview_id()
            set_window_focus(GIMP_id)
            time.sleep(0.5)
            send_xdotool_cmd('key "F7"')
            set_window_focus(self.my_id)

        elif keycode==77 and evt.ControlDown():#ctrl + m
            #new equation without clearing the text box
            GIMP_id = read_window_id()
            activate_window(GIMP_id)
            time.sleep(0.25)
            send_xdotool_cmd('key "shift+F8"')
        elif keycode==78 and evt.ControlDown():#ctrl + n
            #new equation and clear the text box
            self.text.SetValue("")
            GIMP_id = read_window_id()
            activate_window(GIMP_id)
            time.sleep(0.25)
            send_xdotool_cmd('key "shift+F8"')
        elif keycode==69 and evt.ControlDown():#ctrl + e
            self.text.SetValue("")
        elif keycode==344:#F5
            untitled_GIMP_id = get_Untitled_GIMP()
            if untitled_GIMP_id:
                activate_window(untitled_GIMP_id)
                send_xdotool_cmd('key "F11"')
                return
        print('keycode=%s' % keycode)
        print('evt.ControlDown()=%s' % evt.ControlDown())
        if keycode not in flist:
            evt.Skip()
            return
##         print('keycode=%s' % keycode)
##         print('type(keycode)=%s' % type(keycode))
##         print('evt.ControlDown()=%s' % evt.ControlDown())
##         print('evt.AltDown()=%s' % evt.AltDown())
##         print('evt.ShiftDown()=%s' % evt.ShiftDown())
        if evt.ControlDown():
            self.On_Tex_Button(evt)
        else:
            self.On_Eqn_Tex_Button(evt)


    def OnTimeToClose(self, evt):
        """Event handler for the button click."""
#        self.SaveSettings()
        print('closing...')
        self.Close()


class MyApp(wx.App):
    def OnInit(self):
        frame = MyFrame(None, "LaTeX Equation Preview")
        self.SetTopWindow(frame)

        #print "Print statements go to this stdout window by default."

        frame.Show(True)
        return True
        

if __name__ == "__main__":
    app = MyApp(redirect=False)
    app.MainLoop()
