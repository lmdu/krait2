from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

__all__ = ['KraitFilterDialog']

class KraitFilterModel(QAbstractTableModel):
	def __init__(self, parent=None):
		super().__init__(parent)

		self._parent = parent
		self._headers = ["And/Or", "Column Name", "Condition", "Value"]
		self.row_count = 1

	#def index(self, row, column, parent=QModelIndex()):
	#	return self.createIndex(row, column)

	#def parent(self, index):
	#	return QModelIndex()

	def rowCount(self, parent=QModelIndex()):
		return len(self._parent.filters)

	def columnCount(self, parent=QModelIndex()):
		return 4

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		if role == Qt.DisplayRole:
			col = index.column()
			row = index.row()
			return self._parent.filters[row][col]

	def setData(self, index, value, role=Qt.ItemDataRole):
		if role == Qt.EditRole:
			col = index.column()
			row = index.row()

			self._parent.filters[row][col] = value

			self.dataChanged.emit(index, index)
			return True

		return False

	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role != Qt.DisplayRole:
			return None

		if orientation == Qt.Horizontal:
			return self._headers[section]

	def flags(self, index):
		flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemNeverHasChildren | Qt.ItemIsEditable

		return flags

class KraitFilterDelegate(QStyledItemDelegate):
	def __init__(self, parent=None):
		super().__init__(parent)

		self.parent = parent
		self.logics = ["And", "Or"]

	def paint(self, painter, option, index):
		QStyledItemDelegate.paint(self, painter, option, index)

	def createEditor(self, parent, option, index):
		col = index.column()
		row = index.row()
		val = self.parent.filters[row][1]
		idx = self.parent.fields.index(val)

		if col < 3:
			editor = QComboBox(parent)

			if col == 0 and index.row() > 0:
				editor.addItems(self.logics)

			elif col == 1:
				editor.addItems(self.parent.fields)

			elif col == 2:
				if self.parent.types[idx] in ['INTEGER', 'REAL']:
					editor.addItems(['>', '>=', '<', '<=', '='])
				else:
					editor.addItems(['=', 'contains'])

		else:
			if self.parent.types[idx] == 'REAL':
				editor = QDoubleSpinBox(parent)
				editor.setRange(0, 10000)
			elif self.parent.types[idx] == 'INTEGER':
				editor = QSpinBox(parent)
				editor.setRange(0, 1000000000)
			else:
				editor = QStyledItemDelegate.createEditor(self, parent, option, index)

		return editor

	def setEditorData(self, editor, index):
		col = index.column()
		row = index.row()

		val = self.parent.filters[row][col]
		idx = self.parent.fields.index(self.parent.filters[row][1])

		if col == 0 and row > 0:
			idx = editor.findText(val)
			editor.setCurrentIndex(idx)

		elif col == 1 or col == 2:
			idx = editor.findText(val)
			editor.setCurrentIndex(idx)

		elif col == 3 and self.parent.types[idx] in ['REAL', 'INTEGER']:
			editor.setValue(val)

		else:
			QStyledItemDelegate.setEditorData(self, editor, index)

	def setModelData(self, editor, model, index):
		QStyledItemDelegate.setModelData(self, editor, model, index)

#class FilterTreeView(QTreeView):
#	def __init__(self, parent=None):
#		super(FilterTreeView, self).__init__(parent)

