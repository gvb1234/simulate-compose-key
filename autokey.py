#!/usr/bin/python3

# original Copyright (C) 2008 Sam Peterson

# modified by gvb1234

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

try:
    import Xlib.X as X
#    import Xlib.XK
    import Xlib.display as display
    import Xlib.ext.xtest as xtest

except ImportError:
    print('This script requires the python-xlib library')

import re,os
import pyhook3

from subprocess import check_output, CalledProcessError

def find_empty_keycode():
    '''
    Look for an unassigned keycode for the current xmodmap
    '''
    out=check_output(["xmodmap", '-pke'])    
    empties=[]
    for line in out.decode().split('\n'):
        if '=' in line:
            [keycode,val]=line.split('=')
            if len(val)==0:
                empties.append(int(keycode.replace('keycode ','').replace(' ','')))
                
    return empties[-1]


def is_process_running(process):
    '''
    Checks whether process is running.
    '''
    try:
        pidlist = map(int, check_output(["pidof", process]).split())
    except  CalledProcessError:
        pidlist = []
#    print('list of PIDs = ' + ', '.join(str(e) for e in pidlist))
    return len([pid for pid in pidlist])>0

# get the current display
disp=display.Display()

# constants
Multi_Key=[x for x in range(8,256) if pyhook3.lookup_keysym(disp.keycode_to_keysym(x, 0)) == 'Multi_key'][0]
Return=[x for x in range(8,256) if pyhook3.lookup_keysym(disp.keycode_to_keysym(x, 0)) == 'Return'][0]
Shift_L=[x for x in range(8,256) if pyhook3.lookup_keysym(disp.keycode_to_keysym(x, 0)) == 'Shift_L'][0]
Less=[x for x in range(8,256) if pyhook3.lookup_keysym(disp.keycode_to_keysym(x, 0)) == 'less'][0]

try:
#   try getting the keycode for F16    
    F16=[x for x in range(8,256) if pyhook3.lookup_keysym(disp.keycode_to_keysym(x, 0)) == 'F16'][0]
except:
#   if the above failed, there is no F16 key yet, so we look for an empty keycode to assign it to 
    keycode=find_empty_keycode()
    os.system('xmodmap -e "keycode {} = F16"'.format(keycode))
    F16=[x for x in range(8,256) if pyhook3.lookup_keysym(disp.keycode_to_keysym(x, 0)) == 'F16'][0]
    
#print(Multi_Key,F16,Return,Shift_L,Less)

def possible_match(input):
    '''
    Check whether our current input so far matches (the beginning of) one key of the full compose map
    '''
    global compose_map
    for key in compose_map.keys():
        if key[0:len(input)] == input:
            return True
#    print("key not found, stopping input")
    return False

def stop_grab(display):
    '''
    Free the keyboard
    '''
    display.ungrab_keyboard(X.CurrentTime)
    display.flush()

def send_sequence(display, root, sequence):
    '''
    Send a sequence of keys
    '''
    for char in sequence2codes(display, sequence):
        send_key(root, char)

def sequence2codes(display, sequence):
    '''Convert a string to a series of keycodes to be gobled by CRiSP.'''
#   start with F16
    codes = [F16]
    for string in sequence:
#       add "<" to signal start of character
        codes.append(Less)
        for letter in string:
            if letter.isupper():
                # tuple indicates key with modifier pressed
                codes.append((Shift_L,display.keysym_to_keycode(ord(letter))))
            else:
                # int means regular keycode
                codes.append(display.keysym_to_keycode(ord(letter)))
#       add ">" to signal end of character
        codes.append((Shift_L,Less))
#   finish with "Return"
    codes.append(Return)
    return codes

def send_key(window, keycode):
    '''Send a KeyPress and KeyRelease event'''
    if type(keycode) == tuple:
        # send with modifier
        xtest.fake_input(window, X.KeyPress, keycode[0])
        xtest.fake_input(window, X.KeyPress, keycode[1])
        xtest.fake_input(window, X.KeyRelease, keycode[1])
        xtest.fake_input(window, X.KeyRelease, keycode[0])
    else:
        # send without modifier
        xtest.fake_input(window, X.KeyPress, keycode)
        xtest.fake_input(window, X.KeyRelease, keycode)

