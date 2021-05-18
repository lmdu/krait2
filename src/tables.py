from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

__all__ = ['KraitTableView', 'FastaTableView']

class KraitTableSignal(QObject):
	row_count = Signal(int)
	col_count = Signal(int)
	sel_count = Signal(int)
	sel_autom = Signal()

class KraitTableModel(QAbstractTableModel):
	def __init__(self, parent=None, table='ssr'):
		super(KraitTableModel, self).__init__(parent)

		#signals
		self.signals = KraitTableSignal()

		#store ids of displayed row
		self.displayed = []

		#store ids of selected row
		self.selected = set()

		#cache the current row
		self.cache_row = [-1, None]

		#total row counts
		self.total_count = 0

		#readed row counts
		self.read_count = 0

		self._table = table

		#number of readed rows once time
		self._reads = 100

		#filters
		self._filter = ''

		#order by
		self._orderby = ''

		#input file index 
		self._index = ''

		#get column names
		self._header = DB.get_field(table)

	def rowCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return self.read_count

	def columnCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return len(self._header)

	def sort(self, column, order):
		if order == Qt.SortOrder.DescendingOrder:
			self._orderby = "ORDER BY {} DESC".format(self._header[column])

		elif order == Qt.AscendingOrder:
			self._orderby = "ORDER BY {}".format(self._header[column])

		else:
			self._orderby = ""

		self.reset_table()

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

	def setData(self, index, value, role):
		if not index.isValid():
			return False

		row = index.row()
		col = index.column()

		_id = self.displayed[row]

		if col == 0 and role == Qt.CheckStateRole:
			if value == Qt.Checked:
				if _id not in self.selected:
					self.selected.add(_id)
			elif value == Qt.Unchecked:
				if _id in self.selected:
					self.selected.remove(_id)

			#self.dataChanged.emit(index, index)
			self.signals.sel_count.emit(len(self.selected))
			self.signals.sel_autom.emit()

			return True
		
		return False

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if orientation == Qt.Horizontal and role == Qt.DisplayRole:
			return self._header[section]

	def flags(self, index):
		if not index.isValid():
			return Qt.ItemIsSelectable
		
		flag = Qt.ItemIsEnabled | Qt.ItemIsSelectable

		if index.column() == 0:
			flag |= Qt.ItemIsUserCheckable

		return flag

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

	def set_index(self, file_index):
		"""set current file index"""
		self._index = file_index
		self.reset_table()

	@property
	def count_sql(self):
		return "SELECT COUNT(1) FROM {}{} {} LIMIT 1".format(
			self._table,
			self._index,
			self._filter
		)

	@property
	def read_sql(self):
		remainder = self.total_count - self.read_count
		fetch_count = min(self._reads, remainder)

		return "SELECT id FROM {}{} {} {} LIMIT {},{}".format(
			self._table,
			self._index,
			self._filter,
			self._orderby,
			self.read_count,
			fetch_count
		)

	@property
	def all_sql(self):
		return "SELECT id FROM {}{} {}".format(
			self._table,
			self._index,
			self._filter
		)

	@property
	def get_sql(self):
		return "SELECT * FROM {}{} {} {} {} LIMIT 1".format(
			self._table,
			self._index,
			self._filter,
			"AND id=?" if self._filter else "WHERE id=?",
			self._orderby
		)

	def reset_table(self):
		self.read_count = 0
		self.cache_row = [-1, None]

		self.beginResetModel()
		self.total_count = DB.get_one(self.count_sql)
		self.displayed = DB.get_column(self.read_sql)
		self.selected = set()
		self.read_count = len(self.displayed)
		self.endResetModel()

		self.signals.row_count.emit(self.total_count)
		self.signals.col_count.emit(len(self._header))
		self.signals.sel_count.emit(0)

	def get_value(self, row, col):
		if row != self.cache_row[0]:
			self.update_cache(row)

		return self.cache_row[1][col]

	def update_cache(self, row):
		_id = self.displayed[row]
		self.cache_row[0] = row
		self.cache_row[1] = DB.get_row(self.get_sql, (_id,))

	def set_filter(self, conditions=None):
		if conditions:
			self._filter = "WHERE {}".format(conditions)
		else:
			self._filter = ""

		self.reset_table()

	def select_all(self):
		self.beginResetModel()

		if self._filter:
			self.selected = DB.get_set(self.all_sql)
		else:
			self.selected = set(range(1, self.total_count+1))

		self.endResetModel()

		self.signals.sel_count.emit(self.total_count)

	def deselect_all(self):
		self.beginResetModel()
		self.selected = set()
		self.endResetModel()

		self.signals.sel_count.emit(0)

