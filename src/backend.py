import apsw
import threading

__all__ = ['DB']

FASTX_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS fastx (
	id INTEGER PRIMARY KEY,
	name TEXT,
	fpath TEXT,
	status INTEGER,
	message TEXT,
	apath TEXT,
	format TEXT,
	size INTEGER,
	count INTEGER,
	gc REAL,
	ns INTEGER,
	avglen REAL,
	minlen INTEGER,
	maxlen INTEGER,
	bytes INTEGER
)
"""

SSR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ssr_{} (
	id INTEGER PRIMARY KEY,
	chrom TEXT,
	start INTEGER,
	end INTEGER,
	motif TEXT,
	smotif TEXT,
	type INTEGER,
	repeat INTEGER,
	length INTEGER
)
"""

GTR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS gtr_{} (
	id INTEGER PRIMARY KEY,
	chrom TEXT,
	start INTEGER,
	end INTEGER,
	type INTEGER,
	repeat INTEGER,
	length INTEGER,
	motif TEXT
)
"""

CSSR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cssr_{} (
	id INTEGER PRIMARY KEY,
	chrom TEXT,
	start INTEGER,
	end INTEGER,
	complexity INTEGER,
	length INTEGER,
	structure TEXT,
	component TEXT
)
"""

ISSR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS issr_{} (
	id INTEGER PRIMARY KEY,
	chrom TEXT,
	start INTEGER,
	end INTEGER,
	motif TEXT,
	smotif TEXT,
	type INTEGER,
	length INTEGER,
	sstart INTEGER,
	send INTEGER,
	srepeat INTEGER,
	match INTEGER,
	subsitution INTEGER,
	insertion INTEGER,
	deletion INTEGER,
	identity REAL
)
"""

PRIMER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS primer_{} (
	id INTEGER PRIMARY KEY,
	locus TEXT,
	entry INTEGER,
	product_size INTEGER,
	forward_tm REAL,
	forward_gc REAL,
	forward_stability REAL,
	forward_seq TEXT,
	reverse_tm REAL,
	reverse_gc REAL,
	reverse_stability REAL,
	reverse_seq TEXT,
	forward_start INTEGER,
	forward_length INTEGER,
	reverse_start INTEGER,
	reverse_length INTEGER
)
"""

ANNOT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS annot_{} (
	id INTEGER PRIMARY KEY,
	parent INTEGER,
	chrom TEXT,
	type TEXT,
	start INTEGER,
	end INTEGER,
	strand TEXT,
	fid TEXT,
	name TEXT
)
"""

MAPPING_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS map_{} (
	id INTEGER PRIMARY KEY,
	type INTEGER,
	locus INTEGER,
	feature INTEGER,
	parents TEXT
)
"""

