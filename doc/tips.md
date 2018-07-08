Eagle Tips
==========

## Using Eagle

### Ubuntu Installation

  - To use 32bit libraries, install the following:
    - For *12.04* or earlier: `sudo apt-get install ia32-libs`
    - For *13.04* or later: `sudo apt-get install lib32z1 lib32ncurses5`

### Standards for part names (e.g. Resistor &rarr; R, Relay &rarr; K)

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

 - **Don't** change any of the grid / options / etc when making the part symbol.
   Doing so will make your life miserable.
 - Always add `>NAME` and `>VALUE` tags to the board. Make sure that they are on the correct layer, i.e. *Names* (95) and *Values* (96) respectively.
 - If multiple pins have the same name (e.g. `GND`), make sure to add a hint to the corresponding pin (e.g. `GND` on pin 1 and 2 will become `GND@1`and `GND@2`. This will be valuable when connecting symbols and packages when creating the device later-on.
 - Define pin types for pins which are not I/O (the default): you will want to have *VCC* and *GND* on the `pw` option, *not connected* will be `nc` and one-directional pins should be defined as `in` and `out` respectively. This will help Eagle in detecting wrong connections in the DRC (*design rule check*) and ERC (*electrical rule check*) while designing the board.
- To hide pin numbers in the schematic (as they tend to clutter the overall representation), use the `Change`&rarr;`Visible`&rarr;`pin` tool on all pins.

### Packages

 - Put things on the right layers and use the 'magic strings', that is:
   `>NAME` → *tNames* (25), `>VALUE` → *tValues* (27)
 - Make sure you include a part outline
   - You can do this on either *tDocu* (51, won't appear on final board) or
     *tPlace* (21, will appear). Often *tPlace* is the better choice as having
     part outlines is nice when assembling boards.
 - Make sure you include an orientation marking:
   - Put this on *tPlace* (21)
   - Put it somewhere that will not be covered by the part once the part is
     on the board. It's convenient to be able to glance over a board and
     verify things are assembled correctly.
 - Many datasheets include a recommended footprint which will give you a good idea for the initial design.
 - To prevent too much solder paste from unevenly spreading across the exposed GND pad below the chip, it is useful to create the inner SMD zone with the option `Cream` unticked (using _Info_ after creating it). You can then manually add rectangles on the *tCream* layer (31) and only cover parts of the pad with paste.

### Devices

 - Make sure to add a useful description to your device. You can also include links, e.g. to the manufacturer's website, directly using HTML: `<a href='www.lab11.eecs.berkeley.edu'>Great source!</a>`.
 - Add a "Prefix" to your part (See above for standard part names)
   - The _Prefix_ button is in the bottom right of the window
 - Add an "Attribute" that has the vendor / part number
   - The _Attributes_ "button" is in the _Description_ section to the left of the packaging specifics; it
     looks more like a URL than a button.
   - When you add a "New" attribute, set its `Name` to a vendor (e.g.
     DIGIKEY) and its `Value` to the vendor part number.
   - Useful Attributes are:
     - _DATASHEET_ (link)
     - _DESCRIPTION_ (string from Digikey)
     - _DIGIKEY_
     - _MOUSER_
     - _MANUFACTURER_
     - _MPN_ (*Manufacturer Part Number*)
 - Change the symbol name (usually `G$1$`) to something nicer-looking, e.g. `U1`, using the *name* tool.

## Legacy Tips

These help out with older versions of Eagle, but aren't as needed any more

### Copy parts from one sheet to another:

(As of Eagle 8.1.1 you can just ctrl-c / ctrl-v! Crazy!)

1. copy the part
2. select the part with the group tool
3. use the move tool, right click and move group, and then move it to the other sheet