def handle_keypress( display, root_window,HM):
    '''Grabs the keyboard and listens for compose_map sequences'''
    global compose_map
    root_window.grab_keyboard(True, X.GrabModeAsync,
                              X.GrabModeAsync, X.CurrentTime)

#   these will hold our input
    myinput = "" # in sequences of <KEYSYM> (possible keys to compose_map)
    myascii = [] # as ascii to be sent as input if composing fails
    myinput2 = [] # list of KEYSIM

    while True: # loop until explicit break
        event = root_window.display.next_event()
        hookevent=HM.processevents(event) # process the event, takes care of shift, and other crap

        if event.type == X.KeyRelease: # act on keypresses only
            if hookevent.Printable:  # this event contains a "printable" character
                if HM.ison['shift']:
                    event = root_window.display.next_event()
                    HM.processevents(event)
                    myascii.append((Shift_L,hookevent.ScanCode))
                else:
                    myascii.append(hookevent.ScanCode)
                myinput += '<%s>' %hookevent.Key # add the <KEYSYM> to myinput
                myinput2.append(hookevent.Key)

                if myinput in compose_map.keys(): # the compose_map contains a translation

                    stop_grab(display)           # we stop the grab
                    print('Match found. Sending "{}" to active window...'.format(myinput))
                    send_sequence(display,root_window,myinput2)
                    display.flush()

                    return # our job is done

                if not possible_match(myinput):

                    print('No match found. sending "{}" to active window...'.format(myinput))
                    stop_grab(display)
                    for k in myascii:
                        send_key(root_window,k)

                    return

            if event.detail == 9:
                # Esc pressed, ungrab keyboard
                stop_grab(display)
                HM.is_running = False # comment this when everything is working ?
                return

def read_compose_map(compose_file='/usr/share/X11/locale/en_US.UTF-8/Compose'): 
    '''Build the main compose map.'''

    quoted = re.compile('"([^"]*)"')

    compose_map={}
    with open(compose_file) as file:
#       get the lines
        lines=file.readlines()
#       keep only the ones starting with <Multi_key>
        lines=[x for x in lines if len(x)>11 and x[0:11]=='<Multi_key>']
        for line in lines:
#           go over the lines
            if line.find('\t:')>0:
                key,val=line.split('\t:')
                key=key.replace('<Multi_key> ','')
                key=re.sub(r'\s+','',key) # strip whitespaces
                val=val.rstrip() # strip trailing \n
                [val,description]=val.split('# ') # get the description part

                tpr=quoted.findall(val)[0] # extract the content of the first quoted pair
                val=val.replace('"{}"'.format(tpr),'') # strip the first quoted pair
                unicode_val=re.sub(r'\s+','',val) # this is the part that is sandwiched between the " and the #

                val={'printable': tpr , 'unicode': unicode_val , 'description': description }

                compose_map[key]=val

    return compose_map


def main():

    global compose_map
    compose_map=read_compose_map()
    HM=pyhook3.HookManager()

    disp=HM.local_dpy

    root = disp.screen().root
#    root.change_attributes(event_mask = X.KeyPressMask)

#   grab the Multi_Key
    root.grab_key(Multi_Key, X.AnyModifier, 0, X.GrabModeAsync, X.GrabModeAsync)
    try:
        # loop until keyboard interrupt or explicit kill
        while HM.is_running and is_process_running('crisp'):

            event = root.display.next_event() # should block until Multi_Key is pressed

            if event.type == X.KeyRelease:

                hookevent=HM.processevents(event)
                if hookevent.WindowProcName =='crisp':
#                   we are only processing events for CRiSP 
                    handle_keypress(disp, root,HM)
                else:
#                   otherwise, propagate 
                    HM.propagate(event)

            if event.type == X.KeyPress:
                hookevent=HM.processevents(event)
                if hookevent.WindowProcName =='crisp':
#                   for CRiSP, we don't care when Multi_Key is pressed, only released
                    pass
                else:
#                   don't forget to propagate 
                    HM.propagate(event)

#       destroy the HookManager
        HM.cancel()
#       release the Multi_Key 
        root.ungrab_key(Multi_Key, 0)

    except KeyboardInterrupt:
        print('Bye!')

if __name__ == '__main__':

    main()
