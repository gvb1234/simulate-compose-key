# simulate compose key

The goal of this (small, linux) project is to:

  1) catch the "compose key" press (Multi_Key) in linux
  2) if the focus is not in a specific application, propagate that key press (and release) for normal use, but otherwise, catch the next few keys as long as they make up a valid sequence, such as found in 
  
      /usr/share/X11/locale/en_US.UTF-8/Compose
      
  3) if the keys do not form a valid sequence, just type them in said application as regular characters
  4) but otherwise, send the "composed" character (as found in the Compose file above, or some other related thing, more on that below) to the application

That's it.

# Background

I have an editor that I really like. For a long time, it had some weird behaviour when composing keys. It would transform correctly \<Multi_Key\>\<e\>\<asciicircum\> into "ê" (no quotes, obviously),  but would refuse to transform \<Multi_Key\>\<asciicircum\>\<e\>" into ê.
  
  Then, after updating my computer to the latest OpenSuSE, composing keys stopped altogether in that editor (but still work everywhere else).
  
  Since I sometimes type in French (on a US keyboard), I use key composition mostly to type accented letters. "Dead" keys can also produce those, but that mechanism does not work either with said editor.
  
  The great thing about that editor is that it has some C-like macro programming (more on that below).
  
  The bad thing about that editor is that it does not support utf-8 that well (most files get open in latin-1 mode), and does not seem to like receiving anything but "low-ascii" characters as input when you type.
  
  For instance, it would accept "xdotool type à", but would balk at "xdotool type é" (interpreted as Alt-2, go figure).
  
  This weird behaviour ruled out step 4) above (sending dirtectly the composed utf-8 character found in the compose file).
  
  What I ended up doing in step 4) is to send a non-existing key (like F16), followed by the keys to be composed in litteral (low ascii) format like <asciicircum><e>, followed by Return.
  
  The editor catches F16, which invokes a macro which globs all the characters before the Return. That macro then looks up in a table for what it should "insert" into the open buffer, _if_ it can do so (high ascii values are ignored).
  
  Yeah. I know. I am crazy. But this was fun to do.
