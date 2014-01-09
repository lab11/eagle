#!/usr/bin/env bash

function usage {
	echo "USAGE: $0 PDF_TO_NUMBER.pdf [OUTFILE]"
}

if [ ! -r $1 ]; then
	usage
	exit 1
fi

command -v pdftk >/dev/null 2>&1 || {
	echo >&2 "You need pdftk.\nsudo apt-get install pdftk"; exit 1;
}


set -e

tmp=`mktemp -d pdf_numberXXXXXXXXXX`
if [ -z "$2" ]; then
	out=`basename "$1" .pdf`"_numbered.pdf"
else
	out=$2
fi

cp $1 $tmp
pushd $tmp &> /dev/null

echo "Breaking original pdf into individual pages"
pdftk $1 burst output ZXZX_%04d.pdf

echo "Generating latex template..."
cat > page_numbers.tex << EOF
\documentclass{article}
\usepackage[bottom=3cm,pdftex]{geometry}
\pagestyle{plain}
\renewcommand{\familydefault}{\sfdefault}
\begin{document}
EOF

total=0
for f in `ls ZXZX_*pdf`; do
	echo "~ \newpage" >> page_numbers.tex
	let total=total+1
done

echo "\end{document}" >> page_numbers.tex

echo "Creating latex pages"
pdflatex page_numbers.tex &> /dev/null

if [[ ! -e page_numbers.pdf ]]; then
	echo "Failed to create page numbers?"
	exit 1
fi

echo "Breaking latex pages into individual documents"
pdftk page_numbers.pdf burst output b_ZXZX_%04d.pdf

echo "Overlaying pages"
cnt=1
for i in ZXZX_*.pdf; do
	echo "  Processing page $cnt/$total"
	pdftk $i background b_$i output x_$i.pdf
	let cnt=cnt+1
done

echo "Creating unified pdf"
pdftk x_ZXZX_*.pdf cat output $out

popd &> /dev/null

cp $tmp/$out .
rm -rf $tmp

echo "Finished. Numbered pdf saved to '$out'"

