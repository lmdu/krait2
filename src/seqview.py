from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

__all__ = ['SeqViewer']

class SequenceViewer(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)

	def paintEvent(self, event):
		painter = QPainter(self)
		width = painter.device().width()
		height = painter.device().height()
		
		mark_width = 20
		x_start = 10
		y_start = 10

		mark_count = int(width/mark_width)

		painter.drawLine(QPoint(x_start, y_start), QPoint(width-x_start, y_start))

		for i in range(mark_count):
			x = 10 + i * mark_width

			if i % 10 == 0:
				painter.drawLine(QPoint(x, y_start-5), QPoint(x, y_start+5))

			elif i % 5 == 0:
				painter.drawLine(QPoint(x, y_start), QPoint(x, y_start+5))

			else:
				painter.drawLine(QPoint(x, y_start), QPoint(x, y_start+3))




if __name__ == '__main__':
	import sys
	app = QApplication(sys.argv)
	win = SequenceViewer()
	win.show()
	sys.exit(app.exec_())