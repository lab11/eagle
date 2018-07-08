Lab11 and Eagle
===============

We've adopted some conventions and styles over the years. Some of these
require a little more effort up front, but will pay off in the long run
if you end up needing to scale up board production, or simply to make
stuff that's easily usable by others in lab.

## Starting a new board

### Directory Structure

A bunch of scripts rely on this and it works well. Follow it.

    <repo folder>/hardware/<board-name>/<rev-x>/board-name.sch
                            ^^^^^^^^^^          ^^^^^^^^^^
                            Note that these MUST be the same

### Revisions

We use _letters_ for revisions. So this should start with rev-a and
increment appropriately. Once you ship a board for manufacture, that
revision is set in stone. Do not modify it. Even if you only made two
boards and they didn't work because of a silly bug, that revision will
still stick around for all of time. Sometimes boards end up on revision
`e`, `g`, `i`, whatever.

When you need to start a new revision, simply make a new folder
(`rev-b`) and `cp rev-a/board_name.sch rev-a/board-name.brd rev-b/`.
You should then commit this new revision, so that the base starting
point for the new rev is exactly the old rev.

### Schematic Setup and Attributes

Eagle has a metadata system called "Attributes", first, set up some
global attributes for your new board. Go to the Edit menu then Global
Attributes.

  1. The `REV` attribute should be set to A, B, C... depending on the revision
  2. The `TITLE` attribute should be set to the name of the board, in this case `board-name`
  3. The `AUTHOR` attribute should be set to the name of the creator of the board


## Finishing the Schematic and Board

This overview is not going to go into how to design or layout PCBs.

We have some tips and conventions that we've established over time that
are worth reading over:

  - [Lab11 Eagle Tips](tips.md)

There are some additional resources online that may be useful:

  - [Sparkfun: Installing EAGLE](https://learn.sparkfun.com/tutorials/how-to-install-and-setup-eagle)
  - [Sparkfun: EAGLE schematics](https://learn.sparkfun.com/tutorials/using-eagle-schematic) ([old version](https://www.sparkfun.com/tutorials/108))
  - [Sparkfun: EAGLE board layout](https://learn.sparkfun.com/tutorials/using-eagle-board-layout) ([old version](https://www.sparkfun.com/tutorials/109))
  - [Sparkfun: How to create SMD based PCBs](https://learn.sparkfun.com/tutorials/designing-pcbs-advanced-smd)
  - [Sparkfun: Designing PCBs with SMB footprints](https://learn.sparkfun.com/tutorials/designing-pcbs-smd-footprints) ([old version](https://www.sparkfun.com/tutorials/110))
  - [UMich Embedded systems information](http://www.eecs.umich.edu/hub/lessons.html)


## Design Review

Once you think you are done, it's a really good idea to have others
in labe review your work. Recently, we've been creating an emphemeral
slack channel for each board and tossing reviews there. It's been
working pretty well.

If this is an earlier board for you (or even if you're experienced
and this is your first Lab11 board), there will probably be a healthy
amount of feedback. That's a good thing! Learn from it :)


## Creating Gerbers

Once you are happy with the board you need to create gerber files you
can send to a board house.

  - The [Gerbers Documentation](gerbers.md) has more on this.


## Creating a Bill of Materials (BOM)

Creating a BOM is crucial for future assembly, for you, for others in
lab, and for professional assemblers. We've developed a number of
conventions from experience over the years, follow them - if things
change in the world, update them, but talk about it with older lab
folk first.

  - Follow the [BOM Guide](BOM.md) to make your BOM.


## Package Things Up (AKA, run the magic script)

Once you have done all the setup work, it's time to let scripts take over.
These scripts will do several things:

  - Put all the gerbers in a zip.
    - This you can upload to the board house who will make the PCB.
  - Put all the gerbers and a couple addition files in a zip for the assembler.
    - This you can send to an assembler when getting a quote/boards assembled.
  - Create a documenting PDF.
    - This will but the schematic, pictures of all of the copper layers, a
      good graphic to use when assembling the board, and a copy of the bom
      into a PDF.
  - Convert the bom to txt and csv formats.
    - These are not as useful but are good for using grep.
  - Package everything into several a master zips.
    - `board-name_REV_DATE.zip` - an archive of everything, good for posting online or sharing with others
    - `board-name_REV_to_fab_DATE.zip` - files needs for PCB fabrication, good for uploading to board houses
    - `board-name_REV_to_assembler_DATE.zip` - files needed for assembly, good for upload to an assembly shop

To run, simply invoke the meta-script:

    github.com/lab11/eagle/scripts/eagle.py

in the same folder as the .brd and .sch files.

Viola!

## Fabrication

Whoo! You've got a few options to pick from here, including different
board houses and possibly assembly.

  - Head over to the [Fabrication Guide](fabrication.md)

