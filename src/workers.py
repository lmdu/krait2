import os
import time
import stria
import pyfastx
import traceback
import multiprocessing

from PySide6.QtCore import *

from backend import *
from motif import *

__all__ = ['SSRWorker']

class BaseWorker(QObject):
	progress = Signal(int)
	messages = Signal(str)
	errors = Signal(str)
	finished = Signal()

	@property
	def fastas(self):
		for fasta in DB.query("SELECT * FROM fastas"):
			yield fasta

	def process(self):
		pass

	@Slot()
	def run(self):
		self.progress.emit(0)

		try:
			self.process()
		except:
			self.errors.emit(traceback.format_exc())

		self.progress.emit(100)
		self.messages.emit('Finished!')
		self.finished.emit()

class SSRWorker(BaseWorker):
	def __init__(self, min_repeats, standard_level):
		super(SSRWorker, self).__init__()

		self.min_repeats = min_repeats
		self.motifs = StandardMotif(standard_level)
		self.sql = "INSERT INTO ssr{} VALUES (?,?,?,?,?,?,?,?,?)"

	@staticmethod
	def search(name, seq, min_repeats):
		return stria.SSRMiner(name, seq, min_repeats).as_list()

	def rows(self, ssrs):
		for ssr in ssrs:
			row = [None, ssr[0], ssr[1], ssr[2], ssr[3], self.motifs.standard(ssr[3]),
					str(ssr[4]), ssr[5], ssr[6]]
			yield row

	def process(self):
		with multiprocessing.Pool(1) as pool:
			for fasta in self.fastas:
				self.messages.emit('processing file {}'.format(fasta[2]))

				#create ssr table for current file
				DB.create_ssr_table(fasta[0])

				seqs = pyfastx.Fastx(fasta[2], uppercase=True)
				for name, seq, _ in seqs:
					proc = pool.apply_async(self.search, (name, seq, self.min_repeats))
					ssrs = proc.get()

					DB.insert_rows(self.sql.format(fasta[0]), self.rows(ssrs))

