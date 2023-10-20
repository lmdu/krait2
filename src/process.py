import os
import sys
import traceback
import multiprocessing

import pytrf
import primer3
import pyfastx
from PySide6.QtCore import *

from utils import *
from motif import *
from annotate import *

__all__ = ['KraitSSRSearchProcess', 'KraitCSSRSearchProcess',
			'KraitISSRSearchProcess', 'KraitGTRSearchProcess',
			'KraitPrimerDesignProcess', 'KraitMappingProcess',
			'KraitStatisticsProcess']

class KraitBaseProcess(multiprocessing.Process):
	def __init__(self, params, queue, fastx={}):
		super().__init__()
		self.daemon = True
		self.fastx = fastx
		self.params = params
		self.queue = queue
		self.progress = 0

	def send(self, **kwargs):
		kwargs['id'] = self.fastx.get('id', -1)
		self.queue.put(kwargs)

	def finish(self):
		self.send(type='finish')

	def success(self):
		self.send(type='success')

	def error(self, msg):
		print(msg)
		self.send(type='error', message=msg)

	def prepare(self):
		pass

	def do(self):
		pass

	def run(self):
		try:
			self.prepare()
			self.do()
			self.success()

		except:
			errmsg = traceback.format_exc()
			self.error(errmsg)

		finally:
			self.finish()


class KraitSearchProcess(KraitBaseProcess):
	def prepare(self):
		if self.fastx['size']:
			return

		fastx_format = check_fastx_format(self.fastx['fpath'])

		if fastx_format == 'fasta':
			fx = pyfastx.Fasta(self.fastx['fpath'], full_index=True)
			avg_len = round(fx.mean)
			min_len = len(fx.shortest)
			max_len = len(fx.longest)

		elif fastx_format == 'fastq':
			fx = pyfastx.Fastq(self.fastx['fpath'], full_index=True)
			avg_len = round(fx.avglen)
			min_len = fx.minlen
			max_len = fx.maxlen

		else:
			raise Exception("the file format is not fasta or fastq")

		self.fastx['size'] = fx.size

		unknown_base = 0
		base_comp = fx.composition
		for b in base_comp:
			if b.upper() not in ['A', 'T', 'G', 'C']:
				unknown_base += base_comp[b]

		self.send(type = 'fastx',
			records = [fastx_format, fx.size, len(fx), round(fx.gc_content, 2),
				unknown_base, avg_len, min_len, max_len, self.fastx['id']
			]
		)

class KraitSSRSearchProcess(KraitSearchProcess):
	def do(self):
		fx = pyfastx.Fastx(self.fastx['fpath'], uppercase=True)
		SM = StandardMotif(self.params['standard_level'])

		for item in fx:
			name, seq = item[0:2]

			finder = pytrf.STRFinder(name, seq, *self.params['min_repeats'])
			ssrs = finder.as_list()

			rows = []
			for ssr in ssrs:
				smotif = SM.standard(ssr[3])
				rows.append((None, name, ssr[1], ssr[2], ssr[3],
					smotif, ssr[4], ssr[5], ssr[6]))

			self.progress += len(seq)
			p = self.progress/self.fastx['size']*self.fastx['weight']

			self.send(type='ssr', records=rows, progress=p)

class KraitCSSRSearchProcess(KraitSearchProcess):
	def do(self):
		ssrs = self.params['ssrs']
		dmax = self.params['dmax']

		if not ssrs:
			return

		self.total_ssrs = len(ssrs)
		ssrs = iter(ssrs)
		cssrs = [next(ssrs)]

		records = []
		for ssr in ssrs:
			d = ssr[2] - cssrs[-1][3] - 1

			if ssr[1] == cssrs[-1][1]:
				if d <= dmax:
					cssrs.append(ssr)

				else:
					if len(cssrs) > 1:
						records.append(self.join_ssrs(cssrs))

					cssrs = [ssr]
			else:
				if records:
					progress = self.progress/self.total_ssrs
					self.send(type='cssr', records=records, progress=progress)
					records = []
				
				cssrs = [ssr]

			self.progress += 1

		if len(cssrs) > 1:
			records.append(self.join_ssrs(cssrs))

		if records:
			p = self.progress/self.total_ssrs*self.fastx['weight']
			self.send(type='cssr', records=records, progress=p)

	def join_ssrs(self, cssrs):
		chrom = cssrs[0][1]
		start = cssrs[0][2]
		end = cssrs[-1][3]
		complexity = len(cssrs)
		length = sum(cssr[8] for cssr in cssrs)
		structure = '-'.join("({}){}".format(cssr[4], cssr[7]) for cssr in cssrs)
		component = ','.join(str(cssr[0]) for cssr in cssrs)
		return (None, chrom, start, end, complexity, length, structure, component)

