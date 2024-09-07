import os
import csv
import time
import pytrf
import pyfastx
import primer3
import traceback
import multiprocessing

from PySide6.QtGui import *
from PySide6.QtCore import *

from motif import *
from stats import *
from utils import *
from config import *
from backend import *
from process import *
from annotate import *

__all__ = [
	'SSRSearchThread', 'GTRSearchThread',
	'ISSRSearchThread', 'PrimerDesignThread',
	'SaveProjectThread', 'ExportSelectedRowsThread',
	'ExportWholeTableThread', 'ExportAllTablesThread',
	'TRELocatingThread', 'StatisticsThread',
	'KraitSSRSearchWorker', 'KraitCSSRSearchWorker',
	'KraitISSRSearchWorker', 'KraitGTRSearchWorker',
	'KraitPrimerDesignWorker', 'KraitMappingWorker',
	'KraitStatisticsWorker', 'KraitSaveWorker',
	'KraitExportStatisticsWorker', 'KraitExportSelectedWorker'
]

#signals can only be emit from QObject
class KraitWorkerSignals(QObject):
	finished = Signal()
	status = Signal()
	failure = Signal(str)
	show_tab = Signal(str, int)
	progress = Signal(int)
	messages = Signal(str)

class KraitBaseWorker(QRunnable):
	processer = None

	def __init__(self):
		super().__init__()
		self.setAutoDelete(True)
		self.fastx = None
		self.processes = 0
		self.queue = multiprocessing.Queue()
		self.signals = KraitWorkerSignals()
		self.settings = QSettings()
		self.params = self.get_params()

	def exit(self):
		self.queue.close()

	def start_process(self):
		proc = self.processer(self.params, self.queue, self.fastx)
		proc.start()

	def get_params(self):
		pass

	def before_run(self):
		pass

	def submit_process(self):
		self.start_process()
		self.processes += 1

	def call_response(self, data):
		pass

	@Slot()
	def run(self):
		self.before_run()
		self.signals.progress.emit(0)

		try:
			for i in range(self.concurrent):
				self.submit_process()

			while True:
				try:
					data = self.queue.get()
					self.call_response(data)

				except ValueError:
					break

		except:
			error = traceback.format_exc()
			self.signals.failure.emit(error)
			print(error)

		finally:
			self.signals.progress.emit(100)
			self.signals.finished.emit()
			self.signals.messages.emit('Done')

class KraitSearchWorker(KraitBaseWorker):
	table_name = None

	def __init__(self):
		super().__init__()
		
		self.total_size = 0
		self.fastx_query = None
		self.progresses = {}
		self.concurrent = self.settings.value('Run/concurrent', 1, int)
		self.total_fastx = DB.get_count('fastx')

	def get_params(self):
		pass

	def query_fastx(self):
		self.total_size = DB.get_one("SELECT SUM(bytes) FROM fastx")
		self.fastx_query = DB.query("SELECT * FROM fastx")

	def update_progress(self, data):
		self.progresses[data['id']] = data['progress']
		p = sum(self.progresses.values())*100
		self.signals.progress.emit(p)

	def start_process(self, fastx):
		DB.drop_table(self.table_name, fastx['id'])
		DB.create_table(self.table_name, fastx['id'])
		proc = self.processer(self.params, self.queue, fastx)
		proc.start()

	def get_fastx(self):
		row = self.fastx_query.fetchone()

		if row:
			fields = [name for name, _ in self.fastx_query.getdescription()]
			return dict(zip(fields, row))

	def update_status(self, fid=None, status=None):
		if fid is None:
			DB.query("UPDATE fastx SET status=3")
		else:
			DB.update_status(fid, status)

		self.signals.status.emit()

	def update_success(self, fid):
		self.update_status(fid, 1)

	def update_error(self, fid, err):
		DB.query("UPDATE fastx SET message=? WHERE id=?", (err, fid))
		self.update_status(fid, 0)
		self.signals.status.emit()

	def update_info(self, info):
		self.signals.messages.emit(info)

	def submit_process(self):
		if self.fastx_query is None:
			return

		if self.processes >= self.concurrent:
			return

		fastx = self.get_fastx()

		if fastx:
			fastx['weight'] = fastx['bytes']/self.total_size
			self.start_process(fastx)
			self.processes += 1
			self.update_status(fastx['id'], 2)

	def before_run(self):
		self.update_status()
		self.query_fastx()

	def call_response(self, data):
		if data['type'] == 'fastx':
			DB.update_fastx(data['records'])

		elif data['type'] == 'success':
			self.update_success(data['id'])

		elif data['type'] == 'finish':
			self.processes -= 1
			self.submit_process()

			if self.processes == 0:
				self.exit()
				self.signals.show_tab.emit(self.table_name, data['id'])

		elif data['type'] == 'error':
			self.update_error(data['id'], data['message'])

		elif data['type'] == 'info':
			self.update_info(data['message'])

		else:
			table = "{}_{}".format(data['type'], data['id'])
			DB.insert_rows(DB.get_sql(table), data['records'])

			if data['progress']:
				self.update_progress(data)

