import json
import pyfastx

from config import *
from backend import *

__all__ = ['SSRStatistics', 'CSSRStatistics', 'ISSRStatistics',
			'VNTRStatistics', 'FastaStatistics', 'get_stats_report']

class Statistics:
	#total sequence counts
	_count = 0

	#total bases
	_length = 0

	#total bases exclude Ns
	_size = 0

	#insert sql
	_sql = None

	#fasta, ssr category
	_category = None

	#unknown bases
	_unknown = 0

	def __init__(self, findex=0, unit=0, letter=0):
		'''unit 0: Mb, 1: Kb; letter 0: exclude ns, 1: include ns
		'''
		self._unit = unit
		self.letter = letter
		self.findex = findex
		self.result_lists = []
		self.open_fasta()
		self.run()
		self.write()

	def open_fasta(self):
		name, fasta = DB.get_row("SELECT name,fasta FROM fasta_0 WHERE id=?", (self.findex,))
		self.name = name
		self.fasta = pyfastx.Fasta(fasta, full_index=True)

	@property
	def unit(self):
		return {0: 'Mb', 1: 'Kb'}[self._unit]

	@property
	def count(self):
		if not self._count:
			self._count = len(self.fasta)
		return self._count

	@property
	def length(self):
		if not self._length:
			self._length = self.fasta.size
		return self._length

	@property
	def size(self):
		if not self._size:
			self._unknown = self.fasta.composition.get('N', 0)
			self._size = self.length - self._unknown
		return self._size

	@property
	def sql(self):
		if not self._sql:
			self._sql = "INSERT INTO stats_{} VALUES (NULL,?,?,?)"
		return self._sql

	@property
	def transize(self):
		'''transformed size bp to MB or KB'''
		if self.letter == 0:
			total = self.size
		else:
			total = self.length

		scales = {0: 1000000, 1: 1000}

		return total/scales[self._unit]

	def fsql(self, sql):
		return sql.format("{}_{}".format(self._category, self.findex))

	def add(self, option, value):
		self.result_lists.append((self._category, option, value))

	def run(self):
		pass

	def write(self):
		DB.insert_rows(self.sql.format(self.findex), self.result_lists)

	def report(self):
		pass

	def frequency(self, count):
		return round(count/self.transize, 2)

	def density(self, length):
		return round(length/self.transize, 2)

	def calc_group(self, fields, total_count):
		#calc counts and length
		ret = {}
		for k, v in fields.items():
			res = []
			for row in DB.query(self.fsql("SELECT {{0}},COUNT(1),SUM(length) FROM {} GROUP BY {{0}}").format(v)):
				res.append((
					row[0], row[1], row[2],
					round(row[1]/total_count*100, 2),
					round(row[2]/row[1], 2),
					self.frequency(row[1]),
					self.density(row[2])
				))
			self.add(k, json.dumps(res))
			ret[k] = res

		return ret

	def table_format(self, title, headers, rows):
		table = """
		<h3>{}</h3>
		<table width="100%">
			<thead>
				<tr>{}</tr>
			</thead>
			<tbody>{}</tbody>
		</table>
		"""

		titles = "".join(["<th>{}</th>".format(h) for h in headers])
		contents = []
		for row in rows:
			data = "".join(["<td>{}</td>".format(col) for col in row])
			contents.append("<tr>{}</tr>".format(data))
		contents = "".join(contents)

		self.add('statsreport', table.format(title, titles, contents))

class FastaStatistics(Statistics):
	_category = 'fasta'

	def __init__(self, findex=0):
		super().__init__(findex)

	def run(self):
		#add file name
		self.add('fastaname', self.name)

		#get sequence count
		self.add('seqcount', self.count)

		#get total bases
		self.add('totalbase', self.length)

		#get unknown bases
		self.add('unknownbase', self._unknown)

		#get GC content
		gc = round(self.fasta.gc_content, 2)
		self.add('gccontent', gc)

		#generate statistical report
		table = self.table_format(
			"General information of input fasta file",
			["Fasta name", "Sequence count", "Total bases (bp)", "Unknown bases (bp)", "GC content (%)"],
			[(self.name, self.count, self.length, self._unknown, gc)]
		)

class SSRStatistics(Statistics):
	_category = 'ssr'

	def __init__(self, findex):
		super().__init__(findex)

	def run(self):
		#calc all ssr counts
		ssr_count = DB.get_one(self.fsql("SELECT COUNT(1) FROM {} LIMIT 1"))

		if not ssr_count:
			return

		self.add('ssrcount', ssr_count)
		freq = self.frequency(ssr_count)
		self.add('frequency', freq)

		#calc all ssr length
		ssr_length = DB.get_one(self.fsql("SELECT SUM(length) FROM {} LIMIT 1"))
		self.add('ssrlength', ssr_length)
		dens = self.density(ssr_length)
		self.add('density', dens)

		#genome coverage percent
		coverage = round(ssr_length/self.length*100, 2)
		self.add('coverage', coverage)

		#calc average length
		avg_len = round(ssr_length/ssr_count, 2)
		self.add('avglen', avg_len)

		#calc max repeat
		max_repeat = DB.get_one(self.fsql("SELECT MAX(repeats) FROM {} LIMIT 1"))
		self.add('maxrep', max_repeat)

		#calc max length
		max_len = DB.get_one(self.fsql("SELECT MAX(length) FROM {} LIMIT 1"))
		self.add('maxlen', max_len)

		table = self.table_format(
			"Overview of SSRs",
			["Number of SSRs", "Total length (bp)", "Average length (bp)",
			 "Frequency (loci/{})".format(self.unit), "Density (bp/{})".format(self.unit),
			 "Max repeats", "Max length (bp)", "Coverage (%)"],
			[(ssr_count, ssr_length, avg_len, freq, dens, max_repeat, max_len, coverage)]
		)

		fields = {'ssrtypes': 'type', 'ssrmotifs': 'standard', 'ssrrepeats': 'repeats'}
		res = self.calc_group(fields, ssr_count)

		titles = {
			'ssrtypes': ['Type', "Statistical information for each SSR type"],
			'ssrmotifs': ['Motif', "Statistical information for each motif type"],
			'ssrrepeats':['Repeat', "Statistical information for each repeat type"],
		}

		for field in fields:
			self.table_format(
				titles[field][1],
				[titles[field][0], "Counts", "Total length (bp)", "Percentage (%)", "Average length (bp)",
				 "Frequency (loci/{})".format(self.unit), "Density (bp/{})".format(self.unit)],
				res[field]
			)

