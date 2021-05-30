from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

__all__ = ['PreferenceDialog']

class PrimerTagLabel(QLabel):
	base_url = "https://primer3.org/manual.html#{}"

	def __init__(self, name, tag, parent=None):
		super().__init__(parent)
		self.tag = tag
		self.setText('<a href="#{}">{}</a>'.format(tag, name))
		self.linkActivated.connect(self.open_link)

	@Slot()
	def open_link(self):
		url = QUrl(self.base_url.format(self.tag))
		QDesktopServices.openUrl(url)

class PrimerParameterPanel(QWidget):
	def __init__(self, parent=None):
		super(PrimerParameterPanel, self).__init__(parent)
		self.settings = QSettings()

		general_group = KraitGroupBox("General settings")
		general_layout = QVBoxLayout()
		general_group.setLayout(general_layout)
		product_layout = QGridLayout()
		general_layout.addLayout(product_layout)
		product_layout.setColumnStretch(0, 1)

		self.product_size = QLineEdit()
		self.primer_num = QSpinBox()
		
		product_layout.addWidget(PrimerTagLabel("Product size ranges", 'PRIMER_PRODUCT_SIZE_RANGE'), 0, 0)
		product_layout.addWidget(PrimerTagLabel("# of primers to return", 'PRIMER_NUM_RETURN'), 0, 1)
		product_layout.addWidget(self.product_size, 1, 0)
		product_layout.addWidget(self.primer_num, 1, 1)
		
		size_layout = QGridLayout()
		general_layout.addLayout(size_layout)
		size_layout.setColumnStretch(2, 1)
		size_layout.setColumnStretch(4, 1)
		size_layout.setColumnStretch(6, 1)

		self.size_min = QSpinBox()
		self.size_opt = QSpinBox()
		self.size_max = QSpinBox()
		self.gc_min = QDoubleSpinBox()
		self.gc_max = QDoubleSpinBox()
		self.gc_opt = QDoubleSpinBox()
		self.tm_min = QDoubleSpinBox()
		self.tm_opt = QDoubleSpinBox()
		self.tm_max = QDoubleSpinBox()

		size_layout.addWidget(QLabel("Primer size (bp)"), 0, 0)
		size_layout.addWidget(PrimerTagLabel("Min", 'PRIMER_MIN_SIZE'), 0, 1)
		size_layout.addWidget(self.size_min, 0, 2)
		size_layout.addWidget(PrimerTagLabel("Opt", 'PRIMER_OPT_SIZE'), 0, 3)
		size_layout.addWidget(self.size_opt, 0, 4)
		size_layout.addWidget(PrimerTagLabel("Max", 'PRIMER_MAX_SIZE'), 0, 5)
		size_layout.addWidget(self.size_max, 0, 6)
		size_layout.addWidget(QLabel("Primer Tm (℃)"), 1, 0)
		size_layout.addWidget(PrimerTagLabel("Min", 'PRIMER_MIN_TM'), 1, 1)
		size_layout.addWidget(self.tm_min,1, 2)
		size_layout.addWidget(PrimerTagLabel("Opt", 'PRIMER_OPT_TM'), 1, 3)
		size_layout.addWidget(self.tm_opt, 1, 4)
		size_layout.addWidget(PrimerTagLabel("Max", 'PRIMER_MAX_TM'), 1, 5)
		size_layout.addWidget(self.tm_max, 1, 6)
		size_layout.addWidget(QLabel("Primer GC (%)"), 2, 0)
		size_layout.addWidget(PrimerTagLabel("Min", 'PRIMER_MIN_GC'), 2, 1)
		size_layout.addWidget(self.gc_min, 2, 2)
		size_layout.addWidget(PrimerTagLabel("Opt", 'PRIMER_OPT_GC_PERCENT'), 2, 3)
		size_layout.addWidget(self.gc_opt, 2, 4)
		size_layout.addWidget(PrimerTagLabel("Max", 'PRIMER_MAX_GC'), 2, 5)
		size_layout.addWidget(self.gc_max, 2, 6)

		advance_group = KraitGroupBox("Advanced settings")
		advance_layout = QGridLayout()
		advance_group.setLayout(advance_layout)

		self.gc_clamp = QDoubleSpinBox()
		self.max_end_stability = QDoubleSpinBox()
		self.max_end_stability.setMaximum(1000)
		self.max_ns = QSpinBox()
		self.max_diff_tm = QDoubleSpinBox()

		advance_layout.addWidget(PrimerTagLabel("Max Ns", 'PRIMER_MAX_NS_ACCEPTED'), 0, 0)
		advance_layout.addWidget(PrimerTagLabel("GC clamp", 'PRIMER_GC_CLAMP'), 0, 1)
		advance_layout.addWidget(PrimerTagLabel("Max Tm Difference", 'PRIMER_PAIR_MAX_DIFF_TM'), 0, 2)
		advance_layout.addWidget(PrimerTagLabel("Max end stability", 'PRIMER_MAX_END_STABILITY'), 0, 3)
		advance_layout.addWidget(self.max_ns, 1, 0)
		advance_layout.addWidget(self.gc_clamp, 1, 1)
		advance_layout.addWidget(self.max_diff_tm, 1, 2)
		advance_layout.addWidget(self.max_end_stability, 1, 3)

		other_group = KraitGroupBox("Other settings")
		other_layout = QVBoxLayout()
		other_group.setLayout(other_layout)
		self.add_btn = QPushButton(self)
		self.add_btn.clicked.connect(self.add_primer_tag)
		self.add_btn.setIcon(QIcon("icons/plus.svg"))
		self.add_btn.setToolTip("Add primer3 tag")
		self.del_btn = QPushButton(self)
		self.del_btn.clicked.connect(self.del_primer_tag)
		self.del_btn.setIcon(QIcon("icons/minus.svg"))
		self.del_btn.setToolTip("Delete the selected primer3 tag")
		self.clr_btn = QPushButton(self)
		self.clr_btn.clicked.connect(self.clear_primer_tag)
		self.clr_btn.setIcon(QIcon("icons/clear.svg"))
		self.clr_btn.setToolTip("Delete all the primer3 tags")

		btn_layout = QHBoxLayout()
		btn_layout.addWidget(QLabel("Add other primer3 tag settings"), 1)
		btn_layout.addWidget(self.add_btn)
		btn_layout.addWidget(self.del_btn)
		btn_layout.addWidget(self.clr_btn)

		self.tree = QTreeWidget()
		self.tree.setHeaderLabels(["Primer3 tags", "Value"])
		self.tree.header().setStretchLastSection(False)
		self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)

		other_layout.addLayout(btn_layout)
		other_layout.addWidget(self.tree)

		mainLayout = QVBoxLayout()
		mainLayout.addWidget(general_group)
		mainLayout.addWidget(advance_group)
		mainLayout.addWidget(other_group)

		self.setLayout(mainLayout)

		self._mappings = {
			'PRIMER/PRIMER_PRODUCT_SIZE_RANGE': (self.product_size, '100-300', str),
			'PRIMER/PRIMER_NUM_RETURN': (self.primer_num, 1, int),
			'PRIMER/PRIMER_MIN_SIZE': (self.size_min, 18, int),
			'PRIMER/PRIMER_OPT_SIZE': (self.size_opt, 20, int),
			'PRIMER/PRIMER_MAX_SIZE': (self.size_max, 27, int),
			'PRIMER/PRIMER_MIN_GC': (self.gc_min, 20, float),
			'PRIMER/PRIMER_OPT_GC_PERCENT': (self.gc_opt, 50, float),
			'PRIMER/PRIMER_MAX_GC': (self.gc_max, 80, float),
			'PRIMER/PRIMER_MIN_TM': (self.tm_min, 57, float),
			'PRIMER/PRIMER_OPT_TM': (self.tm_opt, 60, float),
			'PRIMER/PRIMER_MAX_TM': (self.tm_max, 63, float),
			'PRIMER/PRIMER_MAX_NS_ACCEPTED': (self.max_ns, 0, int),
			'PRIMER/PRIMER_GC_CLAMP': (self.gc_clamp, 0, int),
			'PRIMER/PRIMER_PAIR_MAX_DIFF_TM': (self.max_diff_tm, 100, float),
			'PRIMER/PRIMER_MAX_END_STABILITY': (self.max_end_stability, 100, float)
		}

		self.read_settings()

	def add_primer_tag(self):
		item = QTreeWidgetItem(self.tree, ["PRIMER_", ''])
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		self.tree.addTopLevelItem(item)
		self.tree.scrollToItem(item)
		self.tree.editItem(item, 0)

	def del_primer_tag(self):
		root = self.tree.invisibleRootItem()
		it = self.tree.currentItem()
		root.removeChild(it)

	def clear_primer_tag(self):
		self.tree.clear()

	def read_settings(self):
		for param in self._mappings:
			box, default, func = self._mappings[param]

			if box == self.product_size:
				box.setText(self.settings.value(param, default))
			else:
				box.setValue(func(self.settings.value(param, default)))

		self.settings.beginGroup("PRIMER")

		for k in self.settings.allKeys():
			if "PRIMER/{}".format(k) not in self._mappings:
				item = QTreeWidgetItem(self.tree, [k, self.settings.value(k)])
				item.setFlags(item.flags() | Qt.ItemIsEditable)
				self.tree.addTopLevelItem(item)

		self.settings.endGroup()

	def write_settings(self):
		for param in self._mappings:
			box, _, _ = self._mappings[param]

			if box == self.product_size:
				self.settings.setValue(param, box.text())
			else:
				self.settings.setValue(param, box.value())

		params = {}
		for i in range(self.tree.topLevelItemCount()):
			item = self.tree.topLevelItem(i)
			tag, val = item.text(0), item.text(1)
			tag = tag.strip()
			val = val.strip()

			if tag and val:
				params[tag] = val

		self.settings.beginGroup("PRIMER")
		#delete other params
		for k in self.settings.allKeys():
			if "PRIMER/{}".format(k) not in self._mappings:
				if k not in params:
					self.settings.remove(k)

		#set other params
		for k in params:
			self.settings.setValue(k, params[k])

		self.settings.endGroup()

