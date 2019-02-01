#!/usr/bin/python

# pyxhook -- an extension to emulate some of the PyHook library on linux.
#
#    Copyright (C) 2008 Tim Alexander <dragonfyre13@gmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#    Thanks to Alex Badea <vamposdecampos@gmail.com> for writing the Record
#    demo for the xlib libraries. It helped me immensely working with these
#    in this library.
#
#    Thanks to the python-xlib team. This wouldn't have been possible without
#    your code.
#    
#    This requires: 
#    at least python-xlib 1.4
#    xwindows must have the "record" extension present, and active.
#    
#    This file has now been somewhat extensively modified by 
#    Daniel Folkinshteyn <nanotube@users.sf.net>
#    So if there are any bugs, they are probably my fault. :)
#
#	  and modified by gvb1234 as well ;-)
 
#import sys
#import os
import re
#import time
#import threading
 

try:
    from Xlib import X, XK, display#, error
#    from Xlib.ext import record
#    from Xlib.protocol import rq
    from Xlib.protocol.event import KeyPress
    from Xlib.protocol.event import KeyRelease
except ImportError:
    print('This script requires the python-xlib library')
 
#######################################################################
########################START CLASS DEF################################
#######################################################################
 
def lookup_keysym(keysym):
    for name in dir(XK):
        if name.startswith("XK_") and getattr(XK, name) == keysym:
            return name.lstrip("XK_")
    return "[%d]" % keysym    
    
class HookManager(object):
    """This is the main class. Instantiate it, and you can hand it KeyDown and KeyUp (functions in your own code) which execute to parse the pyxhookkeyevent class that is returned.
    This simply takes these two values for now:
    KeyDown = The function to execute when a key is pressed, if it returns anything. It hands the function an argument that is the pyxhookkeyevent class.
    KeyUp = The function to execute when a key is released, if it returns anything. It hands the function an argument that is the pyxhookkeyevent class.
    """
     
    def __init__(self):
         
        # Give these some initial values
        self.ison = {"shift":False, "caps":False}
         
        # Compile our regex statements.
        self.isshift = re.compile('^Shift')
        self.iscaps = re.compile('^Caps_Lock')
        self.shiftablechar = re.compile('^[a-z0-9]$|^minus$|^equal$|^bracketleft$|^bracketright$|^semicolon$|^backslash$|^apostrophe$|^comma$|^period$|^slash$|^grave$')
        self.logrelease = re.compile('.*')
        self.isspace = re.compile('^space$')
         
        # Assign default function actions (do nothing).
        self.KeyDown = lambda x: True
        self.KeyUp = lambda x: True
                 
        # Hook to our display.
        self.local_dpy = display.Display()

        self.is_running = True
         
    def cancel(self):
         self.local_dpy.flush()
     
    def printevent(self, event):

        if event.Key == 'Escape':
            self.cancel()

        print(event)
    
    def propagate(self,event):
        
        window = self.local_dpy.get_input_focus()._data['focus']
 
        # If is KeyPress event
        if event.type == X.KeyPress:
            # Get event class
            event_class = KeyPress
        # If is KeyRelease event
        elif event.type == X.KeyRelease:
            # Get event class
            event_class = KeyRelease
        else:
            return
 
        # Create event object
        new_event = event_class(
            detail=event.detail,
            time=event.time,
            root=event.root,
            window=window,
            child=X.NONE,
            root_x=event.root_x,
            root_y=event.root_y,
            event_x=event.event_x,
            event_y=event.event_y,
            state=event.state,
            same_screen=event.same_screen,
        )
 
        # Send event
        self.local_dpy.send_event(window, new_event, propagate=True)
 
        # Flush
        self.local_dpy.flush()


              
    def processevents(self,event):
 
        # If is KeyPress event
        if event.type == X.KeyPress:
            # Get event object
            hookevent = self.keypressevent(event)
 
            # Call event handler
            self.KeyDown(hookevent)
 
        # If is KeyRelease event
        elif event.type == X.KeyRelease:
            # Get event object
            hookevent = self.keyreleaseevent(event)
 
            # Call event handler
            self.KeyUp(hookevent)
 
        # If is not KeyPress or KeyRelease event
        else:
            # Ignore
            return
 
       # Return
        return hookevent
  
    def keypressevent(self, event):
        matchto = lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))

        if self.shiftablechar.match(lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))): ## This is a character that can be typed.
            if self.ison["shift"] == False:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
                return self.makekeyhookevent(keysym, event,True)
            else:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 1)
                return self.makekeyhookevent(keysym, event,True)
        else: ## Not a typable character.
            keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
            if self.isshift.match(matchto):
                self.ison["shift"] = self.ison["shift"] + 1
            elif self.iscaps.match(matchto):
                if self.ison["caps"] == False:
                    self.ison["shift"] = self.ison["shift"] + 1
                    self.ison["caps"] = True
                if self.ison["caps"] == True:
                    self.ison["shift"] = self.ison["shift"] - 1
                    self.ison["caps"] = False
            return self.makekeyhookevent(keysym, event,False)
     
    def keyreleaseevent(self, event):
        if self.shiftablechar.match(lookup_keysym(self.local_dpy.keycode_to_keysym(event.detail, 0))):
            printable=True
            if self.ison["shift"] == False:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
            else:
                keysym = self.local_dpy.keycode_to_keysym(event.detail, 1)
        else:
            printable=False
            keysym = self.local_dpy.keycode_to_keysym(event.detail, 0)
        matchto = lookup_keysym(keysym)
        if self.isshift.match(matchto):
            self.ison["shift"] = self.ison["shift"] - 1
        return self.makekeyhookevent(keysym, event,printable)
   
    def asciivalue(self, keysym):
        asciinum = XK.string_to_keysym(lookup_keysym(keysym))
        if asciinum < 256:
            return asciinum
        else:
            return 0
     
    def makekeyhookevent(self, keysym, event,printable):
        storewm = self.xwindowinfo()
        if event.type == X.KeyPress:
            MessageName = "key down"
        elif event.type == X.KeyRelease:
            MessageName = "key up"
        return pyxhookkeyevent(storewm["handle"], storewm["name"], storewm["class"], lookup_keysym(keysym), self.asciivalue(keysym), printable, event.detail, MessageName)
        
    def xwindowinfo(self):
        try:
            windowvar = self.local_dpy.get_input_focus().focus
            wmname = windowvar.get_wm_name()
            wmclass = windowvar.get_wm_class()
            wmhandle = str(windowvar)[20:30]
        except:
            ## This is to keep things running smoothly. It almost never happens, but still...
          return {"name":None, "class":None, "handle":None}
        if (wmname == None) and (wmclass == None):
            try:
                windowvar = windowvar.query_tree().parent
                wmname = windowvar.get_wm_name()
                wmclass = windowvar.get_wm_class()
                wmhandle = str(windowvar)[20:30]
            except:
                ## This is to keep things running smoothly. It almost never happens, but still...
                return {"name":None, "class":None, "handle":None}
        if wmclass == None:
            return {"name":wmname, "class":wmclass, "handle":wmhandle}
        else:
            return {"name":wmname, "class":wmclass[0], "handle":wmhandle}
 
