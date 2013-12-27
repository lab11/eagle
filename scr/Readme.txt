Replace the eagle.scr file in your eagle/scr folder with this file. 
-- or --
Create a symlink in the eagle/scr folder that points to this. Something like:
$ ln -s ~/shed/eagle/scr/eagle.scr eagle.scr

Each section controls a particular window: 
BRD -> Board
SCH -> Schematic
LBR -> Library
SYM -> Symbol
PAC -> Package

Anything you can set using the Change command can be set in the same way in eagle.scr. 
