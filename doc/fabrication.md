Fabrication
===========

There are Lab accounts for all sites mentioned below; you can find them on the [wiki](https://lab11.eecs.umich.edu/wiki/doku.php).

# PCB manufacturer

We currently like [Quick Turn PCB](http://quickturnpcb.co.kr/). They will do the panelization for you, so just tell them the number of boards and they will work it out.

For custom boards, you can use their [contact email](mailto:gthanuni@quickturnpcb.co.kr) to order special stack-ups.

You generally want the "Special Offer". Be sure to login to the site before starting or you'll have to start over.

# Stencil manufacturer

To make your life easier during assembly, order a stencil. It will help you spread the solder paste manually!

We mostly order from [OSH Stencils](https://www.oshstencils.com/). We usually take the recommended option (*frameless* and *4mm*). Make sure to add an inscription on the stencil, mentioning for which board, revision and side it is used (`boardname-revX-TOP` and `boardname-revX-BOTTOM` respectively).

# Parts

Being the largest vendor of electronic components worldwide, [DigiKey](https://www.digikey.com/) can get you most of the required parts.

You can use their **BOM manager** to directly upload the parts list. After having done so (you can choose any format such as .csv or .txt), you can then assign the correct column names:

- *Digi-Key Part Number:* should match the `DIGIKEY` attribute
- *Manufacturer Part Number:* should math the `MPN` (not mandatory)
- *Quantity:* should match the line where you state the amount of an individual part; make sure that e.g. all 1uF capacitors are aggregated on a single line (it might happen that you copied parts around, in which case some might show MPNs from other components and will not be aggregated).
- *Customer Reference:* should match the reference designators of your parts (e.g. R1, C45, U2); this will make assembly easier, as the parts will be in bags which are already labelled correctly. *Note:* Sometimes, DigiKey also directly shows *Reference designator* as an option.

You can then add all parts. *After* having done so, when clicking to the next page, DigiKey will ask you how many assemblies you desire; here, you can simply multiple the numbers for the number of boards you order. Make sure to add *spare parts* in case some get lost or broken during assembly; we usually order about 10-20% extra for passives and less for more expensive components.
On a last page, it will suggest you to increase to a next price threshold size to save money (larger orders above given thresholds will result in lower prices per piece).

*Attention:* Make sure to verify the `DIGIKEY` attribute of passives before buying. It easily happens that you copied parts on the schematic and then changed the value afterwards. If that given passive already had attributes, those ones will be preserved and the `DIGIKEY` attribute will *not* correspond to the value you actually intend to order.
