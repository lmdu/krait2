import json
import jinja2
import pyfastx

from PySide6.QtCore import *

from config import *
from backend import *

__all__ = [
	'KraitSTRStatistics', 'KraitCSSRStatistics',
	'KraitISSRStatistics', 'KraitGTRStatistics',
	'KraitExportStatistics'
]

class KraitBaseStatistics:
	_size = None
	rep_cat = 1
	motif_col = 5
	type_col = 6
	rep_col = 7
	len_col = 8
	title = None
	stype = None

	def __init__(self, repeats, annots, fastx, unit):
		self.repeats = repeats
		self.annots = annots
		self.fastx = fastx
		self.unit = unit

		self.total_counts = 0
		self.total_length = 0

		self.result_stats = {}

		self.type_stats = {}
		self.motif_stats = {}
		self.repeat_stats = {}
		self.length_stats = {}
		self.annot_stats = {}

		self.do_calculate()
		self.do_annotation()
		self.do_statistics()

	def do_calculate(self):
		pass

	def do_annotation(self):
		pass

	def do_statistics(self):
		pass

	def get_type(self, i):
		return ['', 'Mono', 'Di', 'Tri', 'Tetra', 'Penta', 'Hexa'][i]

	def get_feature(self, i):
		return ['Intergenic', 'CDS', 'Exon', '3UTR', 'UTR', '5UTR', 'Intron'][i]

	@property
	def size(self):
		return self.fastx['size']

	@property
	def uname(self):
		return ['Mb', 'Kb'][self.unit]

	@property
	def transize(self):
		if self._size is None:
			scales = [1000000, 1000]
			self._size = self.fastx['size'] / scales[self.unit]
		return self._size

	def scale(self, num):
		return round(num/self.transize, 2)

	def average(self, length, count):
		if not count:
			return 0

		return round(length/count, 2)

	def coverage(self, length):
		return round(length/self.size*100, 2)

	def percent(self, num, total):
		return round(num/total*100, 2)

	"""
	@classmethod
	def get_reports(cls, repeats, fastx, unit):
		stats = cls(repeats, fastx, unit)
		json_str = stats.json()
		html_str = stats.html()
		return json_str, html_str
	"""

	def json(self):
		return json.dumps(self.result_stats)

	def summary_table(self):
		return """
		<div class="row">
			<div class="col">
				<h3>{}</h3>
				<h4 class="mt-3">Summary statistics</h4>
				<table class="table" cellspacing="0" align="center" cellpadding="10" width="98%">
					<thead>
						<tr>
							<th>Total counts</th>
							<th>Total length (bp)</th>
							<th>Average length (bp)</th>
							<th>Sequence coverage (%)</th>
							<th>Relative abundance (loci/{})</th>
							<th>Relative density (bp/{})</th>
						</tr>
					</thead>
					<tbody class="table-group-divider">
						<tr bgcolor="#f2f2f2">
							<td align="center">{}</td>
							<td align="center">{}</td>
							<td align="center">{}</td>
							<td align="center">{}</td>
							<td align="center">{}</td>
							<td align="center">{}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
		""".format(
			self.title,
			self.uname,
			self.uname,
			self.result_stats['total_counts'],
			self.result_stats['total_length'],
			self.result_stats['average_length'],
			self.result_stats['coverage'],
			self.result_stats['frequency'],
			self.result_stats['density']
		)

	def cssr_table(self):
		return """
		<div class="row mt-3">
			<div class="col">
				<h4 class="mt-3">Summary statistics</h4>
				<table class="table" cellspacing="0" align="center" cellpadding="10" width="98%" class="mt-3">
					<thead>
						<tr>
							<th></th>
							<th>Counts</th>
						</tr>
					</thead>
					<tbody class="table-group-divider">
						<tr bgcolor="#f2f2f2">
							<th>Total number of individual microsatellites forming compound microsatellites</th>
							<td align="center">{}</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>
		""".format(self.result_stats['total_cssrs'])

	def meta(self):
		heads = {
			'type_stats': "Motif type statistics",
			'annot_stats': "Annotation statistics"
		}

		titles = [
			('type_stats', ["Motif type"]),
			('annot_stats', ["Feature"])
		]

		tables = []
		tables.append(self.summary_table())

		if 'total_cssrs' in self.result_stats:
			tables.append(self.cssr_table())

		for k, title in titles:
			if k not in self.result_stats:
				continue

			if not self.result_stats[k]:
				continue

			table = ['''<div class="row mt-3"><div class="col"><h4>{}</h4>\n'''.format(heads[k])]
			table.append('''<table class="table" cellspacing="0" align="center" cellpadding="10" width="98%">\n''')
			title.extend(["Total count", "Total length (bp)", "Percentage (%)", "Average length (bp)",
				"Frequency (loci/{})".format(self.uname), "Density (bp/{})".format(self.uname)])

			table.append('''<thead>\n<tr>{}</tr>\n</thead>\n<tbody class="table-group-divider">\n'''.format(
				''.join("<th>{}</th>\n".format(t) for t in title)))

			i = 0
			for row in self.result_stats[k]:
				i += 1
				color = ['white', '#f2f2f2'][i%2]
				datas = ''.join('''<td align="center">{}</td>\n'''.format(col) for col in row)
				table.append('''<tr bgcolor="{}">{}</tr>\n'''.format(color, datas))

			table.append("</tbody>\n</table>\n</div>\n</div>\n")
			tables.append('\n'.join(table))

		return '\n'.join(tables)

	def html(self):
		heads = {
			'type_stats': "Motif type statistics",
			'annot_stats': "Annotation statistics",
			'motif_stats': "Motif statistics",
			'repeat_stats': "Repeat statistics",
			'length_stats': "Length statistics",
			'complex_stats': "Complexity statistics"
		}

		titles = [
			('type_stats', ["Motif type"]),
			('annot_stats', ["Feature"]),
			('motif_stats', ["Motif"]),
			('repeat_stats', ["Motif type", "Repeat"]),
			('length_stats', ["Motif type", "Length"]),
			('complex_stats', ["Complexity"])
		]

		tables = []
		tables.append(self.summary_table())

		if 'total_cssrs' in self.result_stats:
			tables.append(self.cssr_table())

		for k, title in titles:
			if k not in self.result_stats:
				continue

			if not self.result_stats[k]:
				continue

			table = ['''<div class="row mt-3"><div class="col"><h4>{}</h4>\n'''.format(heads[k])]
			table.append('''<table class="table" cellspacing="0" align="center" cellpadding="10" width="98%">\n''')
			title.extend(["Total count", "Total length (bp)", "Percentage (%)", "Average length (bp)",
				"Frequency (loci/{})".format(self.uname), "Density (bp/{})".format(self.uname)])

			table.append('''<thead>\n<tr>{}</tr>\n</thead>\n<tbody class="table-group-divider">\n'''.format(
				''.join("<th>{}</th>\n".format(t) for t in title)))

			i = 0
			for row in self.result_stats[k]:
				i += 1
				color = ['white', '#f2f2f2'][i%2]
				datas = ''.join('''<td align="center">{}</td>\n'''.format(col) for col in row)
				table.append('''<tr bgcolor="{}">{}</tr>\n'''.format(color, datas))

			table.append("</tbody>\n</table>\n</div>\n</div>\n")
			tables.append('\n'.join(table))

			if k == 'type_stats':
				tables.append('''
				<div class="row mt-3">
					<div class="col-4">
						<div id="{cat}-count-pie-{idx}"></div>
					</div>
					<div class="col-4">
						<div id="{cat}-length-pie-{idx}"></div>
					</div>
					<div class="col-4">
						<div id="{cat}-annot-pie-{idx}"></div>
					</div>
				</div>
				'''.format(
					cat = self.stype,
					idx = self.fastx['id']
				))

			elif k == 'motif_stats':
				tables.append('''
				<div class="row mt-3">
					<div class="col-12">
						<div id="{cat}-motif-bar-{idx}"></div>
					</div>
				</div>
				'''.format(
					cat = self.stype,
					idx = self.fastx['id']
				))

			elif k == 'repeat_stats':
				tables.append('''
				<div class="row mt-3">
					<div class="col-12">
						<div id="{cat}-repeat-line-{idx}"></div>
					</div>
				</div>
				'''.format(
					cat = self.stype,
					idx = self.fastx['id']
				))

			elif k == 'length_stats':
				tables.append('''
				<div class="row mt-3">
					<div class="col-12">
						<div id="{cat}-length-line-{idx}"></div>
					</div>
				</div>
				'''.format(
					cat = self.stype,
					idx = self.fastx['id']
				))

		return '\n'.join(tables)

	def plot(self):
		plots = []

		if 'type_stats' in self.result_stats and self.result_stats['type_stats']:
			names = []
			counts = []
			lengths = []

			for row in self.result_stats['type_stats']:
				names.append(row[0])
				counts.append(row[1])
				lengths.append(row[2])

			plots.append("""
				Plotly.newPlot('{cat}-count-pie-{idx}', [{{
					type: 'pie',
					values: [{counts}],
					labels: [{names}]
				}}], {{
					title: "{cat} count distribution",
					font: {{size: 14}}
				}}, {{
					responsive: true
				}});

				Plotly.newPlot('{cat}-length-pie-{idx}', [{{
					type: 'pie',
					values: [{lengths}],
					labels: [{names}]
				}}], {{
					title: "{cat} length distribution",
					font: {{size: 14}}
				}}, {{
					responsive: true
				}});
			""".format(
				cat = self.stype,
				idx = self.fastx['id'],
				names = ','.join("'{}'".format(n) for n in names),
				counts = ','.join(map(str, counts)),
				lengths = ','.join(map(str, lengths))
			))

		if 'annot_stats' in self.result_stats and self.result_stats['annot_stats']:
			names = []
			counts = []

			for row in self.result_stats['annot_stats']:
				names.append(row[0])
				counts.append(row[1])

			plots.append("""
				Plotly.newPlot('{cat}-annot-pie-{idx}', [{{
					type: 'pie',
					values: [{counts}],
					labels: [{names}]
				}}], {{
					title: "{cat} distribution in different regions",
					font: {{size: 14}}
				}}, {{
					responsive: true
				}});
			""".format(
				cat = self.stype,
				idx = self.fastx['id'],
				names = ','.join("'{}'".format(n) for n in names),
				counts = ','.join(map(str, counts))
			))

		if 'motif_stats' in self.result_stats and self.result_stats['motif_stats']:
			motifs = []
			counts = []

			for row in sorted(self.result_stats['motif_stats'], key=lambda x: (len(x[1]), -x[2])):
				motifs.append(row[1])
				counts.append(row[6])

			plots.append("""
				Plotly.newPlot('{cat}-motif-bar-{idx}', [{{
					type: 'bar',
					y: [{counts}],
					x: [{motifs}]
				}}], {{
					title: "{cat} motif distribution",
					font: {{size: 14}},
					yaxis: {{
						title: {{
							text: "{ylab}"
						}}
					}}
				}}, {{
					responsive: true
				}});
			""".format(
				cat = self.stype,
				idx = self.fastx['id'],
				motifs = ','.join("'{}'".format(n) for n in motifs),
				counts = ','.join(map(str, counts)),
				ylab = "Frequency (loci/{})".format(self.uname)
			))

		if 'repeat_stats' in self.result_stats and self.result_stats['repeat_stats']:
			datasets = {}
			for row in self.result_stats['repeat_stats']:
				if row[0] not in datasets:
					datasets[row[0]] = []
				datasets[row[0]].append((row[1], row[6]))

			data = []
			for t in datasets:
				xs = []
				ys = []
				for x, y in sorted(datasets[t]):
					xs.append(x)
					ys.append(y)

				data.append({
					'name': t,
					'mode': 'lines+markers',
					'x': xs,
					'y': ys
				})

			plots.append("""
				Plotly.newPlot('{cat}-repeat-line-{idx}', {data}, {{
					title: "{cat} repeat distribution",
					font: {{size: 14}},
					yaxis: {{
						title: {{
							text: "{ylab}"
						}}
					}},
					xaxis: {{
						title: {{
							text: "Repeat number"
						}}
					}}
				}}, {{
					responsive: true
				}});
			""".format(
				cat = self.stype,
				idx = self.fastx['id'],
				data = json.dumps(data),
				motifs = ','.join("'{}'".format(n) for n in motifs),
				counts = ','.join(map(str, counts)),
				ylab = "Frequency (loci/{})".format(self.uname)
			))

		if 'length_stats' in self.result_stats and self.result_stats['length_stats']:
			datasets = {}
			for row in self.result_stats['length_stats']:
				if row[0] not in datasets:
					datasets[row[0]] = []
				datasets[row[0]].append((row[1], row[6]))

			data = []
			for t in datasets:
				xs = []
				ys = []
				for x, y in sorted(datasets[t]):
					xs.append(x)
					ys.append(y)

				data.append({
					'name': t,
					'mode': 'lines+markers',
					'x': xs,
					'y': ys
				})

			plots.append("""
				Plotly.newPlot('{cat}-length-line-{idx}', {data}, {{
					title: "{cat} length distribution",
					font: {{size: 14}},
					yaxis: {{
						title: {{
							text: "{ylab}"
						}}
					}},
					xaxis: {{
						title: {{
							text: "Length"
						}}
					}}
				}}, {{
					responsive: true
				}});
			""".format(
				cat = self.stype,
				idx = self.fastx['id'],
				data = json.dumps(data),
				motifs = ','.join("'{}'".format(n) for n in motifs),
				counts = ','.join(map(str, counts)),
				ylab = "Frequency (loci/{})".format(self.uname)
			))

		return '\n'.join(plots)

