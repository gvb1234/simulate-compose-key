# simulate-compose-key

The goal of this (small, linux) project is to:

  1) catch the "compose key" press (Multi_Key) in linux
  2) if the focus is not in a specific application, propagate that key press (and release) for normal use, but otherwise, catch the next few keys as long as they make up a valid sequence, such as found in 
  
      /usr/share/X11/locale/en_US.UTF-8/Compose
      
  3) if the keys do not form a valid sequence, just type them in said application
  4) but otherwise, send the "composed" character (as found in the Compose file above) to the application
