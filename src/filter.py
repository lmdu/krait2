from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

__all__ = ['FilterDialog']

class FilterTreeModel(QAbstractItemModel):
	def __init__(self, parent=None):
		super(FilterTreeModel, self).__init__(parent)
		self._headers = ["logic", "column", "condition", "value"]
		self.row_count = 10

	def index(self, row, column, parent=QModelIndex()):
		return self.createIndex(row, column)

	def parent(self, index):
		return QModelIndex()

	def rowCount(self, parent=QModelIndex()):
		return self.row_count

	def columnCount(self, parent=QModelIndex()):
		return 4

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return None

		if role == Qt.DisplayRole:
			col = index.column()
			return col

		elif role == Qt.UserRole:
			print('yes')

		#elif role == Qt.EditRole:
		#	pass

	def setData(self, index, value, role=Qt.ItemDataRole):
		print(value)
		if role == Qt.EditRole:
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

class FilterTreeDelegate(QStyledItemDelegate):
	def __init__(self, parent=None):
		super(FilterTreeDelegate, self).__init__(parent)

	def paint(self, painter, option, index):
		if index.column() == 1:
			pb = QStyleOptionProgressBar()
			pb.rect = option.rect
			pb.minimum = 0
			pb.maximum = 100
			pb.progress = 20
			pb.text = "20%"
			pb.textVisible = True
			QApplication.style().drawControl(QStyle.CE_ProgressBar, pb, painter)
		else:
			super(FilterTreeDelegate, self).paint(painter, option, index)


#class FilterTreeView(QTreeView):
#	def __init__(self, parent=None):
#		super(FilterTreeView, self).__init__(parent)

class FilterDialog(QDialog):
	def __init__(self, parent=None):
		super(FilterDialog, self).__init__(parent)
		self.setWindowTitle("Add filters")

		self.tree = QTreeView(self)
		self.model = FilterTreeModel(self)
		self.delegate = FilterTreeDelegate(self)
		self.tree.setModel(self.model)
		self.tree.setItemDelegate(self.delegate)

		btn_box = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
		btn_box.accepted.connect(self.accept)
		btn_box.rejected.connect(self.reject)

		layout = QVBoxLayout()
		layout.addWidget(self.tree)
		layout.addWidget(btn_box)

		self.setLayout(layout)

	def add_filter(self):
		pass

	def delete_filter(self):
		pass

