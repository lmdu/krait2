from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from models import *

__all__ = ['KraitFastxTree']

class KraitFastxTree(QTreeView):
	row_clicked = Signal(int)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent

		self.setRootIsDecorated(False)

		self.model = KraitFastxModel(parent)
		self.setModel(self.model)

		self.row_changed = self.model.row_count
		self.clicked.connect(self.on_row_clicked)

	def update_model(self):
		self.model.select()

	@Slot(QModelIndex)
	def on_row_clicked(self, index):
		row_id = index.siblingAtColumn(0).data()
		self.row_clicked.emit(row_id)

class KraitTableView(QTableView):
	modeler = None

	def __init__(self, parent=None):
		super().__init__(parent)

		self.verticalHeader().hide()
		self.horizontalHeader().setHighlightSections(False)
		self.horizontalHeader().setStretchLastSection(True)
		#self.setEditTriggers(QAbstractItemView.DoubleClicked)
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
		self._model = self.modeler()
		self.setModel(self._model)

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

	@Slot()
	def check_all_action(self, checked):
		state = self.checkbox.checkState()

		if state == Qt.Checked:
			self.model.select_all()

		elif state == Qt.Unchecked:
			self.model.deselect_all()

		elif state == Qt.PartiallyChecked:
			self.model.select_all()
			self.checkbox.setCheckState(Qt.Checked)

class KraitSSRTable(KraitTableView):
	modeler = KraitSSRModel

class KraitPrimerDelegate(QStyledItemDelegate):
	def __init__(self, parent=None):
		super().__init__(parent)

	def setEditorData(self, editor, index):
		val = index.data()
		editor.setText(val)

class KraitPrimerTable(KraitTableView):
	modeler = KraitPrimerModel

	def __init__(self, parent=None):
		super().__init__(parent)

		width = self.verticalHeader().defaultSectionSize()
		self.verticalHeader().setDefaultSectionSize(int(width*1.25))

	def create_model(self):
		super().create_model()

		self._delegate = KraitPrimerDelegate(self)
		self.setItemDelegate(self._delegate)
