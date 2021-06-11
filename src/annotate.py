import csv
import gzip

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

	def split_value(self, it):
		pass

	def parse_attrs(self, attr_str):
		attrs = AttrDict()
		for it in attr_str.strip().split(';'):
			attr, val = self.split_value(it)
			attrs[attr] = val

		return attrs

class GFFReader(AnnotReader):
	def __init__(self, annot_file):
		super().__init__(annot_file)

	def split_value(self, it):
		return it.strip().split('=')

class GTFReader(AnnotReader):
	def __init__(self, annot_file):
		super().__init__(annot_file)

	def split_value(self, it):
		cols = it.strip().strip('"').split('"')
		return (cols[0].strip(), cols[1].strip())

if __name__ == '__main__':
	gff = GFFReader('GCF_000005845.2.gff.gz')
	for r in gff:
		print(r)