from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

__all__ = ['KraitFastxModel', 'KraitSSRModel', 'KraitCSSRModel',
			'KraitISSRModel', 'KraitVNTRModel', 'KraitPrimerModel']

class KraitBaseModel(QAbstractTableModel):
	table = None
	custom_headers = []

	row_count = Signal(int)
	col_count = Signal(int)
	sel_count = Signal(int)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent

		#store ids of displayed row
		self.displayed = []

		#store ids of selected row
		self.selected = set()

		#cache the current row
		self.cache_row = [-1, None]

		#total row counts
		self.total_count = 0

		#readed row counts
		self._read_count = 0

		#number of readed rows once time
		self._read_once = 200

		#filters
		self._filter_by = ''

		#sort by
		self._order_by = ''

	def rowCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return self._read_count

	def columnCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return len(self.custom_headers)

	def sort(self, column, order):
		fields = DB.get_field(self.table)

		if order == Qt.SortOrder.DescendingOrder:
			self._order_by = "ORDER BY {} DESC".format(fields[column])

		elif order == Qt.AscendingOrder:
			self._order_by = "ORDER BY {}".format(fields[column])

		else:
			self._order_by = ''

		self.select()

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		row = index.row()
		col = index.column()

		if role == Qt.DisplayRole:
			return self.get_value(row, col)

		elif role == Qt.CheckStateRole:
			if col == 0:
				if self.displayed[row] in self.selected:
					return Qt.Checked

				else:
					return Qt.Unchecked

		#elif role == Qt.BackgroundRole:
		#	pass

	def setData(self, index, value, role):
		if not index.isValid():
			return False

		col = index.column()

		if col != 0:
			return False

		row = index.row()
		row_id = self.displayed[row]

		if role == Qt.CheckStateRole:
			if value == Qt.Checked:
				self.selected.add(row_id)

			else:
				if row_id in self.selected:
					self.selected.remove(row_id)

			self.dataChanged.emit(index, index)
			self.sel_count.emit(len(self.selected))

			return True

		return False

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return self.custom_headers[section]

	def flags(self, index):
		if not index.isValid():
			return

		flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

		if index.column() == 0:
			flags |= Qt.ItemIsUserCheckable

		return flags

	def canFetchMore(self, parent):
		if parent.isValid():
			return False

		if self._read_count < self.total_count:
			return True

		return False

	def fetchMore(self, parent):
		if parent.isValid():
			return

		ids = DB.get_column(self.read_sql)
		fetch_count = len(ids)
		self.beginInsertRows(QModelIndex(), self._read_count, self._read_count+fetch_count-1)
		self.displayed.extend(ids)
		self._read_count += fetch_count
		self.endInsertRows()

	@property
	def count_sql(self):
		return "SELECT COUNT(1) FROM {} {} LIMIT 1".format(self.table, self._filter_by)

	@property
	def read_sql(self):
		remainder = self.total_count - self._read_count
		fetch_count = min(self._read_once, remainder)

		return "SELECT id FROM {} {} {} LIMIT {},{}".format(
			self.table,
			self._filter_by,
			self._order_by,
			self._read_count,
			fetch_count
		)

	@property
	def all_sql(self):
		return "SELECT id FROM {} {}".format(self.table, self._filter_by)

	@property
	def get_sql(self):
		return "SELECT * FROM {} {} {} {} LIMIT 1".format(
			self.table,
			self._filter_by,
			"AND id=?" if self._filter_by else "WHERE id=?",
			self._order_by
		)

	def get_value(self, row, col):
		if row != self.cache_row[0]:
			self.update_cache(row)

		return self.cache_row[1][col]

	def update_cache(self, row):
		row_id = self.displayed[row]
		self.cache_row[0] = row
		self.cache_row[1] = DB.get_row(self.get_sql, (row_id,))

	def select(self):
		self.beginResetModel()
		self._read_count = 0
		self.cache_row = [-1, None]
		self.selected = set()

		self.total_count = DB.get_one(self.count_sql)
		self.displayed = DB.get_column(self.read_sql)
		self._read_count = len(self.displayed)

		self.col_count.emit(len(self.custom_headers))
		self.row_count.emit(self.total_count)
		self.sel_count.emit(0)
		self.endResetModel()

	def reset(self):
		self.beginResetModel()
		self.displayed = []
		self.selected = set()
		self.total_count = 0
		self._read_count = 0
		self.cache_row = [-1, None]
		self.endResetModel()

		self.row_count.emit(0)
		self.col_count.emit(0)
		self.sel_count.emit(0)

	def clear(self):
		DB.query("DELETE FROM {}".format(self.table))
		self.reset()

	def remove(self, row):
		self.beginRemoveRows(QModelIndex(), row, row)
		row_id = self.displayed[row]

		self.displayed.pop(row)
		self.total_count -= 1
		self._read_count -= 1

		if row_id in self.selected:
			self.selected.remove(row_id)

		self.endRemoveRows()

		self.row_count.emit(self.total_count)
		self.sel_count.emit(len(self.selected))

	def set_filter(self, conditions=None):
		if conditions:
			self._filter_by = "WHERE {}".format(conditions)
		else:
			self._filter_by = ""

		self.select()

	def select_all(self):
		self.beginResetModel()

		if self._filter_by:
			self.selected = DB.get_set(self.all_sql)
		else:
			self.selected = set(range(1, self.total_count+1))

		self.endResetModel()

		self.sel_count.emit(len(self.selected))

	def deselect_all(self):
		self.beginResetModel()
		self.selected = set()
		self.endResetModel()
		self.sel_count.emit(0)

	def get_select_state(self):
		select_count = len(self.selected)

		if select_count:
			if select_count == self.total_count:
				return Qt.Checked
			else:
				return Qt.PartiallyChecked

		return Qt.Unchecked

	def count_emit(self):
		self.row_count.emit(self.total_count)
		self.sel_count.emit(len(self.selected))
		self.col_count.emit(len(self.custom_headers))

	def get_row(self, index):
		row_id = index.siblingAtColumn(0).data()
		sql = "SELECT * FROM {} WHERE id=? LIMIT 1".format(self.table)
		return DB.get_dict(sql, (row_id,))

	def get_selected_count(self):
		return len(self.selected)

	def get_selected_rows(self):
		if not self.selected:
			return

		select_count = len(self.selected)
		extract_once = 100

		if select_count == self.total_count:
			sql = self.all_sql.replace("SELECT id FROM", "SELECT * FROM")

			rows = []

			for row in DB.query(sql):
				rows.append(row)

				if len(rows) == extract_once:
					yield rows

			if rows:
				yield rows

		else:
			selected_rows = sorted(self.selected)

			for i in range(0, select_count, extract_once):
				ids = selected_rows[i:i+extract_once]
				sql = "SELECT * FROM {} WHERE id IN ({})".format(
					self.table, ','.join(map(str, ids))
				)

				yield DB.get_rows(sql)

