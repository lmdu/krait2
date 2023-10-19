import time

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import * 

from utils import *
from stats import *
from filter import *
from config import *
from tables import *
from dialog import *
from seqview import *
from backend import *
from workers import *
from widgets import *

__all__ = ['KraitMainWindow']

class KraitMainWindow(QMainWindow):
	def __init__(self):
		super(KraitMainWindow, self).__init__()

		self.setWindowTitle("Krait v{}".format(KRAIT_VERSION))
		self.setWindowIcon(QIcon('icons/logo.svg'))

		self.tab_widget = QTabWidget(self)
		self.tab_widget.currentChanged.connect(self.on_tab_changed)
		#self.tab_widget.setStyleSheet("QTabWidget::pane { border: 0; }")
		#self.tab_widget.setTabBarAutoHide(True)
		#self.tab_widget.setTabShape(QTabWidget.Triangular)
		#self.tab_widget.setFrameStyle(QFrame.NoFrame)
		#self.tab_widget.currentChanged.connect(self.change_current_table)
		self.setCentralWidget(self.tab_widget)

		#self.filter_box = QLineEdit(self)
		#self.filter_box.setPlaceholderText("e.g. motif=AT and repeat>10")
		#self.filter_box.returnPressed.connect(self.set_table_filters)

		self.create_statusbar()

		#self.file_table = FastaTableView(self)
		self.create_fastx_tree()
		self.create_seq_view()
		self.create_annot_view()

		self.create_actions()
		self.create_menus()
		self.create_toolbar()
		
		#self.tab_widget.addTab(self.file_table, "Input Files")

		self.read_settings()

		self.table_widgets = {}

		self.current_worker = None

		#current table in backend displayed
		self.current_table = "fasta_0"

		#current fastx file id
		self.current_file = 0

		#filters
		self.current_filters = {}

		#search for all or selected
		self.search_all = True

		#opened project file
		self.project_file = None

	def create_fastx_tree(self):
		self.fastx_tree = KraitFastxTree(self)
		self.fastx_tree.row_clicked.connect(self.on_fastx_changed)

		self.fastx_dock = QDockWidget("Files", self)
		self.fastx_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
		self.fastx_dock.setWidget(self.fastx_tree)
		self.addDockWidget(Qt.LeftDockWidgetArea, self.fastx_dock)

	def create_seq_view(self):
		self.seq_view = KraitSequenceViewer(self)

		self.seq_dock = QDockWidget("Sequence", self)
		self.seq_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
		self.seq_dock.setWidget(self.seq_view)
		self.addDockWidget(Qt.BottomDockWidgetArea, self.seq_dock)

	def create_annot_view(self):
		self.annot_view = QTreeWidget(self)
		self.annot_view.setHeaderLabels(["Feature", "Position", "Strand", "ID", "Name"])
		self.annot_dock = QDockWidget("Annotaion", self)
		self.annot_dock.setAllowedAreas(Qt.RightDockWidgetArea)
		self.annot_dock.setWidget(self.annot_view)
		self.addDockWidget(Qt.RightDockWidgetArea, self.annot_dock)

	def closeEvent(self, event):
		if DB.has_fastx() and DB.changed:
			ret = QMessageBox.question(self, "Confirmation",
				"Would you like to save the results before closing window?"
			)

			if ret == QMessageBox.Yes:
				self.save_project()
				self.wait_task_finish()

		self.write_settings()

		#stop the running worker
		#if self.current_worker:
		#	self.current_worker.exit()

			#print('closed!')

		#event.ignore()

	def create_actions(self):
		#menu actions
		self.open_action = QAction("&Open project...", self,
			shortcut = QKeySequence.Open,
			#statusTip = "Open a project file",
			toolTip = "Open a project file",
			triggered = self.open_project
		)

		self.close_action = QAction("&Close project", self,
			shortcut = QKeySequence.Close,
			toolTip = "Close the opened project file",
			triggered = self.close_project
		)

		self.save_action = QAction("&Save project", self,
			shortcut = QKeySequence.Save,
			statusTip = "Save project",
			triggered = self.save_project
		)

		self.save_as_action = QAction("&Save project as...", self,
			shortcut = QKeySequence.SaveAs,
			statusTip = "Save project as",
			triggered = self.save_project_as
		)

		self.import_action = QAction("&Import sequence files...", self,
			statusTip = "Import fasta or fastq files",
			triggered = self.import_fastx_files
		)

		self.folder_action = QAction("&Import sequence files from folder...", self,
			statusTip = "Import all fasta or fastq files in a folder",
			triggered = self.import_fastx_folder
		)

		self.annotin_action = QAction("&Import annotation files...", self,
			statusTip = "Import GFF or GTF formatted annotation files",
			triggered = self.import_annotation_files
		)

		self.annotfolder_action = QAction("&Import annotation files from folder...", self,
			statusTip = "Import all GFF or GTF formatted annotation files in a folder",
			triggered = self.import_annotation_folder
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
		self.filter_set_action = QAction("&Do filter for current table", self,
			toolTip = "Filter rows from the current table",
			triggered = self.open_filter_dialog
		)
		self.search_param_action = QAction("&Repeat search parameters", self,
			shortcut = QKeySequence.Preferences,
			statusTip = "Set search parameters",
			triggered = self.open_search_param_dialog
		)

		self.primer_param_action = QAction("&Primer design parameters", self,
			statusTip = "Set primer parameters",
			triggered = self.open_primer_param_dialog
		)

		#view actions
		self.fastx_action = self.fastx_dock.toggleViewAction()
		self.fastx_action.setText("Show sequence files")

		self.seqview_action = self.seq_dock.toggleViewAction()
		self.seqview_action.setText("Show sequence viewer")

		#run actions
		#self.search_group_action = QActionGroup(self)
		#self.search_group_action.triggered.connect(self.search_switch)
		#self.search_all_action = QAction("Running for All Fastas", self, checkable=True, checked=True)
		#self.search_sel_action = QAction("Running for Selected Fastas", self, checkable=True)
		#self.search_group_action.addAction(self.search_all_action)
		#self.search_group_action.addAction(self.search_sel_action)
		self.cancel_action = QAction("&Cancel the running task", self,
			triggered = self.cancel_running_tasks
		)


		#help actions
		self.about_action = QAction("&About krait", self,
			statusTip = "About",
			triggered = self.open_about
		)

		self.doc_action = QAction("&Documentation", self,
			shortcut = QKeySequence.HelpContents,
			statusTip = "Documentation",
			triggered = self.open_documentation
		)

		self.issue_action = QAction("&Report issue", self,
			statusTip = "Report issues",
			triggered = self.report_issue
		)

		self.update_action = QAction("&Check for updates", self,
			statusTip = "Check for any updates",
			triggered = self.check_update
		)

		#toolbar actions
		self.search_ssr_action = QAction(QIcon("icons/ssr.svg"), "SSRs", self,
			#statusTip = "Search for perfect microsatellites",
			toolTip = "Search for perferct microsatellites",
			triggered = self.do_ssr_search
		)

		self.search_cssr_action = QAction(QIcon("icons/cssr.svg"), "cSSRs", self,
			toolTip = "Search for compound microsatellites",
			triggered = self.do_cssr_search
		)

		self.search_gtr_action = QAction(QIcon("icons/gtr.svg"), "GTRs", self,
			toolTip = "Search for GTRs",
			triggered = self.do_gtr_search
		)

		self.search_issr_action = QAction(QIcon("icons/issr.svg"), "iSSRs", self,
			toolTip = "Search for imperfect microsatellites",
			triggered = self.do_issr_search
		)

		self.locating_action = QAction(QIcon("icons/locating.svg"), "Mapping", self,
			toolTip = "Mapping tandem repeat sequences to gene features",
			triggered = self.do_str_mapping
		)

		self.primer_action = QAction(QIcon("icons/primer.svg"), "Primer", self,
			toolTip = "Design primers for selected tandem repeats",
			triggered = self.do_primer_design
		)

		self.stat_action = QAction(QIcon("icons/statistics.svg"), "Statistics", self,
			toolTip = "Perform statistics and generate statistics report",
			triggered = self.perform_stats_analysis
		)

		self.filter_action = QAction(QIcon("icons/filter.svg"), "Filter", self,
			toolTip = "Filter rows from the current table",
			triggered = self.open_filter_dialog
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

		self.view_menu = self.menuBar().addMenu("&View")
		self.view_menu.addAction(self.fastx_action)
		self.view_menu.addAction(self.seqview_action)

		self.run_menu = self.menuBar().addMenu("&Run")
		#self.run_menu.addAction(self.search_all_action)
		#self.run_menu.addAction(self.search_sel_action)
		self.run_menu.addAction(self.cancel_action)

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
		self.tool_bar.addAction(self.search_gtr_action)
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

		#file count label
		flabel = QLabel("File:", self)
		self.status_bar.addPermanentWidget(flabel)
		self.file_counter = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.file_counter)

		#row count label
		rlabel = QLabel("Row:", self)
		self.status_bar.addPermanentWidget(rlabel)
		self.row_counter = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.row_counter)

		#column count label
		clabel = QLabel("Column:", self)
		self.status_bar.addPermanentWidget(clabel)
		self.column_counter = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.column_counter)

		#select count label
		slabel = QLabel("Select:", self)
		self.status_bar.addPermanentWidget(slabel)
		self.select_counter = QLabel("0", self)
		self.status_bar.addPermanentWidget(self.select_counter)

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

	@Slot()
	def on_tab_changed(self, index):
		widget = self.tab_widget.currentWidget()
		widget.count_emit()
		
		if not self.current_filters:
			return

		for table in self.current_filters:
			table = table.split('_')[0]
			tab_widget = self.table_widgets.get(table, None)

			if tab_widget:
				tab_widget.set_filter('')

		self.current_filters = {}

	@Slot()
	def cancel_running_tasks(self):
		pass

	@Slot(int)
	def on_fastx_changed(self, index):
		#if self.current_file == index:
		#	return

		self.current_file = index
		self.current_filters = {}

		tables = ['info', 'ssr', 'cssr', 'issr','gtr', 'primer', 'stats']

		for table in tables:
			self.show_tab_widgets(table)

	@Slot(str, int)
	def show_tab_widgets(self, table, idx=None):
		if idx is not None and self.current_file != idx:
			return

		if self.current_file == 0:
			return

		tab_creators = {
			'info': (KraitTextBrowser, 'Info'),
			'ssr': (KraitSSRTable, 'SSRs'),
			'cssr': (KraitCSSRTable, 'cSSRs'),
			'issr': (KraitISSRTable, 'iSSRs'),
			'gtr': (KraitGTRTable, 'GTRs'),
			'primer': (KraitPrimerTable, 'Primers'),
			'stats': (KraitTextBrowser, 'Statistics')
		}

		if table == 'info':
			has_table = True
		else:
			has_table = DB.table_exists("{}_{}".format(table, self.current_file))

		if has_table:
			if table not in self.table_widgets:
				creator, title = tab_creators[table]
				self.table_widgets[table] = creator(self)
				self.tab_widget.addTab(self.table_widgets[table], title)
				idx = self.tab_widget.indexOf(self.table_widgets[table])
			else:
				idx = self.tab_widget.indexOf(self.table_widgets[table])
				self.tab_widget.setTabVisible(idx, True)

			self.tab_widget.setCurrentIndex(idx)

			if table == 'stats':
				report = get_stats_report(self.current_file)
				self.table_widgets[table].set_html(report)
	
			elif table == 'info':
				content = get_fastx_info(self.current_file)
				self.table_widgets[table].set_html(content)

			else:
				self.table_widgets[table].set_index(self.current_file)

		else:
			if table in self.table_widgets:
				idx = self.tab_widget.indexOf(self.table_widgets[table])
				self.tab_widget.setTabVisible(idx, False)

	def show_dna_sequence(self, category, repeat):
		if not self.seqview_action.isChecked():
			return

		if category == 'primer':
			settings = QSettings()
			default, convert = KRAIT_PRIMER_TAGS['PRIMER_FLANK_LENGTH']
			flank_len = settings.value('PRIMER/PRIMER_FLANK_LENGTH', default, convert)
			target, marks = generate_primer_marks(self.current_file, repeat, flank_len)

		else:
			target, marks = generate_tandem_marks(self.current_file, category, repeat)

		self.seq_view.mark_sequence(self.current_file, target, marks)
		#self.seq_view.set_sequence(self.current_file, cat, trs)

	def show_repeat_annotation(self, category, repeat):
		map_table = "map_{}".format(self.current_file)
		annot_table = "annot_{}".format(self.current_file)
		types = {'ssr': 1, 'cssr': 2, 'gtr': 3, 'issr': 4}
		cat = types.get(category, 0)

		if not cat or not DB.table_exists(map_table) or not DB.table_exists(annot_table):
			self.annot_view.clear()
			return

		sql = "SELECT * FROM {} WHERE type=? AND locus=? LIMIT 1".format(map_table)
		feat = DB.get_dict(sql, (cat, repeat.id))

		if not feat:
			self.annot_view.clear()
			return

		sql = "SELECT * FROM {} WHERE id IN ({})".format(annot_table, feat.parents)

		items = {}
		added = {}
		children = {}
		for parent in DB.get_dicts(sql):
			ancestors = get_feature_parents(parent, self.current_file)
			ancestors.reverse()
			ancestors.append(parent)

			for a in ancestors:
				item = QTreeWidgetItem((a.type,
					"{}:{}-{}".format(a.chrom, a.start, a.end),
					a.strand, a.fid, a.name
				))

				if a.parent == 0:
					if a.id not in items:
						items[a.id] = item

					father = items[a.id]
					father_id = a.id

				else:
					if father_id not in added:
						added[father_id] = set()

					if a.id not in added[father_id]:
						added[father_id].add(a.id)
						father.addChild(item)
						children[a.id] = item

					father = children[a.id]
					father_id = a.id

		self.annot_view.clear()
		self.annot_view.addTopLevelItems(list(items.values()))
		self.annot_view.expandAll()
		self.annot_view.header().setSectionResizeMode(QHeaderView.ResizeToContents)

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
		self.current_filters = {}

		if not isinstance(widget, QTextEdit):
			self.current_table = widget.real_table
			widget.emit_count()
		else:
			self.current_table = None

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

		if DB.has_fastx():
			ret = QMessageBox.question(self, "Confirmation",
				"Would you like to save previous results before opening new project file?"
			)

			if ret == QMessageBox.Yes:
				self.save_project()
				self.wait_task_finish()

		open_file, _ = QFileDialog.getOpenFileName(self, filter="Krait Project File (*.kpf)")

		if not open_file:
			return

		self.project_file = open_file
		DB.change_db(self.project_file)
		self.fastx_tree.update_model()

		self.show_status_message("Open new project file {}".format(self.project_file))

		self.setWindowTitle("{} - Krait v{}".format(self.project_file, KRAIT_VERSION))

	def save_project(self):
		if self.project_file is None:
			save_file, _ = QFileDialog.getSaveFileName(self, filter="Krait Project File (*.kpf)")

			if not save_file:
				return

			self.project_file = save_file
			self.run_work_thread(KraitSaveWorker, save_file)
			self.wait_task_finish()
			DB.change_db(save_file)
			self.setWindowTitle("{} - Krait v{}".format(save_file, KRAIT_VERSION))
			self.fastx_tree.update_model()
			
		else:
			if DB.changed:
				DB.commit()
				DB.begin()

			self.progress_bar.setValue(100)

		self.show_status_message("Successfully saved to {}".format(self.project_file))

	def save_project_as(self):
		save_file, _ = QFileDialog.getSaveFileName(self, filter="Krait Project File (*.kpf)")

		if not save_file:
			return

		self.run_work_thread(KraitSaveWorker, save_file)

	def close_project(self):
		if DB.has_fastx():
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
		self.fastx_tree.update_model()

		self.setWindowTitle("Krait v{}".format(KRAIT_VERSION))

	def import_fastx_files(self):
		files = QFileDialog.getOpenFileNames(self,
			caption = "Select fasta/q files to import",
			dir = "",
			filter = (
				"Fastx file (*.fa *.fas *.fna *.fasta "
				"*.fa.gz *.fas.gz *.fna.gz *.fasta.gz "
				"*.fq *.fastq *.fq.gz *.fastq.gz);;"
				"All files (*.*)"
			)
		)

		fas = []
		for fa in files[0]:
			qf = QFileInfo(fa)
			name = qf.baseName()

			fas.append((name, fa))

		if fas:
			sql = "INSERT INTO fastx (name, fpath) VALUES (?,?)"
			DB.insert_rows(sql, fas)
			self.fastx_tree.update_model()

	def import_fastx_folder(self):
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

			if fa.endswith('.fxi'):
				continue

			qf = QFileInfo(fa)
			name = qf.baseName()
			fas.append((name, fa))

		if fas:
			sql = "INSERT INTO fastx (name, fpath) VALUES (?,?)"
			DB.insert_rows(sql, fas)
			self.fastx_tree.update_model()

	def import_annotation_files(self):
		files = QFileDialog.getOpenFileNames(self,
			caption = "Select GTF/GFF files to import",
			dir = "",
			filter = (
				"GXF (*.gtf *.gff *.gtf.gz *.gff.gz);;"
				"All files (*.*)"
			)
		)

		if not files[0]:
			return

		sql = "SELECT id,name FROM fastx"
		fastx = {row[1]: row[0] for row in DB.query(sql)}

		annot_files = []
		error_files = []
		for af in files[0]:
			qf = QFileInfo(af)
			name = qf.baseName()

			if name in fastx:
				annot_files.append((af, fastx[name]))
			else:
				error_files.append(af)

		if annot_files:
			sql = "UPDATE fastx SET apath=? WHERE id=?"
			DB.update_rows(sql, annot_files)

		if error_files:
			msg = (
				"Could not find corresponding sequence files for:<br> {}<br>"
				"Make sure annotation and sequence files have the same name"
			).format("<br>".join(error_files))

			QMessageBox.warning(self, "Warning", msg)

	def import_annotation_folder(self):
		folder = QFileDialog.getExistingDirectory(self,
			caption = "Select a folder",
			dir = "",
			options = QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
		)

		if not folder:
			return

		sql = "SELECT id,name FROM fastx"
		fastx = {row[1]: row[0] for row in DB.query(sql)}

		it = QDirIterator(folder, QDir.Files, QDirIterator.Subdirectories)
		
		annot_files = []
		error_files = []
		
		while it.hasNext():
			af = it.next()
			qf = QFileInfo(af)
			name = qf.baseName()

			if name in fastx:
				annot_files.append((af, fastx[name]))
			else:
				error_files.append(af)

		if annot_files:
			sql = "UPDATE fastx SET apath=? WHERE id=?"
			DB.update_rows(sql, annot_files)

		if error_files:
			msg = (
				"Could not find corresponding sequence files for:<br> {}"
				"<br>Make sure annotation and sequence files have the same name"
			).format("<br>".join(error_files))

			QMessageBox.warning(self, "Warning", msg)

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
		pool = QThreadPool.globalInstance()
		pool.waitForDone()

	def perform_new_task(self, worker):
		if not DB.has_fastx():
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

	def check_work_thread(self):
		pool = QThreadPool.globalInstance()

		if pool.activeThreadCount() > 0:
			QMessageBox.warning(self, "Warning", "A task is already running")
			return False

		return True

	def check_input_fastx(self):
		if not DB.has_fastx():
			QMessageBox.critical(self, "Error", "There are no input fasta or fastq files")
			return False

		return True

	def run_work_thread(self, threader, *args):
		if not self.check_input_fastx():
			return

		if not self.check_work_thread():
			return

		self.current_worker = threader(*args)
		self.current_worker.signals.progress.connect(self.progress_bar.setValue)
		self.current_worker.signals.failure.connect(self.show_error_message)
		self.current_worker.signals.show_tab.connect(self.show_tab_widgets)
		self.current_worker.signals.messages.connect(self.show_status_message)
		QThreadPool.globalInstance().start(self.current_worker)

	def do_ssr_search(self):
		self.run_work_thread(KraitSSRSearchWorker)

	def check_ssr_search(self):
		for table in DB.get_tables():
			if table.startswith('ssr'):
				if DB.get_count(table):
					return True

		QMessageBox.critical(self, "Error", "Please search for SSRs first before searching cSSRs.")
		return False

	def do_cssr_search(self):
		if not self.check_ssr_search():
			return

		self.run_work_thread(KraitCSSRSearchWorker)

	def do_gtr_search(self):
		self.run_work_thread(KraitGTRSearchWorker)

	def do_issr_search(self):
		self.run_work_thread(KraitISSRSearchWorker)

	def do_str_mapping(self):
		self.run_work_thread(KraitMappingWorker)

	def do_primer_design(self):
		try:
			widget = self.tab_widget.currentWidget()
			rtype, count, rows = widget.get_selected_rows()
		except:
			count = 0

		if not count or rtype not in {'ssr', 'issr', 'cssr', 'gtr'}:
			QMessageBox.warning(self, "Warning", "Please select some tandem repeats for primer design")
			return

		self.run_work_thread(KraitPrimerDesignWorker, self.current_file, count, rows, rtype)

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

	def get_current_table(self):
		try:
			tab_widget = self.tab_widget.currentWidget()
			table = tab_widget.table_real
		except:
			table = None

		return table

	def open_filter_dialog(self):
		table = self.get_current_table()

		if table is None:
			return QMessageBox.warning(self, "Warning", "There is no table to filter")

		dialog = KraitFilterDialog(self, table)
		dialog.show()

	def set_filter(self, table, filters):
		try:
			tab_widget = self.tab_widget.currentWidget()

			if table == tab_widget.table_real:
				tab_widget.set_filter(filters)
		except:
			pass

	def open_search_param_dialog(self):
		dialog = KraitSearchSettingDialog(self)
		dialog.show()

	def open_primer_param_dialog(self):
		dialog = KraitPrimerSettingDialog(self)
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
