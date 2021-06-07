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
	def __init__(self, parent):
		super().__init__(parent)
		self._editor = parent

	def sizeHint(self):
		return QSize(self._editor.line_number_area_width(), 0)

	def paintEvent(self, event):
		self._editor.lineno_bar_area_paint_event(event)

class SequenceScaler(QWidget):
	def __init__(self, parent):
		super().__init__(parent)
		self._editor = parent

	def sizeHint(self):
		return QSize(0, self.scale_bar_area_height())

	def paintEvent(self, event):
		self._editor.scale_bar_paint_event(event)

class SequenceViewer(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent
		self.setReadOnly(True)
		self.setFrameStyle(QFrame.NoFrame)
		#self.viewport().setAutoFillBackground(False)

		#set font family
		font = QFont("Roboto Mono")
		font.setPointSize(12)
		self.setFont(font)

		#set line letter spacing
		fmt = QTextCharFormat()
		fmt.setFontLetterSpacing(200)
		self.setCurrentCharFormat(fmt)

		#scaler bar settings
		self.scale_top_space = 5
		self.scale_mark_space = 1
		self.scale_mark_height = 10

		#lineno bar settings
		self.lineno_left_space = 5
		self.lineno_right_space = 20

		#locus start position on sequence
		self.locus_start = 0

		#locus sequence length
		self.locus_length = 0

		#create line number and scaler bar
		self.line_number_area = LineNumberArea(self)
		self.scale_bar_area = SequenceScaler(self)

		#action triggered
		self.blockCountChanged.connect(self.update_line_number_area_width)
		self.updateRequest.connect(self.update_line_number_area)

		self.update_line_number_area_width(0)

		#set dna sequence highlighter
		self.highlighter = SequenceHighlighter()
		self.highlighter.setDocument(self.document())

		#event connect
		self.selectionChanged.connect(self.change_select_count)

	def set_locus_position(self, start, length):
		self.locus_start = start
		self.locus_length = length

	def line_number_area_width(self):
		#digits = 1
		#max_num = max(1, self.blockCount())
		#max_num = max(1, self.document().lineCount())
		#while max_num >= 10:
		#	max_num *= 0.1
		#	digits += 1
		#space = 25 + self.fontMetrics().horizontalAdvance('9') * digits
		#return space

		max_num = self.locus_start + self.locus_length - 1
		text_width = self.fontMetrics().averageCharWidth() * len(str(max_num))
		return self.lineno_left_space + text_width + self.lineno_right_space

	def scale_bar_area_height(self):
		font_height = self.fontMetrics().height()
		return self.scale_top_space + font_height + self.scale_mark_space + self.scale_mark_height

	def scale_bar_area_width(self):
		return self.width()

	def resizeEvent(self, event):
		super().resizeEvent(event)
		cr = self.contentsRect()
		lineno_bar_width = self.line_number_area_width()
		scale_bar_height = self.scale_bar_area_height()
		
		rect = QRect(cr.left(), cr.top()+scale_bar_height, lineno_bar_width, cr.height())
		self.line_number_area.setGeometry(rect)

		rect = QRect(cr.left(), cr.top(), cr.width(), scale_bar_height)
		self.scale_bar_area.setGeometry(rect)

	def scale_bar_paint_event(self, event):
		painter = QPainter(self.scale_bar_area)
		painter.fillRect(event.rect(), Qt.white)

		start = self.line_number_area_width()
		block = self.firstVisibleBlock()
		line = block.layout().lineAt(0)
		column_count = line.textLength()
		column_width = line.naturalTextWidth()/column_count
		char_width = self.fontMetrics().averageCharWidth()
		char_height = self.fontMetrics().height()
		scale_height = self.scale_bar_area_height()

		#correct the start position
		start = start + line.x() + char_width/2

		#draw cross mark line
		painter.drawLine(QPoint(start, scale_height-1), QPoint(start+column_width*(column_count-1), scale_height-1))

		#draw first mark
		mark_y = self.scale_top_space + char_height + self.scale_mark_space
		painter.drawLine(QPoint(start, mark_y + 2), QPoint(start, scale_height))

		#draw first mark text
		text_x = start - char_width/2
		text_y = self.scale_top_space + char_height
		painter.drawText(text_x, text_y, str(1))

		for i in range(1, column_count+1):
			mark_x = start + (i-1)*column_width
			text_x = mark_x - char_width * (len(str(i))*0.5)

			if i % 10 == 0:
				painter.drawLine(QPoint(mark_x, mark_y + 2), QPoint(mark_x, scale_height))
				painter.drawText(text_x, text_y, str(i))
			elif i % 5 == 0:
				painter.drawLine(QPoint(mark_x, mark_y + 5), QPoint(mark_x, scale_height))
				painter.drawText(text_x, text_y, str(i))
			else:
				painter.drawLine(QPoint(mark_x, mark_y + 7), QPoint(mark_x, scale_height))

	def lineno_bar_area_paint_event(self, event):
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
				line_start = self.locus_start + (line_number - 1) * line_char

				dx = self.blockBoundingGeometry(block).x()
				dy = self.blockBoundingGeometry(block).y()
				line = block.layout().lineAt(i)
				top = line.rect().translated(offset).translated(dx, dy).y()
				painter.setPen(Qt.gray)
				painter.drawText(0, top, width-self.lineno_right_space, height, Qt.AlignRight, str(line_start))

			block = block.next()

	@Slot(int)
	def update_line_number_area_width(self, newBlockCount):
		self.setViewportMargins(self.line_number_area_width(), self.scale_bar_area_height(), 0, 0)

	@Slot(QRect, int)
	def update_line_number_area(self, rect, dy):
		if dy:
			self.line_number_area.scroll(0, dy)
		else:
			width = self.line_number_area.width()
			self.line_number_area.update(0, rect.y(), width, rect.height())

		if rect.contains(self.viewport().rect()):
			self.update_line_number_area_width(0)

		self.change_line_number()

	def change_line_number(self):
		count = 0
		block = self.firstVisibleBlock()
		while block.isValid():
			count += block.lineCount()
			block = block.next()

		self.parent.line_number.setText(str(count))

	@Slot()
	def change_select_count(self):
		cursor = self.textCursor()
		if cursor.hasSelection():
			count = cursor.selectionEnd() - cursor.selectionStart()
		else:
			count = 0

		self.parent.select_count.setText(str(count))

	def add_format(self):
		fmt = QTextCharFormat()
		fmt.setUnderlineColor(QColor(0,0,0))
		fmt.setUnderlineStyle(QTextCharFormat.DashDotLine)
		cursor = self.textCursor()
		cursor.setPosition(1)
		cursor.setPosition(10, QTextCursor.KeepAnchor)
		cursor.mergeCharFormat(fmt)

		extra_selections = []
		selection = QTextEdit.ExtraSelection()
		selection.format.setBackground(Qt.yellow)
		selection.cursor = self.textCursor()
		selection.cursor.setPosition(20)
		selection.cursor.setPosition(25, QTextCursor.KeepAnchor)
		extra_selections.append(selection)
		self.setExtraSelections(extra_selections)

class SequenceDialog(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Sequence viewer")
		#self.setWindowFlags(Qt.Dialog)
		self.setWindowModality(Qt.ApplicationModal)

		self.create_statusbar()

		self.editor = SequenceViewer(self)
		self.setCentralWidget(self.editor)
		self.resize(QSize(700, 500))

	def create_statusbar(self):
		self.status_bar = self.statusBar()

		#line number
		self.status_bar.addPermanentWidget(QLabel("Line:", self))
		self.line_number = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.line_number)

		#select columns
		self.status_bar.addPermanentWidget(QLabel("Select:", self))
		self.select_count = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.select_count)

	def set_sequence(self, seq="ATGCAAAGCCTTTG", start=1):
		seq = "ATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTG"
		self.editor.setPlainText(seq)
		self.editor.set_locus_position(start, len(seq))
		self.editor.add_format()


if __name__ == '__main__':
	import sys
	app = QApplication(sys.argv)
	QFontDatabase.addApplicationFont("fonts/robotomono.ttf")
	win = SequenceDialog()
	win.set_sequence()
	win.show()
	sys.exit(app.exec_())