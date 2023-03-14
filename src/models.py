from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

__all__ = ['KraitFastxModel']

class KraitBaseModel(QAbstractTableModel):
	table = None
	custom_headers = []
	row_count = Signal(int)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent

		#store ids of displayed row
		self.displayed = []

		#cache the current row
		self.cache_row = [-1, None]

		#total row counts
		self.total_count = 0

		#readed row counts
		self.read_count = 0

		#number of readed rows once time
		self._reads = 200

	def rowCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return self.read_count

	def columnCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return len(self.custom_headers)

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		row = index.row()
		col = index.column()

		if role == Qt.DisplayRole:
			return self.get_value(row, col)

		elif role == Qt.BackgroundRole:
			pass

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return self.custom_headers[section]

		elif orientation == Qt.Vertical and role == Qt.DisplayRole:
			return section+1

	def canFetchMore(self, parent):
		if parent.isValid():
			return False

		if self.read_count < self.total_count:
			return True

		return False

	def fetchMore(self, parent):
		if parent.isValid():
			return

		ids = DB.get_column(self.read_sql)
		fetch_count = len(ids)
		self.beginInsertRows(QModelIndex(), self.read_count, self.read_count+fetch_count-1)
		self.displayed.extend(ids)
		self.read_count += fetch_count
		self.endInsertRows()

	@property
	def count_sql(self):
		return "SELECT COUNT(1) FROM {} LIMIT 1".format(self.table)

	@property
	def read_sql(self):
		remainder = self.total_count - self.read_count
		fetch_count = min(self._reads, remainder)

		return "SELECT id FROM {} LIMIT {},{}".format(
			self.table,
			self.read_count,
			fetch_count
		)

	@property
	def all_sql(self):
		return "SELECT id FROM {}".format(self.table)

	@property
	def get_sql(self):
		return "SELECT * FROM {} WHERE id=? LIMIT 1".format(self.table)

	def get_value(self, row, col):
		if row != self.cache_row[0]:
			self.update_cache(row)

		return self.cache_row[1][col]

	def update_cache(self, row):
		_id = self.displayed[row]
		self.cache_row[0] = row
		self.cache_row[1] = DB.get_row(self.get_sql, (_id,))

	def get_total(self):
		return DB.get_count(self.table)

	def select(self):
		self.beginResetModel()
		self.read_count = 0
		self.total_count = self.get_total()
		self.displayed = DB.get_column(self.read_sql)
		self.read_count = len(self.displayed)
		self.cache_row = [-1, None]
		self.endResetModel()
		self.row_count.emit(self.total_count)

	def reset(self):
		self.beginResetModel()
		self.cache_row = [-1, None]
		self.read_count = 0
		self.displayed = []
		self.total_count = 0
		self.endResetModel()
		self.row_count.emit(self.total_count)

	def clear(self):
		DB.query("DELETE FROM {}".format(self.table))
		self.reset()

	def remove(self, row):
		self.beginRemoveRows(QModelIndex(), row, row)
		self.displayed.pop(row)
		self.total_count -= 1
		self.read_count -= 1
		self.endRemoveRows()
		self.row_count.emit(self.total_count)

class KraitFastxModel(KraitBaseModel):
	table = 'fastx'
	custom_headers = ["Name", "Size", "Count", "GC", "Ns"]

	@property
	def get_sql(self):
		return "SELECT name,size,count,gc,ns FROM {} WHERE id=? LIMIT 1".format(self.table)

	#def index(self, row, column, parent):
	#	return QModelIndex()

	#def parent(self, index):
	#	return QModelIndex()