STATS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stats_{} (
	id INTEGER PRIMARY KEY,
	type TEXT,
	json TEXT,
	html TEXT,
	meta TEXT,
	plot TEXT
)
"""

TABLE_SQL_MAPPING = {
	'fastx': FASTX_TABLE_SQL,
	'ssr': SSR_TABLE_SQL,
	'gtr': GTR_TABLE_SQL,
	'cssr': CSSR_TABLE_SQL,
	'issr': ISSR_TABLE_SQL,
	'primer': PRIMER_TABLE_SQL,
	'annot': ANNOT_TABLE_SQL,
	'map': MAPPING_TABLE_SQL,
	'stats': STATS_TABLE_SQL,
}

class DataRow(dict):
	def __getattr__(self, attr):
		return self[attr]

def row_factory(cursor, row):
	fields = [name for name, _ in cursor.getdescription()]
	return DataRow(zip(fields, row))

class DataBackend:
	conn = None

	def __init__(self):
		self._lock = threading.RLock()
		self._connect_to_db()

	def __del__(self):
		if self.conn:
			self.conn.close()

	#def __getstate__(self):
	#	return self.db_file

	#def __setstate__(self, state):
	#	self._connect_to_db(state)

	@property
	def cursor(self):
		with self._lock:
			yield self.conn.cursor()

	def _optimize(self):
		self.query("PRAGMA synchronous=OFF")
		self.query(TABLE_SQL_MAPPING['fastx'])
		self.begin()

	#def _create_tables(self):
	#	for sql in TABLE_SQL_MAPPING.values():
	#		self.cursor.execute(sql.format(''))

	def _connect_to_db(self, db_file=':memory:'):
		if not self.conn:
			self.conn = apsw.Connection(db_file)
			#self.conn.setrowtrace(row_factory)
			self._optimize()
			#self._create_tables()
			self.db_file = db_file

	def change_db(self, db_file):
		if self.conn:
			self.conn.close()
		
		self.conn = apsw.Connection(db_file)
		self._optimize()
		self.db_file = db_file

	def create_table(self, table, idx):
		sql = TABLE_SQL_MAPPING[table].format(idx)
		self.cursor.execute(sql)

	def drop_table(self, table, idx):
		table = "{}_{}".format(table, idx)

		if self.table_exists(table):
			self.query("DELETE FROM {}".format(table))

	def drop_index(self, table, idx):
		self.query("DROP INDEX IF EXISTS index_{}".format(idx))

	def clear_table(self, table, idx):
		self.query("DELETE FROM {}_{}".format(table, idx))

	def insert_rows(self, sql, rows):
		self.cursor.executemany(sql, rows)

	def update_rows(self, sql, rows):
		self.cursor.executemany(sql, rows)

	def update_status(self, rowid, status):
		sql = "UPDATE fastx SET status=? WHERE id=?"
		self.query(sql, (status, rowid))

	def update_fastx(self, row):
		sql = "UPDATE fastx SET format=?,size=?,count=?,gc=?,ns=?,avglen=?,minlen=?,maxlen=? WHERE id=?"
		self.query(sql, row)

	def has_fastx(self):
		sql = "SELECT 1 FROM fastx LIMIT 1"
		res = self.get_one(sql)
		return True if res else False

	def has_table(self, table):
		sql = "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1"
		res = self.get_one(sql)
		return True if res else False

	def query(self, sql, paras=None):
		if paras is None:
			return self.cursor.execute(sql)
		else:
			return self.cursor.execute(sql, paras)

	def table_exists(self, table):
		return self.conn.table_exists(None, table)

	def get_one(self, sql, paras=None):
		for row in self.query(sql, paras):
			return row[0]

	def get_row(self, sql, paras=None):
		for row in self.query(sql, paras):
			return row

	def get_rows(self, sql, paras=None):
		return [row for row in self.query(sql, paras)]

	def get_column(self, sql, paras=None):
		return [row[0] for row in self.query(sql, paras)]

	def get_set(self, sql, paras=None):
		return {row[0] for row in self.query(sql, paras)}

	def get_count(self, table):
		if self.table_exists(table):
			return self.get_one("SELECT COUNT(1) FROM {}".format(table))
		else:
			return 0

	def get_dict(self, sql, paras=None):
		cur = self.query(sql, paras)

		for row in cur:
			fields = [col[0] for col in cur.getdescription()]
			return dict(zip(fields, row))

	def get_dicts(self, sql, paras=None):
		cur = self.query(sql, paras)

		for row in cur:
			fields = [col[0] for col in cur.getdescription()]
			yield dict(zip(fields, row))

	def get_object(self, sql, paras=None):
		cur = self.query(sql, paras)

		for row in cur:
			fields = [col[0] for col in cur.getdescription()]
			return DataRow(zip(fields, row))

	def get_objects(self, sql, paras=None):
		cur = self.query(sql, paras)

		for row in cur:
			fields = [col[0] for col in cur.getdescription()]
			yield DataRow(zip(fields, row))

	def get_field(self, table):
		return [row[1] for row in self.query("PRAGMA table_info({})".format(table))]

	def get_field_type(self, table):
		return [row[2] for row in self.query("PRAGMA table_info({})".format(table))]

	def get_sql(self, table):
		fields = self.get_field(table)
		sql = "INSERT INTO {} VALUES ({})".format(table, ','.join(['?']*len(fields)))
		return sql

	def get_tables(self):
		sql = "SELECT name FROM sqlite_master WHERE type=?"
		return self.get_column(sql, ('table',))

	def save_to_file(self, dbfile):
		target = apsw.Connection(dbfile)
		return target.backup("main", self.conn, "main")

	def begin(self):
		self.query("BEGIN")

	def commit(self):
		if not self.autocommit:
			self.query("COMMIT")

	@property
	def autocommit(self):
		return self.conn.getautocommit()

	@property
	def changed(self):
		return self.conn.changes() > 0

	def export_to_file(self, table, out_file, out_format='csv'):
		if out_format == 'tsv':
			out_format = 'tabs'

		with open(out_file, 'w') as fw:
			shell = apsw.Shell(stdout=fw, db=self.conn)
			shell.process_command(".mode {}".format(out_format))
			shell.process_command(".headers on")
			shell.process_complete_line("SELECT * FROM {}".format(table))

DB = DataBackend()
