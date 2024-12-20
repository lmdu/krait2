import json
import gzip
import pygros
import pyfastx

from utils import *

__all__ = ['get_annotation_mapper']

class GXFReader:
	def __init__(self, annot_file):
		if pyfastx.gzip_check(annot_file):
			self.reader = gzip.open(annot_file, 'rt')
		else:
			self.reader = open(annot_file)

	def __del__(self):
		self.reader.close()

	def __iter__(self):
		for line in self.reader:
			row = line.strip('\n').split('\t')

			if row[0][0] == '#':
				continue

			if len(row) < 9:
				continue

			yield AttrDict(
				chrom = row[0],
				type = row[2].lower(),
				start = int(row[3]),
				end = int(row[4]),
				strand = row[6],
				attrs = self.parse_attrs(row[8])
			)

	def split_value(self, item):
		return None, None

	def split_attrs(self, item):
		return None, None

	def parse_attrs(self, attr_str):
		attrs = AttrDict()
		items = self.split_attrs(attr_str)

		for item in items:
			if not item: continue
			attr, val = self.split_value(item)
			attrs[attr.lower()] = val

		return attrs

class GFFReader(GXFReader):
	def split_attrs(self, item):
		return item.strip().split(';')

	def split_value(self, item):
		cols = item.strip().split('=')
		return (cols[0].strip(), cols[1].strip())

class GTFReader(GXFReader):
	def split_attrs(self, item):
		return item.strip().split('";')

	def split_value(self, item):
		cols = item.strip().split('"')
		return (cols[0].strip(), cols[1].strip())

class GXFMapper:
	def __init__(self, annot_file):
		self.annot_file = annot_file
		self.feature_records = []
		self.feature_mapping = {}
		self.parent_mapping = {}
		self.feature_id = 0
		self.ranges = pygros.Ranges()
		self.create_reader()
		self.parse()
		self.ranges.index()

	def create_reader(self):
		pass

	def parse(self):
		pass

	def contain(self, chrom, start, end):
		rs = self.ranges.contain(chrom, start, end)
		return [(r[2], self.feature_mapping[r[2]]) for r in rs]

	def get_attr(self, keys, attrs):
		for k in keys:
			if k in attrs:
				return attrs.get(k)

class GFFMapper(GXFMapper):
	def create_reader(self):
		self.reader = GFFReader(self.annot_file)

	def generate_introns(self, exons):
		if exons:
			chrom = exons[0].chrom
			strand = exons[0].strand
			pid = self.parent_mapping[exons[0].attrs.parent]

			for i in range(len(exons)-1):
				self.feature_id += 1

				#intron position
				start = exons[i].end + 1
				end = exons[i+1].start - 1

				self.feature_records.append([self.feature_id, pid, chrom, 'intron', start, end, strand, '', ''])
				self.feature_mapping[self.feature_id] = 4
				self.ranges.add(chrom, start, end, self.feature_id)

	def parse(self):
		cds = []
		exons = []

		for r in self.reader:
			self.feature_id += 1
			self.parent_mapping[r.attrs.id] = self.feature_id

			if 'parent' in r.attrs:
				pid = self.parent_mapping[r.attrs.parent]
			else:
				pid = 0

			fid = r.attrs.id
			name_keys = ['name', 'gene', 'gene_name', 'exon_name', 'cds_name', 'utr_name', 'id']
			fname = self.get_attr(name_keys, r.attrs)

			self.feature_records.append([self.feature_id, pid, r.chrom, r.type, r.start, r.end, r.strand, fid, fname])

			if r.type == 'cds':
				self.ranges.add(r.chrom, r.start, r.end, self.feature_id)
				cds.append(r)
				self.feature_mapping[self.feature_id] = 1

			elif r.type == 'exon':
				self.ranges.add(r.chrom, r.start, r.end, self.feature_id)
				exons.append(r)
				self.feature_mapping[self.feature_id] = 2

			elif 'utr' in r.type:
				self.ranges.add(r.chrom, r.start, r.end, self.feature_id)

				if '3' in r.type or 'three' in r.type:
					self.feature_mapping[self.feature_id] = 3

				elif '5' in r.type or 'five' in r.type:
					self.feature_mapping[self.feature_id] = 5

				else:
					self.feature_mapping[self.feature_id] = 4

			else:
				self.generate_introns(exons or cds)

				cds = []
				exons = []

		self.generate_introns(exons or cds)

