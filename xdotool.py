#!/usr/bin/env python

def send_xdotool_cmd(cmd_str):
    import subprocess
#    p = subprocess.Popen(['xdotool',cmd_str], \
#                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    xdotool_cmd = 'xdotool '+cmd_str
    p = subprocess.Popen(xdotool_cmd, shell=True, \
                         stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    output, errors = p.communicate()
    return output.strip()

def get_window_ids(cmd_str):
    win = send_xdotool_cmd(cmd_str)
    my_list = win.split('\n')
    return my_list

def windows_with_str_in_title(str_in):
    return get_window_ids('search --title %s' % str_in)

def GIMP_windows():
    return windows_with_str_in_title('GIMP')

def Untitled_windows():
    return windows_with_str_in_title('Untitled')

def get_Untitled_GIMP():
    GIMP_list = GIMP_windows()
    Untitled_list = Untitled_windows()
    filt_Untitled = [item for item in Untitled_list if \
                     item in GIMP_list]
    if len(filt_Untitled) == 1:
        return filt_Untitled[0]
    else:
        print('Could not find one Untitled window in GIMP list:')
        print('GIMP_list=%s' % GIMP_list)
        print('Untitled_list=%s' % Untitled_list)

def latex_eqn_preview_id():
    id_list = windows_with_str_in_title("'Latex Equation Preview'")
    if id_list[0]:
        return id_list[0]

def set_window_focus(id):
    send_xdotool_cmd('windowfocus %s' % id)

def activate_window(id):
    send_xdotool_cmd('windowfocus %s' % id)
    send_xdotool_cmd('windowraise %s' % id)
