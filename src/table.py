from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

__all__ = ['KraitTableView', 'FastaTableView',
			'PrimerTableView']

class KraitTableSignal(QObject):
	row_count = Signal(int)
	col_count = Signal(int)
	sel_count = Signal(int)
	sel_autom = Signal()

class KraitTableModel(QAbstractTableModel):
	_custom_headers = []

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
		self._index = 0

		self._header = []

		#has annotation
		self.annotated = 0

	def rowCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		return self.read_count

	def columnCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0

		if self._custom_headers:
			return len(self._custom_headers)
		else:
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

		elif role == Qt.BackgroundRole:
			if self.annotated and self._table != 'primer':
				return self.get_color(index)

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
			if self._custom_headers:
				return self._custom_headers[section]
			else:
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
		#get column names
		if not self._header:
			self._header = DB.get_field("{}_{}".format(self._table, self._index))
		self.reset_table()

	@property
	def count_sql(self):
		return "SELECT COUNT(1) FROM {}_{} {} LIMIT 1".format(
			self._table,
			self._index,
			self._filter
		)

	@property
	def read_sql(self):
		remainder = self.total_count - self.read_count
		fetch_count = min(self._reads, remainder)

		return "SELECT id FROM {}_{} {} {} LIMIT {},{}".format(
			self._table,
			self._index,
			self._filter,
			self._orderby,
			self.read_count,
			fetch_count
		)

	@property
	def all_sql(self):
		return "SELECT id FROM {}_{} {}".format(
			self._table,
			self._index,
			self._filter
		)

	@property
	def get_sql(self):
		return "SELECT * FROM {}_{} {} {} {} LIMIT 1".format(
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


	def get_color(self, index):
		_id = self.displayed[index.row()]

		colors = {
			1: QColor(245, 183, 177), 
			2: QColor(250, 215, 160), 
			3: QColor(169, 223, 191),
			4: QColor(174, 214, 241),
			5: QColor(255, 255, 255),
			6: QColor(255, 255, 255)
		}

		type_mapping = {
			'ssr': 1, 'cssr': 2,
			'vntr': 3, 'itr': 4
		}
		
		sql = "SELECT feature_id FROM locate_{} WHERE str_id=? AND str_type=? LIMIT 1".format(self._index)
		feat_id = DB.get_one(sql, (_id, type_mapping[self._table]))

		if feat_id:
			return colors.get(feat_id, QColor(255, 255, 255))

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
		self.real_table = None

		self.verticalHeader().hide()
		self.horizontalHeader().setHighlightSections(False)
		self.horizontalHeader().setStretchLastSection(True)
		self.setEditTriggers(QAbstractItemView.DoubleClicked)
		self.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.setSelectionMode(QAbstractItemView.SingleSelection)
		self.setSortingEnabled(True)

		#self.setFrameStyle(QFrame.NoFrame)

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

	def update_table(self, file_index=0):
		if DB.table_exists("locate_{}".format(file_index)):
			self.model.annotated = 1
		else:
			self.model.annotated = 0
		self.model.set_index(file_index)
		self.real_table = "{}_{}".format(self.table, file_index)

	def set_filter(self, filters):
		self.model.set_filter(filters)

	def get_clicked_rowid(self, index):
		return self.model.displayed[index.row()]

	def get_selected_rows(self):
		return self.model.selected

	def has_selection(self):
		if self.model.selected:
			return True
		else:
			return False

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
	_custom_headers = ['id', 'name', 'size', 'status', 'fasta']

	def __init__(self, parent=None, table="fasta"):
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
		super().__init__(parent, "fasta")
		self.clicked.connect(parent.change_current_file)

	def create_model(self):
		self.model = FastaTableModel(self)
		self.setModel(self.model)

	def update_status(self, fasta_id):
		row = self.model.displayed.index(fasta_id)
		index = self.model.createIndex(row, 3)
		self.model.update_cache(row)
		self.model.dataChanged.emit(index, index)

	def update_table(self, file_index=0):
		self.model.set_index(file_index)
		self.real_table = "{}_{}".format(self.table, file_index)
		annots = DB.get_column("SELECT annotation FROM fasta_0")
		if any(annots):
			if 'annotation' not in self.model._custom_headers:
				self.model._custom_headers.append('annotation')
				self.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

class PrimerTableDelegate(QStyledItemDelegate):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent

	def setEditorData(self, editor, index):
		val = self.parent.model.get_value(index.row(), index.column())
		editor.setText(val)

class PrimerTableModel(KraitTableModel):
	_custom_headers = ['id', 'Locus', 'Entry', 'Product size',
						'Primer', 'Sequence', 'Tm (°C)', 'GC (%)', 'End stability']

	def __init__(self, parent=None, table="primer"):
		super().__init__(parent, table)

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

		flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable

		if index.column() == 0:
			flags |= Qt.ItemIsUserCheckable

		elif index.column() == 5:
			flags |= Qt.ItemIsEditable

		return flags

	def sort(self, column, order):
		if column > 3:
			return

		super().sort(column, order)

class PrimerTableView(KraitTableView):
	def __init__(self, parent=None):
		super().__init__(parent, "primer")
		width = self.verticalHeader().defaultSectionSize()
		self.verticalHeader().setDefaultSectionSize(int(width*1.5))

	def create_model(self):
		self.model = PrimerTableModel(self)
		self.setModel(self.model)

		self.delegate = PrimerTableDelegate(self)
		self.setItemDelegate(self.delegate)
