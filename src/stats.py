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

	@classmethod
	def get_reports(cls, repeats, fastx, unit):
		stats = cls(repeats, fastx, unit)
		json_str = stats.json()
		html_str = stats.html()
		return json_str, html_str

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
	def __init__(self, uname='Mb'):
		self.uname = uname
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
					if s in data:
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

	def draw_bar_plot(self, pid, title, data, ylab):
		pvar = pid.replace('-', '_')
		return """
			var {pvar} = echarts.init(document.getElementById('{pid}'));
			{pvar}.setOption({{
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
					name: "{ylab}",
					nameGap: 50,
					nameLocation: 'center',
					nameTextStyle: {{
						color: '#000',
						fontSize: 16,
					}}
				}},
				series: {data}
			}});
			window.addEventListener('resize', function(){{
				{pvar}.resize();
			}});
		""".format(pvar=pvar, pid=pid, title=title, data=data, ylab=ylab)

	def draw_line_plot(self, pid, title, datasets, xlab, ylab):
		pvar = pid.replace('-', '_')
		return """
			var {pvar} = echarts.init(document.getElementById('{pid}'));
			{pvar}.setOption({{
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
					name: "{ylab}",
					nameLocation: 'center'
				}},
				series: {datasets}
			}});
			window.addEventListener('resize', function(){{
				{pvar}.resize();
			}});
		""".format(pvar=pvar, pid=pid, title=title, datasets=datasets, xlab=xlab, ylab=ylab)

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

						pid = "{}-annot-pie-{}".format(rtype, f.id)
						title = "{} distribution in different gene regions".format(rtype)
						name = "{} annotation".format(rtype)
						plots[pid] = self.draw_pie_plot(pid, title, name, counts)

					if s == 'motif_stats':
						datasets = {}
						for row in datai[s]:
							if row[0] not in datasets:
								datasets[row[0]] = []

							datasets[row[0]].append((row[1], row[6]))

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

						pid = "{}-motif-bar-{}".format(rtype, f.id)
						title = "{} motif distribution".format(rtype)
						ylab = "{} counts".format(rtype)
						plots[pid] = self.draw_bar_plot(pid, title, series, ylab)

					if s == 'repeat_stats':
						datasets = {}
						for row in datai[s]:
							if row[0] not in datasets:
								datasets[row[0]] = []
							datasets[row[0]].append((row[1], row[6]))

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

						pid = "{}-repeat-line-{}".format(rtype, f.id)
						title = "{} repeat distribution".format(rtype)
						xlab = "Repeat number"
						ylab = "Frequency (loci/{})".format(self.uname)
						plots[pid] = self.draw_line_plot(pid, title, series, xlab, ylab)

					if s == 'length_stats':
						datasets = {}
						for row in datai[s]:
							if row[0] not in datasets:
								datasets[row[0]] = []
							datasets[row[0]].append((row[1], row[6]))

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

						pid = "{}-length-line-{}".format(rtype, f.id)
						title = "{} length distribution".format(rtype)
						xlab = "Length"
						ylab = "Frequency (loci/{})".format(self.uname)
						plots[pid] = self.draw_line_plot(pid, title, series, xlab, ylab)

		return plots

	def perform_comparative_analysis(self):
		ssr_summary = []
		ssr_types = []
		ssr_annot = []

		for i, f in enumerate(self.fastx_files):
			datas = self.fastx_datas[i]

			for k, datai in datas.items():
				if rtype != 'ssr_stats':
					continue

				ssr_summary.append([
					f.name
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
						item = []
						for j in [1, 2, 5, 6]:
							for m in ['Mono', 'Di', 'Tri', 'Tetra', 'Penta', 'Hexa']:
								row = rows.get(m, None):

								if row is None:
									item.append(0)
								else:
									item.append(row[j])

					elif s == 'annot_stats':
						pass

					elif s == 'motif_stats':
						pass









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

		return template.render(
			styles = styles,
			scripts = scripts,
			fastxs = self.fastx_files,
			tables = tables,
			plots = plots
		)
