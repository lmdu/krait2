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
from config import *

__all__ = ['SSRSearchThread', 'VNTRSearchThread',
			'ITRSearchThread', 'PrimerDesignThread']

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
		errmsg = traceback.format_exc()
		self.signals.errors.emit(errmsg)
		print(errmsg)

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
	_table = ''

	def __init__(self, parent=None):
		super().__init__(parent)
		self.findex = 0

	@property
	def table(self):
		return "{}_{}".format(self._table, self.findex)

	@property
	def fastas(self):
		self.total_file = DB.get_one("SELECT COUNT(1) FROM fasta_0 LIMIT 1")
		for fasta in DB.query("SELECT * FROM fasta_0"):
			yield fasta

	def sql(self):
		self.columns = len(DB.get_field(self.table)) - 1
		return "INSERT INTO {} VALUES (NULL{})".format(
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
				DB.create_table(self._table, self.findex)
				self.change_status('running')

				seqs = pyfastx.Fastx(fasta[4], uppercase=True)
				sql = self.sql()

				for name, seq, _ in seqs:
					self.signals.messages.emit('processing sequence {} in file {}'.format(name, fasta[1]))

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
	_table = 'ssr'

	def __init__(self, parent):
		super().__init__(parent)
		self.settings.beginGroup("SSR")
		self.min_repeats = [
			self.settings.value('mono', 12, int),
			self.settings.value('di', 7, int),
			self.settings.value('tri', 5, int),
			self.settings.value('tetra', 4, int),
			self.settings.value('penta', 4, int),
			self.settings.value('hexa', 4, int)
		]
		self.settings.endGroup()

		standard_level = self.settings.value('STR/level', 3, type=int)
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
	_table = 'cssr'

	def __init__(self, parent):
		super().__init__(parent)
		params = ['SSR/mono', 'SSR/di', 'SSR/tri', 'SSR/tetra', 'SSR/penta', 'SSR/hexa']
		self.min_repeats = []
		for param in params:
			default, func = KRAIT_PARAMETERS[param]
			self.min_repeats.append(self.settings.value(param, default, func))

		default, func = KRAIT_PARAMETERS['CSSR/dmax']
		self.dmax = self.settings.value('CSSR/dmax', default, func)

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
	_table = 'vntr'

	def __init__(self, parent):
		super().__init__(parent)
		self.params = []

		params = ['VNTR/minmotif', 'VNTR/maxmotif', 'VNTR/minrepeat']
		for param in params:
			default, func = KRAIT_PARAMETERS[param]
			self.params.append(self.settings.value(param, default, func))

	def args(self, name, seq):
		return (name, seq, *self.params)

	@staticmethod
	def search(*args):
		return stria.VNTRMiner(*args).as_list()

	def rows(self, vntrs):
		for vntr in vntrs:
			row = list(vntr)
			row[4] = iupac_numerical_multiplier(row[4])
			yield row

class ITRSearchThread(SearchThread):
	_table = 'itr'

	def __init__(self, parent):
		super(ITRWorkerThread, self).__init__(parent)
		self.params = []
		params = ['ITR/minmsize', 'ITR/maxmsize', 'ITR/minsrep', 'ITR/minslen',
					'ITR/maxerr', 'ITR/subpena', 'ITR/inspena', 'ITR/delpena',
					'ITR/matratio', 'ITR/maxextend']
		for param in params:
			default, func = KRAIT_PARAMETERS[param]
			self.params.append(self.settings.value(param, default, func))

	def args(self, name, seq):
		return (name, seq, *self.params)

	@staticmethod
	def search(*args):
		return stria.ITRMiner(*args).as_list()

	def rows(self, itrs):
		return itrs

class PrimerDesignThread(WorkerThread):
	def __init__(self, parent=None, table=None):
		super().__init__(parent)
		self.parent = parent
		self.batch = 100

		#current table is tandem repeat table, not primer table
		self.table, self.findex = table.split('_')		

		param = "STR/flank"
		default, func = KRAIT_PARAMETERS[param]
		self.flank_len = self.settings.value(param, default, func)
		
		self._sql = "SELECT * FROM {} WHERE id IN ({})".format(table, ','.join(['?']*self.batch))
		self._isql = "INSERT INTO primer_{} VALUES (NULL{})".format(self.findex, ',?'*15)

		DB.create_table('primer', self.findex)
		DB.clear_table('primer', self.findex)

		self.read_primer_settings()

	def read_primer_settings(self):
		self.primer_tags = {}

		self.settings.beginGroup("PRIMER")
		for k in self.settings.allKeys():
			default, func = primer_tag_format(k)
			self.primer_tags[k] = self.settings.value(k, default, func)
		self.settings.endGroup()

		if not self.primer_tags:
			for param in PRIMER_COMMONS:
				default, _ = PRIMER_PARAMETERS[param]
				self.primer_tags = default

		size_ranges = self.primer_tags['PRIMER_PRODUCT_SIZE_RANGE']
		self.primer_tags['PRIMER_PRODUCT_SIZE_RANGE'] =	product_size_format(size_ranges)
		self.primer_tags['PRIMER_TASK'] = 'generic'
		self.primer_tags['PRIMER_PICK_LEFT_PRIMER'] = 1
		self.primer_tags['PRIMER_PICK_INTERNAL_OLIGO'] = 0
		self.primer_tags['PRIMER_PICK_RIGHT_PRIMER'] = 1

	def sql(self, num):
		if num == self.batch:
			return self._sql
		else:
			return "SELECT * FROM {}_{} WHERE id IN ({})".format(self.table, self.findex, ','.join(['?']*num))

	def process(self):
		#get fasta file path
		fasta_file = DB.get_one("SELECT path FROM fasta_0 WHERE id=?", self.findex)
		fasta = pyfastx.Fasta(fasta_file, uppercase=True)

		print(self.primer_tags)

		primer3.bindings.setP3Globals(self.primer_tags)
		
		selected = sorted(self.parent.get_selected_rows())
		total = len(selected)
		processed = 0
		progress = 0
		slice_start = 0
		slice_end = 0

		while slice_start < total:
			slice_end = slice_start + self.batch
			ids = selected[slice_start:slice_end]
			slice_start = slice_end

			primer_list = []
			for tr in DB.query(self.sql(len(ids)), ids):
				tr_start = tr[2] - self.flank_len
				if tr_start < 1:
					tr_start = 1

				tr_end = tr[3] + self.flank_len

				if tr_end > len(fasta[tr[1]]):
					tr_end = len(fasta[tr[1]])

				tr_seq = fasta.fetch(tr[1], (tr_start, tr_end))
				tr_len = tr[3] - tr[2] + 1

				locus = "{}.{}.{}".format(self.table, self.findex, tr[0])

				primer3.bindings.setP3SeqArgs({
					'SEQUENCE_ID': locus,
					'SEQUENCE_TEMPLATE': tr_seq,
					'SEQUENCE_TARGET': [tr[2]-tr_start, tr_len],
					#'SEQUENCE_INTERNAL_EXCLUDED_REGION': [tr[2]-tr_start, tr_len]
				})

				res = primer3.bindings.runP3Design()

				print(res)

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

