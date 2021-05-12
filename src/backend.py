import apsw

__all__ = ['DB']

CREATE_TABLES_SQL = """

CREATE TABLE IF NOT EXISTS fastas (
	id INTEGER PRIMARY KEY,
	name TEXT,
	path TEXT
);

"""

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

	def _connect_to_db(self, db_file=':memory:'):
		if not self.conn:
			self.conn = apsw.Connection(db_file)
			#self.conn.setrowtrace(row_factory)
			self._optimize()
			self.cursor.execute(CREATE_TABLES_SQL)

	def change_db(self, db_file):
		if self.conn:
			self.conn.close()
		self._connect_to_db(db_file)

	def create_ssr_table(self, idx):
		sql = """
			CREATE TABLE IF NOT EXISTS ssr{} (
				id INTEGER PRIMARY KEY,
				chrom TEXT,
				start INTEGER,
				end INTEGER,
				motif TEXT,
				standard TEXT,
				type TEXT,
				repeats INTEGER,
				length INTEGER
			);""".format(idx)
		self.cursor.execute(sql)

	def insert_rows(self, sql, rows):
		self.cursor.executemany(sql, rows)

	def query(self, sql, paras=None):
		if paras is None:
			return self.cursor.execute(sql)
		else:
			return self.cursor.execute(sql, paras)

	def get_one(self, sql, paras=None):
		for row in self.query(sql, paras):
			return row[0]

	def get_row(self, sql, paras=None):
		for row in self.query(sql, paras):
			return row

	def get_column(self, sql, paras=None):
		return [row[0] for row in self.query(sql, paras)]

	def save_to_file(self, dbfile):
		target = apsw.Connection(dbfile)
		return target.backup("main", self.conn, "main")

DB = DataBackend()
