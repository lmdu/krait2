import time

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 

from utils import *
from stats import *
from filter import *
from config import *
from tables import *
from backend import *
from workers import *
from preference import *

__all__ = ['KraitMainWindow']

class KraitMainWindow(QMainWindow):
	def __init__(self):
		super(KraitMainWindow, self).__init__()

		self.setWindowTitle("Krait2 v{}".format(KRAIT_VERSION))
		self.setWindowIcon(QIcon('icons/logo.svg'))

		self.tab_widget = QTabWidget(self)
		#self.tab_widget.setStyleSheet("QTabWidget::pane { border: 0; }")
		#self.tab_widget.setTabBarAutoHide(True)
		#self.tab_widget.setTabShape(QTabWidget.Triangular)
		#self.tab_widget.setFrameStyle(QFrame.NoFrame)
		self.tab_widget.currentChanged.connect(self.change_current_table)
		self.setCentralWidget(self.tab_widget)

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

		self.table_widgets = {
			'ssr': None,
			'cssr': None,
			'vntr': None,
			'issr': None,
			'primer': None,
			'stats': None
		}

		self.threader = None

		#current table in backend displayed
		self.current_table = "fasta_0"

		#current fasta file id
		self.current_file = 0

		#filters
		self.current_filter = []

		#search for all or selected
		self.search_all = True

		#opened project file
		self.project_file = None

	def closeEvent(self, event):
		self.write_settings()

	def create_actions(self):
		#menu actions
		self.open_action = QAction("&Open Project...", self,
			shortcut = QKeySequence.Open,
			#statusTip = "Open a project file",
			toolTip = "Open a project file",
			triggered = self.open_project
		)

		self.close_action = QAction("&Close Project", self,
			shortcut = QKeySequence.Close,
			toolTip = "Close the opened project file",
			triggered = self.close_project
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
			triggered = self.import_annot_files
		)

		self.annotfolder_action = QAction("&Import Annotation Files in Folder...", self,
			statusTip = "Import all GFF or GTF formatted annotation files in a folder",
			triggered = self.import_annot_folder
		)

		self.export_select_action = QAction("&Export Selected Rows...", self,
			statusTip = "Export selected rows in the current table",
			triggered = self.export_selected_rows
		)

		self.export_whole_action = QAction("&Export All Rows...", self,
			statusTip = "Export all rows in the current table",
			triggered = self.export_current_table
		)

		self.export_all_action = QAction("&Export All Tables...", self,
			statusTip = "Export all result tables of all input files to a folder",
			triggered = self.export_all_tables
		)

		self.exit_action = QAction("&Exit", self,
			shortcut = "Alt+Q",
			statusTip = "Exit",
			triggered = self.close
		)

		#edit actions
		self.filter_set_action = QAction("&Filter Rows in Current Table", self,
			toolTip = "Filter rows from the current table",
			triggered = self.open_filter
		)
		self.search_param_action = QAction("&Set Search Parameters", self,
			shortcut = QKeySequence.Preferences,
			statusTip = "Set search parameters",
			triggered = self.open_search_param_dialog
		)

		self.primer_param_action = QAction("&Set Primer Parameters", self,
			statusTip = "Set primer parameters",
			triggered = self.open_primer_param_dialog
		)

		#run actions
		self.search_group_action = QActionGroup(self)
		self.search_group_action.triggered.connect(self.search_switch)
		self.search_all_action = QAction("Running for All Fastas", self, checkable=True, checked=True)
		self.search_sel_action = QAction("Running for Selected Fastas", self, checkable=True)
		self.search_group_action.addAction(self.search_all_action)
		self.search_group_action.addAction(self.search_sel_action)

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

		self.search_issr_action = QAction(QIcon("icons/issr.svg"), "iSSRs", self,
			toolTip = "Search for imperfect microsatellites",
			triggered = self.perform_issr_search
		)

		self.locating_action = QAction(QIcon("icons/locating.svg"), "locating", self,
			toolTip = "Locate tandem repeat sequences to gene features",
			triggered = self.perform_tre_locating
		)

		self.primer_action = QAction(QIcon("icons/primer.svg"), "Primer", self,
			toolTip = "Design primers for selected repeats",
			triggered = self.perform_primer_design
		)

		self.stat_action = QAction(QIcon("icons/statistics.svg"), "Statistics", self,
			toolTip = "Perform statistics and generate statistics report",
			triggered = self.perform_stats_analysis
		)

		self.filter_action = QAction(QIcon("icons/filter.svg"), "Filter", self,
			toolTip = "Filter rows from the current table",
			triggered = self.open_filter
		)

	def create_menus(self):
		self.file_menu = self.menuBar().addMenu("&File")
		self.file_menu.addAction(self.open_action)
		self.file_menu.addAction(self.close_action)
		self.file_menu.addAction(self.save_action)
		self.file_menu.addAction(self.save_as_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(self.import_action)
		self.file_menu.addAction(self.folder_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(self.annotin_action)
		self.file_menu.addAction(self.annotfolder_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(self.export_select_action)
		self.file_menu.addAction(self.export_whole_action)
		self.file_menu.addAction(self.export_all_action)
		self.file_menu.addSeparator()
		self.file_menu.addAction(self.exit_action)

		self.edit_menu = self.menuBar().addMenu("&Edit")
		self.edit_menu.addAction(self.filter_set_action)
		self.edit_menu.addSeparator()
		self.edit_menu.addAction(self.search_param_action)
		self.edit_menu.addAction(self.primer_param_action)

		self.run_menu = self.menuBar().addMenu("&Run")
		self.run_menu.addAction(self.search_all_action)
		self.run_menu.addAction(self.search_sel_action)

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
		self.tool_bar.addAction(self.search_issr_action)
		self.tool_bar.addAction(self.locating_action)
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

	def show_table(self, table):
		if DB.table_exists("{}_{}".format(table, self.current_file)):
			if self.table_widgets[table] is None:
				if table == 'primer':
					self.table_widgets[table] = PrimerTableView(self)
					title = "Primer Results"

				elif table == 'stats':
					self.table_widgets[table] = QTextEdit(self)
					self.table_widgets[table].setReadOnly(True)
					title = "Statistical Report"

				else:
					self.table_widgets[table] = KraitTableView(self, table)
					title = "{} Results".format(table.upper())

				self.tab_widget.addTab(self.table_widgets[table], title)

			else:
				idx = self.tab_widget.indexOf(self.table_widgets[table])
				self.tab_widget.setTabVisible(idx, True)

			if table == 'stats':
				report = get_stats_report(self.current_file)
				self.table_widgets[table].setHtml(report)
			else:
				self.table_widgets[table].update_table(self.current_file)

		else:
			if self.table_widgets[table] is not None:
				idx = self.tab_widget.indexOf(self.table_widgets[table])
				self.tab_widget.setTabVisible(idx, False)

	@Slot()
	def search_switch(self, action):
		if action == self.search_all_action:
			self.search_all = True
		else:
			self.search_all = False

	@Slot()
	def show_primer_table(self):
		self.show_table('primer')

	@Slot()
	def show_stats_view(self):
		self.show_table('stats')

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
		self.current_filter = []

		if not isinstance(widget, QTextEdit):
			self.current_table = widget.real_table
			widget.emit_count()
		else:
			self.current_table = None

	@Slot()
	def change_current_file(self, index):
		#get current fasta id in backend
		self.current_file = self.file_table.get_clicked_rowid(index)
		tables = ['ssr', 'cssr', 'vntr', 'issr', 'primer', 'stats']

		for table in tables:
			self.show_table(table)

	@Slot(str)
	def show_status_message(self, msg):
		self.status_bar.showMessage(msg)

	@Slot(str)
	def show_error_message(self, err):
		QMessageBox.critical(self, 'Error', err)

	def open_project(self):
		if self.project_file:
			ret = QMessageBox.question(self, "Confirmation",
				"A project file is already opened. Would you like to open a new project file?"
			)

			if ret == QMessageBox.No:
				return

		if DB.has_fasta():
			ret = QMessageBox.question(self, "Confirmation",
				"Would you like to save previous results before opening new project file?"
			)

			if ret == QMessageBox.Yes:
				self.save_project()

				#wait for save task finish
				self.wait_task_finish()

		open_file, _ = QFileDialog.getOpenFileName(self, filter="Krait Database (*.kdb)")

		if not open_file:
			return

		self.project_file = open_file
		DB.change_db(self.project_file)
		self.file_table.update_table()

		self.show_status_message("Open new project file {}".format(self.project_file))

	def save_project(self):
		if self.project_file is None:
			save_file, _ = QFileDialog.getSaveFileName(self, filter="Krait Database (*.kdb)")

			if not save_file:
				return

			self.project_file = save_file

			worker = SaveProjectThread(self, self.project_file)
			worker.finished.connect(lambda : DB.change_db(self.project_file))
			self.perform_new_task(worker)
		else:
			if DB.changed:
				DB.commit()
				DB.begin()

			self.show_status_message("Successfully saved to {}".format(self.project_file))
			self.progress_bar.setValue(100)			

	def save_project_as(self):
		save_file, _ = QFileDialog.getSaveFileName(self, filter="Krait Database (*.kdb)")

		if not save_file:
			return

		worker = SaveProjectThread(self, save_file)
		self.perform_new_task(worker)

		self.show_status_message("Successfully saved to {}".format(save_file))

	def close_project(self):
		if DB.has_fasta():
			if not self.project_file or (self.project_file and DB.changed):
				ret = QMessageBox.question(self, "Confirmation",
					"Would you like to save results before closing project",
					QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
				)

				if ret == QMessageBox.Cancel:
					return

				if ret == QMessageBox.Yes:
					self.save_project()
					self.wait_task_finish()

		self.project_file = None
		DB.change_db(':memory:')
		self.file_table.update_table()

		self.show_status_message("Project was successfully closed")

	def import_fasta_files(self):
		files = QFileDialog.getOpenFileNames(self,
			caption = "Select one or more files to import",
			dir = "",
			filter = "Fasta file (*.fa *.fas *.fna *.fasta *.fa.gz *.fas.gz *.fna.gz *.fasta.gz);;All files (*.*)"
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
			DB.insert_rows("INSERT INTO fasta_0 VALUES (NULL,?,?,?,?,NULL)", fas)
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
			DB.insert_rows("INSERT INTO fasta_0 VALUES (NULL,?,?,?,?,NULL)", fas)
			self.file_table.update_table()

	def import_annot_files(self):
		files = QFileDialog.getOpenFileNames(self,
			caption = "Select one or more files to import",
			dir = "",
			filter = "GFF or GTF (*.gtf *.gff *.gtf.gz *.gff.gz);;All files (*.*)"
		)

		annot_files = []
		for af in files[0]:
			qf = QFileInfo(af)
			name = qf.baseName()
			fa_id = DB.get_one("SELECT id FROM fasta_0 WHERE name=?", (name,))

			if fa_id:
				annot_files.append((af, fa_id))

		if annot_files:
			DB.insert_rows("UPDATE fasta_0 SET annotation=? WHERE id=?", annot_files)
			self.file_table.update_table()

	def import_annot_folder(self):
		folder = QFileDialog.getExistingDirectory(self,
			caption = "Select a folder",
			dir = "",
			options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
		)

		if not folder:
			return

		it = QDirIterator(folder, QDir.Files, QDirIterator.Subdirectories)
		annot_files = []
		while it.hasNext():
			af = it.next()
			qf = QFileInfo(af)
			name = qf.baseName()

			fa_id = DB.get_one("SELECT id FROM fasta_0 WHERE name=?", (name,))

			if fa_id:
				annot_files.append((af, fa_id))

		if annot_files:
			DB.insert_rows("UPDATE fasta_0 SET annotation=? WHERE id=?", annot_files)
			self.file_table.update_table()

	def export_selected_rows(self):
		out_file, _ = QFileDialog.getSaveFileName(self, filter="TSV (*.tsv);;CSV (*.csv)")

		if not out_file:
			return

		worker = ExportSelectedRowsThread(self, self.current_table, out_file)
		self.perform_new_task(worker)

	def export_current_table(self):
		out_file, _ = QFileDialog.getSaveFileName(self, filter="TSV (*.tsv);;CSV (*.csv)")

		if not out_file:
			return

		worker = ExportWholeTableThread(self, self.current_table, out_file)
		self.perform_new_task(worker)

	def export_all_tables(self):
		out_dir = QFileDialog.getExistingDirectory(self)

		if not out_dir:
			return

		worker = ExportAllTablesThread(self, out_dir)
		self.perform_new_task(worker)

	def wait_task_finish(self):
		if self.threader:
			self.threader.wait()

	def perform_new_task(self, worker):
		if not DB.has_fasta():
			return QMessageBox.critical(self, "Error",
				"There are no input fasta files to process. Please import fasta files!"
			)

		if not self.search_all:
			if not self.file_table.has_selection():
				return QMessageBox.critical(self, "Error",
					'You have specified "Search for Selected Fastas" mode. However, no input fastas were selected to process!'
				)

		if self.threader is not None and self.threader.isRunning():
			return QMessageBox.warning(self, "Warning",
				"Could not start new task. There is already another task running. Please wait..."
			)

		self.threader = worker
		self.threader.start()

	def perform_ssr_search(self):
		worker = SSRSearchThread(self)
		self.perform_new_task(worker)

	def perform_vntr_search(self):
		worker = VNTRSearchThread(self)
		self.perform_new_task(worker)

	def perform_issr_search(self):
		worker = ISSRSearchThread(self)
		self.perform_new_task(worker)

	def perform_primer_design(self):
		worker = PrimerDesignThread(self, self.current_table)
		worker.finished.connect(self.show_primer_table)
		self.perform_new_task(worker)

	def perform_tre_locating(self):
		worker = TRELocatingThread(self)
		self.perform_new_task(worker)

	def perform_stats_analysis(self):
		worker = StatisticsThread(self)
		worker.finished.connect(self.show_stats_view)
		self.perform_new_task(worker)

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