class KraitGroupBox(QGroupBox):
	def __init__(self, title):
		super(KraitGroupBox, self).__init__(title)
		self.setStyleSheet("QGroupBox{font-weight: bold;}")

class SearchParameterPanel(QWidget):
	def __init__(self, parent=None):
		super(SearchParameterPanel, self).__init__(parent)
		self.settings = QSettings()
		
		ssr_layout = QGridLayout()
		ssr_group = KraitGroupBox("Microsatellites (SSRs)")
		ssr_group.setLayout(ssr_layout)

		self.mono_box = QSpinBox()
		self.di_box = QSpinBox()
		self.tri_box = QSpinBox()
		self.tetra_box = QSpinBox()
		self.penta_box = QSpinBox()
		self.hexa_box = QSpinBox()
		self.mono_box.setMinimum(2)
		self.di_box.setMinimum(2)
		self.tri_box.setMinimum(2)
		self.tetra_box.setMinimum(2)
		self.penta_box.setMinimum(2)
		self.hexa_box.setMinimum(2)
		
		ssr_layout.setColumnStretch(1, 1)
		ssr_layout.setColumnStretch(3, 1)
		ssr_layout.setColumnStretch(5, 1)
		ssr_layout.addWidget(QLabel("Minimum repeats required for each type to form an SSR"), 0, 0, 1, 6)
		ssr_layout.addWidget(QLabel("Mono"), 1, 0)
		ssr_layout.addWidget(self.mono_box, 1, 1)
		ssr_layout.addWidget(QLabel("Di"), 1, 2)
		ssr_layout.addWidget(self.di_box, 1, 3)
		ssr_layout.addWidget(QLabel("Tri"), 1, 4)
		ssr_layout.addWidget(self.tri_box, 1, 5)
		ssr_layout.addWidget(QLabel("Tetra"), 2, 0)
		ssr_layout.addWidget(self.tetra_box, 2, 1)
		ssr_layout.addWidget(QLabel("Penta"), 2, 2)
		ssr_layout.addWidget(self.penta_box, 2, 3)
		ssr_layout.addWidget(QLabel("Hexa"), 2, 4)
		ssr_layout.addWidget(self.hexa_box, 2, 5)


		cssr_group = KraitGroupBox("Compound microsatellites (cSSRs)")
		cssr_layout = QHBoxLayout()
		cssr_group.setLayout(cssr_layout)

		self.dmax_box = QSpinBox()
		self.dmax_box.setMaximum(1000)
		
		cssr_layout.addWidget(QLabel("Maximum distance allowed between two adjacent SSRs (d<sub>MAX</sub>)"))
		cssr_layout.addWidget(self.dmax_box, 1)
		

		vntr_group = KraitGroupBox("Minisatellites (VNTRs)")
		vntr_layout = QGridLayout()
		vntr_group.setLayout(vntr_layout)

		self.minmotif_box = QSpinBox()
		self.minmotif_box.setMinimum(1)
		self.maxmotif_box = QSpinBox()
		self.maxmotif_box.setMinimum(1)
		self.minrep_box = QSpinBox()
		self.minrep_box.setMinimum(2)

		vntr_layout.addWidget(QLabel("Min motif size"), 0, 0)
		vntr_layout.addWidget(self.minmotif_box, 0, 1)
		vntr_layout.addWidget(QLabel("Max motif size"), 0, 2)
		vntr_layout.addWidget(self.maxmotif_box, 0, 3)
		vntr_layout.addWidget(QLabel("Min repeats"), 0, 4)
		vntr_layout.addWidget(self.minrep_box, 0, 5)


		itr_group = KraitGroupBox("Imperfect tandem repeats (ITRs)")
		itr_layout = QGridLayout()
		itr_group.setLayout(itr_layout)

		self.minmsize_box = QSpinBox()
		self.minmsize_box.setMinimum(1)
		self.maxmsize_box = QSpinBox()
		self.maxmsize_box.setMinimum(1)
		self.minsrep_box = QSpinBox()
		self.minsrep_box.setMinimum(2)
		self.minslen_box = QSpinBox()
		self.maxerr_box = QSpinBox()
		self.subpena_box = QDoubleSpinBox()
		self.inspena_box = QDoubleSpinBox()
		self.delpena_box = QDoubleSpinBox()
		self.matratio_box = QDoubleSpinBox()
		self.matratio_box.setMaximum(1)
		self.maxextend_box = QSpinBox()

		itr_layout.addWidget(QLabel("Min motif size"), 0, 0)
		itr_layout.addWidget(QLabel("Max motif size"), 0, 1)
		itr_layout.addWidget(QLabel("Min seed repeats"), 0, 2)
		itr_layout.addWidget(QLabel("Min seed length"), 0, 3)
		itr_layout.addWidget(self.minmsize_box, 1, 0)
		itr_layout.addWidget(self.maxmsize_box, 1, 1)
		itr_layout.addWidget(self.minsrep_box, 1, 2)
		itr_layout.addWidget(self.minslen_box, 1, 3)
		itr_layout.addWidget(QLabel("Substitution penalty"), 2, 0)
		itr_layout.addWidget(QLabel("Insertion penalty"), 2, 1)
		itr_layout.addWidget(QLabel("Deletion penalty"), 2, 2)
		itr_layout.addWidget(QLabel("Min match ratio"), 2, 3)
		itr_layout.addWidget(self.subpena_box, 3, 0)
		itr_layout.addWidget(self.inspena_box, 3, 1)
		itr_layout.addWidget(self.delpena_box, 3, 2)
		itr_layout.addWidget(self.matratio_box, 3, 3)
		itr_layout.addWidget(QLabel("Max continuous errors"), 4, 0)
		itr_layout.addWidget(self.maxerr_box, 4, 1)
		itr_layout.addWidget(QLabel("Max extend length"), 4, 2)
		itr_layout.addWidget(self.maxextend_box, 4, 3)


		other_layout = QHBoxLayout()
		level_group = KraitGroupBox("Motif standardization")
		other_layout.addWidget(level_group)
		level_layout = QHBoxLayout()
		level_group.setLayout(level_layout)

		self.level_box = QComboBox()
		self.level_box.addItems([
			"Level 0",
			"Level 1",
			"Level 2",
			"Level 3",
			"Level 4"
		])

		level_layout.addWidget(QLabel("Level"))
		level_layout.addWidget(self.level_box, 1)


		flank_group = KraitGroupBox("Flank sequence")
		other_layout.addWidget(flank_group)
		flank_layout = QHBoxLayout()
		flank_group.setLayout(flank_layout)

		self.flank_box = QSpinBox()
		self.flank_box.setMaximum(10000)

		flank_layout.addWidget(QLabel("Length"))
		flank_layout.addWidget(self.flank_box, 1)
		

		main_layout = QVBoxLayout()
		main_layout.addWidget(ssr_group)
		main_layout.addWidget(cssr_group)
		main_layout.addWidget(vntr_group)
		main_layout.addWidget(itr_group)
		main_layout.addLayout(other_layout)
		self.setLayout(main_layout)

		self._mappings = {
			'SSR/mono': (self.mono_box, 12, int),
			'SSR/di': (self.di_box, 7, int),
			'SSR/tri': (self.tri_box, 5, int),
			'SSR/tetra': (self.tetra_box, 4, int),
			'SSR/penta': (self.penta_box, 4, int),
			'SSR/hexa': (self.hexa_box, 4, int),
			'CSSR/dmax': (self.dmax_box, 10, int),
			'VNTR/minmotif': (self.minmotif_box, 7, int),
			'VNTR/maxmotif': (self.maxmotif_box, 30, int),
			'VNTR/minrep': (self.minrep_box, 3, int),
			'ITR/minmsize': (self.minmsize_box, 1, int),
			'ITR/maxmsize': (self.maxmsize_box, 6,int),
			'ITR/minsrep': (self.minsrep_box, 3, int),
			'ITR/mixslen': (self.minslen_box, 10, int),
			'ITR/maxerr': (self.maxerr_box, 2, int),
			'ITR/subpena': (self.subpena_box, 0.5, float),
			'ITR/inspena': (self.inspena_box, 1.0, float),
			'ITR/delpena': (self.delpena_box, 1.0, float),
			'ITR/matratio': (self.matratio_box, 0.7, float),
			'ITR/maxextend': (self.maxextend_box, 2000, int),
			'STR/level': (self.level_box, 3, int),
			'STR/flank': (self.flank_box, 100, int)
		}

		self.read_settings()

	def read_settings(self):
		for param in self._mappings:
			box, default, func = self._mappings[param]

			if box == self.level_box:
				box.setCurrentIndex(func(self.settings.value(param, default)))
			else:
				box.setValue(func(self.settings.value(param, default)))

	def write_settings(self):
		for param in self._mappings:
			box, _, _ = self._mappings[param]

			if box == self.level_box:
				self.settings.setValue(param, box.currentIndex())
			else:
				self.settings.setValue(param, box.value())

