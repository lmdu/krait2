import os
import time
import stria
import pyfastx
import traceback
import multiprocessing

from PySide6.QtCore import *

from backend import *
from motif import *

__all__ = ['SSRWorkerThread']

def iupac_number(n):
	mapping = ['', 'Mono', 'Di', 'Tri', 'Tetra', 'Penta' 'Hexa', 'Hepta']
	return mapping[n]

class WorkerSignal(QObject):
	progress = Signal(int)
	messages = Signal(str)
	errors = Signal(str)
	finished = Signal()

class WorkerThread(QThread):
	def __init__(self, parent=None):
		QThread.__init__(self, parent)
		self.signals = WorkerSignal()

		self.signals.messages.connect(parent.show_status_message)
		self.signals.errors.connect(parent.show_error_message)

	@property
	def fastas(self):
		self.total = DB.get_one("SELECT COUNT(*) FROM fastas LIMIT 1")
		for fasta in DB.query("SELECT * FROM fastas"):
			yield fasta

	def process(self):
		pass

	def run(self):
		self.signals.progress.emit(0)

		try:
			self.process()
		except:
			self.errors.emit(traceback.format_exc())

		self.signals.progress.emit(1)
		self.signals.messages.emit('Finished!')
		self.signals.finished.emit()

class SSRWorkerThread(WorkerThread):
	def __init__(self, parent, min_repeats, standard_level):
		super(SSRWorkerThread, self).__init__(parent)

		self.finished.connect(parent.show_ssr_result)

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
		processed_fasta = 0
		for fasta in self.fastas:
			self.signals.messages.emit('processing file {}'.format(fasta[2]))

			#create ssr table for current file
			DB.create_ssr_table(fasta[0])

			seqs = pyfastx.Fastx(fasta[2], uppercase=True)

			with multiprocessing.Pool(1) as pool:
				for name, seq, _ in seqs:
					proc = pool.apply_async(self.search, (name, seq, self.min_repeats))
					ssrs = proc.get()
					DB.insert_rows(self.sql.format(fasta[0]), self.rows(ssrs))
			
			processed_fasta += 1

			p = processed_fasta/self.total
			self.signals.progress.emit(p)

