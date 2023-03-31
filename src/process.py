import os
import stria
import primer3
import pyfastx
import traceback
import multiprocessing

from PySide6.QtCore import *

from utils import *
from motif import *

__all__ = ['KraitSSRSearchProcess', 'KraitCSSRSearchProcess',
			'KraitISSRSearchProcess', 'KraitVNTRSearchProcess',
			'KraitPrimerDesignProcess']

class KraitSearchProcess(multiprocessing.Process):
	def __init__(self, fastx, params, sender):
		super().__init__()
		self.daemon = True
		self.fastx = fastx
		self.params = params
		self.sender = sender
		self.progress = 0

	def build_index(self):
		if self.fastx['size']:
			return

		fastx_format = check_fastx_format(self.fastx['fpath'])

		if fastx_format == 'fasta':
			fx = pyfastx.Fasta(self.fastx['fpath'], full_index=True)

		elif fastx_format == 'fastq':
			fx = pyfastx.Fastq(self.fastx['fpath'], full_index=True)

		else:
			raise Exception("the file format is not fasta or fastq")

		self.fastx['size'] = fx.size

		self.sender.send({
			'type': 'fastx',
			'records': [fx.size, len(fx), round(fx.gc_content, 2),
				fx.composition.get('N', 0), fastx_format, self.fastx['id']
			]
		})

	def finish(self):
		self.sender.send({
			'id': self.fastx['id'],
			'type': 'finish'
		})

	def do(self):
		pass

	def run(self):
		try:
			self.build_index()
			self.do()
			self.finish()
		except:
			error = traceback.format_exc()
			print(error)
		finally:
			self.sender.close()

class KraitSSRSearchProcess(KraitSearchProcess):
	def do(self):
		fx = pyfastx.Fastx(self.fastx['fpath'], uppercase=True)
		SM = StandardMotif(self.params['standard_level'])

		for item in fx:
			name, seq = item[0:2]

			miner = stria.SSRMiner(name, seq, self.params['min_repeats'])
			ssrs = miner.as_list()

			records = []
			for ssr in ssrs:
				standard_motif = SM.standard(ssr[3])
				ssr_type = iupac_numerical_multiplier(ssr[4])
				records.append((None, name, ssr[1], ssr[2], ssr[3],
					standard_motif, ssr_type, ssr[5], ssr[6]))

			self.progress += len(seq)
			progress = self.progress/self.fastx['size']

			self.sender.send({
				'id': self.fastx['id'],
				'type': 'ssr',
				'records': records,
				'progress': progress
			})

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
					self.sender.send({
						'id': self.fastx['id'],
						'type': 'cssr',
						'records': records,
						'progress': progress
					})
					records = []
				
				cssrs = [ssr]

			self.progress += 1

		if len(cssrs) > 1:
			records.append(self.join_ssrs(cssrs))

		if records:
			progress = self.progress/self.total_ssrs
			self.sender.send({
				'id': self.fastx['id'],
				'type': 'cssr',
				'records': records,
				'progress': progress
			})

	def join_ssrs(self, cssrs):
		chrom = cssrs[0][1]
		start = cssrs[0][2]
		end = cssrs[-1][3]
		complexity = len(cssrs)
		length = sum(cssr[8] for cssr in cssrs)
		structure = '-'.join("({}){}".format(cssr[4], cssr[7]) for cssr in cssrs)
		return (None, chrom, start, end, complexity, length, structure)

class KraitISSRSearchProcess(KraitSearchProcess):
	def do(self):
		fx = pyfastx.Fastx(self.fastx['fpath'], uppercase=True)
		SM = StandardMotif(self.params['standard_level'])

		for item in fx:
			name, seq = item[0:2]

			miner = stria.ITRMiner(name, seq,
				min_motif_size = 1,
				max_motif_size = 6,
				seed_min_repeat = self.params['minsrep'],
				seed_min_length = self.params['minslen'],
				max_continuous_errors = self.params['maxerr'],
				substitution_penalty = self.params['subpena'],
				insertion_penalty = self.params['inspena'],
				deletion_penalty = self.params['delpena'],
				min_match_ratio = self.params['matratio'],
				max_extend_length = self.params['maxextend']
			)
			issrs = miner.as_list()

			records = []
			for issr in issrs:
				standard_motif = SM.standard(issr[3])
				issr_type = iupac_numerical_multiplier(issr[4])
				records.append((None, name, issr[1], issr[2], issr[3],
					standard_motif, issr_type, issr[5], issr[6], issr[7],
					issr[8], issr[9], issr[10]))

			self.progress += len(seq)
			progress = self.progress/self.fastx['size']

			self.sender.send({
				'id': self.fastx['id'],
				'type': 'issr',
				'records': records,
				'progress': progress
			})

class KraitVNTRSearchProcess(KraitSearchProcess):
	def do(self):
		fx = pyfastx.Fastx(self.fastx['fpath'], uppercase=True)

		for item in fx:
			name, seq = item[0:2]

			miner = stria.VNTRMiner(name, seq,
				min_motif_size = self.params['minmotif'],
				max_motif_size = self.params['maxmotif'],
				min_repeat = self.params['minrep']
			)
			vntrs = miner.as_list()

			records = []
			for vntr in vntrs:
				vntr_type = iupac_numerical_multiplier(vntr[4])
				records.append((None, name, vntr[1], vntr[2], vntr[3],
					vntr_type, vntr[5], vntr[6]))

			self.progress += len(seq)
			progress = self.progress/self.fastx['size']

			self.sender.send({
				'id': self.fastx['id'],
				'type': 'vntr',
				'records': records,
				'progress': progress
			})

class KraitPrimerDesignProcess(multiprocessing.Process):
	def __init__(self, fastx, repeats, params, sender):
		super().__init__()
		self.daemon = True
		self.fastx = fastx
		self.repeats = repeats
		self.params = params
		self.sender = sender
		self.progress = 0

	def finish(self):
		self.sender.send({
			'id': self.fastx['id'],
			'type': 'finish'
		})

	def do(self):
		seq_name = None
		seq_cache = None
		flank_len = self.params.pop('PRIMER_FLANK_LENGTH')

		if self.fastx['format'] == 'fasta':
			fx = pyfastx.Fasta(self.fastx['fpath'])
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

			results = primer3.design_primers(
				seq_args = {
					'SEQUENCE_ID': "{}-tr-{}".format(trs[1], trs[0]),
					'SEQUENCE_TEMPLATE': seq_cache[start-1:end],
					'SEQUENCE_TARGET': [target_start, target_len],
					'SEQUENCE_INTERNAL_EXCLUDED_REGION': [target_start, target_len]
				},
				global_args = self.params
			)

			primer_count = results['PRIMER_PAIR_NUM_RETURNED']

			for i in range(primer_count):
				primer = [None, trs[0], i+1]
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

		self.sender.send({
			'id': self.fastx['id'],
			'type': 'primer',
			'records': records,
			'progress': len(self.repeats)
		})

	def run(self):
		try:
			self.do()
			self.finish()
		except:
			error = traceback.format_exc()
			print(error)
		finally:
			self.sender.close()