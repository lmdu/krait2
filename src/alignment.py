import pyfastx

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

__all__ = ['generate_alignment_sequence']

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
		"<span>{}</span>\n"
		"<span>{}</span>\n"
		"<span>{}</span>\n"
		"<span>{}</span>\n"
	)

	for i in range(len(origin)):
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

		patterns.append(template.format(mtype, origin[i], align, perfect[i]))

	return patterns

def generate_alignment_sequence(left, seq, right, motif):
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

	return ''.join(patterns)

class KraitAlignmentViewer(QTextBrowser):
	def __init__(self, parent=None):
		super().__init__(parent)

	def mark_alignment(self, file, issr):
		fa = pyfastx.Fasta(file, uppercase=True)
		left = fa[issr.chrom][start-1:issr.sstart].seq
		seq = fa[issr.chrom][issr.sstart-1:issr.send].seq
		right = fa[issr.chrom][issr]





if __name__ == '__main__':
	seq = "ATGACGATGAGACTG"
	motif = "ATG"
	mx = wrap_around_extend(seq, motif, 1)

	for row in mx:
		print(row)

	origin, perfect = wrap_around_backtrace(mx, seq, motif, 1)
	
	for row in generate_alignment_pattern((origin, perfect)):
		print(row)
		