class KraitSSRSearchWorker(KraitSearchWorker):
	table_name = 'ssr'
	processer = KraitSSRSearchProcess

	def get_params(self):
		keys = ['SSR/mono', 'SSR/di', 'SSR/tri', 'SSR/tetra', 'SSR/penta', 'SSR/hexa']
		min_repeats = [self.settings.value(k, KRAIT_SEARCH_PARAMETERS[k][0], int) for k in keys]
		standard_level = self.settings.value('STR/level', KRAIT_SEARCH_PARAMETERS['STR/level'][0], int)
		return {'min_repeats': min_repeats, 'standard_level': standard_level}

class KraitCSSRSearchWorker(KraitSearchWorker):
	table_name = 'cssr'
	processer = KraitCSSRSearchProcess

	def start_process(self, fastx):
		DB.create_table(self.table_name, fastx['id'])
		sql = "SELECT * FROM ssr_{}".format(fastx['id'])
		self.params['ssrs'] = DB.get_rows(sql)
		proc = self.processer(self.params, self.queue, fastx)
		proc.start()

	def get_params(self):
		return {
			'dmax': self.settings.value('CSSR/dmax', KRAIT_SEARCH_PARAMETERS['CSSR/dmax'][0], int)
		}

class KraitISSRSearchWorker(KraitSearchWorker):
	table_name = 'issr'
	processer = KraitISSRSearchProcess

	def get_params(self):
		params = {
			'standard_level': self.settings.value('STR/level', KRAIT_SEARCH_PARAMETERS['STR/level'][0], int)
		}

		for k in KRAIT_SEARCH_PARAMETERS:
			if not k.startswith('ISSR'):
				continue

			default, converter = KRAIT_SEARCH_PARAMETERS[k]
			p = k.split('/')[1]
			params[p] = self.settings.value(k, default, converter)

		return params

class KraitGTRSearchWorker(KraitSearchWorker):
	table_name = 'gtr'
	processer = KraitGTRSearchProcess

	def get_params(self):
		params = {}

		for k in KRAIT_SEARCH_PARAMETERS:
			if not k.startswith('GTR'):
				continue

			default, convert = KRAIT_SEARCH_PARAMETERS[k]
			p = k.split('/')[1]
			params[p] = self.settings.value(k, default, convert)

		return params

