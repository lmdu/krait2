import pyfastx

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

__all__ = ['KraitSequenceViewer']

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

class KraitSequenceViewer(QPlainTextEdit):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent = parent
		self.setReadOnly(True)
		self.setFrameStyle(QFrame.NoFrame)
		#self.viewport().setAutoFillBackground(False)

		#set font family
		font = QFont("Roboto Mono")
		font.setPointSize(10)
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

		#set dna sequence highlighter
		self.highlighter = SequenceHighlighter()
		self.highlighter.setDocument(self.document())

		#event connect
		self.selectionChanged.connect(self.change_select_count)

		self.fastx_file = None
		self.fastx_index = None

		self.flank_length = 100
		self.flank_step = 50

		#self.set_sequence()

	def wheelEvent(self, event):
		y = event.angleDelta().y()
		
		if y > 0:
			if self.flank_length == 10000:
				return

			self.flank_length += self.flank_step

			if self.flank_length > 10000:
				self.flank_length = 10000

		else:
			if self.flank_length == 100:
				return

			self.flank_length -= self.flank_step

			if self.flank_length < 100:
				self.flank_length = 100

		self.update_mark_sequence()

	def sizeHint(self):
		return QSize(100, 150)

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

		block = self.firstVisibleBlock()
		start = self.line_number_area_width()
		line = block.layout().lineAt(0)
		column_count = line.textLength()
		if column_count == 0:
			return
		column_width = line.naturalTextWidth()/column_count
		char_width = self.fontMetrics().averageCharWidth()
		char_height = self.fontMetrics().height()
		scale_height = self.scale_bar_area_height() - 1

		#correct the start position
		start = start + line.x() + char_width/2

		#draw cross mark line
		painter.drawLine(QPoint(start, scale_height), QPoint(start+column_width*(column_count-1), scale_height))

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
		if line_char == 0:
			return

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
		self.change_line_number()
		self.scale_bar_area.update()

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

		#self.parent.line_number.setText(str(count))

	@Slot()
	def change_select_count(self):
		cursor = self.textCursor()
		if cursor.hasSelection():
			count = cursor.selectionEnd() - cursor.selectionStart()
		else:
			count = 0

		#self.parent.select_count.setText(str(count))

	"""
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
		#selection.format.setBackground(Qt.yellow)
		selection.format.setProperty(QTextFormat.OutlinePen, QPen(Qt.darkGray))
		selection.cursor = self.textCursor()
		selection.cursor.setPosition(20)
		selection.cursor.setPosition(25, QTextCursor.KeepAnchor)
		extra_selections.append(selection)

		selection = QTextEdit.ExtraSelection()
		#selection.format.setBackground(Qt.yellow)
		selection.format.setProperty(QTextFormat.OutlinePen, QPen(QColor(125, 60, 152)))
		selection.cursor = self.textCursor()
		selection.cursor.setPosition(25)
		selection.cursor.setPosition(30, QTextCursor.KeepAnchor)
		extra_selections.append(selection)

		self.setExtraSelections(extra_selections)
	"""

	"""
	def format_tandem_repeat(self):
		extra_selections = []
		motif_length = len(self.tandem_repeat.motif)
		positions = range(self.target_start, self.target_end, motif_length)

		for pos in positions:
			selection = QTextEdit.ExtraSelection()
			selection.format.setProperty(QTextFormat.BackgroundBrush, QBrush(Qt.lightGray))
			selection.format.setProperty(QTextFormat.OutlinePen, QPen(Qt.darkGray))
			selection.cursor = self.textCursor()
			selection.cursor.setPosition(pos)
			selection.cursor.setPosition(pos + motif_length, QTextCursor.KeepAnchor)
			extra_selections.append(selection)

		self.setExtraSelections(extra_selections)
	"""

	def update_sequence(self):
		start = self.target.start - self.flank_length - 1

		if start < 0:
			start = 0

		end = self.target.end + self.flank_length

		seq = self.fastx_file[self.target.chrom][start:end].seq

		self.set_locus_position(start, len(seq))
		self.setPlainText(seq)

		self.seq_start = start + 1
		self.seq_end = start + len(seq)

	def update_marks(self):
		sels = []

		for mark in self.marks:
			start = mark.start - self.seq_start
			end = start + mark.end - mark.start + 1

			if mark.style == 'tandem':
				mlen = mark.type
				
				for pos in range(start, end, mlen):
					sel = QTextEdit.ExtraSelection()
					sel.format.setProperty(QTextFormat.BackgroundBrush, QBrush(Qt.lightGray))
					sel.format.setProperty(QTextFormat.OutlinePen, QPen(Qt.black))
					sel.cursor = self.textCursor()
					sel.cursor.setPosition(pos)
					sel.cursor.setPosition(pos + mlen, QTextCursor.KeepAnchor)
					sels.append(sel)

			elif mark.style == 'align':
				sel = QTextEdit.ExtraSelection()
				sel.format.setProperty(QTextFormat.BackgroundBrush, QBrush(Qt.transparent))
				sel.format.setProperty(QTextFormat.OutlinePen, QPen(Qt.black))
				sel.cursor = self.textCursor()
				sel.cursor.setPosition(start)
				sel.cursor.setPosition(end, QTextCursor.KeepAnchor)
				sels.append(sel)

			elif mark.style == 'primer':
				sel = QTextEdit.ExtraSelection()
				sel.format.setProperty(QTextFormat.BackgroundBrush, QBrush(Qt.transparent))
				sel.format.setProperty(QTextFormat.OutlinePen, QPen(Qt.black, 1, Qt.DashLine))
				sel.cursor = self.textCursor()
				sel.cursor.setPosition(start)
				sel.cursor.setPosition(end, QTextCursor.KeepAnchor)
				sels.append(sel)

				"""
				fmt = QTextCharFormat()
				fmt.setUnderlineColor(QColor(0,0,0))
				fmt.setUnderlineStyle(QTextCharFormat.SingleUnderline)
				cursor = self.textCursor()
				cursor.setPosition(start)
				cursor.setPosition(end, QTextCursor.KeepAnchor)
				cursor.mergeCharFormat(fmt)
				"""
		self.setExtraSelections(sels)

	def update_mark_sequence(self):
		self.update_sequence()
		self.update_marks()
		self.update_line_number_area_width(0)

	def mark_sequence(self, index, target, marks):
		if self.fastx_index != index:
			self.fastx_index = index
			fastx = DB.get_object("SELECT * FROM fastx WHERE id=? LIMIT 1", (index,))

			if fastx.format == 'fasta':
				self.fastx_file = pyfastx.Fasta(fastx.fpath, uppercase=True)
			else:
				self.fastx_file = pyfastx.Fastq(fastx.fpath)

		self.target = target
		self.marks = marks

		self.update_mark_sequence()

