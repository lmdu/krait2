import time

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 

from config import *
from tables import *
from backend import *
from workers import *

__all__ = ['KraitMainWindow']

class KraitMainWindow(QMainWindow):
	def __init__(self):
		super(KraitMainWindow, self).__init__()

		self.setWindowTitle("Krait2 v{}".format(KRAIT_VERSION))
		self.setWindowIcon(QIcon('icons/logo.ico'))

		self.tab_widget = QTabWidget(self)
		self.setCentralWidget(self.tab_widget)

		#self.info_widget = QTextBrowser(self)
		#self._info_widget.setFrameShape(QFrame.NoFrame)
		self.file_table = KraitTableView(self, 'fastas')
		self.file_table.clicked.connect(self.change_current_file)
		self.tab_widget.addTab(self.file_table, "Input Files")

		self.ssr_table = None
		self.cssr_table = None
		self.vntr_table = None
		self.itr_table = None
		#self.ssr_table = KraitTableView(self)
		#self.tab_widget.addTab(self.ssr_table, "SSR Results")

		#self.cssr_table = KraitTableView(self, 'cssr')
		#self.tab_widget.addTab(self.cssr_table, "cSSR Results")

		#self.file_select = QComboBox(self)
		#self.file_select.setSizeAdjustPolicy(QComboBox.AdjustToContents)
		#self.file_model = FileSelectModel(self)
		#self.file_select.setModel(self.file_model)

		#self._file_select.addItems(["file {}".format(i) for i in range(10)])

		self.create_actions()
		self.create_menus()
		self.create_toolbar()
		self.create_statusbar()


	def create_actions(self):
		#menu actions
		self.open_action = QAction("&Open project", self,
			shortcut = QKeySequence.Open,
			statusTip = "Open a project file",
			triggered = self.open_project
		)

		self.save_action = QAction("&Save project", self,
			shortcut = QKeySequence.Save,
			statusTip = "Save project",
			triggered = self.save_project
		)

		self.save_as_action = QAction("&Save project as", self,
			shortcut = QKeySequence.SaveAs,
			statusTip = "Save project as",
			triggered = self.save_project_as
		)

		self.import_action = QAction("&Import fasta files", self,
			statusTip = "Import fasta files",
			triggered = self.import_fasta_files
		)

		self.folder_action = QAction("&Import fastas from folder", self,
			statusTip = "Import all fasta files from a folder",
			triggered = self.import_fasta_folder
		)

		self.close_action = QAction("&Exit", self,
			shortcut = "Alt+Q",
			statusTip = "Exit",
			triggered = self.close
		)

		#toolbar actions
		self.search_ssr_action = QAction(QIcon("icons/ssr.png"), "Search SSRs", self,
			statusTip = "Search for perfect microsatellites",
			triggered = self.perform_ssr_search
		)

		self.search_cssr_action = QAction(QIcon("icons/cssr.png"), "Search cSSRs", self,
			statusTip = "Search for compound microsatellites",
			triggered = self.close
		)

		self.search_vntr_action = QAction(QIcon("icons/vntr.png"), "Search VNTRs", self,
			statusTip = "Search for VNTRs",
			triggered = self.close
		)

		self.search_itr_action = QAction(QIcon("icons/issr.png"), "Search ITRs", self,
			statusTip = "Search for imperfect tandem repeats",
			triggered = self.close
		)

		self.mapping_action = QAction(QIcon("icons/locate.png"), "Mapping", self,
			statusTip = "Mapping tandem repeats to gene",
			triggered = self.close
		)

		self.primer_action = QAction(QIcon("icons/primer.png"), "Design primer", self,
			statusTip = "Design primers for selected repeats",
			triggered = self.close
		)

	def create_menus(self):
		self.file_menu = self.menuBar().addMenu("&File")
		self.file_menu.addAction(self.open_action)
		self.file_menu.addAction(self.save_action)
		self.file_menu.addAction(self.save_as_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(self.import_action)
		self.file_menu.addAction(self.folder_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(self.close_action)

		self.edit_menu = self.menuBar().addMenu("&Edit")

		self.menuBar().addSeparator()

		self.help_menu = self.menuBar().addMenu("&Help")

	def create_toolbar(self):
		self.tool_bar = self.addToolBar('')
		self.tool_bar.setMovable(False)
		#self.tool_bar.setIconSize(QtCore.QSize(36, 36))
		self.tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

		self.tool_bar.addAction(self.search_ssr_action)
		self.tool_bar.addAction(self.search_cssr_action)
		self.tool_bar.addAction(self.search_vntr_action)
		self.tool_bar.addAction(self.search_itr_action)
		self.tool_bar.addAction(self.mapping_action)
		self.tool_bar.addAction(self.primer_action)

		#spacer = QWidget(self)
		#spacer.setSizePolicy(
		#	QSizePolicy.Expanding,
		#	QSizePolicy.Preferred
		#)
		#label = QLabel("Select file: ", self)

		#self.tool_bar.addWidget(spacer)
		#self.tool_bar.addWidget(label)
		#self.tool_bar.addWidget(self.file_select)

	def create_statusbar(self):
		self.status_bar = self.statusBar()
		self.status_bar.showMessage("Welcome to Krait2")

		#row count label
		rlabel = QLabel("Row:", self)
		self.status_bar.addPermanentWidget(rlabel)
		self.row_label = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.row_label)

		#column count label
		clabel = QLabel("Column:", self)
		self.status_bar.addPermanentWidget(clabel)
		self.col_label = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.col_label)

		#select count label
		slabel = QLabel("Select:", self)
		self.status_bar.addPermanentWidget(slabel)
		self.sel_label = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.sel_label)

	@Slot(int)
	def change_row_count(self, count):
		self.row_label.setText(str(count))

	@Slot(int)
	def change_column_count(self, count):
		self.col_label.setText(str(count))

	@Slot(int)
	def change_select_count(self, count):
		self.sel_label.setText(str(count))

	@Slot()
	def change_current_file(self, index):
		tables = ['ssr', 'cssr', 'vntr', 'itr', 'primer']
		rowid = self.file_table.get_clicked_rowid(index)

		if DB.table_exists('ssr{}'.format(rowid)):
			if self.ssr_table is None:
				self.ssr_table = KraitTableView(self, 'ssr')
				self.tab_widget.addTab(self.ssr_table, "SSR Results")
			else:
				idx = self.tab_widget.indexOf(self.ssr_table)
				self.tab_widget.setTabVisible(idx, True)

			self.ssr_table.update_table(rowid)

		else:
			if self.ssr_table is not None:
				idx = self.tab_widget.indexOf(self.ssr_table)
				self.tab_widget.setTabVisible(idx, False)

	@Slot(str)
	def show_status_message(self, msg):
		self.status_bar.showMessage(msg)

	@Slot(str)
	def show_error_message(self, err):
		QMessageBox.critical(self, 'Error', err)

	def open_project(self):
		pass

	def save_project(self):
		pass

	def save_project_as(self):
		save_file, _ = QFileDialog.getSaveFileName(self, filter="Krait Database (*.kdb)")

		if not save_file:
			return

		with DB.save_to_file(save_file) as backup:
			while not backup.done:
				backup.step(100)

	def import_fasta_files(self):
		files = QFileDialog.getOpenFileNames(self,
			caption = "Select one or more files to import",
			dir = "",
			filter = (
				"Fastas (*.fa *.fas *.fna *.fasta);;Gzipped Fastas "
				"(*.fa.gz *.fas.gz *.fna.gz *.fasta.gz);;All files (*.*)"
			)
		)

		fas = []
		for fa in files[0]:
			qf = QFileInfo(fa)
			fas.append((qf.baseName(), qf.size(), 'pending', fa))

		if fas:
			DB.insert_rows("INSERT INTO fastas VALUES (NULL,?,?,?,?)", fas)
			self.file_table.update_table()

	def import_fasta_folder(self):
		folder = QFileDialog.getExistingDirectory(self,
			caption = "Select a folder",
			dir = "",
			options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
		)

		if not folder:
			return

		it = QDirIterator(folder, QDir.Files, QDirIterator.Subdirectories)
		fas = []
		while it.hasNext():
			fa = it.next()
			qf = QFileInfo(fa)
			fas.append((qf.baseName(), qf.size(), 'pending', fa))

		if fas:
			DB.insert_rows("INSERT INTO fastas VALUES (NULL,?,?,?,?)", fas)
			self.file_table.update_table()


	def perform_ssr_search(self):
		threader = SSRWorkerThread(self, [12,7,5,4,4,4], 3)
		threader.start()
