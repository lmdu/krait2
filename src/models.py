from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

class KraitFastxModel(QAbstractItemModel):
	def __init__(self):
		super().__init__()

		self.headers = []
		self.table_name = 'fastx'
		self.total_rows = DB.get_count(self.table_name)

	def columnCount(self, parent):
		return len(self.headers)

	def rowCount(self, parent):
		return self.total_rows

	def parent(self, index):
		pass

	def data(self, index, role):
		pass