class SequenceDialog(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Sequence viewer")
		#self.setWindowFlags(Qt.Dialog)
		self.setWindowModality(Qt.ApplicationModal)

		self.create_statusbar()

		self.editor = KraitSequenceViewer(self)
		self.setCentralWidget(self.editor)
		self.resize(QSize(600, 400))

	def create_statusbar(self):
		self.status_bar = self.statusBar()

		#flank length slider
		self.flank_slider = QSlider(Qt.Horizontal, self)
		self.flank_slider.setMinimum(1)
		self.flank_slider.setMaximum(1000)
		self.flank_slider.setPageStep(1)
		self.flank_slider.valueChanged.connect(self.on_flank_moved)
		self.flank_slider.sliderReleased.connect(self.on_flank_changed)

		#flank value
		self.status_bar.addPermanentWidget(QLabel("Flank length:", self))
		self.flank_len = QLabel("100", self)
		self.status_bar.addPermanentWidget(self.flank_len)
		self.status_bar.addPermanentWidget(self.flank_slider, 1)

		#line number
		self.status_bar.addPermanentWidget(QLabel("Line:", self))
		self.line_number = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.line_number)

		#select columns
		self.status_bar.addPermanentWidget(QLabel("Select:", self))
		self.select_count = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.select_count)

	def set_sequence(self, seq="ATGCAAAGCCTTTG", start=1456789):
		seq = "ATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTGATGCAAAGCCTTTG"
		self.editor.setPlainText(seq)
		self.editor.set_locus_position(start, len(seq))
		self.editor.add_format()
		self.editor.update_line_number_area_width(0)

	@Slot(int)
	def on_flank_moved(self, pos):
		self.flank_len.setText(str(pos))

	@Slot()
	def on_flank_changed(self):
		print(self.flank_slider.value())

if __name__ == '__main__':
	import sys
	app = QApplication(sys.argv)
	QFontDatabase.addApplicationFont("fonts/robotomono.ttf")
	win = SequenceDialog()
	#win.set_sequence()
	win.show()
	sys.exit(app.exec())