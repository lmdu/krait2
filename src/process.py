import os
import stria
import multiprocessing

from PySide6.QtCore import *

__all__ = []

class BaseProcess(multiprocessing.Process):
	def __init__(self, infile, params, producer):
		super().__init__()
		self.daemon = True
		self.infile = infile
		self.params = params
		self.producer = producer

	def build_index(self):
		if self.infile.size:
			return

		if self.infile.format == 'fasta':
			fx = pyfastx.Fasta(self.infile.fpath, full_index=True)

		elif self.infile.format == 'fastq':
			fx = pyfastx.Fastq(self.infile.fpath, full_index=True)

		self.seq_size = fx.size
		self.seq_count = len(fx)
		self.seq_gc = fx.gc_content
		self.seq_ns = fx.composition['N']

		self.producer.send({
			'data': (self.infile.id, self.seq_size, self.seq_count, self.seq_gc, self.seq_ns)
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
			self.producer.close()

class SSRProcess(BaseProcess):
	def do(self):
		fx = pyfastx.Fastx(self.infile.fpath, uppercase=True)

		for item in fx:
			name, seq = item[0:2]

			ssrs = stria.SSRMiner(name, seq, self.params.min_reps).as_list()