class KraitPrimerDesignWorker(KraitBaseWorker):
	table_name = 'primer'
	processer = KraitPrimerDesignProcess

	def __init__(self, index, total, repeats, category):
		super().__init__()
		self.index = index
		self.total_count = total
		self.repeats = repeats
		self.category = category
		self.concurrent = 1
		self.progress = 0

	def get_params(self):
		params = {}

		self.settings.beginGroup("PRIMER")

		for k in KRAIT_PRIMER_TAGS:
			default, convert = KRAIT_PRIMER_TAGS[k]
			v = self.settings.value(k, default, convert)

			if v != default or k == 'PRIMER_FLANK_LENGTH':
				params[k] = v

		self.settings.endGroup()

		p = 'PRIMER_PRODUCT_SIZE_RANGE'

		if p in params:
			params[p] = [r.split('-') for r in params[p].split()]

		return params

	def start_process(self, trs):
		proc = self.processer(trs, self.index, self.category, self.params, self.queue, self.fastx)
		proc.start()

	def before_run(self):
		sql = "SELECT * FROM fastx WHERE id=? LIMIT 1"
		self.fastx = DB.get_dict(sql, (self.index,))
		DB.drop_table(self.table_name, self.index)
		DB.create_table(self.table_name, self.index)

	def submit_process(self):
		try:
			trs = next(self.repeats)
		except StopIteration:
			return

		self.start_process(trs)
		self.processes += 1

	def call_response(self, data):
		if data['type'] == 'success':
			pass

		elif data['type'] == 'info':
			self.signals.messages.emit(data['message'])

		elif data['type'] == 'finish':
			self.processes -= 1
			self.submit_process()

			if self.processes == 0:
				self.queue.close()

			self.signals.show_tab.emit(self.table_name, data['id'])

		else:
			table = "{}_{}".format(data['type'], data['id'])
			DB.insert_rows(DB.get_sql(table), data['records'])
			self.update_progress(data)

	def update_progress(self, data):
		self.progress += data['progress']
		p = self.progress/self.total_count*100
		self.signals.progress.emit(p)

class KraitMappingWorker(KraitSearchWorker):
	table_name = 'map'
	processer = KraitMappingProcess

	def before_run(self):
		for i in range(1, self.total_fastx+1):
			DB.drop_index('map', i)
		
		super().before_run()

	def start_process(self, repeats, fastx):
		DB.drop_table('map', fastx['id'])
		DB.drop_table('annot', fastx['id'])

		DB.create_table('map', fastx['id'])
		DB.create_table('annot', fastx['id'])
		
		proc = self.processer(repeats, self.queue, fastx)
		proc.start()

	def get_repeats(self, index):
		self.signals.messages.emit("Preparing repeats for annotation ...")

		types = {'ssr': 1, 'cssr': 2, 'gtr': 3, 'issr': 4}

		repeats = []
		for k, v in types.items():
			table = "{}_{}".format(k, index)
			if DB.table_exists(table):
				sql = "SELECT id,chrom,start,end FROM {}".format(table)
				for row in DB.query(sql):
					row = list(row)
					row.append(v)
					repeats.append(row)

		return repeats

	def submit_process(self):
		if self.fastx_query is None:
			return

		if self.processes >= self.concurrent:
			return

		fastx = self.get_fastx()

		if fastx:
			fastx['weight'] = fastx['bytes']/self.total_size
			repeats = self.get_repeats(fastx['id'])
			self.start_process(repeats, fastx)
			self.processes += 1
			self.update_status(fastx['id'], 2)

	def create_index(self, tid):
		self.signals.messages.emit("Create query index ...")
		sql = "CREATE INDEX index_{0} ON map_{0}(type, locus)"
		DB.query(sql.format(tid))

	def call_response(self, data):
		if data['type'] == 'annot':
			table = "{}_{}".format(data['type'], data['id'])
			DB.insert_rows(DB.get_sql(table), data['records'])

		elif data['type'] == 'success':
			self.create_index(data['id'])
			self.update_success(data['id'])

		elif data['type'] == 'info':
			self.update_info(data['message'])

		elif data['type'] == 'finish':
			self.processes -= 1
			self.submit_process()

			if self.processes == 0:
				self.exit()

		elif data['type'] == 'error':
			self.update_error(data['id'], data['message'])

		else:
			table = "{}_{}".format(data['type'], data['id'])
			DB.insert_rows(DB.get_sql(table), data['records'])

			if data['progress']:
				self.update_progress(data)

