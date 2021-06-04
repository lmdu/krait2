from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

__all__ = ['SeqViewer']

class SequenceScaler(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.editor_width = 0
		self.line_number = 0

	def paintEvent(self, event):
		painter = QPainter(self)
		width = painter.device().width()
		height = painter.device().height()

		x = self.line_number

		painter.drawLine(QPoint(x, 0), QPoint(x, 10))
		painter.drawLine(QPoint(x, 5), QPoint(self.editor_width+self.line_number-1, 5))
		painter.drawLine(QPoint(self.editor_width+self.line_number-1, 0), QPoint(self.editor_width+self.line_number-1, 10))
		
		#painter.drawLine(QPoint(1, 0), QPoint(1, 10))
		
		#painter.drawLine(QPoint(width-1, 0), QPoint(width-1, 10))

	def minimumSizeHint(self):
		return QSize(0, 10)

	@Slot(int, int)
	def update_scale(self, width, line):
		self.editor_width = width
		self.line_number = line
		self.update()

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

class SequenceViewer(QPlainTextEdit):
	resized = Signal(int, int)

	def __init__(self, parent):
		super().__init__(parent)
		#self.setReadOnly(True)
		self.setFrameStyle(QFrame.NoFrame)
		#self.viewport().setAutoFillBackground(False)

		self.line_number_area = LineNumberArea(self)

		self.blockCountChanged.connect(self.update_line_number_area_width)
		self.updateRequest.connect(self.update_line_number_area)

		self.update_line_number_area_width(0)

		#fmt = QTextCharFormat()
		#fmt.setFontLetterSpacingType(QFont.AbsoluteSpacing)
		#fmt.setFontLetterSpacing(10)
		#self.setCurrentCharFormat(fmt)

		font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
		font.setPointSize(13)
		self.setFont(font)


	def line_number_area_width(self):
		digits = 1
		max_num = max(1, self.blockCount())
		while max_num >= 10:
			max_num *= 0.1
			digits += 1

		space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
		return space

	def resizeEvent(self, e):
		super().resizeEvent(e)
		cr = self.contentsRect()
		width = self.line_number_area_width()
		rect = QRect(cr.left(), cr.top(), width, cr.height())
		self.line_number_area.setGeometry(rect)
		self.resized.emit(self.viewport().width(), width)

	def lineNumberAreaPaintEvent(self, event):
		painter = QPainter(self.line_number_area)
		painter.fillRect(event.rect(), Qt.transparent)
		block = self.firstVisibleBlock()
		block_number = block.blockNumber()
		offset = self.contentOffset()
		top = self.blockBoundingGeometry(block).translated(offset).top()
		bottom = top + self.blockBoundingRect(block).height()

		width = self.line_number_area.width()
		height = self.fontMetrics().height()

		

		for i in range(self.document().lineCount()):
			lh = int(self.fontMetrics().lineSpacing())

			print(height, lh)
			painter.drawText(0, top, width, height, Qt.AlignRight, str(i+1))
			top += lh

		'''
		while block.isValid() and top <= event.rect().bottom():
			if block.isVisible() and bottom >= event.rect().top():
				number = str(block_number + 1)
				painter.setPen(Qt.black)
				width = self.line_number_area.width()
				height = self.fontMetrics().height()
				painter.drawText(0, top, width, height, Qt.AlignRight, number)

			block = block.next()
			top = bottom
			bottom = top + self.blockBoundingRect(block).height()
			block_number += 1
		'''

	@Slot()
	def update_line_number_area_width(self, newBlockCount):
		self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

	@Slot()
	def update_line_number_area(self, rect, dy):
		if dy:
			self.line_number_area.scroll(0, dy)
		else:
			width = self.line_number_area.width()
			self.line_number_area.update(0, rect.y(), width, rect.height())

		if rect.contains(self.viewport().rect()):
			self.update_line_number_area_width(0)

class SequenceDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Sequence viewer")
		self.highlighter = SequenceHighlighter()
		self.editor = SequenceViewer(self)
		self.scaler = SequenceScaler(self)
		self.editor.resized.connect(self.scaler.update_scale)
		layout = QVBoxLayout(self)
		layout.addWidget(self.scaler)
		layout.addWidget(self.editor)
		self.setLayout(layout)
		self.highlighter.setDocument(self.editor.document())

	def set_sequence(self, seq="ATGCAAAGCCTTTG"):
		self.editor.setPlainText(seq)


if __name__ == '__main__':
	import sys
	app = QApplication(sys.argv)
	win = SequenceDialog()
	win.set_sequence()
	win.show()
	sys.exit(app.exec_())