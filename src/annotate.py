import csv
import gzip
import pygrange

from utils import *

__all__ = []

class AttrDict(dict):
	def __getattr__(self, attr):
		return self[attr]

class AnnotReader:
	def __init__(self, annot_file):
		if is_gzip_compressed(annot_file):
			self.handler = gzip.open(annot_file, 'rt')
		else:
			self.handler = open(annot_file)

		self.reader = csv.reader(self.handler, delimiter='\t')

	def __del__(self):
		self.handler.close()

	def __iter__(self):
		for row in self.reader:
			if row[0][0] == '#':
				continue

			yield AttrDict(
				chrom = row[0],
				feature = row[2].lower(),
				start = int(row[3]),
				end = int(row[4]),
				strand = row[6],
				attrs = self.parse_attrs(row[-1])
			)

	def split_value(self, item):
		pass

	def parse_attrs(self, attr_str):
		attrs = AttrDict()
		items = attr_str.strip().split(';')
		if not items[-1]:
			items.pop()

		for item in items:
			attr, val = self.split_value(item)
			attrs[attr] = val

		return attrs

class GFFReader(AnnotReader):
	def __init__(self, annot_file):
		super().__init__(annot_file)

	def split_value(self, item):
		return item.strip().split('=')

class GTFReader(AnnotReader):
	def __init__(self, annot_file):
		super().__init__(annot_file)

	def split_value(self, item):
		cols = item.strip().split('"')
		return (cols[0].strip(), cols[1].strip())

class GeneLocator:
	def __init__(self, annot_file):
		self.annot_file = annot_file
		self.parent_mapping = {0: 0}
		self.feature_mapping = {}
		self.ranges = pygrange.Ranges()
		self.create_reader()
		self.parse()

	def create_reader(self):
		pass

	def parse(self):
		pass

class GFFLocator(GeneLocator):
	def __init__(self, annot_file):
		super().__init__(annot_file)

	def create_reader(self):
		self.reader = GFFReader(self.annot_file)

	def parse(self):
		annot_id = 0
		annot_rows = []

		for r in self.reader:
			annot_id += 1

			if r.feature == 'cds':
				pass

			elif r.feature == 'exon':
				pass

			elif 'utr' in r.feature:
				pass
			else:
				parent = self.parent_mapping[r.attrs.get('parent', 0)]

				annot_rows.append((annot_id, parent, r.chrom, r.feature, r.start, r.end, r.strand))


if __name__ == '__main__':
	gff = GFFReader('GCF_000005845.2.gff.gz')
	for r in gff:
		print(r)