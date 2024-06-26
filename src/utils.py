import os
import sys
import gzip
import struct
import pyfastx

from config import *
from backend import *

__all__ = ["check_fastx_format", "AttrDict", "get_fastx_info",
			"iupac_numerical_multiplier", "primer_tag_format",
			"product_size_format", "get_annotation_format",
			'generate_tandem_marks', 'generate_primer_marks',
			'get_feature_parents', 'get_file_size',
			'get_stats_report'
			]

class AttrDict(dict):
	def __getattr__(self, attr):
		return self[attr]

def get_file_size(fastx):
	_size = os.path.getsize(fastx)

	if pyfastx.gzip_check(fastx):
		#estimate gzip uncompressed size
		#from https://github.com/turicas/rows
		with open(fastx, 'rb') as fh:
			fh.seek(-4, 2)
			usize = struct.unpack("<I", fh.read())[0]

		if _size > usize:
			i, v = 32, usize

			while v <= 2**32 and v < _size:
				v = (1 << i) ^ usize
				i += 1

			usize = v

		_size = usize

	return _size

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
	if pyfastx.gzip_check(annot_file):
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

			#attr = cols[8].split(';')[0]

			if 'gene_id "' in cols[8] or 'transcript_id "' in cols[8]:
				return 'gtf'

			elif '=' in cols[8].split(';')[0]:
				return 'gff'

			else:
				raise Exception("the annotation file is not GFF or GTF formatted file")

def get_fastx_info(index):
	fastx = DB.get_object("SELECT * FROM fastx WHERE id=?", (index,))

	fields = [
		('id', 'File ID'),
		('name', 'File name'),
		('format', 'Sequence format'),
		('fpath', 'Full path'),
		('apath', 'Annotation file'),
		('size', 'Total bases'),
		('ns', 'Unknown bases'),
		('count', 'Sequence count'),
		('gc', 'GC content'),
		('avglen', 'Average sequence length'),
		('minlen', 'Minimum sequence length'),
		('maxlen', 'Maximum sequence length'),
		('message', 'Message')
	]

	contents = ['<table cellspacing="0" align="center" cellpadding="12" width="98%">']

	i = -1
	for field, title in fields:
		val = fastx[field]

		if val:
			if field == 'ns':
				val = "{} ({}%)".format(val, round(val/fastx['size']*100, 2))

			elif field == 'gc':
				val = "{}%".format(val)

			elif field == 'message':
				if fastx.status != 0:
					continue

			i += 1
			color = ['white', '#f2f2f2'][i%2]
			contents.append("""
				<tr bgcolor="{}">
					<th align="left">{}: </th>
					<td>{}</td>
				</tr>
			""".format(color, title, val))

	contents.append('</table>')

	return ''.join(contents)

def generate_etr_marks(etr):
	marks = [AttrDict(
		style = 'tandem',
		start = etr.start,
		end = etr.end,
		type = etr.type
	)]

	return marks

def generate_cssr_marks(index, cssr):
	sql = "SELECT * FROM ssr_{} WHERE id IN ({})".format(index, cssr.component)
	marks = [AttrDict(style='tandem', start=ssr[2], end=ssr[3], type=ssr[6]) for ssr in DB.query(sql)]
	
	return marks

def generate_issr_marks(issr):
	marks = [AttrDict(
		style = 'tandem',
		start = issr.sstart,
		end = issr.send,
		type = issr.type
	)]

	if issr.sstart > issr.start:
		marks.append(AttrDict(
			style = 'align',
			start = issr.start,
			end = issr.sstart - 1
		))

	if issr.send < issr.end:
		marks.append(AttrDict(
			style = 'align',
			start = issr.send + 1,
			end = issr.end
		))

	return marks

def generate_tandem_marks(index, category, repeat):
	target = AttrDict(
		chrom = repeat.chrom,
		start = repeat.start,
		end = repeat.end
	)

	if category == 'ssr' or category == 'gtr':
		marks = generate_etr_marks(repeat)

	elif category == 'cssr':
		marks = generate_cssr_marks(index, repeat)

	elif category == 'issr':
		marks = generate_issr_marks(repeat)

	else:
		marks = []

	return target, marks

def generate_primer_marks(index, primer, flank=100):
	category, _, locus = primer.locus.split('-')

	sql = "SELECT * FROM {}_{} WHERE id=?".format(category, index)
	repeat = DB.get_object(sql, (int(locus),))

	print(repeat)

	start = repeat.start - flank
	if start < 1: start = 1

	end = repeat.end + flank

	target = AttrDict(
		chrom = repeat.chrom,
		start = start,
		end = end
	)

	_, marks = generate_tandem_marks(index, category, repeat)

	marks.append(AttrDict(
		style = 'primer',
		start = start + primer.forward_start,
		end = start + primer.forward_start + primer.forward_length - 1
	))

	marks.append(AttrDict(
		style = 'primer',
		start = start + primer.reverse_start - primer.reverse_length + 1,
		end = start + primer.reverse_start
	))

	return target, marks


def get_feature_parents(feature, index):
	parents = []

	if feature.parent == 0:
		return parents

	sql = "SELECT * FROM annot_{} WHERE id=?".format(index)
	parent = DB.get_object(sql, (feature.parent,))
	parents.append(parent)

	tmp = get_feature_parents(parent, index)
	parents.extend(tmp)
	return parents

def get_stats_report(file_index):
	sql = "SELECT meta FROM stats_{}".format(file_index)
	rows = [row[0] for row in DB.query(sql)]

	if len(rows) > 1:
		return ''.join(rows)

	else:
		return rows[0]

if __name__ == '__main__':
	affix = iupac_numerical_multiplier(int(sys.argv[1]))
	print(affix)