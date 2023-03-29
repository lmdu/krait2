import sys
import gzip
import pyfastx

from config import *
from backend import *

__all__ = ["check_fastx_format", "AttrDict", "get_fastx_info",
			"iupac_numerical_multiplier", "primer_tag_format",
			"product_size_format", "get_annotation_format",
			]

class AttrDict(dict):
	def __getattr__(self, attr):
		return self[attr]

def check_fastx_format(fastx):
	if pyfastx.gzip_check(fastx):
		fp = gzip.open(fastx, 'rt')
	else:
		fp = open(fastx)

	for line in fp:
		line = line.strip()

		if not line:
			continue

		if line[0] == '>':
			return 'fasta'
		elif line[0] == '@':
			return 'fastq'
		else:
			return None

#https://en.wikipedia.org/wiki/IUPAC_numerical_multiplier
#https://www.qmul.ac.uk/sbcs/iupac/misc/numb.html
def iupac_numerical_multiplier(num):
	mapping = {
		-1: 'mono',
		-2: 'di',
		 1: 'hen',
		 2: 'do',
		 3: 'tri',
		 4: 'tetra',
		 5: 'penta',
		 6: 'hexa',
		 7: 'hepta',
		 8: 'octa',
		 9: 'nona',
		10: 'deca',
		11: 'undeca',
		20: 'icosa',
		30: 'triaconta',
		40: 'tetraconta',
		50: 'pentaconta',
		60: 'hexaconta',
		70: 'heptaconta',
		80: 'octaconta',
		90: 'nonaconta',
		100: 'hecta',
		200: 'dicta',
		300: 'tricta',
		400: 'tetracta',
		500: 'pentacta',
		600: 'hexacta',
		700: 'heptacta',
		800: 'octacta',
		900: 'nonacta',
		1000: 'kilia',
		2000: 'dilia',
		3000: 'trilia',
		4000: 'tetralia',
		5000: 'pentalia',
		6000: 'hexalia',
		7000: 'heptalia',
		8000: 'octalia',
		9000: 'nonalia'
	}

	assert num < 10000, "the number is too large"

	if num == 1 or num == 2:
		num = -num

	affix = mapping.get(num, None)

	if affix is not None:
		return affix

	affixs = []
	scales = [0, 10, 100, 1000]

	num = [int(i) for i in list(str(num))]
	num.reverse()

	for i, n in enumerate(num):
		if n > 0:
			if i > 0:
				n = n*scales[i]

			affixs.append(mapping[n])

	return ''.join(affixs)

def product_size_format(ranges):
	size_ranges = []
	for r in ranges.split():
		size_ranges.append([int(n) for n in r.split('-')])
	return size_ranges

def primer_tag_format(tag):
	try:
		return KRAIT_PRIMER_TAGS[tag]
	except:
		raise Exception("The {} tag is not a primer3 tag".format(tag))

#gff or gtf file validation
def get_annotation_format(annot_file):
	if is_gzip_compressed(annot_file):
		handler = gzip.open(annot_file, 'rt')
	else:
		handler = open(annot_file)

	with handler as fh:
		for line in fh:
			if line[0] == '#':
				continue

			cols = line.strip().split('\t')

			if len(cols) != 9:
				raise Exception("the annotation file is not GFF or GTF formatted file")

			attr = cols[-1].split(';')[0]

			if '=' in attr:
				return 'gff'
			elif ' ' in attr and '"' in attr:
				return 'gtf'
			else:
				raise Exception("the annotation file is not GFF or GTF formatted file")

def get_fastx_info(index):
	fastx = DB.get_dict("SELECT * FROM fastx WHERE id=?", (index,))

	fields = [
		('id', 'File ID'),
		('name', 'File name'),
		('format', 'Sequence format'),
		('fpath', 'Full path'),
		('apath', 'Annotation file'),
		['hr', False],
		('size', 'Total bases'),
		('ns', 'Unknown bases'),
		('count', 'Sequence count'),
		('gc', 'GC content'),
		['hr', False],
		('message', 'Message')
	]

	if any((fastx.size, fastx.ns, fastx.count, fastx.gc)):
		fields[5][1] = True

	if fastx.message:
		fields[10][1] = True

	contents = ['<table width="100%">']

	for field, title in fields:
		if field == 'hr':
			if title:
				contents.append("""
					<tr>
						<td colspan="2"><hr></td>
					</tr>
				""")
		else:
			val = fastx[field]

			if val:
				contents.append("""
					<tr>
						<th align="left">{}: </th>
						<td></td>
					</tr>
					<tr>
						<th></th>
						<td align="left">{}</td>
					</tr>
				""".format(title, val))

	contents.append('</table>')

	return ''.join(contents)

if __name__ == '__main__':
	affix = iupac_numerical_multiplier(int(sys.argv[1]))
	print(affix)