class KraitStatisticsWorker(KraitSearchWorker):
	table_name = 'stats'
	processer = KraitStatisticsProcess

	def get_params(self):
		default, convert = KRAIT_SEARCH_PARAMETERS['STAT/unit']
		unit = self.settings.value('STAT/unit', default, convert)
		return {'unit': unit}

	def start_process(self, repeats, annots, fastx):
		DB.drop_table(self.table_name, fastx['id'])
		DB.create_table(self.table_name, fastx['id'])
		self.proc = self.processer(repeats, annots, self.params, self.queue, fastx)
		self.proc.start()

	def get_repeats(self):
		fastx = self.get_fastx()

		if not fastx:
			return None, None, None

		repeats = []
		for rtype in ['ssr', 'cssr', 'gtr', 'issr']:
			table = "{}_{}".format(rtype, fastx['id'])

			if DB.table_exists(table):
				rows = DB.get_rows("SELECT * FROM {}".format(table))

				if rows:
					repeats.append((rtype, rows))

		table = "map_{}".format(fastx['id'])
		if DB.table_exists(table):
			annots = DB.get_rows("SELECT * FROM {}".format(table))
		else:
			annots = []

		return fastx, repeats, annots

	def submit_process(self):
		if self.fastx_query is None:
			return

		if self.processes >= self.concurrent:
			return

		fastx, repeats, annots = self.get_repeats()

		if fastx:
			fastx['weight'] = fastx['bytes']/self.total_size
			self.start_process(repeats, annots, fastx)
			self.processes += 1

	def call_response(self, data):
		if data['type'] == 'success':
			self.update_success(data['id'])

		elif data['type'] == 'info':
			self.update_info(data['message'])

		elif data['type'] == 'finish':
			self.processes -= 1
			self.submit_process()

			if self.processes == 0:
				self.queue.close()

			self.signals.show_tab.emit(self.table_name, data['id'])

		elif data['type'] == 'error':
			self.update_error(data['id'], data['message'])

		else:
			table = "{}_{}".format(data['type'], data['id'])
			DB.insert_rows(DB.get_sql(table), data['records'])
			self.update_progress(data)

class KraitExportWorker(QRunnable):
	def __init__(self, export_dest=None):
		super().__init__()
		self.setAutoDelete(True)
		self.export_dest = export_dest
		self.signals = KraitWorkerSignals()

	def before_run(self):
		pass

	def do(self):
		pass

	def run(self):
		self.before_run()
		self.signals.progress.emit(0)

		try:
			self.do()

		except:
			error = traceback.format_exc()
			self.signals.failure.emit(error)
			print(error)

		finally:
			self.signals.progress.emit(100)
			self.signals.finished.emit()
			#self.signals.messages.emit('Done')


class KraitSaveWorker(KraitExportWorker):
	def do(self):
		self.signals.messages.emit("Saving to {}".format(self.export_dest))
		progress = 0

		#close transaction
		DB.commit()

		with DB.save_to_file(self.export_dest) as backup:
			while not backup.done:
				backup.step(10)
				p = int((backup.pagecount - backup.remaining)/backup.pagecount*100)

				if p > progress:
					self.signals.progress.emit(p)
					progress = p

		self.signals.messages.emit("Successfully saved to {}".format(self.export_dest))

class KraitExportStatisticsWorker(KraitExportWorker):
	def do(self):
		self.signals.messages.emit("Exporting report to {}".format(self.export_dest))
		progress = 0

		stats = KraitExportStatistics()
		html = stats.generate_summary_report()

		with open(self.export_dest, 'w', encoding='utf-8') as fw:
			fw.write(html)

		self.signals.messages.emit("Successfully export to {}".format(self.export_dest))
		self.signals.show_tab.emit(self.export_dest, 0)

class KraitExportSelectedWorker(KraitExportWorker):
	def __init__(self, parent, export_dest):
		super().__init__(export_dest)
		self.parent = parent 

	def do(self):
		table, total, selected = self.parent.get_selected_rows()
		title = DB.get_field(table)

		processed = 0
		progress = 0

		if self.export_dest.endswith('.csv'):
			separator = ','
		else:
			separator = '\t'

		with open(self.export_dest, 'w') as fh:
			writer = csv.writer(fh, delimiter=separator)
			writer.writerow(title)

			for rows in selected:
				for row in rows:
					writer.writerow(row)

				processed += len(rows)
				p = int(processed/total*100)
				if p > progress:
					self.signals.progress.emit(p)
					progress = p

		self.signals.messages.emit("Successfully exported {} selected rows to {}".format(total, self.export_dest))