class KraitSTRStatistics(KraitBaseStatistics):
	title = "Perfect microsatellite"
	stype = 'ssr'

	def do_calculate(self):
		self.total_counts = len(self.repeats)
		self.total_length = 0

		m = self.motif_col
		t = self.type_col
		r = self.rep_col
		l = self.len_col

		for s in self.repeats:
			self.total_length += s[l]

			if s[t] not in self.type_stats:
				self.type_stats[s[t]] = [0, 0]

			self.type_stats[s[t]][0] += 1
			self.type_stats[s[t]][1] += s[l]

			#if s[m] not in self.motif_stats:
			#	self.motif_stats[s[m]] = [0, 0]

			#self.motif_stats[s[m]][0] += 1
			#self.motif_stats[s[m]][1] += s[l]

			if s[t] not in self.repeat_stats:
				self.motif_stats[s[t]] = {}
				self.repeat_stats[s[t]] = {}
				self.length_stats[s[t]] = {}

			if s[m] not in self.motif_stats[s[t]]:
				self.motif_stats[s[t]][s[m]] = [0, 0]

			if s[r] not in self.repeat_stats[s[t]]:
				self.repeat_stats[s[t]][s[r]] = [0, 0]

			if s[l] not in self.length_stats[s[t]]:
				self.length_stats[s[t]][s[l]] = [0, 0]

			self.motif_stats[s[t]][s[m]][0] += 1
			self.motif_stats[s[t]][s[m]][1] += s[l]

			self.repeat_stats[s[t]][s[r]][0] += 1
			self.repeat_stats[s[t]][s[r]][1] += s[l]

			self.length_stats[s[t]][s[l]][0] += 1
			self.length_stats[s[t]][s[l]][1] += s[l]

	def do_annotation(self):
		tc = 0
		tl = 0
		l = self.len_col
		for a in self.annots:
			if a[1] != self.rep_cat:
				continue

			if a[3] not in self.annot_stats:
				self.annot_stats[a[3]] = [0, 0]

			self.annot_stats[a[3]][0] += 1
			self.annot_stats[a[3]][1] += self.repeats[a[2]-1][l]

			tc += 1
			tl += self.repeats[a[2]-1][l]

		if self.annot_stats:
			self.annot_stats[0] = [self.total_counts-tc, self.total_length-tl]

	def do_statistics(self):
		self.result_stats['total_counts'] = self.total_counts
		self.result_stats['total_length'] = self.total_length
		self.result_stats['average_length'] = self.average(self.total_length, self.total_counts)
		self.result_stats['coverage'] = self.coverage(self.total_length)
		self.result_stats['frequency'] = self.scale(self.total_counts)
		self.result_stats['density'] = self.scale(self.total_length)
		self.result_stats['unit'] = self.uname

		self.result_stats['type_stats'] = []
		for t in sorted(self.type_stats):
			self.result_stats['type_stats'].append((
				self.get_type(t),
				self.type_stats[t][0],
				self.type_stats[t][1],
				self.percent(self.type_stats[t][0], self.total_counts),
				self.average(self.type_stats[t][1], self.type_stats[t][0]),
				self.scale(self.type_stats[t][0]),
				self.scale(self.type_stats[t][1])
			))

		self.result_stats['motif_stats'] = []
		for t in sorted(self.motif_stats):
			for m in sorted(self.motif_stats[t]):
				self.result_stats['motif_stats'].append((self.get_type(t), m,
					self.motif_stats[t][m][0],
					self.motif_stats[t][m][1],
					self.percent(self.motif_stats[t][m][0], self.total_counts),
					self.average(self.motif_stats[t][m][1], self.motif_stats[t][m][0]),
					self.scale(self.motif_stats[t][m][0]),
					self.scale(self.motif_stats[t][m][1])
				))

		self.result_stats['repeat_stats'] = []
		for t in sorted(self.repeat_stats):
			for r in sorted(self.repeat_stats[t]):
				self.result_stats['repeat_stats'].append((self.get_type(t), r,
					self.repeat_stats[t][r][0],
					self.repeat_stats[t][r][1],
					self.percent(self.repeat_stats[t][r][0], self.total_counts),
					self.average(self.repeat_stats[t][r][1], self.repeat_stats[t][r][0]),
					self.scale(self.repeat_stats[t][r][0]),
					self.scale(self.repeat_stats[t][r][1])
				))

		self.result_stats['length_stats'] = []
		for t in sorted(self.length_stats):
			for l in sorted(self.length_stats[t]):
				self.result_stats['length_stats'].append((self.get_type(t), l,
					self.length_stats[t][l][0],
					self.length_stats[t][l][1],
					self.percent(self.length_stats[t][l][0], self.total_counts),
					self.average(self.length_stats[t][l][1], self.length_stats[t][l][0]),
					self.scale(self.length_stats[t][l][0]),
					self.scale(self.length_stats[t][l][1])
				))

		self.result_stats['annot_stats'] = []
		for a in sorted(self.annot_stats):
			self.result_stats['annot_stats'].append((
				self.get_feature(a),
				self.annot_stats[a][0],
				self.annot_stats[a][1],
				self.percent(self.annot_stats[a][0], self.total_counts),
				self.average(self.annot_stats[a][1], self.annot_stats[a][0]),
				self.scale(self.annot_stats[a][0]),
				self.scale(self.annot_stats[a][1])
			))