class pyxhookkeyevent:
    """This is the class that is returned with each key event.
    It simply creates the variables below in the class.
     
    Window = The handle of the window.
    WindowName = The name of the window.
    WindowProcName = The backend process for the window.
    Key = The key pressed, shifted to the correct caps value.
    Ascii = An ascii representation of the key. It returns 0 if the ascii value is not between 31 and 256.
    Printable = A flag saying whether the key pressed is supposed to "type" something out (as opposed to, say, cursor keys).
    ScanCode = Please don't use this. It differs for pretty much every type of keyboard. X11 abstracts this information anyway.
    MessageName = "key down", "key up".
    """
     
    def __init__(self, Window, WindowName, WindowProcName, Key, Ascii, Printable, ScanCode, MessageName):
        self.Window = Window
        self.WindowName = WindowName
        self.WindowProcName = WindowProcName
        self.Key = Key
        self.Ascii = Ascii
        self.ScanCode = ScanCode
        self.Printable = Printable
        self.MessageName = MessageName
     
    def __str__(self):
        return "Window Handle: " + str(self.Window) + "\nWindow Name: " + str(self.WindowName) + "\nWindow's Process Name: " + str(self.WindowProcName) + "\nKey Pressed: " + str(self.Key) + "\nAscii Value: " + str(self.Ascii) + "\nScanCode: " + str(self.ScanCode) + "\nMessageName: " + str(self.MessageName) + "\n"
 

#######################################################################
#########################END CLASS DEF#################################
#######################################################################
