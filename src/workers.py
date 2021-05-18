import os
import time
import stria
import pyfastx
import traceback
import multiprocessing

from PySide6.QtCore import *

from backend import *
from motif import *

__all__ = ['SSRWorkerThread', 'VNTRWorkerThread',
			'ITRWorkerThread']

def iupac_number(n):
	mapping = {
		0: 'mono',
		1: 'hen',
		2: 'di',
		3: 'tri',
		4: 'tetra',
		5: 'penta',
		6: 'hexa'
	}

	return mapping.get(n, str(n))

class WorkerSignal(QObject):
	progress = Signal(int)
	messages = Signal(str)
	errors = Signal(str)
	finished = Signal()
	status = Signal(int)

class WorkerThread(QThread):
	table = ''

	def __init__(self, parent=None):
		super(WorkerThread, self).__init__(parent)
		self.signals = WorkerSignal()
		self.signals.messages.connect(parent.show_status_message)
		self.signals.errors.connect(parent.show_error_message)
		self.signals.status.connect(parent.change_task_status)
		self.columns = len(DB.get_field(self.table)) - 1
		self.settings = QSettings()
		self.findex = 0

	@property
	def fastas(self):
		self.total = DB.get_one("SELECT COUNT(*) FROM fastas LIMIT 1")
		for fasta in DB.query("SELECT * FROM fastas"):
			yield fasta

	@property
	def sql(self):
		return "INSERT INTO {}{{}} VALUES (NULL{})".format(
			self.table,
			",?" * self.columns
		)

	def args(self, name, seq):
		return (name, seq)

	@staticmethod
	def search(*args):
		pass

	def rows(self, trs):
		pass

	def process(self):
		processed_fasta = 0

		with multiprocessing.Pool(1) as pool:
			for fasta in self.fastas:
				self.signals.messages.emit('processing file {}'.format(fasta[1]))
				self.findex = fasta[0]
				#create ssr table for current file
				DB.create_table(self.table, self.findex)
				self.change_status('running')

				seqs = pyfastx.Fastx(fasta[4], uppercase=True)
				sql = self.sql.format(self.findex)

				for name, seq, _ in seqs:
					proc = pool.apply_async(self.search, self.args(name, seq))
					trs = proc.get()
					DB.insert_rows(sql, self.rows(trs))
				
				processed_fasta += 1

				p = processed_fasta/self.total
				self.signals.progress.emit(p)

				self.change_status('success')

	def run(self):
		self.signals.progress.emit(0)

		try:
			self.process()
		except:
			self.signals.errors.emit(traceback.format_exc())
			self.change_status('failure')

		self.signals.progress.emit(1)
		self.signals.messages.emit('Finished!')
		self.signals.finished.emit()

	def change_status(self, status):
		DB.update_status(self.findex, status)
		self.signals.status.emit(self.findex)

class SSRWorkerThread(WorkerThread):
	table = 'ssr'

	def __init__(self, parent):
		super(SSRWorkerThread, self).__init__(parent)
		self.settings.beginGroup("SSR")
		self.min_repeats = self.settings.value('min_repeats', [12, 7, 5, 4, 4, 4])
		self.settings.endGroup()
		self.min_repeats = [int(mr) for mr in self.min_repeats]

		self.settings.beginGroup("Stat")
		standard_level = self.settings.value('standard_level', 0, int)
		self.settings.endGroup()
		self.motifs = StandardMotif(standard_level)

	def args(self, name, seq):
		return (name, seq, self.min_repeats)

	@staticmethod
	def search(*args):
		return stria.SSRMiner(*args).as_list()

	def rows(self, ssrs):
		for ssr in ssrs:
			row = [ssr[0], ssr[1], ssr[2], ssr[3], self.motifs.standard(ssr[3]),
					iupac_number(ssr[4]), ssr[5], ssr[6]]
			yield row

class CSSRWorkerThread(WorkerThread):
	table = 'cssr'

	def __init__(self, parent):
		self.settings.beginGroup("SSR")
		self.min_repeats = self.settings.value('min_repeats', [12, 7, 5, 4, 4, 4])
		self.settings.endGroup()
		self.min_repeats = [int(mr) for mr in self.min_repeats]

		self.settings.beginGroup("CSSR")
		self.dmax = self.settings.value('dmax', 10)
		self.settings.endGroup()

	def args(self, name, seq):
		return (name, seq, self.min_repeats)

	@staticmethod
	def search(*args):
		return stria.SSRMiner(*args).as_list()
	'''
	def rows(self, ssrs):
		cssrs = [next(ssrs)]

		for ssr in ssrs:
			dmax = ssr[1] - cssrs[-1][2] - 1

			if dmax <= self.dmax:
				cssrs.append(ssr)

			else:
				if len(cssrs) > 1:
					pass

				cssrs = [ssr]

		if len(cssrs) > 1:
			self.

	def adjacent_join(self, cssrs):
		return (cssrs[0][0], cssrs[0][1], cssrs[-1][2], len(cssrs),
			cssrs[-1][2] - cssrs[0][1] + 1,
			"{}-{}".format(cssrs[0])
		)
	'''

class VNTRWorkerThread(WorkerThread):
	table = 'vntr'

	def __init__(self, parent):
		super(VNTRWorkerThread, self).__init__(parent)
		self.settings.beginGroup("VNTR")
		self.min_motif = self.settings.value('min_motif', 7)
		self.max_motif = self.settings.value('max_motif', 30)
		self.min_repeat = self.settings.value('min_repeat', 3)
		self.settings.endGroup()

	def args(self, name, seq):
		return (name, seq, self.min_motif, self.max_motif, self.min_repeat)

	@staticmethod
	def search(*args):
		return stria.VNTRMiner(*args).as_list()

	def rows(self, vntrs):
		for vntr in vntrs:
			row = list(vntr)
			row[4] = iupac_number(row[4])
			yield row

class ITRWorkerThread(WorkerThread):
	table = 'itr'

	def __init__(self, parent):
		super(ITRWorkerThread, self).__init__(parent)
		self.settings.beginGroup("ITR")
		self.min_motif = self.settings.value('min_motif', 1)
		self.max_motif = self.settings.value('max_motif', 6)
		self.min_srep = self.settings.value('min_srep', 3)
		self.min_slen = self.settings.value('min_slen', 10)
		self.max_errors = self.settings.value('max_errors', 2)
		self.sub_penalty = self.settings.value('sub_penalty', 0.5)
		self.ins_penalty = self.settings.value('ins_penalty', 1.0)
		self.del_penalty = self.settings.value('del_penalty', 1.0)
		self.min_ratio = self.settings.value('min_ratio', 0.7)
		self.max_extend = self.settings.value('max_extend', 2000)
		self.settings.endGroup()

	def args(self, name, seq):
		return (name, seq, self.min_motif, self.max_motif, self.min_srep, self.min_slen,
				self.max_errors, self.sub_penalty, self.ins_penalty, self.del_penalty,
				self.min_ratio, self.max_extend)

	@staticmethod
	def search(*args):
		return stria.ITRMiner(*args).as_list()

	def rows(self, itrs):
		return itrs