class KraitCSSRStatistics(KraitBaseStatistics):
	rep_cat = 2
	len_col = 5
	title = "Compound microsatellite"
	stype = 'cssr'

	def do_calculate(self):
		self.total_counts = len(self.repeats)
		self.total_length = 0
		self.total_cssrs = 0
		self.complex_stats = {}

		for s in self.repeats:
			self.total_length += s[5]
			self.total_cssrs += s[4]

			if s[4] not in self.complex_stats:
				self.complex_stats[s[4]] = [0, 0]

			self.complex_stats[s[4]][0] += 1
			self.complex_stats[s[4]][1] += s[5]

	def do_statistics(self):
		self.result_stats['total_counts'] = self.total_counts
		self.result_stats['total_length'] = self.total_length
		self.result_stats['total_cssrs'] = self.total_cssrs
		self.result_stats['average_length'] = self.average(self.total_length, self.total_counts)
		self.result_stats['coverage'] = self.coverage(self.total_length)
		self.result_stats['frequency'] = self.scale(self.total_counts)
		self.result_stats['density'] = self.scale(self.total_length)
		self.result_stats['unit'] = self.uname

		self.result_stats['complex_stats'] = []
		for c in sorted(self.complex_stats):
			self.result_stats['complex_stats'].append((
				c,
				self.complex_stats[c][0],
				self.complex_stats[c][1],
				self.percent(self.complex_stats[c][0], self.total_counts),
				self.average(self.complex_stats[c][1], self.complex_stats[c][0]),
				self.scale(self.complex_stats[c][0]),
				self.scale(self.complex_stats[c][1])
			))

