Gerbers
=======

# CAM files

To manufacture your board, you first need to convert the EAGLE files into a format which board manufacturers understand, a so-called *Computer-Aided Manufacturing* (CAM) file. Due to historic reasons, for PCBs this format is called *Gerber*.

For more information, visit:
- [Autodesk: How to generate your Gerber and NC drill files](https://www.autodesk.com/products/eagle/blog/gerber-nc-drill-pcb-manufacturing-basics-1/)
- [SparkFun: Generate Gerbers](https://learn.sparkfun.com/tutorials/using-eagle-board-layout/generating-gerbers)

## Creating Gerber  files

Open the `CAM Processor` (File → CAM Processor) and load the appropriate [CAM job](../cam) for your board. For standard 4-layer boards, we use the [4LPlus-Sunstone.cam](../cam/4LPlus-Sunstone.cam).

**Attention:** If running your job takes an unexpectedly long time, check your polygon widths; they should always be equal to the width of the smallest traces on your board (usually 4 or 6 mil). Especially ground pour polygons and logos can cause problems.

TODO: CAM job selection (other board houses)

## NC files
Gerbers only contain information about the different layers. For vias and other holes requiring drilling, you will also need to run the drill job, which for historic reason is referred to as *Excellon*. You can find the job in the same folder ([excellon](../cam/excellon.cam)). This will generate additional NC (Numeric Controlled) Drill files which tell the manufacturer where he should drill the holes for vias, screws etc.

# Gerber inspection

To make sure that the Gerber files actually represent the board as you intended, we use a separate Gerber viewer to inspect it before shipping. For this, we recommend the free & open source tools [gerbv](http://gerbv.geda-project.org/) ([direct download](https://sourceforge.net/projects/gerbv/)). There are also online tools available to quickly have a look at Gerbers such as the [Online Gerber Viewer](http://www.gerber-viewer.com/).

When inspecting the NC drill file (.drd), make sure that you *first* add another layer (such as L1) and *then* add the drilling information; otherwise, the files might not overlay and seem incorrect due to some dimension information missing in the drill file.

# Panelizing

In order to produce more price-efficient boards, you can panelize your boards to fit multiple ones onto the same panel. While we generally do not do this ourselves (it is often done by the board manufacturer directly), feel free to try out EAGLE's new *design block* feature and add multiple versions of your board to the design.