class KraitISSRSearchProcess(KraitSearchProcess):
	def do(self):
		fx = pyfastx.Fastx(self.fastx['fpath'], uppercase=True)
		SM = StandardMotif(self.params['standard_level'])

		for item in fx:
			name, seq = item[0:2]

			finder = pytrf.ATRFinder(name, seq,
				min_motif_size = 1,
				max_motif_size = 6,
				min_seed_repeat = self.params['minsrep'],
				min_seed_length = self.params['minslen'],
				max_consecutive_error = self.params['maxerr'],
				min_extend_identity = self.params['identity'],
				max_extend_length = self.params['maxextend']
			)

			issrs = finder.as_list()

			records = []
			for issr in issrs:
				smotif = SM.standard(issr[3])
				records.append((None, name, issr[6], issr[7], issr[3], smotif,
					issr[4], issr[8], issr[9], issr[1], issr[2], issr[5],
					issr[10], issr[11], issr[12], issr[13], round(issr[14], 2)))

			self.progress += len(seq)
			p = self.progress/self.fastx['size']*self.fastx['weight']

			self.send(type='issr', records=records, progress=p)

class KraitGTRSearchProcess(KraitSearchProcess):
	def do(self):
		fx = pyfastx.Fastx(self.fastx['fpath'], uppercase=True)

		for item in fx:
			name, seq = item[0:2]

			finder = pytrf.GTRFinder(name, seq,
				min_motif = self.params['minmotif'],
				max_motif = self.params['maxmotif'],
				min_repeat = self.params['minrep'],
				min_length = self.params['minlen']
			)
			gtrs = finder.as_list()

			records = []
			for gtr in gtrs:
				records.append((None, name, gtr[1], gtr[2], gtr[4],
					gtr[5], gtr[6], gtr[3]))

			self.progress += len(seq)
			p = self.progress/self.fastx['size']*self.fastx['weight']

			self.send(type='gtr', records=records, progress=p)

class KraitPrimerDesignProcess(KraitBaseProcess):
	def __init__(self, repeats, index, category, params, queue, fastx):
		super().__init__(params, queue, fastx)
		self.repeats = repeats
		self.index = index
		self.category = category

	def do(self):
		seq_name = None
		seq_cache = None
		flank_len = self.params.pop('PRIMER_FLANK_LENGTH')

		if self.fastx['format'] == 'fasta':
			fx = pyfastx.Fasta(self.fastx['fpath'], uppercase=True)
		else:
			fx = pyfastx.Fastq(self.fastx['fpath'])

		records = []
		for trs in self.repeats:
			if trs[1] != seq_name:
				seq_name = trs[1]
				seq_cache = fx[seq_name].seq

			start = trs[2] - flank_len

			if start < 1:
				start = 1

			end = trs[3] + flank_len

			target_start = trs[2] - start
			target_len = trs[3] - trs[2] + 1

			locus = "{}-{}-{}".format(self.category, self.index, trs[0])

			results = primer3.design_primers(
				seq_args = {
					'SEQUENCE_ID': locus,
					'SEQUENCE_TEMPLATE': seq_cache[start-1:end],
					'SEQUENCE_TARGET': [target_start, target_len],
					'SEQUENCE_INTERNAL_EXCLUDED_REGION': [target_start, target_len]
				},
				global_args = self.params
			)

			primer_count = results['PRIMER_PAIR_NUM_RETURNED']

			for i in range(primer_count):
				primer = [None, locus, i+1]
				primer.append(results['PRIMER_PAIR_{}_PRODUCT_SIZE'.format(i)])
				primer.append(round(results['PRIMER_LEFT_{}_TM'.format(i)], 2))
				primer.append(round(results['PRIMER_LEFT_{}_GC_PERCENT'.format(i)], 2))
				primer.append(round(results['PRIMER_LEFT_{}_END_STABILITY'.format(i)], 2))
				primer.append(results['PRIMER_LEFT_{}_SEQUENCE'.format(i)])
				primer.append(round(results['PRIMER_RIGHT_{}_TM'.format(i)], 2))
				primer.append(round(results['PRIMER_RIGHT_{}_GC_PERCENT'.format(i)], 2))
				primer.append(round(results['PRIMER_RIGHT_{}_END_STABILITY'.format(i)], 2))
				primer.append(results['PRIMER_RIGHT_{}_SEQUENCE'.format(i)])
				primer.extend(results['PRIMER_LEFT_{}'.format(i)])
				primer.extend(results['PRIMER_RIGHT_{}'.format(i)])

				records.append(primer)

		self.send(type='primer', records=records, progress=len(self.repeats))

class KraitMappingProcess(KraitBaseProcess):
	def __init__(self, repeats, queue, fastx):
		super().__init__(None, queue, fastx)
		self.repeats = repeats
		self.total = len(repeats)

	def do(self):
		if not self.fastx['apath']:
			return

		mapper = get_annotation_mapper(self.fastx['apath'])
		features = mapper.feature_records

		for i in range(0, len(features), 200):
			chunk = features[i:i+200]
			self.send(type='annot', records=chunk)

		rows = []
		for r in self.repeats:
			fs = mapper.contain(r[1], r[2], r[3])

			if fs:
				ft = min(f[1] for f in fs)
				ps = ','.join(str(f[0]) for f in set(fs))
				rows.append((None, r[4], r[0], ft, ps))

				if len(rows) == 200:
					self.progress += 200
					p = self.progress/self.total*self.fastx['weight']
					self.send(type='map', records=rows, progress=p)
					rows = []

		if rows:
			self.progress += len(rows)
			p = self.progress/self.total*self.fastx['weight']
			self.send(type='map', records=rows, progress=p)

class KraitStatisticsProcess(multiprocessing.Process):
	pass
