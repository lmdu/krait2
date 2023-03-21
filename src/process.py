import os
import stria
import pyfastx
import traceback
import multiprocessing

from PySide6.QtCore import *

from utils import *
from motif import *

__all__ = ['SSRSearchProcess', 'CSSRSearchProcess']

class SearchProcess(multiprocessing.Process):
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

	def do(self):
		pass

	def run(self):
		try:
			self.build_index()
			self.do()
		except:
			error = traceback.format_exc()
			print(error)
		finally:
			self.sender.close()

class SSRSearchProcess(SearchProcess):
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

		self.sender.send({
			'id': self.fastx['id'],
			'type': 'finish'
		})

class CSSRSearchProcess(SearchProcess):
	def do(self):
		table =  "ssr_{}".format(self.fastx['id'])
		self.total_ssrs = DB.get_count(table)
		ssrs = DB.query("SELECT * FROM {}".format(table))
		cssrs = [next(ssrs)]

		records = []
		for ssr in ssrs:
			d = ssr[2] - cssrs[-1][3] - 1

			if ssr[1] == cssrs[-1][1]:
				if d <= self.params['dmax']:
					cssrs.append(ssr)

				else:
					if len(cssrs) > 1:
						records.append(self.join_ssrs(cssrs))

					cssrs = [ssr]
			else:
				self.sender.send({
					'id': self.fastx['id'],
					'type': 'cssr',
					'records': records
				})
				records = []
				cssrs = [ssr]

		if len(cssrs) > 1:
			records.append(self.join_ssrs(cssrs))

		if records:
			self.sender.send({
				'id': self.fastx['id'],
				'type': 'cssr',
				'records': records
			})

	def join_ssrs(cssrs):
		chrom = cssrs[0][1]
		start = cssrs[0][2]
		end = cssrs[-1][3]
		complexity = len(cssrs)
		length = sum(cssr[8] for cssr in cssrs)
		structure = '-'.join("({}){}".format(cssr[4], cssr[7]) for cssr in ssrs)
		return (None, chrom, start, end, complexity, length, structure)





