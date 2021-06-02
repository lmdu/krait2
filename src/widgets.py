import time

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 

from config import *
from tables import *
from backend import *
from workers import *
from utils import *
from filter import *
from preference import *

__all__ = ['KraitMainWindow']

class KraitMainWindow(QMainWindow):
	def __init__(self):
		super(KraitMainWindow, self).__init__()

		self.setWindowTitle("Krait2 v{}".format(KRAIT_VERSION))
		self.setWindowIcon(QIcon('icons/logo.svg'))

		self.tab_widget = QTabWidget(self)
		self.setCentralWidget(self.tab_widget)
		self.tab_widget.currentChanged.connect(self.change_current_table)

		#self.filter_box = QLineEdit(self)
		#self.filter_box.setPlaceholderText("e.g. motif=AT and repeat>10")
		#self.filter_box.returnPressed.connect(self.set_table_filters)

		self.create_actions()
		self.create_menus()
		self.create_toolbar()
		self.create_statusbar()

		self.file_table = FastaTableView(self)
		self.tab_widget.addTab(self.file_table, "Input Files")

		self.read_settings()

		self.ssr_table = None
		self.cssr_table = None
		self.vntr_table = None
		self.itr_table = None
		self.threader = None

		#current table in backend displayed
		self.current_table = "fasta"

		#filters
		self.current_filter = []

	def closeEvent(self, event):
		self.write_settings()

	def create_actions(self):
		#menu actions
		self.open_action = QAction("&Open Project...", self,
			shortcut = QKeySequence.Open,
			statusTip = "Open a project file",
			triggered = self.open_project
		)

		self.save_action = QAction("&Save Project", self,
			shortcut = QKeySequence.Save,
			statusTip = "Save project",
			triggered = self.save_project
		)

		self.save_as_action = QAction("&Save Project As...", self,
			shortcut = QKeySequence.SaveAs,
			statusTip = "Save project as",
			triggered = self.save_project_as
		)

		self.import_action = QAction("&Import Fasta Files...", self,
			statusTip = "Import fasta files",
			triggered = self.import_fasta_files
		)

		self.folder_action = QAction("&Import Fasta Files in Folder...", self,
			statusTip = "Import all fasta files in a folder",
			triggered = self.import_fasta_folder
		)

		self.annotin_action = QAction("&Import Annotation Files...", self,
			statusTip = "Import GFF or GTF formatted annotation files",
			triggered = self.import_fasta_files
		)

		self.annotfolder_action = QAction("&Import Annotation Files in Folder...", self,
			statusTip = "Import all GFF or GTF formatted annotation files in a folder",
			triggered = self.import_fasta_folder
		)

		self.close_action = QAction("&Exit", self,
			shortcut = "Alt+Q",
			statusTip = "Exit",
			triggered = self.close
		)

		#edit actions
		self.search_param_action = QAction("&Set Search Parameters", self,
			shortcut = QKeySequence.Preferences,
			statusTip = "Set search parameters",
			triggered = self.open_search_param_dialog
		)

		self.primer_param_action = QAction("&Set Primer Parameters", self,
			statusTip = "Set primer parameters",
			triggered = self.open_primer_param_dialog
		)

		#help actions
		self.about_action = QAction("&About Krait2", self,
			statusTip = "About",
			triggered = self.open_about
		)

		self.doc_action = QAction("&Documentation", self,
			shortcut = QKeySequence.HelpContents,
			statusTip = "Documentation",
			triggered = self.open_documentation
		)

		self.issue_action = QAction("&Report Issue", self,
			statusTip = "Report issues",
			triggered = self.report_issue
		)

		self.update_action = QAction("&Check for Updates", self,
			statusTip = "Check for any updates",
			triggered = self.check_update
		)

		#toolbar actions
		self.search_ssr_action = QAction(QIcon("icons/ssr.svg"), "SSRs", self,
			#statusTip = "Search for perfect microsatellites",
			toolTip = "Search for perferct microsatellites",
			triggered = self.perform_ssr_search
		)

		self.search_cssr_action = QAction(QIcon("icons/cssr.svg"), "cSSRs", self,
			toolTip = "Search for compound microsatellites",
			triggered = self.close
		)

		self.search_vntr_action = QAction(QIcon("icons/vntr.svg"), "VNTRs", self,
			toolTip = "Search for VNTRs",
			triggered = self.perform_vntr_search
		)

		self.search_itr_action = QAction(QIcon("icons/itr.svg"), "ITRs", self,
			toolTip = "Search for imperfect tandem repeats",
			triggered = self.perform_itr_search
		)

		self.mapping_action = QAction(QIcon("icons/mapping.svg"), "Mapping", self,
			toolTip = "Mapping tandem repeats to gene",
			triggered = self.close
		)

		self.primer_action = QAction(QIcon("icons/primer.svg"), "Primer", self,
			toolTip = "Design primers for selected repeats",
			triggered = self.close
		)

		self.stat_action = QAction(QIcon("icons/statistics.svg"), "Statistics", self,
			toolTip = "Perform statistics and generate statistics report",
			triggered = self.close
		)

		self.filter_action = QAction(QIcon("icons/filter.svg"), "Filter", self,
			toolTip = "Filter rows from the current table",
			triggered = self.open_filter
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
		self.file_menu.addAction(self.annotin_action)
		self.file_menu.addAction(self.annotfolder_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(self.close_action)

		self.edit_menu = self.menuBar().addMenu("&Edit")
		self.edit_menu.addAction(self.search_param_action)
		self.edit_menu.addAction(self.primer_param_action)

		#self.menuBar().addSeparator()

		self.help_menu = self.menuBar().addMenu("&Help")
		self.help_menu.addAction(self.doc_action)
		self.help_menu.addAction(self.issue_action)
		self.help_menu.addSeparator()
		self.help_menu.addAction(self.update_action)
		self.help_menu.addSeparator()
		self.help_menu.addAction(self.about_action)
		

	def create_toolbar(self):
		self.tool_bar = self.addToolBar('')
		self.tool_bar.setMovable(False)
		#self.tool_bar.setIconSize(QtCore.QSize(36, 36))
		#self.tool_bar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.tool_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

		self.tool_bar.addAction(self.search_ssr_action)
		self.tool_bar.addAction(self.search_cssr_action)
		self.tool_bar.addAction(self.search_vntr_action)
		self.tool_bar.addAction(self.search_itr_action)
		self.tool_bar.addAction(self.mapping_action)
		self.tool_bar.addAction(self.primer_action)
		self.tool_bar.addAction(self.stat_action)
		self.tool_bar.addAction(self.filter_action)

		#spacer = QWidget(self)
		#spacer.setSizePolicy(
		#	QSizePolicy.Expanding,
		#	QSizePolicy.Preferred
		#)
		#label = QLabel("Select file: ", self)

		#self.tool_bar.addWidget(spacer)
		#self.tool_bar.addWidget(label)
		#self.tool_bar.addWidget(self.file_select)

		#progress_circle = ProgressCircle()
		#progress_circle.setFixedSize(30, 30)
		#self.tool_bar.addWidget(progress_circle)
		#self.tool_bar.addWidget(self.filter_box)


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

		#progress bar
		self.progress_bar = QProgressBar(self)
		self.progress_bar.setMaximumWidth(100)
		self.progress_bar.setMaximumHeight(15)
		self.progress_bar.setAlignment(Qt.AlignCenter)
		self.status_bar.addPermanentWidget(self.progress_bar)

	def write_settings(self):
		settings = QSettings()

		settings.beginGroup("SSR")
		settings.setValue("min_repeats", [12, 7, 5, 4, 4, 4])
		settings.endGroup()

		if not self.isMaximized():
			settings.beginGroup("Window")
			settings.setValue("size", self.size())
			settings.setValue("pos", self.pos())
			settings.endGroup()

	def read_settings(self):
		settings = QSettings()
		settings.beginGroup("Window")
		self.resize(settings.value("size", QSize(800, 600)))
		self.move(settings.value("pos", QPoint(200, 200)))

	@Slot(int)
	def change_progress(self, p):
		self.progress_bar.setValue(p)

	@Slot(int)
	def change_task_status(self, fasta_id):
		self.file_table.update_status(fasta_id)

	@Slot(int)
	def change_row_count(self, count):
		self.row_label.setText(str(count))

	@Slot(int)
	def change_column_count(self, count):
		self.col_label.setText(str(count))

	@Slot(int)
	def change_select_count(self, count):
		self.sel_label.setText(str(count))

	@Slot(int)
	def change_current_table(self, index):
		widget = self.tab_widget.widget(index)
		widget.emit_count()
		self.current_table = widget.real_table
		self.current_filter = []

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

		if DB.table_exists('vntr{}'.format(rowid)):
			if self.vntr_table is None:
				self.vntr_table = KraitTableView(self, 'vntr')
				self.tab_widget.addTab(self.vntr_table, "VNTR Results")
			else:
				idx = self.tab_widget.indexOf(self.vntr_table)
				self.tab_widget.setTabVisible(idx, True)

			self.vntr_table.update_table(rowid)

		else:
			if self.vntr_table is not None:
				idx = self.tab_widget.indexOf(self.vntr_table)
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
			name = qf.baseName()
			size = qf.size()

			if is_gzip_compressed(fa):
				isize = get_uncompressed_size(fa)

				if isize > size:
					size = isize

			fas.append((name, size, 'pending', fa))

		if fas:
			DB.insert_rows("INSERT INTO fasta VALUES (NULL,?,?,?,?)", fas)
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
			name = qf.baseName()
			size = qf.size()

			if is_gzip_compressed(fa):
				isize = get_uncompressed_size(fa)

				if isize > size:
					size = isize

			fas.append((name, size, 'pending', fa))

		if fas:
			DB.insert_rows("INSERT INTO fasta VALUES (NULL,?,?,?,?)", fas)
			self.file_table.update_table()

	def perform_ssr_search(self):
		self.threader = SSRSearchThread(self)
		self.threader.start()

	def perform_vntr_search(self):
		#self.threader = VNTRSearchThread(self)
		#self.threader.start()

		if self.threader:
			print('yes')
		else:
			print('no')

	def perform_itr_search(self):
		self.threader = ITRSearchThread(self)
		self.threader.start()

	def perform_primer_design(self):
		self.threader = PrimerDesignThread(self, self.current_table)
		self.threader.start()

	def open_filter(self):
		dialog = FilterDialog(self)
		dialog.show()

	def set_filter(self, filters):
		table_widget = self.tab_widget.currentWidget()
		table_widget.set_filter(filters)

	def open_search_param_dialog(self):
		dialog = PreferenceDialog(self)
		dialog.show()

	def open_primer_param_dialog(self):
		dialog = PreferenceDialog(self)
		dialog.goto_primer_panel()
		dialog.show()

	def open_about(self):
		QMessageBox.about(self, "About", KRAIT_ABOUT)

	def open_documentation(self):
		QDesktopServices.openUrl(QUrl("https://krait2.readthedocs.io"))

	def report_issue(self):
		QDesktopServices.openUrl(QUrl("https://github.com/lmdu/krait2/issues"))

	def check_update(self):
		QDesktopServices.openUrl(QUrl("https://github.com/lmdu/krait2/releases"))

	def get_selected_rows(self):
		table_widget = self.tab_widget.currentWidget()
		return table_widget.get_selected_rows()
