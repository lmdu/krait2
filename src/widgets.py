from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from models import *

__all__ = ['KraitFastxTree']

class KraitFastxTree(QTreeView):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent

		self.setRootIsDecorated(False)

		self.model = KraitFastxModel(parent)
		self.setModel(self.model)

		self.row_changed = self.model.row_count

	def update_model(self):
		self.model.select()
