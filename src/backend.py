import apsw

__all__ = ['DB']

FASTA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS fasta (
	id INTEGER PRIMARY KEY,
	name TEXT,
	size INTEGER,
	status TEXT,
	path TEXT
);
"""

SSR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ssr_{} (
	id INTEGER PRIMARY KEY,
	chrom TEXT,
	start INTEGER,
	end INTEGER,
	motif TEXT,
	standard TEXT,
	type TEXT,
	repeats INTEGER,
	length INTEGER
);
"""

VNTR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS vntr_{} (
	id INTEGER PRIMARY KEY,
	chrom TEXT,
	start INTEGER,
	end INTEGER,
	motif TEXT,
	type TEXT,
	repeats INTEGER,
	length INTEGER
);
"""

CSSR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS cssr_{} (
	id INTEGER PRIMARY KEY,
	chrom TEXT,
	start INTEGER,
	end INTEGER,
	complexity INTEGER,
	length INTEGER,
	structure TEXT
)
"""

ITR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS itr_{} (
	id INTEGER PRIMARY KEY,
	chrom TEXT,
	start INTEGER,
	end INTEGER,
	motif TEXT,
	type TEXT,
	length INTEGER,
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
	forward_seq TEXT,
	forward_tm REAL,
	forward_gc REAL,
	forward_stability REAL,
	reverse_seq TEXT,
	reverse_tm REAL,
	reverse_gc REAL,
	reverse_stability REAL,
	forward_start INTEGER,
	forward_length INTEGER,
	reverse_start INTEGER,
	reverse_length INTEGER
)
"""

TABLE_SQL_MAPPING = {
	'fasta': FASTA_TABLE_SQL,
	'ssr': SSR_TABLE_SQL,
	'vntr': VNTR_TABLE_SQL,
	'cssr': CSSR_TABLE_SQL,
	'itr': ITR_TABLE_SQL,
	'primer': PRIMER_TABLE_SQL,
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
		self._connect_to_db()

	@property
	def cursor(self):
		return self.conn.cursor()

	def _optimize(self):
		self.cursor.execute("PRAGMA synchronous=OFF")

	def _create_tables(self):
		for sql in TABLE_SQL_MAPPING.values():
			self.cursor.execute(sql.format(''))

	def _connect_to_db(self, db_file=':memory:'):
		if not self.conn:
			self.conn = apsw.Connection(db_file)
			#self.conn.setrowtrace(row_factory)
			self._optimize()
			self._create_tables()

	def change_db(self, db_file):
		if self.conn:
			self.conn.close()
		self._connect_to_db(db_file)

	def create_table(self, table, idx):
		sql = TABLE_SQL_MAPPING[table].format(idx)
		self.cursor.execute(sql)

	def insert_rows(self, sql, rows):
		self.cursor.executemany(sql, rows)

	def update_status(self, rowid, status):
		sql = "UPDATE fastas SET status=? WHERE id=?"
		self.query(sql, (status, rowid))

	def query(self, sql, paras=None):
		if paras is None:
			return self.cursor.execute(sql)
		else:
			return self.cursor.execute(sql, paras)

	def table_exists(self, table):
		try:
			self.query("SELECT 1 FROM {}".format(table))
			return True
		except:
			return False

	def get_one(self, sql, paras=None):
		for row in self.query(sql, paras):
			return row[0]

	def get_row(self, sql, paras=None):
		for row in self.query(sql, paras):
			return row

	def get_column(self, sql, paras=None):
		return [row[0] for row in self.query(sql, paras)]

	def get_set(self, sql, paras=None):
		return {row[0] for row in self.query(sql, paras)}

	def get_field(self, table):
		return [row[1] for row in self.query("PRAGMA table_info({})".format(table))]

	def get_field_type(self, table):
		return [row[2] for row in self.query("PRAGMA table_info({})".format(table))]

	def save_to_file(self, dbfile):
		target = apsw.Connection(dbfile)
		return target.backup("main", self.conn, "main")

	def clear_table(self, table, idx):
		self.query("DELETE FROM {}".format(table))

DB = DataBackend()