class CSSRStatistics(Statistics):
	_category = 'cssr'

	def __init__(self, findex=0):
		super().__init__(findex)

	def run(self):
		#calc all cssr counts
		cm_count = DB.get_one(self.fsql("SELECT COUNT(1) FROM {} LIMIT 1"))

		if not cm_count:
			return

		self.add('cmcount', cm_count)
		self.add('frequency', self.frequency(cm_count))

		#calc all cssr length
		cm_length = DB.get_one(self.fsql("SELECT SUM(length) FROM {} LIMIT 1"))
		self.add('cmlength', cm_length)
		self.add('density', self.density(cm_length))

		#calc cssr count
		cssr_count = DB.get_one(self.fsql("SELECT SUM(complexity) FROM {} LIMIT 1"))
		self.add('cssrcount', cssr_count)

		#calc average length
		self.add('avglen', round(cm_length/cm_count, 2))

		#calc max complexity
		max_complex = DB.get_one(self.fsql("SELECT MAX(complexity) FROM {} LIMIT 1"))
		self.add('maxcomplex', max_complex)

		#calc max length
		max_len = DB.get_one(self.fsql("SELECT MAX(length) FROM {} LIMIT 1"))
		self.add('maxlen', max_len)

		fields = {'cssrcomplex': 'complexity', 'cssrlength': 'length'}
		self.calc_group(fields, cm_count)

class VNTRStatistics(Statistics):
	_category = 'vntr'

	def __init__(self, findex):
		super().__init__(findex)

	def run(self):
		#calc all vntr counts
		vntr_count = DB.get_one(self.fsql("SELECT COUNT(1) FROM {} LIMIT 1"))

		if not vntr_count:
			return

		self.add('vntrcount', vntr_count)
		self.add('frequency', self.frequency(vntr_count))

		#calc all vntr length
		vntr_length = DB.get_one(self.fsql("SELECT SUM(length) FROM {} LIMIT 1"))
		self.add('vntrlength', vntr_length)
		self.add('density', self.density(vntr_length))

		#genome coverage percent
		self.add('coverage', round(vntr_length/self.length*100, 2))

		#calc average length
		self.add('avglen', round(vntr_length/vntr_count, 2))

		#calc max repeat
		max_repeat = DB.get_one(self.fsql("SELECT MAX(repeats) FROM {} LIMIT 1"))
		self.add('maxrep', max_repeat)

		#calc max length
		max_len = DB.get_one(self.fsql("SELECT MAX(length) FROM {} LIMIT 1"))
		self.add('maxlen', max_len)

		fields = {'vntrtypes': 'type', 'vntrmotifs': 'motif', 'vntrrepeats': 'repeats'}
		self.calc_group(fields, vntr_count)

class ISSRStatistics(Statistics):
	_category = 'issr'

	def __init__(self, findex):
		super().__init__(findex)

	def run(self):
		#calc all ssr counts
		issr_count = DB.get_one(self.fsql("SELECT COUNT(1) FROM {} LIMIT 1"))

		if not issr_count:
			return

		self.add('issrcount', issr_count)
		self.add('frequency', self.frequency(issr_count))

		#calc all ssr length
		issr_length = DB.get_one(self.fsql("SELECT SUM(length) FROM {} LIMIT 1"))
		self.add('issrlength', issr_length)
		self.add('density', self.density(issr_length))

		#genome coverage percent
		self.add('coverage', round(issr_length/self.length*100, 2))

		#calc average length
		self.add('avglen', round(issr_length/issr_count, 2))

		#calc max repeat
		#max_repeat = DB.get_one(self.fsql("SELECT MAX(repeats) FROM {} LIMIT 1"))
		#self.add('maxrep', max_repeat)

		#calc max length
		max_len = DB.get_one(self.fsql("SELECT MAX(length) FROM {} LIMIT 1"))
		self.add('maxlen', max_len)

		fields = {'issrtypes': 'type', 'issrmotifs': 'standard'}
		self.calc_group(fields, issr_count)

def get_stats_report(file_index):
	sql = "SELECT value FROM stats_{} WHERE option=?".format(file_index)
	reports = DB.get_column(sql, ('statsreport',))

	html = """
	<html>
	<head>
	<style type="text/css">
	body {{
		margin: 20px;
	}}
	table {{
		border-collapse: collapse;
		border-width: 1px;
		border-color:black;
	}}
	table th,
	table td {{
		padding: 5px 15px;
	}}
	.center {{
		text-align: center;
	}}
	</style>
	</head>
	<body>
		<h2 class="center">Statistical Report</h2>
		<p class="center"><i>This report was generate by Krait2 v{0}.</i></p>
		{1}
	</body>
	</html>"""

	return html.format(KRAIT_VERSION, "".join(reports))