class WorkerSignal(QObject):
	progress = Signal(int)
	messages = Signal(str)
	errors = Signal(str)
	finished = Signal()
	status = Signal(int)

class WorkerThread(QThread):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent
		self.search_all = parent.search_all
		self.signals = WorkerSignal()
		self.signals.progress.connect(parent.change_progress)
		self.signals.messages.connect(parent.show_status_message)
		self.signals.errors.connect(parent.show_error_message)
		self.signals.status.connect(parent.change_task_status)
		#self.signals.finished.connect(self.deleteLater)
		self.settings = QSettings()

	def error(self):
		errmsg = traceback.format_exc()
		self.signals.errors.emit(errmsg)
		print(errmsg)

	def process(self):
		pass

	def run(self):
		self.signals.progress.emit(0)

		try:
			self.process()
		except:
			self.error()

		self.signals.progress.emit(100)
		#self.signals.messages.emit('Finished!')
		self.signals.finished.emit()

class SearchThread(WorkerThread):
	_table = ''

	def __init__(self, parent=None):
		super().__init__(parent)
		self.findex = 0
		self.batch = 100

	@property
	def table(self):
		return "{}_{}".format(self._table, self.findex)

	@property
	def fastas(self):
		if not self.search_all:
			selected = sorted(self.parent.file_table.get_selected_rows())
		else:
			selected = []

		self.total_file = DB.get_one("SELECT COUNT(1) FROM fasta_0 LIMIT 1")
		
		if self.search_all or len(selected) == self.total_file:
			for fasta in DB.query("SELECT * FROM fasta_0"):
				yield fasta
		else:
			self.total_file = len(selected)
			slice_start = 0
			slice_end = 0
			
			while slice_start < self.total_file:
				slice_end = slice_start + self.batch
				ids = selected[slice_start:slice_end]
				slice_start = slice_end

				sql = "SELECT * FROM fasta_0 WHERE id IN ({})".format(','.join(['?']*len(ids)))
				for fasta in DB.query(sql, ids):
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
		params = ['SSR/mono', 'SSR/di', 'SSR/tri', 'SSR/tetra', 'SSR/penta', 'SSR/hexa']
		self.min_repeats = []
		for param in params:
			default, func = KRAIT_SEARCH_PARAMETERS[param]
			self.min_repeats.append(self.settings.value(param, default, func))

		default, func = KRAIT_SEARCH_PARAMETERS['STR/level']
		standard_level = self.settings.value('STR/level', default, type=func)
		self.motifs = StandardMotif(standard_level)

	def args(self, name, seq):
		return (name, seq, *self.min_repeats)

	@staticmethod
	def search(*args):
		return pytrf.STRFinder(*args).as_list()

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
			default, func = KRAIT_SEARCH_PARAMETERS[param]
			self.min_repeats.append(self.settings.value(param, default, func))

		default, func = KRAIT_SEARCH_PARAMETERS['CSSR/dmax']
		self.dmax = self.settings.value('CSSR/dmax', default, func)

	def args(self, name, seq):
		return (name, seq, self.min_repeats)

	@staticmethod
	def search(*args):
		return pytrf.STRFinder(*args).as_list()
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

class GTRSearchThread(SearchThread):
	_table = 'gtr'

	def __init__(self, parent):
		super().__init__(parent)
		self.params = []

		params = ['GTR/minmotif', 'GTR/maxmotif', 'GTR/minrep']
		for param in params:
			default, func = KRAIT_SEARCH_PARAMETERS[param]
			self.params.append(self.settings.value(param, default, func))

	def args(self, name, seq):
		return (name, seq, *self.params)

	@staticmethod
	def search(*args):
		return pytrf.GTRFinder(*args).as_list()

	def rows(self, vntrs):
		for vntr in vntrs:
			row = list(vntr)
			row[4] = iupac_numerical_multiplier(row[4])
			yield row

