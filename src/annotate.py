import csv
import json
import gzip
import pygros

from utils import *

__all__ = ['annotation_parser']

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
				type = row[2].lower(),
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
			attrs[attr.lower()] = val

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
		self.ranges = pygros.Ranges()
		self.create_reader()
		self.parse()

	def create_reader(self):
		pass

	def parse(self):
		pass

	def index(self):
		self.ranges.index()

	def locate(self, chrom, start, end):
		res = self.ranges.locate(chrom, start, end)
		return [self.feature_mapping[ret[2]] for ret in res]

class GFFLocator(GeneLocator):
	def __init__(self, annot_file):
		super().__init__(annot_file)

	def create_reader(self):
		self.reader = GFFReader(self.annot_file)

	def parse(self):
		annot_id = 0
		feat_id = 0
		annot_rows = []
		cds = []
		cds_num = 0
		exons = []
		exon_num = 0
		introns = []
		intron_num = 0

		for r in self.reader:
			parent = self.parent_mapping[r.attrs.get('parent', 0)]

			if r.type == 'cds':
				feat_id += 1
				cds_num += 1
				if r.strand == '+':
					self.ranges.add(r.chrom, r.start, r.end, feat_id)
				self.feature_mapping[feat_id] = (parent, 1, cds_num)
				cds.append(r)

			elif r.type == 'exon':
				feat_id += 1
				exon_num += 1
				if r.strand == '+':
					self.ranges.add(r.chrom, r.start, r.end, feat_id)
				self.feature_mapping[feat_id] = (parent, 2, exon_num)
				exons.append(r)

			elif 'utr' in r.type:
				feat_id += 1
				self.ranges.add(r.chrom, r.start, r.end, feat_id)

				if 'three' in r.type or '3' in r.type:
					self.feature_mapping[feat_id] = (parent, 3, 3)
				elif 'five' in r.type or '5' in r.type:
					self.feature_mapping[feat_id] = (parent, 5, 5)
				else:
					self.feature_mapping[feat_id] = (parent, 4, 4)
			else:
				annot_id += 1
				annot_rows.append((annot_id, parent, r.chrom, r.type, r.start,
									r.end, r.strand, json.dumps(r.attrs)))
				self.parent_mapping[r.attrs.id] = annot_id

				if not exons:
					exons = cds

				if exons:
					strand = exons[0].strand
					parent = self.parent_mapping[exons[0].attrs.get('parent', 0)]

					if strand == '-':
						exon_num = len(exons)
						for e in exons:
							feat_id += 1
							self.ranges.add(e.chrom, e.start, e.end, feat_id)
							self.feature_mapping[feat_id] = (parent, 2, exon_num)
							exon_num -= 1

						intron_num = len(exons) - 1
					else:
						intron_num = 0

					for i in range(len(exons)-1):
						feat_id += 1
						#previous exon
						pe = exons[i]

						#next exon
						ne = exons[i+1]

						if strand == '+':
							intron_num += 1
						else:
							intron_num -= 1
			
						self.ranges.add(pe.chrom, pe.end+1, ne.start-1, feat_id)
						self.feature_mapping[feat_id] = (parent, 6, intron_num)

				cds = []
				cds_num = 0
				exons = []
				exon_num = 0

class GTFLocator(GeneLocator):
	def __init__(self, annot_file):
		super().__init__(annot_file)

	def create_reader(self):
		self.reader = GTFReader(self.annot_file)

	def parse(self):
		annot_id = 0
		feat_id = 0
		annot_rows = []
		cds = []
		cds_num = 0
		exons = []
		exon_num = 0
		introns = []
		intron_num = 0

		for r in self.reader:
			if r.type == 'cds':
				feat_id += 1
				cds_num += 1
				parent = self.parent_mapping.get(r.attrs.transcript_id, self.parent_mapping[r.attrs.gene_id])
				self.ranges.add(r.chrom, r.start, r.end, feat_id)
				self.feature_mapping[feat_id] = (parent, 1, cds_num)
				cds.append(r)

			elif r.type == 'exon':
				feat_id += 1
				exon_num += 1
				parent = self.parent_mapping.get(r.attrs.transcript_id, self.parent_mapping[r.attrs.gene_id])
				self.ranges.add(r.chrom, r.start, r.end, feat_id)
				self.feature_mapping[feat_id] = (parent, 2, exon_num)
				exons.append(r)

			elif 'utr' in r.type:
				feat_id += 1
				self.ranges.add(r.chrom, r.start, r.end, feat_id)
				parent = self.parent_mapping.get(r.attrs.transcript_id, self.parent_mapping[r.attrs.gene_id])
				if 'three' in r.type or '3' in r.type:
					self.feature_mapping[feat_id] = (parent, 3, 3)
				elif 'five' in r.type or '5' in r.type:
					self.feature_mapping[feat_id] = (parent, 5, 5)
				else:
					self.feature_mapping[feat_id] = (parent, 4, 4)
			else:
				annot_id += 1

				if r.attrs.transcript_id:
					parent = self.parent_mapping[r.attrs.gene_id]
					self.parent_mapping[r.attrs.transcript_id] = annot_id
				else:
					parent = 0
					self.parent_mapping[r.attrs.gene_id] = annot_id

				annot_rows.append((annot_id, parent, r.chrom, r.type, r.start,
									r.end, r.strand, json.dumps(r.attrs)))


				if not exons:
					exons = cds

				if exons:
					intron_num = 0
					strand = exons[0].strand
					parent = self.parent_mapping[exons[0].attrs.transcript_id]
					for i in range(len(exons)-1):
						feat_id += 1
						#previous exon
						pe = exons[i]

						#next exon
						ne = exons[i+1]

						intron_num += 1
						if strand == '+':
							self.ranges.add(pe.chrom, pe.end+1, ne.start-1, feat_id)
						else:
							self.ranges.add(pe.chrom, ne.end+1, pe.start-1, feat_id)
						self.feature_mapping[feat_id] = (parent, 6, intron_num)

				cds = []
				cds_num = 0
				exons = []
				exon_num = 0

def annotation_parser(annot_file):
	_format = get_annotation_format(annot_file)
	if _format == 'gtf':
		return GTFLocator(annot_file)
	else:
		return GFFLocator(annot_file)


if __name__ == '__main__':
	gff = annotation_parser('GCF_000005845.2.gtf.gz')
