BOM Generation
==============

Creating a Bill of Material is crucial for being able to assemble a board in
the future.

## Renumber Passives

Before generating your BOM, you should renumber your passives so that
like values are grouped together and are sorted by value (e.g. all
22 pF caps are C1-C4, 10 µF are C5-12, etc). The
[eagle_renumber.py](../scripts/eagle_renumber.py) script will do this
correctly for you. Parts set with a value of DNP will be numbered last in
order.

_Tip:_ If you don't want the renumber script to touch a certain part, give
it a part number in the thousands (i.e. D1000 and R1000) and the renumber
script will ignore those parts.

**Attention:** You'll want to do this step *before* sending the board off to the manufacturer, as it will also change the reference designators on the boards directly and with it the silk screen. Therefore, we suggest you to do this before you start finalizing the silk screen, as you might otherwise have to take a look at it and re-align names again as the names might change their lengths.

## Add Part Attributes

Eagle allows you to add attributes to parts. We primarily use this to
add a `DIGIKEY` attribute to facilitate ordering. All parts in the Lab11
part libraries should already have a `DIGIKEY` attribute.

> If a _specific part_ (e.g. an IC, specific inductor, etc) doesn't have
> an attribute, please edit it in the library, add it there, and update
> the part on your board

For passives, we don't want to update the library with a specific 10 kΩ
resistor, because it really doesn't matter that much (and they are currently sold out in a matter of weeks most of the time). Some of us like to add attributes to all the parts in the schematic, some of us hold off
until the BOM is made and add the part purchased for that run there. It's
a bit of a fuzzier personal taste here.

**Attention:** If you copy parts of your schematic from other boards, it can easily happen that you include parts (such as passives) which already contain a `DIGIKEY` attribute. This becomes dangerous when you start *copying* those parts around and change the value of them, as the attribute does not correspond to the correct value anymore and you end up order the wrong components. Always double-check your passives before ordering!


## Export BOM from Eagle

In Eagle Schematic mode go File → Export → BOM. Change "List Type" to
"Values" and "Output Type" to "CSV". Then save that to a file named
`board-name_bom.csv`.

### Cleaning up the BOM

Open that CSV file in Libre Office or Excel (see below). Now you want to clean it up.

  1. I always start by sorting by the "Parts" column.
  2. Delete the things that aren't actually parts (e.g. LOGOs)
  3. Merge rows displaying the same components; this should usually be done directly by EAGLE when exporting parts, but does not happen when one variant of the component already contains attributes and others do not (such as when you copied parts and changed their value).
  4. Make sure all the parts are accurately represented in the BOM.
     - There should be a `DIGIKEY` column that contains the digikey part numbers
       for all of the parts.
     - If a different place carries the part then add that as a column as well.
       For instance maybe only mouser sells a part. Then add a column called
       `MOUSER` and put the part number in that column.

Save the bom as `board-name_bom.xlsx`. Yes, it's a little weird to use
Excel format, but it is the industry standard. All assemblers will accept
and understand it and that just makes everything easier.

**Delete the original csv file** as the packaging scripts will convert the
new xlsx file to an updated csv for you.

#### Using LibreOffice

Counter-intuitively, LibreOffice is actually the best at converting the "csv"
into an "xlsx" file. Just open the "csv" file directly, use the "Semicolon"
separator, and hit okay. Then run `Sort` on column "Parts" with the options
"Range contains Column labels", "Include formats", and "Enable natural sort".
This will leave you with a properly sorted BOM which you should "Save As..." an
"xlsx" file.


#### Handling `;`-separated "csv" in Excel

Eagle's "csv" export tool gives semicolon-separated values, not comma-separated.
*Do not* open this "csv" in Excel directly, rather:

  1. Open a new instance of Excel and choose `File > Import` then `CSV file`.
  2. Make sure `Delimited` is selected
  3. Change the `File origin` to `Unicode (UTF-8)`
  4. Click Next
  5. Choose the right delimiters so the data in the preview looks right,
     probably just have the `Semicolon` box checked
  6. Click Finish, you want the data in the `Existing Sheet` at the default place