class ISSRSearchThread(SearchThread):
	_table = 'issr'

	def __init__(self, parent):
		super().__init__(parent)
		self.params = [1, 6]
		params = ['ISSR/minsrep', 'ISSR/minslen', 'ISSR/maxerr', 
					'ISSR/subpena', 'ISSR/inspena', 'ISSR/delpena',
					'ISSR/matratio', 'ISSR/maxextend']
		for param in params:
			default, func = KRAIT_SEARCH_PARAMETERS[param]
			self.params.append(self.settings.value(param, default, func))

		standard_level = self.settings.value('STR/level', 3, type=int)
		self.motifs = StandardMotif(standard_level)

	def args(self, name, seq):
		return (name, seq, *self.params)

	@staticmethod
	def search(*args):
		return pytrf.ITRFinder(*args).as_list()

	def rows(self, issrs):
		for issr in issrs:
			row = issr[0:4]
			row.append(self.motifs.standard(issr[3]))
			row.append(iupac_numerical_multiplier(ssr[4]))
			row.extend(issr[5:])
			yield row

class PrimerDesignThread(WorkerThread):
	def __init__(self, parent=None, table=None):
		super().__init__(parent)
		self.batch = 100

		#current table is tandem repeat table, not primer table
		self.table, self.findex = table.split('_')		

		param = "STR/flank"
		default, func = KRAIT_SEARCH_PARAMETERS[param]
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
		fasta_file = DB.get_one("SELECT fasta FROM fasta_0 WHERE id=?", self.findex)
		fasta = pyfastx.Fasta(fasta_file, uppercase=True)

		#primerdesign.setGlobals(self.primer_tags, None, None)
		
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

				#primerdesign.setSeqArgs({
				#	'SEQUENCE_ID': locus,
				#	'SEQUENCE_TEMPLATE': tr_seq,
				#	'SEQUENCE_TARGET': [tr[2]-tr_start, tr_len]
				#})

				#res = primerdesign.runDesign(False)

				res = primer3.design_primers({
					'SEQUENCE_ID': locus,
					'SEQUENCE_TEMPLATE': tr_seq,
					'SEQUENCE_TARGET': [tr[2]-tr_start, tr_len]
				}, self.primer_tags)

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

class SaveProjectThread(WorkerThread):
	def __init__(self, parent=None, save_file=None):
		super().__init__(parent)
		self.save_file = save_file

	def process(self):
		self.signals.messages.emit("Saving to {}".format(self.save_file))
		progress = 0

		#close transaction
		DB.commit()

		with DB.save_to_file(self.save_file) as backup:
			while not backup.done:
				backup.step(10)
				p = int((backup.pagecount - backup.remaining)/backup.pagecount*100)
				if p > progress:
					self.signals.progress.emit(p)
					progress = p

		self.signals.messages.emit("Successfully saved to {}".format(self.save_file))

class ExportSelectedRowsThread(WorkerThread):
	def __init__(self, parent=None, table=None, out_file=None):
		super().__init__(parent)
		self.table = table
		self.out_file = out_file
		self.batch = 100

	def process(self):
		selected = sorted(self.parent.get_selected_rows())
		title = DB.get_field(self.table)

		total = len(selected)
		processed = 0
		progress = 0
		slice_start = 0
		slice_end = 0

		if self.out_file.endswith('.csv'):
			separator = ','
		else:
			separator = '\t'

		with open(self.out_file, 'w') as fh:
			writer = csv.writer(fh, delimiter=separator)
			writer.writerow(title)

			while slice_start < total:
				slice_end = slice_start + self.batch
				ids = selected[slice_start:slice_end]
				slice_start = slice_end
				sql = "SELECT * FROM {} WHERE id IN ({})".format(self.table, ','.join(['?']*len(ids)))

				for row in DB.query(sql, ids):
					writer.writerow(row)

				processed += len(ids)
				p = int(processed/total*100)
				if p > progress:
					self.signals.progress.emit(p)
					progress = p

		self.signals.messages.emit("Successfully exported {} rows to {}".format(total, self.out_file))