class KraitFastxModel(KraitBaseModel):
	table = 'fastx'
	custom_headers = ["ID", "Name"]

class KraitTableModel(KraitBaseModel):
	def set_index(self, index):
		self.table = "{}_{}".format(self.table.split('_')[0], index)
		self.select()

class KraitSSRModel(KraitTableModel):
	table = 'ssr'
	custom_headers = ['ID', 'Chrom', 'Start', 'End', 'Motif',
					 'Smotif', 'Type', 'Repeats', 'Length']

class KraitVNTRModel(KraitTableModel):
	table = 'vntr'
	custom_headers = ['ID', 'Chrom', 'Start', 'End', 'Motif',
						'Type', 'Repeats', 'Length']

class KraitCSSRModel(KraitTableModel):
	table = 'cssr'
	custom_headers = ['ID', 'Chrom', 'Start', 'End', 'Complexity',
						'Length', 'Structure']

class KraitISSRModel(KraitTableModel):
	table = 'issr'
	custom_headers = ['ID', 'Chrom', 'Start', 'End', 'Motif', 'Smotif',
						'Type', 'Length', 'Match', 'Subsitution', 'Insertion',
						'Deletion', 'Identity']

class KraitPrimerModel(KraitTableModel):
	table = 'primer'
	custom_headers = ['ID', 'Locus', 'Entry', 'Product size', 'Strand',
					  'Tm (°C)', 'GC content (%)', 'End stability', 'Sequence']

	def get_value(self, row, col):
		if row != self.cache_row[0]:
			self.update_cache(row)

		if col == 4:
			return 'Forward\nReverse'

		elif col > 4:
			return "{}\n{}".format(
				self.cache_row[1][col-1],
				self.cache_row[1][col+3]
			)

		else:
			return self.cache_row[1][col]

	def flags(self, index):
		if not index.isValid():
			return Qt.ItemIsSelectable

		flags = super().flags(index)

		if index.column() == 5:
			flags |= Qt.ItemIsEditable

		return flags

	def sort(self, column, order):
		if column > 3:
			return

		super().sort(column, order)
