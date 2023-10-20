from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from models import *

__all__ = ['KraitFastxTree', 'KraitSSRTable', 'KraitCSSRTable',
			'KraitISSRTable', 'KraitGTRTable', 'KraitPrimerTable',
			'KraitTextBrowser']

class KraitFastxTree(QTreeView):
	row_clicked = Signal(int)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent

		#self.setRootIsDecorated(True)

		self._model = KraitFastxModel(parent)
		self.setModel(self._model)
		self._model.row_count.connect(self.parent.file_counter.setNum)

		self.setColumnHidden(0, True)
		self.header().hide()

		self.clicked.connect(self.on_fastx_file_clicked)

	def update_model(self):
		self._model.select()

	@Slot()
	def on_fastx_file_clicked(self, index):
		row_id = index.siblingAtColumn(0).data()
		self.row_clicked.emit(row_id)

class KraitTextBrowser(QTextBrowser):
	def __init__(self, parent):
		super().__init__(parent)
		self.parent = parent

	def set_html(self, html):
		self.setHtml(html)

	def count_emit(self):
		self.parent.column_counter.setNum(0)
		self.parent.row_counter.setNum(0)
		self.parent.select_counter.setNum(0)

class KraitTableView(QTableView):
	modeler = None

	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent

		self.setSortingEnabled(True)
		self.verticalHeader().hide()
		self.horizontalHeader().setHighlightSections(False)
		self.horizontalHeader().setStretchLastSection(True)
		#self.setEditTriggers(QAbstractItemView.DoubleClicked)
		self.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.setSelectionMode(QAbstractItemView.SingleSelection)
		self.clicked.connect(self.on_row_clicked)

		self.create_check()
		self.create_model()

	def create_check(self):
		self.select_all_btn = QCheckBox(self.horizontalHeader())
		self.select_all_btn.setGeometry(QRect(3,5,20,20))
		self.select_all_btn.clicked.connect(self.on_select_all_clicked)

	def create_model(self):
		self._model = self.modeler()
		self.setModel(self._model)

		self._model.col_count.connect(self.parent.column_counter.setNum)
		self._model.row_count.connect(self.parent.row_counter.setNum)
		self._model.sel_count.connect(self.parent.select_counter.setNum)
		self._model.sel_count.connect(self.change_select_all_state)

	def set_index(self, index):
		self._model.set_index(index)

	def set_filter(self, filters):
		self._model.set_filter(filters)

	def has_selection(self):
		if self._model.selected:
			return True
		else:
			return False

	@property
	def table_name(self):
		return self._model.table.split('_')[0]

	@property
	def table_real(self):
		return self._model.table

	def get_selected_rows(self):
		count = self._model.get_selected_count()
		rows = self._model.get_selected_rows()
		return (self.table_name, count, rows)

	@Slot()
	def on_row_clicked(self, index):
		types = {'ssr', 'cssr', 'issr', 'gtr', 'primer'}

		if self.table_name not in types:
			return

		repeat = self._model.get_row(index)
		self.parent.show_dna_sequence(self.table_name, repeat)
		self.parent.show_repeat_annotation(self.table_name, repeat)

	@Slot()
	def change_select_all_state(self, select):
		state = self._model.get_select_state()
		self.select_all_btn.setCheckState(state)

	@Slot()
	def on_select_all_clicked(self, checked):
		state = self.select_all_btn.checkState()

		if state == Qt.Checked:
			self._model.select_all()

		elif state == Qt.Unchecked:
			self._model.deselect_all()

		elif state == Qt.PartiallyChecked:
			self._model.select_all()
			self.select_all_btn.setCheckState(Qt.Checked)

	def count_emit(self):
		self._model.count_emit()

class KraitSSRTable(KraitTableView):
	modeler = KraitSSRModel

class KraitCSSRTable(KraitTableView):
	modeler = KraitCSSRModel

class KraitISSRTable(KraitTableView):
	modeler = KraitISSRModel

class KraitGTRTable(KraitTableView):
	modeler = KraitGTRModel

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
		self.verticalHeader().setDefaultSectionSize(int(width*1.5))

	def create_model(self):
		super().create_model()

		self._delegate = KraitPrimerDelegate(self)
		self.setItemDelegate(self._delegate)
