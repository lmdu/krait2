import pyfastx

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from backend import *

__all__ = ['KraitAlignmentViewer']

def create_matrix(n, m):
	d = []
	for i in range(n+1):
		d.append([])

		for j in range(m+1):
			d[i].append(0)

	for i in range(n+1):
		d[i][0] = i

	for j in range(m+1):
		d[0][j] = j

	return d

def wrap_around_distance(b, s, i, d):
	m = len(s)

	c = int(not b == s[0])
	d[i][1] = min(d[i-1][0]+c, d[i-1][m]+c, d[i-1][1]+1)

	for j in range(2, m+1):
		c = int( not b == s[j-1])
		d[i][j] = min(d[i-1][j-1]+c, d[i][j-1]+1, d[i-1][j]+1)

	d[i][1] = min(d[i][1], d[i][m]+1)

	for j in range(2, m):
		d[i][j] = min(d[i][j], d[i][j-1]+1)

	return d[i][m] > d[i-1][m]

def wrap_around_extend(s, ms, dr):
	mx = create_matrix(len(s), len(ms))
	n = len(s)

	if dr == -1:
		ms = ms[::-1]
		st = n
	else:
		st = -1

	for i in range(1, n+1):
		wrap_around_distance(s[st+i*dr], ms, i, mx)

	return mx

def wrap_around_backtrace(mx, s, ms, dr):
	j = m = len(ms)
	i = len(s)

	if dr == -1:
		ms = ms[::-1]
		s = s[::-1]

	origin = []
	perfect = []

	while i > 0 or j > 0:
		if i > 0 and j > 0 and j < m:
			if j == 1:
				if mx[i][j] == mx[i][m] + 1:
					#deletion
					origin.append('-')
					perfect.append(ms[j-1])

					j = m
					continue
			else:
				if mx[i][j] == mx[i][j-1] + 1:
					#deletion
					origin.append('-')
					perfect.append(ms[j-1])

					j -= 1
					continue

		elif i == 0:
			#deletion
			origin.append('-')
			perfect.append(ms[j-1])

			j -= 1
			continue

		if j == 1:
			v = min(mx[i-1][m], mx[i-1][0], mx[i-1][1])

			if v == mx[i-1][m]:
				#match and mismatch
				origin.append(s[i-1])
				perfect.append(ms[j-1])

				i -= 1
				j = m
			elif v == mx[i-1][0]:
				#match and mismatch
				origin.append(s[i-1])
				perfect.append(ms[j-1])

				i -= 1
				j -= 1
			elif v == mx[i-1][1]:
				#insertion
				origin.append(s[i-1])
				perfect.append('-')

				i -= 1
		else:
			v = min(mx[i-1][j-1], mx[i-1][j], mx[i][j-1])

			if v == mx[i-1][j-1]:
				#match and mismatch
				origin.append(s[i-1])
				perfect.append(ms[j-1])

				i -= 1
				j -= 1
			elif v == mx[i-1][j]:
				#insertion
				origin.append(s[i-1])
				perfect.append('-')

				i -= 1
			elif v == mx[i][j-1]:
				#deletion
				origin.append('-')
				perfect.append(ms[j-1])

				j -= 1

	if dr == 1:
		origin.reverse()
		perfect.reverse()

	#return eds
	return (''.join(origin), ''.join(perfect))

def generate_alignment_pattern(seqs):
	origin, perfect = seqs
	patterns = []
	template = (
		'<td class="B">'
		'<span>{}</span><br>'
		'<span class="{}">{}</span><br>'
		'<span>{}</span><br>'
		'<span class="{}">{}</span>'
		'</td>'
	)

	for i in range(len(origin)):
		ob = origin[i]
		pb = perfect[i]

		align = ''

		if origin[i] == perfect[i]:
			mtype = ''
			align = '|'
		elif origin[i] == '-':
			mtype = 'd'
		elif perfect[i] == '-':
			mtype = 'i'
		else:
			mtype = 's'

		patterns.append(template.format(mtype, ob, ob, align, pb, pb))

	return patterns

def generate_alignment_sequence(left, seq, right, motif, num):
	patterns = []

	if left:
		mx = wrap_around_extend(left, motif, -1)
		seqs = wrap_around_backtrace(mx, left, motif, -1)
		patterns += generate_alignment_pattern(seqs)

	patterns += generate_alignment_pattern((seq, seq))

	if right:
		mx = wrap_around_extend(right, motif, 1)
		seqs = wrap_around_backtrace(mx, right, motif, 1)
		patterns += generate_alignment_pattern(seqs)

	rows = ['<tr>']

	for i, p in enumerate(patterns, 1):
		rows.append(p)

		if i % num == 0:
			rows.append('</tr><tr>')

	rows.append('</tr>')

	return ''.join(rows)

class KraitAlignmentViewer(QTextBrowser):
	def __init__(self, parent=None):
		super().__init__(parent)

		font = QFont("Roboto Mono")
		font.setPointSize(10)
		self.setFont(font)

		self.target = None

	def update_alignment(self):
		ww = self.width()
		fw = self.fontMetrics().averageCharWidth() * 2
		mw = self.contentsMargins()
		num = int((ww - mw.left() - mw.right()) / fw)

		patterns = generate_alignment_sequence(*self.target, num)
		#content = "<table>{}</table>".format(patterns)
		content = """
		<html>
			<head>
				<style>
					*{{
						margin: 0;
						padding: 0;
					}}
					.B{{
						white-space: pre-line;
						text-align: center;
						display: inline-block;
					}}
					.A{{color:#5050ff;}}
					.T{{color:#ffd700;}}
					.G{{color:#00c000;}}
					.C{{color:#f40000;}}
				</style>
			</head>
			<body>
				<table boder="0" cellpadding="0" cellspacing="0">{}</table>
			</body>
		</html>

		""".format(patterns)
		self.setHtml(content)

		with open('report.html', 'w') as fw:
			print(content, file=fw)

	#def resizeEvent(self, event):
	#	super().resizeEvent(event)

	#	if not self.target:
	#		return

	#	if event.oldSize().width() == event.size().width():
	#		return

	#	self.update_alignment()

	def mark_alignment(self, findex, issr):
		sql = "SELECT * FROM fastx WHERE id=? LIMIT 1"
		fastx = DB.get_object(sql, (findex,))

		if fastx.format == 'fasta':
			fastx_file = pyfastx.Fasta(fastx.fpath, uppercase=True)
		else:
			fastx_file = pyfastx.Fastq(fastx.fpath)

		left = fastx_file[issr.chrom][issr.start-1:issr.sstart-1].seq
		seq = fastx_file[issr.chrom][issr.sstart-1:issr.send].seq
		right = fastx_file[issr.chrom][issr.send:issr.end].seq
		self.target = (left, seq, right, issr.motif)
		self.update_alignment()







if __name__ == '__main__':
	seq = "ATGACGATGAGACTG"
	motif = "ATG"
	mx = wrap_around_extend(seq, motif, 1)

	for row in mx:
		print(row)

	origin, perfect = wrap_around_backtrace(mx, seq, motif, 1)
	
	for row in generate_alignment_pattern((origin, perfect)):
		print(row)
		