class PreferenceDialog(QDialog):
	def __init__(self, parent=None):
		super(PreferenceDialog, self).__init__(parent)
		self.settings = QSettings()
		self.setWindowTitle(self.tr("Preferences"))
		#self.setMinimumWidth(500)

		self.search_panel = SearchParameterPanel(self)
		self.primer_panel = PrimerParameterPanel(self)

		self.tab_widget = QTabWidget()
		self.tab_widget.addTab(self.search_panel, 'Search')
		self.tab_widget.addTab(self.primer_panel, 'Primer')

		btn_box = QDialogButtonBox(QDialogButtonBox.RestoreDefaults | QDialogButtonBox.Save | QDialogButtonBox.Cancel)
		btn_box.accepted.connect(self.accept)
		btn_box.rejected.connect(self.reject)
		btn_box.accepted.connect(self.write_settings)
		btn_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_settings)

		spacer = QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

		layout = QVBoxLayout()
		layout.addWidget(self.tab_widget)
		layout.addItem(spacer)
		layout.addWidget(btn_box)

		self.setLayout(layout)

	def write_settings(self):
		self.search_panel.write_settings()
		self.primer_panel.write_settings()

	def restore_settings(self):
		self.settings.clear()
		self.search_panel.read_settings()
		self.primer_panel.clear_primer_tag()
		self.primer_panel.read_settings()
		self.write_settings()

	def goto_primer_panel(self):
		self.tab_widget.setCurrentIndex(1)