class KraitGTRStatistics(KraitSTRStatistics):
	rep_cat = 3
	motif_col = 7
	type_col = 4
	rep_col = 5
	len_col = 6
	title = "Generic tandem repeat"
	stype = 'gtr'

	def get_type(self, i):
		return i

class KraitISSRStatistics(KraitSTRStatistics):
	rep_cat = 4
	title = "Imperfect microsatellite"
	stype = 'issr'

class KraitExportStatistics:
	def __init__(self):
		self.uname = 'Mb'
		self.fastx_files = [f for f in DB.get_objects("SELECT * FROM fastx")]
		self.fastx_datas = []
		sql = "SELECT type,json FROM stats_{}"

		for fastx_file in self.fastx_files:
			res = DB.get_objects(sql.format(fastx_file.id))
			self.fastx_datas.append({r.type: json.loads(r.json) for r in res})

	def get_style_css(self):
		css_files = [
			":/scripts/tabler.min.css",
			":/scripts/datatables.min.css"
		]

		styles = []
		for css_file in css_files:
			f = QFile(css_file)
			text = None

			if f.open(QIODevice.ReadOnly | QFile.Text):
				text = QTextStream(f).readAll()

			f.close()

			if text:
				styles.append(text)

		return '\n'.join(styles)

	def get_script_js(self):
		js_files = [
			":/scripts/tabler.min.js",
			":/scripts/datatables.min.js",
			":/scripts/echarts.min.js"
		]

		js = []
		for js_file in js_files:
			f = QFile(js_file)
			text = None

			if f.open(QIODevice.ReadOnly | QFile.Text):
				text = QTextStream(f).readAll()

			f.close()

			if text:
				js.append(text)

		return '\n'.join(js)

	def get_file_summary_table(self):
		rows = []

		for f in self.fastx_files:
			rows.append([
				f.id,
				f.name,
				f.format,
				f.size,
				f.count,
				round(f.gc, 2),
				f.ns,
				f.avglen,
				f.minlen,
				f.maxlen
			])

		return {'input-file-table': rows}

	def get_repeat_summary_table(self, rtype, fastx, data):
		rtype = rtype.split('_')[0]
		tid = '{}-summary-table-{}'.format(rtype, fastx)
		self.uname = data['unit']
		return {tid: [[
			data['total_counts'],
			data['total_length'],
			data['average_length'],
			data['coverage'],
			data['frequency'],
			data['density']
		]]}

	def get_cssr_summary_table(self, fastx, data):
		tid = 'cssr-total-table-{}'.format(fastx)
		return {tid: [["Total number of individual microsatellites forming compound microsatellites", data['total_cssrs']]]}

	def get_repeat_detail_table(self, rtype, stype, fastx, data):
		rtype = rtype.split('_')[0]
		stype = stype.split('_')[0]
		tid = '{}-{}-table-{}'.format(rtype, stype, fastx)
		return {tid: data}

	def get_stats_tables(self):
		stats = ['type_stats', 'annot_stats', 'motif_stats',
			'repeat_stats', 'length_stats', 'complex_stats'
		]

		tables = {}
		tables.update(self.get_file_summary_table())

		for i, f in enumerate(self.fastx_files):
			datas = self.fastx_datas[i]

			for k, data in datas.items():
				if k == 'cssr_stats':
					tables.update(self.get_cssr_summary_table(f.id, data))
				
				tables.update(self.get_repeat_summary_table(k, f.id, data))
				
				for s in stats:
					if s in data and data[s]:
						tables.update(self.get_repeat_detail_table(k, s, f.id, data[s]))

		return tables

	def draw_pie_plot(self, pid, title, name, data):
		pvar = pid.replace('-', '_')
		return """
			var {pvar} = echarts.init(document.getElementById('{pid}'));
			{pvar}.setOption({{
				title: {{
					text: "{title}"
				}},
				tooltip: {{
					trigger: 'item',
					formatter: '{{b}}<br>{{c}}, {{d}}%'
				}},
				toolbox: {{
					show: true,
					feature: {{
						dataView: {{readOnly: true}},
						saveAsImage: {{}}
					}}
				}},
				series: [{{
					name: "{name}",
					type: 'pie',
					radius: ['40%', '70%'],
					label: {{
						show: true,
					}},
					emphasis: {{
						label: {{
							show: true,
							fontSize: 32,
							fontWeight: 'bold'
						}}
					}},
					data: {data}
				}}]
			}});
			window.addEventListener('resize', function(){{
				{pvar}.resize();
			}});
		""".format(pvar=pvar, pid=pid, title=title, name=name, data=data)

	def draw_bar_plot(self, pid, title, datasets):
		pvar = pid.replace('-', '_')
		return """
			var {pvar}_source = {datasets};

			var {pvar}_height = $('<input>', {{id: '{pvar}-height'}}).prependTo($('#{pid}').parent());
			{pvar}_height.attr('value', 400).attr('type', 'number');
			$('<span>').addClass('ms-3').text('Plot height:').prependTo($('#{pid}').parent());

			var {pvar}_select = $('<select>', {{id: '{pvar}-select'}}).prependTo($('#{pid}').parent());
			for (key in {pvar}_source) {{
				{pvar}_select.append($("<option>").attr('value', key).text(key));
			}}
			$('<span>').text('Data type:').prependTo($('#{pid}').parent());

			var {pvar} = echarts.init(document.getElementById('{pid}'));
			var {pvar}_option = {{
				title: {{
					text: "{title}"
				}},
				tooltip: {{
					trigger: 'item'
				}},
				legend: {{}},
				toolbox: {{
					show: true,
					feature: {{
						dataView: {{readOnly: true}},
						saveAsImage: {{}}
					}}
				}},
				xAxis: {{
					type: 'category',
					axisLabel: {{
						rotate: 30
					}}
				}},
				yAxis: {{
					type: 'value',
					name: "SSR count",
					nameGap: 50,
					nameLocation: 'center',
					nameTextStyle: {{
						fontSize: 16,
					}}
				}},
				series: {pvar}_source[Object.keys({pvar}_source)[0]]
			}};

			{pvar}.setOption({pvar}_option);
			{pvar}_select.on('change', function() {{
				{pvar}_option.series = {pvar}_source[this.value];
				{pvar}_option.yAxis.name = this.value;
				{pvar}.setOption({pvar}_option);
			}});
			{pvar}_height.on('change', function(){{
				$('#{pid}').height(this.value);
				window.dispatchEvent(new Event('resize'));
			}});

			window.addEventListener('resize', function(){{
				{pvar}.resize();
			}});
		""".format(pvar=pvar, pid=pid, title=title, datasets=datasets)

	def draw_line_plot(self, pid, title, xlab, datasets):
		pvar = pid.replace('-', '_')
		return """
			var {pvar}_source = {datasets};

			var {pvar}_height = $('<input>', {{id: '{pvar}-height'}}).prependTo($('#{pid}').parent());
			{pvar}_height.attr('value', 400).attr('type', 'number');
			$('<span>').addClass('ms-3').text('Plot height:').prependTo($('#{pid}').parent());

			var {pvar}_select = $('<select>', {{id: '{pvar}-select'}}).prependTo($('#{pid}').parent());
			for (key in {pvar}_source) {{
				{pvar}_select.append($("<option>").attr('value', key).text(key));
			}}
			$('<span>').text('Data type:').prependTo($('#{pid}').parent());

			var {pvar} = echarts.init(document.getElementById('{pid}'));

			var {pvar}_option = {{
				title: {{
					text: "{title}"
				}},
				tooltip: {{
					trigger: 'item'
				}},
				toolbox: {{
					show: true,
					feature: {{
						dataView: {{readOnly: true}},
						saveAsImage: {{}}
					}}
				}},
				legend: {{}},
				xAxis: {{
					name: "{xlab}",
					nameLocation: 'center'
				}},
				yAxis: {{
					name: "SSR count",
					nameLocation: 'center',
					nameGap: 50,
					nameLocation: 'center',
					nameTextStyle: {{
						fontSize: 16,
					}}
				}},
				series: {pvar}_source[Object.keys({pvar}_source)[0]]
			}};

			{pvar}.setOption({pvar}_option);
			{pvar}_select.on('change', function() {{
				{pvar}_option.series = {pvar}_source[this.value];
				{pvar}_option.yAxis.name = this.value;
				{pvar}.setOption({pvar}_option);
			}});
			{pvar}_height.on('change', function(){{
				$('#{pid}').height(this.value);
				window.dispatchEvent(new Event('resize'));
			}});

			window.addEventListener('resize', function(){{
				{pvar}.resize();
			}});
		""".format(pvar=pvar, pid=pid, title=title, datasets=datasets, xlab=xlab)

	def get_stats_plots(self):
		plots = {}

		for i, f in enumerate(self.fastx_files):
			datas = self.fastx_datas[i]

			for k, datai in datas.items():
				rtype = k.split('_')[0]

				for s in datai:
					if s == 'type_stats':
						counts = []
						lengths = []

						for row in datai[s]:
							counts.append({'value': row[1], 'name': row[0]})
							lengths.append({'value': row[2], 'name': row[0]})

						pid = "{}-count-pie-{}".format(rtype, f.id)
						title = "{} count distribution".format(rtype)
						name = "{} count".format(rtype)
						plots[pid] = self.draw_pie_plot(pid, title, name, counts)

						pid = "{}-length-pie-{}".format(rtype, f.id)
						title = "{} length distribution".format(rtype)
						name = "{} length".format(rtype)
						plots[pid] = self.draw_pie_plot(pid, title, name, counts)

					if s == 'annot_stats':
						counts = []

						for row in datai[s]:
							counts.append({'value': row[1], 'name': row[0]})

						if counts:
							pid = "{}-annot-pie-{}".format(rtype, f.id)
							title = "{} count in different gene regions".format(rtype)
							name = "{} annotation".format(rtype)
							plots[pid] = self.draw_pie_plot(pid, title, name, counts)

					if s == 'motif_stats':
						data_types = {
							'SSR count': 2,
							'SSR length': 3,
							'SSR frequency': 6,
							'SSR density': 7
						}
						
						motif_pdata = {}

						for dtype, dindex in data_types.items():
							datasets = {}
							for row in datai[s]:
								if row[0] not in datasets:
									datasets[row[0]] = []

								datasets[row[0]].append((row[1], row[dindex]))

							series = []
							for t in datasets:
								data = []
								for x, y in sorted(datasets[t]):
									data.append([x, y])

								series.append({
									'name': t,
									'type': 'bar',
									'stack': 'stack',
									'data': data,
								})

							motif_pdata[dtype] = series

						pid = "{}-motif-bar-{}".format(rtype, f.id)
						title = "{} motif distribution".format(rtype)
						plots[pid] = self.draw_bar_plot(pid, title, motif_pdata)

					if s == 'repeat_stats':
						data_types = {
							'SSR count': 2,
							'SSR length': 3,
							'SSR frequency': 6,
							'SSR density': 7
						}
						
						repeat_pdata = {}
						for dtype, dindex in data_types.items():
							datasets = {}
							for row in datai[s]:
								if row[0] not in datasets:
									datasets[row[0]] = []
								datasets[row[0]].append((row[1], row[dindex]))

							series = []
							for t in datasets:
								data = []
								for x, y in sorted(datasets[t]):
									data.append([x, y])

								series.append({
									'name': t,
									'type': 'line',
									'smooth': 1,
									'data': data,
								})

							repeat_pdata[dtype] = series

						pid = "{}-repeat-line-{}".format(rtype, f.id)
						title = "{} repeat distribution".format(rtype)
						xlab = "Repeat number"
						plots[pid] = self.draw_line_plot(pid, title, xlab, repeat_pdata)

					if s == 'length_stats':
						data_types = {
							'SSR count': 2,
							'SSR length': 3,
							'SSR frequency': 6,
							'SSR density': 7
						}
						
						repeat_pdata = {}
						for dtype, dindex in data_types.items():
							datasets = {}
							for row in datai[s]:
								if row[0] not in datasets:
									datasets[row[0]] = []
								datasets[row[0]].append((row[1], row[dindex]))

							series = []
							for t in datasets:
								data = []

								for x, y in sorted(datasets[t]):
									data.append([x, y])

								series.append({
									'name': t,
									'type': 'line',
									'smooth': 1,
									'data': data
								})

							repeat_pdata[dtype] = series

						pid = "{}-length-line-{}".format(rtype, f.id)
						title = "{} length distribution".format(rtype)
						xlab = "Length"
						plots[pid] = self.draw_line_plot(pid, title, xlab, repeat_pdata)

		return plots

	def draw_line_bar_mix_plot(self, pid, names, datasets):
		pvar = pid.replace('-', '_')
		return """
		var {pvar}_source = {datasets};

		var {pvar}_height = $('<input>', {{id: '{pvar}-height'}}).prependTo($('#{pid}').parent());
		{pvar}_height.attr('value', 400).attr('type', 'number');
		$('<span>').addClass('ms-3').text('Plot height:').prependTo($('#{pid}').parent());

		var {pvar}_select = $('<select>', {{id: '{pvar}-select'}}).prependTo($('#{pid}').parent());
		for (key in {pvar}_source) {{
			{pvar}_select.append($("<option>").attr('value', key).text(key));
		}}
		$('<span>').text('Data type:').prependTo($('#{pid}').parent());

		var {pvar} = echarts.init(document.getElementById('{pid}'));
		var {pvar}_option = {{
			tooltip: {{
				trigger: 'item'
			}},
			toolbox: {{
				show: true,
				feature: {{
					dataView: {{readOnly: true}},
					saveAsImage: {{}},
					magicType: {{
						type: ['bar', 'line']
					}},
				}}
			}},
			xAxis: {{
				type: 'category',
				data: {names},
				axisLabel: {{
					rotate: 30
				}}
			}},
			yAxis: {{
				type: 'value',
				name: Object.keys({pvar}_source)[0],
				nameGap: 50,
				nameLocation: 'center',
				nameTextStyle: {{
					color: '#000',
					fontSize: 16,
				}}
			}},
			series: [{{
				data: {pvar}_source[Object.keys({pvar}_source)[0]],
				type: 'bar'
			}}]
		}};
		{pvar}.setOption({pvar}_option);
		{pvar}_select.on('change', function() {{
			{pvar}_option.yAxis.name = this.value;
			{pvar}_option.series[0].data = {pvar}_source[this.value];
			{pvar}.setOption({pvar}_option);
		}});{pvar}_height.on('change', function(){{
			$('#{pid}').height(this.value);
			window.dispatchEvent(new Event('resize'));
		}});

		{pvar}_height.on('change', function(){{
			$('#{pid}').height(this.value);
			window.dispatchEvent(new Event('resize'));
		}});

		window.addEventListener('resize', function(){{
			{pvar}.resize();
		}});
		""".format(pid=pid, pvar=pvar, names=names, datasets=datasets)

	def draw_stack_bar_mix_plot(self, pid, names, datasets):
		pvar = pid.replace('-', '_')
		return """
		var {pvar}_source = {datasets};

		var {pvar}_height = $('<input>', {{id: '{pvar}-height'}}).prependTo($('#{pid}').parent());
		{pvar}_height.attr('value', 400).attr('type', 'number');
		$('<span>').addClass('ms-3').text('Plot height:').prependTo($('#{pid}').parent());

		var {pvar}_circos = $('<select>', {{id: '{pvar}-circos'}}).prependTo($('#{pid}').parent());
		{pvar}_circos.append($("<option>").attr('value', 'bar').text('bar'));
		{pvar}_circos.append($("<option>").attr('value', 'circle').text('circle'));
		$('<span>').addClass('ms-3').text('Plot type:').prependTo($('#{pid}').parent());

		var {pvar}_select = $('<select>', {{id: '{pvar}-select'}}).prependTo($('#{pid}').parent());
		for (key in {pvar}_source) {{
			{pvar}_select.append($("<option>").attr('value', key).text(key));
		}}
		$('<span>').text('Data type:').prependTo($('#{pid}').parent());

		var {pvar} = echarts.init(document.getElementById('{pid}'));
		var {pvar}_option_circos = {{
			angleAxis: {{
				type: 'category',
				data: {names}
			}},
			tooltip: {{
				trigger: 'item'
			}},
			toolbox: {{
				show: true,
				feature: {{
					dataView: {{readOnly: true}},
					saveAsImage: {{}}
				}}
			}},
			radiusAxis: {{}},
			polar: {{}},
			legend: {{}},
			series: []
		}};

		var {pvar}_option_bar = {{
			legend: {{}},
			tooltip: {{
				trigger: 'item'
			}},
			toolbox: {{
				show: true,
				feature: {{
					dataView: {{readOnly: true}},
					saveAsImage: {{}}
				}}
			}},
			yAxis: {{
				type: 'category',
				data: {names}
			}},
			xAxis: {{
				type: 'value',
				name: Object.keys({pvar}_source)[0],
				nameGap: 50,
				nameLocation: 'center',
				nameTextStyle: {{
					color: '#000',
					fontSize: 16,
				}}
			}},
			series: {pvar}_source[Object.keys({pvar}_source)[0]]
		}};

		var {pvar}_option = {pvar}_option_bar;
		{pvar}.setOption({pvar}_option);

		{pvar}_circos.on('change', function(){{
			var {pvar}_series = {pvar}_source[{pvar}_select.val()];
			if (this.value === 'circle') {{
				{pvar}_option = {pvar}_option_circos;

				for (var i = 0; i < {pvar}_series.length; i++) {{
					{pvar}_series[i].coordinateSystem = 'polar';
					{pvar}_series[i].barCategoryGap = 0;
				}}

			}} else {{
				{pvar}_option = {pvar}_option_bar;

				for (var i = 0; i < {pvar}_series.length; i++) {{
					{pvar}_series[i].coordinateSystem = 'cartesian2d';
					delete {pvar}_series[i].barCategoryGap;
				}}
			}}
			{pvar}_option.series = {pvar}_series;
			{pvar}.clear();
			{pvar}.setOption({pvar}_option);
		}});

		{pvar}_select.on('change', function() {{
			var {pvar}_series = {pvar}_source[this.value];
			if ({pvar}_circos.val() === 'circle') {{
				{pvar}_option = {pvar}_option_circos;

				for (var i = 0; i < {pvar}_series.length; i++) {{
					{pvar}_series[i].coordinateSystem = 'polar';
					{pvar}_series[i].barCategoryGap = 0;
				}}

			}} else {{
				{pvar}_option = {pvar}_option_bar;

				for (var i = 0; i < {pvar}_series.length; i++) {{
					{pvar}_series[i].coordinateSystem = 'cartesian2d';
					delete {pvar}_series[i].barCategoryGap;
				}}
			}}

			//{pvar}_option.xAxis.name = this.value;
			//{pvar}_option.series = {pvar}_source[this.value];
			{pvar}_option.series = {pvar}_series;
			{pvar}.clear();
			{pvar}.setOption({pvar}_option);
		}});

		{pvar}_height.on('change', function(){{
			$('#{pid}').height(this.value);
			window.dispatchEvent(new Event('resize'));
		}});

		window.addEventListener('resize', function(){{
			{pvar}.resize();
		}});
		""".format(pid=pid, pvar=pvar, names=names, datasets=datasets)

	def draw_heatmap_plot(self, pid, xlabels, ylabels, datasets):
		pvar = pid.replace('-', '_')
		return """
		var {pvar}_source = {datasets};

		var {pvar}_height = $('<input>', {{id: '{pvar}-height'}}).prependTo($('#{pid}').parent());
		{pvar}_height.attr('value', 400).attr('type', 'number');
		$('<span>').addClass('ms-3').text('Plot height:').prependTo($('#{pid}').parent());

		var {pvar}_select = $('<select>', {{id: '{pvar}-select'}}).prependTo($('#{pid}').parent());
		for (key in {pvar}_source) {{
			{pvar}_select.append($("<option>").attr('value', key).text(key));
		}}
		$('<span>').text('Data type:').prependTo($('#{pid}').parent());

		var {pvar} = echarts.init(document.getElementById('{pid}'));
		var {pvar}_option = {{
			tooltip: {{
				position: 'top'
			}},
			toolbox: {{
				show: true,
				feature: {{
					dataView: {{readOnly: true}},
					saveAsImage: {{}}
				}}
			}},
			legend: {{}},
			xAxis: {{
				type: 'category',
				data: {xlabels},
				splitArea: {{
					show: true
				}},
				axisLabel: {{
					rotate: 30
				}}
			}},
			yAxis: {{
				type: 'category',
				data: {ylabels},
				splitArea: {{
					show: true
				}}
			}},
			visualMap: {{
				calculable: true,
				orient: 'horizontal',
				left: 'center'
			}},
			series: {pvar}_source[Object.keys({pvar}_source)[0]]
		}}
		{pvar}.setOption({pvar}_option);
		{pvar}_select.on('change', function() {{
			{pvar}_option.series = {pvar}_source[this.value];
			{pvar}.setOption({pvar}_option);
		}});
		{pvar}_height.on('change', function(){{
			$('#{pid}').height(this.value);
			window.dispatchEvent(new Event('resize'));
		}});
		window.addEventListener('resize', function(){{
			{pvar}.resize();
		}});
		""".format(pid=pid, pvar=pvar, xlabels=xlabels, ylabels=ylabels, datasets=datasets)

	def perform_comparative_analysis(self):
		if len(self.fastx_files) < 2:
			return {}, {}

		ssr_summary = []
		ssr_types = []
		ssr_annot = []
		ssr_motif = set()
		annot_type = set()
		motif_data = []
		ssr_files = []

		for i, f in enumerate(self.fastx_files):
			datas = self.fastx_datas[i]
			ssr_files.append(f.name)

			for k, datai in datas.items():
				if k != 'ssr_stats':
					continue

				ssr_summary.append([
					f.id,
					f.name,
					datai['total_counts'],
					datai['total_length'],
					datai['average_length'],
					datai['coverage'],
					datai['frequency'],
					datai['density']
				])

				for s in datai:
					if s == 'type_stats':
						rows = {row[0]: row for row in datai[s]}
						item = [f.id, f.name]
						for j in [1, 2, 5, 6]:
							for m in ['Mono', 'Di', 'Tri', 'Tetra', 'Penta', 'Hexa']:
								row = rows.get(m, None)

								if row is None:
									item.append(0)
								else:
									item.append(row[j])

						ssr_types.append(item)

					elif s == 'annot_stats':
						annot_nums = {}
						for row in datai[s]:
							annot_type.add(row[0])
							annot_nums[row[0]] = [row[1], row[2], row[5], row[6]]

						ssr_annot.append(annot_nums)

					elif s == 'motif_stats':
						motif_nums = {}
						for row in datai[s]:
							ssr_motif.add(row[1])
							motif_nums[row[1]] = [row[2], row[3], row[6], row[7]]

						motif_data.append(motif_nums)

		tables = {}
		plots = {}

		if ssr_summary:
			tables['ssr-count-compare-table'] = ssr_summary
			tables['ssr-type-compare-table'] = ssr_types
		
		summary_pdata = {
			'SSR count': [],
			'SSR length': [],
			'SSR frequency': [],
			'SSR density': []
		}
		for row in ssr_summary:
			summary_pdata['SSR count'].append(row[2])
			summary_pdata['SSR length'].append(row[3])
			summary_pdata['SSR frequency'].append(row[6])
			summary_pdata['SSR density'].append(row[7])

		pid = 'ssr-summary-plot'

		if summary_pdata:
			plots[pid] = self.draw_line_bar_mix_plot(pid, ssr_files, summary_pdata)

		type_pdata = {}
		type_names = {
			'SSR count': 2,
			'SSR count percent': 2,
			'SSR length': 8,
			'SSR length percent': 8,
			'SSR frequency': 14,
			'SSR density': 20
		}

		for dtype, dindex in type_names.items():
			type_pdata[dtype] = []
			value_list = [[], [], [], [], [], []]

			for row in ssr_types:
				if 'percent' in dtype:
					total = sum(row[dindex:dindex+6])

					for j in range(6):
						value_list[j].append(round(row[dindex+j]/total*100, 2))
				else:
					for j in range(6):
						value_list[j].append(row[dindex+j])

			ts = ['Mono', 'Di', 'Tri', 'Tetra', 'Penta', 'Hexa']
			for l, t in enumerate(ts):
				type_pdata[dtype].append({
					'name': t,
					'type': 'bar',
					'stack': 'total',
					'coordinateSystem': 'cartesian2d',
					'data': value_list[l]
				})

		pid = 'ssr-type-compare-plot'

		if ssr_types:
			plots[pid] = self.draw_stack_bar_mix_plot(pid, ssr_files, type_pdata)

		annot_pdata = {}
		type_names = {
			'SSR count': 0,
			'SSR count percent': 0,
			'SSR length': 1,
			'SSR length percent': 1,
			'SSR frequency': 2,
			'SSR density': 3
		}

		annot_type = sorted(annot_type)
		for dtype, dindex in type_names.items():
			annot_pdata[dtype] = []
			value_list = []
			for at in range(len(annot_type)):
				value_list.append([])

			for nums in ssr_annot:
				if 'percent' in dtype:
					total = sum(num[dindex] for num in nums.values())

				for i, at in enumerate(annot_type):
					if at in nums:
						sv = nums[at][dindex]
					else:
						sv = 0

					if 'percent' in dtype:
						value_list[i].append(round(sv/total*100, 2))
					else:
						value_list[i].append(sv)

			for l, t in enumerate(annot_type):
				annot_pdata[dtype].append({
					'name': t,
					'type': 'bar',
					'stack': 'total',
					'coordinateSystem': 'cartesian2d',
					'data': value_list[l]
				})

		pid = 'ssr-annot-compare-plot'

		if ssr_annot and ssr_annot[0]:
			plots[pid] = self.draw_stack_bar_mix_plot(pid, ssr_files, annot_pdata)

		type_names = {
			'SSR count': 0,
			'SSR length': 1,
			'SSR frequency': 2,
			'SSR density': 3
		}
		motif_pdata = {}

		xlabels = sorted(ssr_motif, key=lambda x: (len(x), x))
		ylabels = ssr_files
		
		for dtype, dindex in type_names.items():
			motif_pdata[dtype] = []
			value_list = [[], [], [], [], [], []]
		
			for y, nums in enumerate(motif_data):
				for x, motif in enumerate(xlabels):
					if motif in nums:
						sv = nums[motif][dindex]
					else:
						sv = 0

					value_list[len(motif)-1].append([x, y, sv])

			ts = ['Mono', 'Di', 'Tri', 'Tetra', 'Penta', 'Hexa']
			for l, t in enumerate(ts):
				motif_pdata[dtype].append({
					'name': t,
					'type': 'heatmap',
					'data': value_list[l]
				})

		pid = 'ssr-motif-compare-plot'

		if motif_data:
			plots[pid] = self.draw_heatmap_plot(pid, xlabels, ylabels, motif_pdata)

		return tables, plots

	def generate_summary_report(self):
		f = QFile(':/template/stats.html')
		f.open(QIODevice.ReadOnly | QFile.Text)
		content = QTextStream(f).readAll()
		f.close()

		template = jinja2.Template(content)

		styles = self.get_style_css()
		scripts = self.get_script_js()
		tables = self.get_stats_tables()
		plots = self.get_stats_plots()

		forms, charts = self.perform_comparative_analysis()
		tables.update(forms)
		plots.update(charts)

		return template.render(
			styles = styles,
			scripts = scripts,
			fastxs = self.fastx_files,
			tables = tables,
			plots = plots,
			uname = self.uname
		)
