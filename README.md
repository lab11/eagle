Lab11 Eagle Support Files
=========================

Part libraries, packaging scripts, CAM jobs, and other files we use with [EAGLE](https://www.autodesk.com/products/eagle/overview).

### Required package installation

#### Ubuntu (assuming default python 3.8)

```
sudo apt install pdftk unoconv texlive-core
pip install -r requirements.txt
```

#### Process
We highly recommend reading over some of the [Lab11 Eagle Documentation](doc/).

Generally:
- Generate bom with ulp. Sort by values and output to csv.
- Generate gerber files with eagle
- Open csv, add notes, delete rows for DNP footprints, and save as xlsx
- Run the main eagle.py script from the board file directory