class GTFMapper(GXFMapper):
	def create_reader(self):
		self.reader = GTFReader(self.annot_file)

	def generate_introns(self, exons):
		if exons:
			chrom = exons[0].chrom
			strand = exons[0].strand

			if 'transcript_id' in exons[0].attrs:
				pid = self.parent_mapping[exons[0].attrs.transcript_id]
			else:
				pid = self.parent_mapping[exons[0].attrs.gene_id]

			for i in range(len(exons)-1):
				self.feature_id += 1

				#intron position
				start = exons[i].end + 1
				end = exons[i+1].start - 1

				self.feature_records.append([self.feature_id, pid, chrom, 'intron', start, end, strand, '', ''])
				self.feature_mapping[self.feature_id] = 6
				self.ranges.add(chrom, start, end, self.feature_id)

	def parse(self):
		cds = []
		exons = []

		for r in self.reader:
			self.feature_id += 1

			if r.attrs.gene_id not in self.parent_mapping:
				self.parent_mapping[r.attrs.gene_id] = self.feature_id
				pid = 0
				fid = r.attrs.gene_id

				name_keys = ['gene', 'gene_name', 'name', 'locus_tag', 'product', 'protein_id', 'gene_id']
				fname = self.get_attr(name_keys, r.attrs)

			elif r.attrs.transcript_id not in self.parent_mapping:
				self.parent_mapping[r.attrs.transcript_id] = self.feature_id
				pid = self.parent_mapping[r.attrs.gene_id]
				fid = r.attrs.transcript_id

				name_keys = ['transcript_name', 'name', 'transcript_id']
				fname = self.get_attr(name_keys, r.attrs)

			else:
				id_keys = ['exon_id', 'cds_id', 'utr_id', 'id', 'exon_number', 'cds_number']
				fid = ''
				for k in id_keys:
					if k in r.attrs:
						fid = r.attrs.get(k)

						if 'number' in k:
							fid = "{}{}".format(r.type, fid)

						break

				name_keys = ['name', 'exon_name', 'cds_name', 'utr_name']
				fname = self.get_attr(name_keys, r.attrs)

				pid = self.parent_mapping.get(r.attrs.transcript_id, self.parent_mapping[r.attrs.gene_id])

			self.feature_records.append([self.feature_id, pid, r.chrom, r.type, r.start, r.end, r.strand, fid, fname])

			if r.type == 'cds':
				self.ranges.add(r.chrom, r.start, r.end, self.feature_id)
				cds.append(r)
				self.feature_mapping[self.feature_id] = 1

			elif r.type == 'exon':
				self.ranges.add(r.chrom, r.start, r.end, self.feature_id)
				exons.append(r)
				self.feature_mapping[self.feature_id] = 2

			elif 'utr' in r.type:
				self.ranges.add(r.chrom, r.start, r.end, self.feature_id)
				self.feature_mapping[self.feature_id] = 3

			else:
				self.generate_introns(exons or cds)

				cds = []
				exons = []

		self.generate_introns(exons or cds)

def get_annotation_mapper(annot_file):
	annot_format = get_annotation_format(annot_file)

	if annot_format == 'gtf':
		return GTFMapper(annot_file)
	else:
		return GFFMapper(annot_file)


if __name__ == '__main__':
	gff = annotation_parser('GCF_000005845.2.gtf.gz')
