import os
import time
import stria
import primer3
import pyfastx
import traceback
import multiprocessing

from PySide6.QtCore import *

from backend import *
from motif import *
from utils import *

__all__ = ['SSRWorkerThread', 'VNTRWorkerThread',
			'ITRWorkerThread']

class WorkerSignal(QObject):
	progress = Signal(int)
	messages = Signal(str)
	errors = Signal(str)
	finished = Signal()
	status = Signal(int)

class WorkerThread(QThread):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.signals = WorkerSignal()
		self.signals.progress.connect(parent.change_progress)
		self.signals.messages.connect(parent.show_status_message)
		self.signals.errors.connect(parent.show_error_message)
		self.signals.status.connect(parent.change_task_status)
		self.settings = QSettings()

	def process(self):
		pass

	def error(self):
		self.signals.errors.emit(traceback.format_exc())

	def run(self):
		self.signals.progress.emit(0)

		try:
			self.process()
		except:
			self.error()

		self.signals.progress.emit(100)
		self.signals.messages.emit('Finished!')
		self.signals.finished.emit()

class SearchThread(WorkerThread):
	table = ''

	def __init__(self, parent=None):
		super().__init__(parent)
		self.columns = len(DB.get_field(self.table)) - 1
		self.findex = 0

	@property
	def fastas(self):
		self.total_file = DB.get_one("SELECT COUNT(1) FROM fasta LIMIT 1")
		for fasta in DB.query("SELECT * FROM fasta"):
			yield fasta

	@property
	def sql(self):
		return "INSERT INTO {}_{{}} VALUES (NULL{})".format(
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
		progress = 0
		processed_size = 0
		processed_file = 0

		with multiprocessing.Pool(1) as pool:
			for fasta in self.fastas:
				self.findex = fasta[0]
				total_size = fasta[2]
				#create ssr table for current file
				DB.create_table(self.table, self.findex)
				self.change_status('running')

				seqs = pyfastx.Fastx(fasta[4], uppercase=True)
				sql = self.sql.format(self.findex)

				for name, seq, _ in seqs:
					self.signals.messages.emit('processing sequence {} in {}'.format(name, fasta[1]))
					proc = pool.apply_async(self.search, self.args(name, seq))
					trs = proc.get()
					DB.insert_rows(sql, self.rows(trs))

					processed_size += len(seq)

					if processed_size > total_size:
						r = 0
					else:
						r = processed_size/total_size

					p = int((processed_file + r)/self.total_file*100)

					if p > progress:
						self.signals.progress.emit(p)
						progress = p

				processed_file += 1
				self.change_status('success')

	def error(self):
		self.signals.errors.emit(traceback.format_exc())
		self.change_status('failure')

	def change_status(self, status):
		DB.update_status(self.findex, status)
		self.signals.status.emit(self.findex)

class SSRSearchThread(SearchThread):
	table = 'ssr'

	def __init__(self, parent):
		super().__init__(parent)
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
					iupac_numerical_multiplier(ssr[4]), ssr[5], ssr[6]]
			yield row

class CSSRSearchThread(SearchThread):
	table = 'cssr'

	def __init__(self, parent):
		super().__init__(parent)

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

class VNTRSearchThread(SearchThread):
	table = 'vntr'

	def __init__(self, parent):
		super().__init__(parent)
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
			row[4] = iupac_numerical_multiplier(row[4])
			yield row

class ITRSearchThread(SearchThread):
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

class PrimerDesignThread(WorkerThread):
	def __init__(self, parent=None, table=None):
		super().__init__(parent)
		self.table, self.findex = table.split('_')
		self.parent = parent
		self.batch = 100
		self.flank_len = int(self.settings.getValue("STR/flank"))
		self._sql = "SELECT * FROM {}_{} WHERE id IN ({})".format(table, ','.join(['?']*self.batch))
		self._isql = "INSERT INTO primer_{} VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(self.findex)

		DB.create_table(self.table, self.findex)
		DB.clear_table(table)

		self.read_primer_settings()

	def read_primer_settings(self):
		self.settings.beginGroup("PRIMER")
		self.primer_tags = {k: self.settings.getValue(k) for k in self.settings.allKeys()}
		self.settings.endGroup()
		size_ranges = []
		for r in self.primer_tags['PRIMER_PRODUCT_SIZE_RANGE'].split():
			size_ranges.append(r.split('-'))
		self.primer_tags['PRIMER_PRODUCT_SIZE_RANGE'] = size_ranges

	def sql(self, num):
		if num == self.batch:
			return self._sql
		else:
			return "SELECT * FROM {}_{} WHERE id IN ({})".format(self.table, self.findex, ','.join(['?']*num))

	def process(self):
		#get fasta file path
		fasta_file = DB.get_one("SELECT path FROM fasta WHERE id=?", self.findex)
		fasta = pyfastx.Fasta(fasta_file, uppercase=True)

		selected = sorted(self.parent.get_selected_rows())
		total = len(selected)
		processed = 0
		progress = 0
		tr_type = self.table.split('_')[0]

		primer3.bindings.setP3Globals(self.primer_tags)

		while start < total:
			end = start + self.batch
			ids = selected[start:end]
			primer_list = []

			for tr in DB.query(self.sql(len(ids)), ids):
				start = tr[2] - self.flank_len
				if start < 1:
					start = 1

				end = tr[3] + self.flank_len

				if end > len(fasta[tr[0]]):
					end = len(fasta[tr[0]])

				seq = fasta.fetch(tr[1], (start, end))
				slen = tr[3] - tr[1] + 1

				locus = "{}.{}.{}".format(tr_type, self.findex, tr[0])

				primer3.bindings.setP3SeqArgs({
					'SEQUENCE_ID': locus,
					'SEQUENCE_TEMPLATE': seq,
					'SEQUENCE_TARGET': [tr[2]-start, slen],
					'SEQUENCE_INTERNAL_EXCLUDED_REGION': [tr[2]-start, slen]
				})

				res = primer3.bindings.runP3Design()

				if res:
					primer_count = res['PRIMER_PAIR_NUM_RETURNED']
					
					for i in range(primer_count):
						primer_info = [locus, i+1,
							res['PRIMER_PAIR_%s_PRODUCT_SIZE' % i],
							res['PRIMER_LEFT_%s_SEQUENCE' % i],
							round(res['PRIMER_LEFT_%s_TM' % i], 2),
							round(res['PRIMER_LEFT_%s_GC_PERCENT' % i], 2),
							round(res['PRIMER_LEFT_%s_END_STABILITY' % i], 2),
							res['PRIMER_RIGHT_%s_SEQUENCE' % i],
							round(res['PRIMER_RIGHT_%s_TM' % i], 2),
							round(res['PRIMER_RIGHT_%s_GC_PERCENT' % i], 2),
							round(res['PRIMER_RIGHT_%s_END_STABILITY' % i], 2),
						]
						primer_info.extend(res['PRIMER_LEFT_%s' % i])
						primer_info.extend(res['PRIMER_RIGHT_%s' % i])
						primer_list.append(primer_info)

			if primer_list:
				DB.insert_rows(self._isql, primer_list)

			processed += len(ids)
			p = int(processed/total*100)
			if p > progress:
				self.signals.progress.emit(p)
				progress = p