class ExportWholeTableThread(WorkerThread):
	def __init__(self, parent=None, table=None, out_file=None):
		super().__init__(parent)
		self.table = table
		self.out_file = out_file

	def process(self):
		title = DB.get_field(self.table)
		total = DB.get_one("SELECT COUNT(1) FROM {}".format(self.table))
		processed = 0
		progress = 0

		if self.out_file.endswith('.csv'):
			separator = ','
		else:
			separator = '\t'

		with open(self.out_file, 'w') as fh:
			writer = csv.writer(fh, delimiter=separator)
			writer.writerow(title)

			for row in DB.query("SELECT * FROM {}".format(self.table)):
				writer.writerow(row)

				processed += 1
				p = int(processed/total*100)
				if p > progress:
					self.signals.progress.emit(p)
					progress = p

		self.signals.messages.emit("Successfully exported the whole table to {}".format(total, self.out_file))

class ExportAllTablesThread(WorkerThread):
	def __init__(self, parent=None, out_dir=None):
		super().__init__(parent)
		self.out_dir = out_dir

	def process(self):
		tables = DB.get_tables()
		total = len(tables)
		processed = 0
		progress = 0

		#get fasta name and id mapping
		fasta_mapping = {}
		for row in DB.query("SELECT id, name FROM fasta_0"):
			fasta_mapping[str(row[0])] = row[1]

		for table in tables:
			if table == 'fasta_0':
				out_file = os.path.join(self.out_dir, 'input_fastas.csv')
			else:
				_type, _id = table.split('_')

				out_file = os.path.join(self.out_dir, '{}_{}.csv'.format(
					fasta_mapping[_id], _type
				))

			DB.export_to_csv(table, out_file)

			processed += 1
			p = processed/total*100
			if p > progress:
				self.signals.progress.emit(p)
				progress = p

class TRELocatingThread(SearchThread):
	_table = 'locate'
	def __init__(self, parent=None):
		super().__init__(parent)
		self.type_mapping = {'ssr': 1, 'cssr': 2,
							'vntr': 3, 'itr': 4}

	def process(self):
		progress = 0
		processed = 0
		for fasta in self.fastas:
			self.findex = fasta[0]
			self.change_status('running')

			annot_file = fasta[5]

			if not annot_file:
				continue

			tre_types = {
				'ssr': DB.get_count("ssr_{}".format(self.findex)),
				'vntr': DB.get_count("vntr_{}".format(self.findex)),
				'cssr': DB.get_count("cssr_{}".format(self.findex)),
				'itr': DB.get_count("itr_{}".format(self.findex))
			}

			if any(tre_types.values()):
				#parse annotation file
				locator = annotation_parser(annot_file)

				#build index
				locator.index()
			else:
				continue

			#create annotation table for current file
			DB.create_table(self._table, self.findex)

			for tre_type in tre_types:
				if not tre_types[tre_type]:
					continue

				feat_id = self.type_mapping[tre_type]

				tre_annots = []
				for tre in DB.query("SELECT * FROM {}_{}".format(tre_type, self.findex)):
					locs = locator.locate(tre[1], tre[2], tre[3])
					for loc in locs:
						tre_annots.append((tre[0], feat_id, *loc))

				if tre_annots:
					DB.insert_rows(self.sql(), tre_annots)

class StatisticsThread(WorkerThread):
	def __init__(self, parent=None):
		super().__init__(parent)

	@property
	def fastas(self):
		if not self.search_all:
			selected = sorted(self.parent.file_table.get_selected_rows())
		else:
			selected = []

		self.total_file = DB.get_one("SELECT COUNT(1) FROM fasta_0 LIMIT 1")
		
		if self.search_all or len(selected) == self.total_file:
			for fasta in DB.query("SELECT id FROM fasta_0"):
				yield fasta[0]
		else:
			for _id in selected:
				return _id

	def process(self):
		for fasta_id in self.fastas:
			#create stats result table
			DB.create_table('stats', fasta_id)

			#perform fasta general stats
			self.signals.messages.emit("Extracting fasta file information...")
			FastaStatistics(fasta_id)

			#perform ssr stats
			if DB.table_exists('ssr_{}'.format(fasta_id)):
				self.signals.messages.emit("Performing SSR statistics...")
				SSRStatistics(fasta_id)
