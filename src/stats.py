import json

from backend import *

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
		'''unit 0: Mb, 1: Kb; letter 0: exclude ns, 1: include
		'''
		self.unit = unit
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
			self._size = self._length - self._unknown
		return self._size

	@property
	def sql(self):
		if not self._sql:
			self._sql = self.fsql("INSERT INTO stats_{} VALUES (NULL,?,?,?)")
		return self._sql

	@property
	def transize(self):
		'''transformed size bp to MB or KB'''
		if self.letter == 0:
			total = self.size
		else:
			total = self.length

		scales = {0: 1000000, 1: 1000}

		return total/scales[self.unit]

	def fsql(self, sql):
		return sql.format("{}_{}".format(self._category, self.findex))

	def add(self, option, value):
		self.result_lists.append((self._category, option, value))

	def run(self):
		pass

	def write(self):
		DB.insert_rows(self.sql, result_lists)

	def frequency(self, count):
		return round(count/self.transize, 2)

	def density(self, length):
		return round(length/self.transize, 2)

	def calc_group(self, fields, total_count):
		#calc counts and length
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
		self.add('gccontent', round(self.fasta.gc_content, 2))

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
		self.add('frequency', self.frequency(ssr_count))

		#calc all ssr length
		ssr_length = DB.get_one(self.fsql("SELECT SUM(length) FROM {} LIMIT 1"))
		self.add('ssrlength', ssr_length)
		self.add('density', self.density(ssr_length))

		#genome coverage percent
		self.add('coverage', round(ssr_length/self.length*100, 2))

		#calc average length
		self.add('avglen', round(ssr_length/ssr_count, 2))

		#calc max repeat
		max_repeat = DB.get_one(self.fsql("SELECT MAX(repeats) FROM {} LIMIT 1"))
		self.add('maxrep', max_repeat)

		#calc max length
		max_len = DB.get_one(self.fsql("SELECT MAX(length) FROM {} LIMIT 1"))
		self.add('maxlen', max_len)

		fields = {'ssrtypes': 'type', 'ssrmotifs': 'standard', 'ssrrepeats': 'repeats'}
		self.calc_group(fields, ssr_count)

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
