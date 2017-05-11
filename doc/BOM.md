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


## Add Part Attributes

Eagle allows you to add attributes to parts. We primarily use this to
add a DIGIKEY attribute to facilitate ordering. All parts in the Lab11
part libraries should already have a DIGIKEY attribute.

> If a _specific part_ (e.g. an IC, specific inductor, etc) doesn't have
> an attribute, please edit it in the library, add it there, and update
> the part on your board

For passives, we don't want to update the library with a specific 10 kΩ
resistor, because it really doesn't matter that much. Some of us like to
add attributes to all the parts in the schematic, some of us hold off
until the BOM is made and add the part purchased for that run there. It's
a bit of a fuzzier personal taste here.


## Export BOM from Eagle

In Eagle Schematic mode go File → Export → BOM. Change "List Type" to
"Values" and "Output Type" to "CSV". Then save that to a file named
`board-name_bom.csv`.

### Cleaning up the BOM

Open that CSV file in Libre Office or Excel. Now you want to clean it up.
I always start by sorting by the "Parts" column.  Make sure all the parts
are accurately represented in the BOM.  There should be a DIGIKEY column
that contains the digikey part numbers for all of the parts. If a different
place carries the part then add that as a column as well. For instance
maybe only mouser sells a part. Then add a column called MOUSER and put the
part number in that column.

Save the bom as `board-name_bom.xlsx`. Yes, it's a little weird to use
Excel format, but it is the industry standard. All assemblers will accept
and understand it and that just makes everything easier.