class KraitFilterDialog(QDialog):
	def __init__(self, parent=None, table=None):
		super().__init__(parent)

		self.setWindowTitle("Filters")
		self.resize(QSize(500, 300))
		self.setModal(False)
		self.parent = parent
		self.table = table

		self.fields = DB.get_field(self.table)
		self.types = DB.get_field_type(self.table)

		self.filters = self.parent.current_filters.get(self.table, [])
		self.features = self.parent.current_filters.get('feature', [])

		if not self.filters:
			self.filters = [['', 'id', '>', 0]]

		self.tree = QTreeView(self)
		self.tree.setRootIsDecorated(False)
		self.model = KraitFilterModel(self)
		self.delegate = KraitFilterDelegate(self)
		self.tree.setModel(self.model)
		self.tree.setItemDelegate(self.delegate)

		filter_box = QDialogButtonBox()
		add_btn = QPushButton(self)
		add_btn.setIcon(QIcon(":/icons/plus.svg"))
		add_btn.setToolTip("Add filter")
		add_btn.clicked.connect(self.add_filter)
		del_btn = QPushButton(self)
		del_btn.setIcon(QIcon(":/icons/minus.svg"))
		del_btn.setToolTip("Delete the selected filter")
		del_btn.clicked.connect(self.delete_filter)
		clr_btn = QPushButton(self)
		clr_btn.setIcon(QIcon(":/icons/clear.svg"))
		clr_btn.setToolTip("Delete all the filters")
		clr_btn.clicked.connect(self.clear_filter)
		filter_box.addButton(add_btn, QDialogButtonBox.ActionRole)
		filter_box.addButton(del_btn, QDialogButtonBox.ActionRole)
		filter_box.addButton(clr_btn, QDialogButtonBox.ActionRole)

		self.cds_check = QCheckBox('CDS', self)
		self.cds_check.setChecked(1 in self.features)
		self.exon_check = QCheckBox('exon', self)
		self.exon_check.setChecked(2 in self.features)
		self.utr3_check = QCheckBox("3'UTR", self)
		self.utr3_check.setChecked(3 in self.features)
		self.utr5_check = QCheckBox("5'UTR", self)
		self.utr3_check.setChecked(5 in self.features)
		self.intron_check = QCheckBox('intron', self)
		self.intron_check.setChecked(6 in self.features)

		check_layout = QHBoxLayout()
		check_layout.addWidget(QLabel("Only display repeats on: "))
		check_layout.addWidget(self.cds_check)
		check_layout.addWidget(self.exon_check)
		check_layout.addWidget(self.utr3_check)
		check_layout.addWidget(self.utr5_check)
		check_layout.addWidget(self.intron_check)
		check_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

		btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
		btn_box.button(QDialogButtonBox.Ok).setText("Update table")
		btn_box.button(QDialogButtonBox.Ok).setIcon(QIcon(":/icons/update.svg"))
		btn_box.accepted.connect(self.update_filter)

		layout = QVBoxLayout()
		layout.addWidget(filter_box)
		layout.addWidget(self.tree)
		layout.addLayout(check_layout)
		layout.addWidget(btn_box)

		self.setLayout(layout)

	def add_filter(self):
		self.model.beginResetModel()
		if self.filters:
			self.filters.append(['And', 'id', '>', 0])
		else:
			self.filters.append(['', 'id', '>', 0])
		self.model.endResetModel()

	def delete_filter(self):
		self.model.beginResetModel()
		index = self.tree.currentIndex()
		row = index.row()

		if self.filters:
			self.filters.pop(row)

		if self.filters and self.filters[0][0]:
			self.filters[0][0] = ""

		self.model.endResetModel()

	def clear_filter(self):
		self.model.beginResetModel()
		self.filters = []
		self.model.endResetModel()

	def update_filter(self):
		_filters = []
		_features = []

		_type, _index = self.table.split('_')

		if self.cds_check.isChecked(): _features.append(1)
		if self.exon_check.isChecked(): _features.append(2)
		if self.utr3_check.isChecked(): _features.append(3)
		if self.utr5_check.isChecked(): _features.append(5)
		if self.intron_check.isChecked(): _features.append(6)

		for row in self.filters:
			for idx, col in enumerate(row):
				if idx == 2:
					_filters.append(col.replace('contains', 'like'))

				elif idx == 3:
					if row[2] == 'contains':
						_filters.append("'%{}%'".format(col))

					elif isinstance(col, str):
						_filters.append("'{}'".format(col))

					else:
						_filters.append(str(col))

				else:
					_filters.append(col)

		self.parent.current_filters = {}

		if self.filters:
			self.parent.current_filters[self.table] = self.filters

		if _features and _type != 'primer':
			self.parent.current_filters['feature'] = _features
			types = {'ssr': 1, 'cssr': 2, 'gtr': 3, 'issr': 4}

			if len(_features) > 1:
				_filters.append("AND id IN (SELECT locus FROM map_{} WHERE type={} AND feature IN ({}))".format(
					_index,
					types[_type],
					','.join(map(str, _features))
				))
			else:
				_filters.append("AND id IN (SELECT locus FROM map_{} WHERE type={} AND feature={})".format(
					_index,
					types[_type],
					_features[0]
				))

		_filters = ' '.join(_filters)
		self.parent.set_filter(self.table, _filters)
