Eagle Tips
==========

## Using Eagle

### Ubuntu Installation

  - `sudo apt-get install ia32-libs`

### Standards for part names (e.g. Resistor –> R, Relay –> K)

  - http://electronics.stackexchange.com/questions/36008/pcb-part-naming-for-leds

### Hide certain airwires:

  - `ratsnest ! gnd`

### Flip text

  - check the spin box when editing the text

### Filled in circle

  - set the line width of a circle to 0

### Ripup only polygons (useful when running rats and having polygons fill)

  - `rip @;`

### Run ratsnest without having polygons fill at all

  - `set polygon_ratsnest off`


### Delete excess layers (hack stolen [from here](http://www.sparkfun.com/tutorials/157)):

1. Open the DRC
2. Go to the 'Layers' Tab
3. Change the 'Setup' field from `"(1*16)"` to `"1*16"` [remove parentheses]
4. Click Apply
5. Change the 'Setup' field back to `"(1*16)"` [seriously]
6. Click Apply


## Making Parts

### Symbols

 - Don't change any of the grid / options / etc when making the part symbol.
   Doing so will make your life miserable.

### Packages

 - Put things on the right layers and use the 'magic strings', that is:
   `>NAME` → tNames (25), `>VALUE` → tValues (27)
 - Make sure you include a part outline
   - You can do this on either tDocu (51, won't appear on final board) or
     tPlace (21, will appear). Often tPlace is the better choice as having
     part outlines is nice when assembling boards
 - Make sure you include an orientation marking
   - Put this on tPlace (21)
   - Put it somewhere that will not be covered by the part once the part is
     on the board. It's convenient to be able to glance over a board and
     verify things are assembled correctly.

### Devices

 - Add a "Prefix" to your part (See above for standard part names)
   - The prefix button is in the bottom right of the window
 - Add an "Attribute" that has the vendor / part number
   - The Attribute "button" is just to the left of the prefix button; it
     looks more like a URL than a button.
   - When you add a "New" attribute, set its `Name` to a vendor (e.g.
     DIGIKEY) and its `Value` to the vendor part number

## Legacy Tips

These help out with older versions of Eagle, but aren't as needed any more

### Copy parts from one sheet to another:

(As of Eagle 8.1.1 you can just ctrl-c / ctrl-v! Crazy!)

1. copy the part
2. select the part with the group tool
3. use the move tool, right click and move group, and then move it to the other sheet
