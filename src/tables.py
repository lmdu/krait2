from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

__all__ = ['KraitTableView']

class KraitTableModel(QAbstractTableModel):
	row_count = Signal(int)
	col_count = Signal(int)
	sel_count = Signal(int)

	def __init__(self, parent=None):
		super(KraitTableModel, self).__init__(parent)

		self.displayed = []
		self.cache_row = [-1, None]
		self.total_count = 0
		self.read_count = 0
		self.file_index = 0
		self.headers = ['id', 'chrom', 'start', 'end', 'motif', 'standard', 'type', 'repeats', 'length']

	def set_file_index(self, file_index):
		self.file_index = file_index
		self.sql = "SELECT * FROM ssr{} WHERE id=? LIMIT 1".format(self.file_index)
		self.total_count = DB.get_one("SELECT COUNT(*) FROM ssr{} LIMIT 1".format(self.file_index))
		self.cache_row = [-1, None]
		self.beginResetModel()
		self.displayed = DB.get_column("SELECT id from ssr{} LIMIT 100".format(self.file_index))
		self.read_count = len(self.displayed)
		self.endResetModel()

		if self.total_count:
			self.row_count.emit(self.total_count)
			self.sel_count.emit(0)

	def value(self, index):
		row = index.row()
		col = index.column() - 1

		if row != self.cache_row[0]:
			_id = self.displayed[row]
			self.cache_row[0] = row
			self.cache_row[1] = DB.get_row(self.sql, (_id,))

		return self.cache_row[1][col]

	def rowCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return self.read_count

	def columnCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return 10

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		if not (0 <= index.row() < self.rowCount()):
			return None

		elif role == Qt.DisplayRole:
			if index.column() > 0:
				return self.value(index)

			else:
				return None

		return None

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role != Qt.DisplayRole:
			return None

		if orientation == Qt.Horizontal:
			if section == 0:
				return None
			else:
				return self.headers[section-1]
		
		elif orientation == Qt.Vertical:
			#return self.value(section, 1)
			if role == Qt.CheckStateRole:
				if index.column() == 0:
					if self.displayed[index.row()] in self.selected:
						return Qt.ItemIsUserCheckable
					else:
						return Qt.ItemIsUserCheckable

		return None

	def canFetchMore(self, parent):
		return not parent.isValid() and (self.read_count < self.total_count)

	def fetchMore(self, parent):
		if parent.isValid():
			return
		
		remainder = self.total_count - self.read_count
		fetch_count = min(100, remainder)
		sql = "SELECT id FROM ssr{} LIMIT {},{}".format(self.file_index, self.read_count, fetch_count)
		ids = self.db.get_column(sql)
		self.beginInsertRows(QModelIndex(), self.read_count, self.read_count+fetch_count-1)
		self.displayed.extend(ids)
		self.read_count += fetch_count
		self.endInsertRows()

class KraitTableView(QTableView):
	def __init__(self, parent=None):
		super(KraitTableView, self).__init__(parent)

		self.verticalHeader().hide()
		self.horizontalHeader().setHighlightSections(False)
		self.horizontalHeader().setStretchLastSection(True)
		self.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.setSelectionMode(QAbstractItemView.SingleSelection)
		#self.setSelectionMode(QAbstractItemView.MultiSelection)
		self.setSortingEnabled(True)

		self.checkbox = QCheckBox(self.horizontalHeader())
		self.checkbox.setGeometry(QRect(3,5,20,20))
		#self.checkbox.stateChanged.connect(self.checkboxAction)

		self.model = KraitTableModel(self)
		self.setModel(self.model)

	def set_file_index(self, file_index):
		self.model.set_file_index(file_index)