class KraitTableView(QTableView):
	def __init__(self, parent=None, table='ssr'):
		super(KraitTableView, self).__init__(parent)
		self.table = table

		self.verticalHeader().hide()
		self.horizontalHeader().setHighlightSections(False)
		self.horizontalHeader().setStretchLastSection(True)
		self.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.setSelectionMode(QAbstractItemView.SingleSelection)
		self.setSortingEnabled(True)

		self.checkbox = QCheckBox(self.horizontalHeader())
		self.checkbox.setGeometry(QRect(3,5,20,20))
		self.checkbox.clicked.connect(self.check_all_action)

		self.create_model()

		self.model.signals.sel_autom.connect(self.change_checkbox_state)
		self.model.signals.col_count.connect(parent.change_column_count)
		self.model.signals.row_count.connect(parent.change_row_count)
		self.model.signals.sel_count.connect(parent.change_select_count)

	def create_model(self):
		self.model = KraitTableModel(self, self.table)
		self.setModel(self.model)

	def update_table(self, file_index=''):
		self.model.set_index(file_index)

	def get_clicked_rowid(self, index):
		return self.model.displayed[index.row()]

	def emit_count(self):
		self.model.signals.row_count.emit(self.model.total_count)
		self.model.signals.col_count.emit(len(self.model._header))
		self.model.signals.sel_count.emit(len(self.model.selected))

	@Slot()
	def change_checkbox_state(self):
		selected = len(self.model.selected)

		if selected:
			displayed = len(self.model.displayed)

			if selected < displayed:
				self.checkbox.setCheckState(Qt.PartiallyChecked)
			else:
				self.checkbox.setCheckState(Qt.Checked)

		else:
			self.checkbox.setCheckState(Qt.Unchecked)

	@Slot(bool)
	def check_all_action(self, checked):
		state = self.checkbox.checkState()

		if state == Qt.Checked:
			self.model.select_all()
		elif state == Qt.Unchecked:
			self.model.deselect_all()
		elif state == Qt.PartiallyChecked:
			self.model.select_all()
			self.checkbox.setCheckState(Qt.Checked)

class FastaTableModel(KraitTableModel):
	def __init__(self, parent=None, table="fastas"):
		super(FastaTableModel, self).__init__(parent, table)
		self.color_mapping = {
			'pending': QColor(221, 221, 221),
			'running': QColor(100, 181, 246),
			'success': QColor(129, 199, 132),
			'failure': QColor(229, 115, 115)
		}

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		row = index.row()
		col = index.column()

		if role == Qt.DisplayRole:
			return self.get_value(row, col)

		elif col == 0 and role == Qt.CheckStateRole:
			if self.displayed[row] in self.selected:
				return Qt.Checked
			else:
				return Qt.Unchecked

		elif col == 3 and role == Qt.BackgroundRole:
			val = self.get_value(row, col)
			return self.color_mapping.get(val, Qt.white)


class FastaTableView(KraitTableView):
	def __init__(self, parent=None):
		super(FastaTableView, self).__init__(parent, "fastas")
		self.clicked.connect(parent.change_current_file)

	def create_model(self):
		self.model = FastaTableModel(self)
		self.setModel(self.model)

	def update_status(self, fasta_id):
		row = self.model.displayed.index(fasta_id)
		index = self.model.createIndex(row, 3)
		self.model.update_cache(row)
		self.model.dataChanged.emit(index, index)
