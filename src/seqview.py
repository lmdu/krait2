from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

__all__ = ['SeqViewer']

class SequenceHighlighter(QSyntaxHighlighter):
	def __init__(self, parent=None):
		super().__init__(parent)

		self.rules = []

		a_format = QTextCharFormat()
		a_format.setForeground(QColor(80,80,255))
		self.rules.append((QRegularExpression("[Aa]+"), a_format))

		t_format = QTextCharFormat()
		t_format.setForeground(QColor(255,215,0))
		self.rules.append((QRegularExpression("[Tt]+"), t_format))

		g_format = QTextCharFormat()
		g_format.setForeground(QColor(0,192,0))
		self.rules.append((QRegularExpression("[Gg]+"), g_format))

		c_format = QTextCharFormat()
		c_format.setForeground(QColor(224,0,0))
		self.rules.append((QRegularExpression("[Cc]+"), c_format))

	def highlightBlock(self, text):
		for pattern, _format in self.rules:
			matches = pattern.globalMatch(text)
			while matches.hasNext():
				match = matches.next()
				self.setFormat(match.capturedStart(), match.capturedLength(), _format)

		self.setCurrentBlockState(0)


class LineNumberArea(QWidget):
	def __init__(self, editor):
		super().__init__(editor)
		self._editor = editor

	def sizeHint(self):
		return QSize(self._editor.line_number_area_width(), 0)

	def paintEvent(self, event):
		self._editor.lineNumberAreaPaintEvent(event)

class SequenceScaler(QWidget):
	def __init__(self, editor):
		super().__init__(editor)
		self._editor = editor

	def sizeHint(self):
		return QSize(self._editor.scale_bar_area_width(), 20)

	def paintEvent(self, event):
		self._editor.scaleBarAreaPaintEvent(event)

class SequenceViewer(QPlainTextEdit):
	def __init__(self, parent=None, start=206578, length=70):
		super().__init__(parent)
		self.start = start
		self.length = length

		self.setReadOnly(True)
		self.setFrameStyle(QFrame.NoFrame)
		#self.viewport().setAutoFillBackground(False)
		font = QFont("Roboto Mono")
		font.setPointSize(12)
		self.setFont(font)

		fmt = QTextCharFormat()
		fmt.setFontLetterSpacing(200)
		self.setCurrentCharFormat(fmt)

		self.line_number_area = LineNumberArea(self)
		self.scale_bar_area = SequenceScaler(self)

		self.blockCountChanged.connect(self.update_line_number_area_width)
		self.updateRequest.connect(self.update_line_number_area)

		self.update_line_number_area_width(0)


	def line_number_area_width(self):
		digits = 1
		#max_num = max(1, self.blockCount())
		#max_num = max(1, self.document().lineCount())
		max_num = self.start + self.length - 1
		while max_num >= 10:
			max_num *= 0.1
			digits += 1

		space = 25 + self.fontMetrics().horizontalAdvance('9') * digits
		return space

	def scale_bar_area_width(self):
		return self.width()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		cr = self.contentsRect()
		width = self.line_number_area_width()
		rect = QRect(cr.left(), cr.top()+20, width, cr.height())
		self.line_number_area.setGeometry(rect)

		rect = QRect(cr.left(), cr.top(), self.scale_bar_area_width(), 20)
		self.scale_bar_area.setGeometry(rect)

	def scaleBarAreaPaintEvent(self, event):
		painter = QPainter(self.scale_bar_area)
		painter.fillRect(event.rect(), Qt.white)

		start = self.line_number_area_width()
		block = self.firstVisibleBlock()
		line = block.layout().lineAt(0)
		columns = line.textLength()
		column_width = line.naturalTextWidth()/columns

		start = start + line.x() + self.fontMetrics().averageCharWidth()/2

		painter.drawLine(QPoint(start, 20), QPoint(start+column_width*(columns-1), 20))
		painter.drawLine(QPoint(start, 12), QPoint(start, 20))
		painter.drawText(start, 10, str(1))

		for i in range(1, columns+1):
			x = start + (i-1)*column_width

			if i % 10 == 0:
				painter.drawLine(QPoint(x, 12), QPoint(x, 20))
				painter.drawText(x, 10, str(i))
			elif i % 5 == 0:
				painter.drawLine(QPoint(x, 15), QPoint(x, 20))
				painter.drawText(x, 10, str(i))
			else:
				painter.drawLine(QPoint(x, 17), QPoint(x, 20))


	def lineNumberAreaPaintEvent(self, event):
		painter = QPainter(self.line_number_area)
		painter.fillRect(event.rect(), Qt.white)

		block = self.firstVisibleBlock()
		offset = self.contentOffset()
		top = self.blockBoundingGeometry(block).translated(offset).top()
		bottom = top + self.blockBoundingRect(block).height()

		width = self.line_number_area_width()
		height = self.fontMetrics().height()

		line_char = block.layout().lineAt(0).textLength()

		line_number = 0

		while block.isValid():
			for i in range(block.lineCount()):
				line_number += 1
				
				line_start = self.start + (line_number - 1) * line_char

				dx = self.blockBoundingGeometry(block).x()
				dy = self.blockBoundingGeometry(block).y()
				line = block.layout().lineAt(i)
				top = line.rect().translated(offset).translated(dx, dy).y()
				painter.setPen(Qt.gray)
				painter.drawText(0, top, width-20, height, Qt.AlignRight, str(line_start))

			block = block.next()

	@Slot(int)
	def update_line_number_area_width(self, newBlockCount):
		self.setViewportMargins(self.line_number_area_width(), 20, 0, 0)

	@Slot(QRect, int)
	def update_line_number_area(self, rect, dy):
		if dy:
			self.line_number_area.scroll(0, dy)
		else:
			width = self.line_number_area.width()
			self.line_number_area.update(0, rect.y(), width, rect.height())

		if rect.contains(self.viewport().rect()):
			self.update_line_number_area_width(0)


class SequenceDialog(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Sequence viewer")
		#self.setWindowFlags(Qt.Dialog)
		self.setWindowModality(Qt.ApplicationModal)
		self.highlighter = SequenceHighlighter()
		self.editor = SequenceViewer(self)
		#self.scaler = SequenceScaler(self)
		#self.editor.resized.connect(self.scaler.update_scale)
		#layout = QVBoxLayout(self)
		#layout.addWidget(self.scaler)
		#layout.addWidget(self.editor)
		#layout.setSpacing(0)
		#self.setLayout(layout)
		self.highlighter.setDocument(self.editor.document())
		self.setCentralWidget(self.editor)

	def set_sequence(self, seq="ATGCAAAGCCTTTG"):
		self.editor.setPlainText("ATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTG")


if __name__ == '__main__':
	import sys
	app = QApplication(sys.argv)
	QFontDatabase.addApplicationFont("fonts/robotomono.ttf")
	win = SequenceDialog()
	win.set_sequence()
	win.show()
	sys.exit(app.exec_())