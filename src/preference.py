from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from config import *

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

class PrimerTagTree(QTreeWidget):
	def sizeHint(self):
		return QSize(0, 0)

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
		self.primer_num.setRange(1, 100)
		
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
		self.size_min.setRange(0, 1000)
		self.size_opt.setRange(0, 1000)
		self.size_max.setRange(0, 1000)
		self.gc_min = QDoubleSpinBox()
		self.gc_max = QDoubleSpinBox()
		self.gc_opt = QDoubleSpinBox()
		self.tm_min = QDoubleSpinBox()
		self.tm_opt = QDoubleSpinBox()
		self.tm_max = QDoubleSpinBox()
		self.gc_min.setRange(0, 100)
		self.gc_max.setRange(0, 100)
		self.gc_opt.setRange(0, 100)
		self.tm_min.setRange(0, 1000)
		self.tm_opt.setRange(0, 1000)
		self.tm_max.setRange(0, 1000)

		size_layout.addWidget(QLabel("Primer size (bp)"), 0, 0)
		size_layout.addWidget(PrimerTagLabel("Min", 'PRIMER_MIN_SIZE'), 0, 1)
		size_layout.addWidget(self.size_min, 0, 2)
		size_layout.addWidget(PrimerTagLabel("Opt", 'PRIMER_OPT_SIZE'), 0, 3)
		size_layout.addWidget(self.size_opt, 0, 4)
		size_layout.addWidget(PrimerTagLabel("Max", 'PRIMER_MAX_SIZE'), 0, 5)
		size_layout.addWidget(self.size_max, 0, 6)
		size_layout.addWidget(QLabel("Primer Tm (???)"), 1, 0)
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

		self.gc_clamp = QSpinBox()
		self.gc_clamp.setMaximum(1000)
		self.max_end_stability = QDoubleSpinBox()
		self.max_end_stability.setMaximum(1000)
		self.max_ns = QSpinBox()
		self.max_ns.setMaximum(1000)
		self.max_diff_tm = QDoubleSpinBox()
		self.max_diff_tm.setMaximum(1000)

		advance_layout.addWidget(PrimerTagLabel("Max Ns", 'PRIMER_MAX_NS_ACCEPTED'), 0, 0)
		advance_layout.addWidget(PrimerTagLabel("GC clamp", 'PRIMER_GC_CLAMP'), 1, 0)
		advance_layout.addWidget(self.max_ns, 0, 1)
		advance_layout.addWidget(self.gc_clamp, 1, 1)

		advance_layout.addWidget(PrimerTagLabel("Max Tm Difference", 'PRIMER_PAIR_MAX_DIFF_TM'), 0, 2)
		advance_layout.addWidget(PrimerTagLabel("Max end stability", 'PRIMER_MAX_END_STABILITY'), 1, 2)
		advance_layout.addWidget(self.max_diff_tm, 0, 3)
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
		btn_layout.addWidget(QLabel("Add other primer3 tag settings"))
		btn_layout.addWidget(PrimerTagLabel("learn more", ''), 1)
		btn_layout.addWidget(self.add_btn)
		btn_layout.addWidget(self.del_btn)
		btn_layout.addWidget(self.clr_btn)

		self.tree = PrimerTagTree()
		self.tree.setHeaderLabels(["Primer3 tags", "Value"])
		self.tree.header().setStretchLastSection(False)
		self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)

		other_layout.addLayout(btn_layout)
		other_layout.addWidget(self.tree, 1)

		mainLayout = QVBoxLayout()
		mainLayout.addWidget(general_group)
		mainLayout.addWidget(advance_group)
		mainLayout.addWidget(other_group, 1)

		self.setLayout(mainLayout)

		self._mappings = {
			'PRIMER_PRODUCT_SIZE_RANGE': self.product_size,
			'PRIMER_NUM_RETURN': self.primer_num,
			'PRIMER_MIN_SIZE': self.size_min,
			'PRIMER_OPT_SIZE': self.size_opt,
			'PRIMER_MAX_SIZE': self.size_max,
			'PRIMER_MIN_GC': self.gc_min,
			'PRIMER_OPT_GC_PERCENT': self.gc_opt,
			'PRIMER_MAX_GC': self.gc_max,
			'PRIMER_MIN_TM': self.tm_min,
			'PRIMER_OPT_TM': self.tm_opt,
			'PRIMER_MAX_TM': self.tm_max,
			'PRIMER_MAX_NS_ACCEPTED': self.max_ns,
			'PRIMER_GC_CLAMP': self.gc_clamp,
			'PRIMER_PAIR_MAX_DIFF_TM': self.max_diff_tm,
			'PRIMER_MAX_END_STABILITY': self.max_end_stability,
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
		self.settings.beginGroup("PRIMER")
		for param in self._mappings:
			box = self._mappings[param]
			default, func = PRIMER_PARAMETERS[param]

			if box == self.product_size:
				box.setText(self.settings.value(param, default))
			else:
				box.setValue(self.settings.value(param, default, func))

		for k in self.settings.allKeys():
			if k not in self._mappings:
				item = QTreeWidgetItem(self.tree, [k, self.settings.value(k)])
				item.setFlags(item.flags() | Qt.ItemIsEditable)
				self.tree.addTopLevelItem(item)

		self.settings.endGroup()

	def write_settings(self):
		self.settings.beginGroup("PRIMER")
		for param in self._mappings:
			box = self._mappings[param]

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

		#delete other params
		for k in self.settings.allKeys():
			if k not in self._mappings:
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
		self.mono_box.setRange(2, 1000)
		self.di_box = QSpinBox()
		self.di_box.setRange(2, 1000)
		self.tri_box = QSpinBox()
		self.tri_box.setRange(2, 1000)
		self.tetra_box = QSpinBox()
		self.tetra_box.setRange(2, 1000)
		self.penta_box = QSpinBox()
		self.penta_box.setRange(2, 1000)
		self.hexa_box = QSpinBox()
		self.hexa_box.setRange(2, 1000)
		
		ssr_layout.setColumnStretch(1, 1)
		ssr_layout.setColumnStretch(3, 1)
		ssr_layout.setColumnStretch(5, 1)
		ssr_layout.addWidget(QLabel("Minimum repeats required for each type to form an SSR"),
							 0, 0, 1, 6)
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
		self.dmax_box.setRange(0, 1000)
		
		cssr_layout.addWidget(QLabel("Maximum distance allowed between two adjacent SSRs (d<sub>MAX</sub>)"))
		cssr_layout.addWidget(self.dmax_box, 1)
		

		vntr_group = KraitGroupBox("Minisatellites (VNTRs)")
		vntr_layout = QGridLayout()
		vntr_group.setLayout(vntr_layout)

		self.minmotif_box = QSpinBox()
		self.minmotif_box.setRange(1, 1000)
		self.maxmotif_box = QSpinBox()
		self.maxmotif_box.setRange(1, 1000)
		self.minrep_box = QSpinBox()
		self.minrep_box.setRange(2, 1000)

		vntr_layout.addWidget(QLabel("Min motif size"), 0, 0)
		vntr_layout.addWidget(self.minmotif_box, 0, 1)
		vntr_layout.addWidget(QLabel("Max motif size"), 0, 2)
		vntr_layout.addWidget(self.maxmotif_box, 0, 3)
		vntr_layout.addWidget(QLabel("Min repeats"), 0, 4)
		vntr_layout.addWidget(self.minrep_box, 0, 5)

		itr_group = KraitGroupBox("Imperfect microsatellites (iSSRs)")
		itr_layout = QGridLayout()
		itr_group.setLayout(itr_layout)

		#self.minmsize_box = QSpinBox()
		#self.minmsize_box.setRange(1, 1000)
		#self.maxmsize_box = QSpinBox()
		#self.maxmsize_box.setRange(1, 1000)
		self.minsrep_box = QSpinBox()
		self.minsrep_box.setRange(2, 1000)
		self.minslen_box = QSpinBox()
		self.minslen_box.setRange(1, 1000)
		self.maxerr_box = QSpinBox()
		self.maxerr_box.setRange(0, 1000)
		self.subpena_box = QDoubleSpinBox()
		self.subpena_box.setRange(0, 100)
		self.subpena_box.setSingleStep(0.1)
		self.inspena_box = QDoubleSpinBox()
		self.inspena_box.setRange(0, 100)
		self.inspena_box.setSingleStep(0.1)
		self.delpena_box = QDoubleSpinBox()
		self.delpena_box.setRange(0, 100)
		self.delpena_box.setSingleStep(0.1)
		self.matratio_box = QDoubleSpinBox()
		self.matratio_box.setSingleStep(0.05)
		self.matratio_box.setRange(0, 1)
		self.maxextend_box = QSpinBox()
		self.maxextend_box.setMaximum(1000000)
		self.maxextend_box.setSingleStep(50)

		#itr_layout.addWidget(QLabel("Min motif size"), 0, 0)
		#itr_layout.addWidget(QLabel("Max motif size"), 1, 0)
		itr_layout.addWidget(QLabel("Min seed repeats"),0, 0)
		itr_layout.addWidget(QLabel("Min seed length"), 1, 0)
		itr_layout.addWidget(QLabel("Max continuous errors"), 2, 0)
		itr_layout.addWidget(QLabel("Max extend length"), 3, 0)
		#itr_layout.addWidget(self.minmsize_box, 0, 1)
		#itr_layout.addWidget(self.maxmsize_box, 1, 1)
		itr_layout.addWidget(self.minsrep_box, 0, 1)
		itr_layout.addWidget(self.minslen_box, 1, 1)
		itr_layout.addWidget(self.maxerr_box, 2, 1)
		itr_layout.addWidget(self.maxextend_box, 3, 1)

		itr_layout.addWidget(QLabel("Substitution penalty"), 0, 2)
		itr_layout.addWidget(QLabel("Insertion penalty"), 1, 2)
		itr_layout.addWidget(QLabel("Deletion penalty"), 2, 2)
		itr_layout.addWidget(QLabel("Min match ratio"), 3, 2)
		itr_layout.addWidget(self.subpena_box, 0, 3)
		itr_layout.addWidget(self.inspena_box, 1, 3)
		itr_layout.addWidget(self.delpena_box, 2, 3)
		itr_layout.addWidget(self.matratio_box, 3, 3)
		

		other_layout = QHBoxLayout()
		level_group = KraitGroupBox("Motif standardization")
		other_layout.addWidget(level_group)
		level_layout = QHBoxLayout()
		level_group.setLayout(level_layout)

		self.level_box = QComboBox()
		self.level_box.addItems(["Level {}".format(i) for i in range(5)])

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


		stats_group = KraitGroupBox("Statistics")
		other_layout.addWidget(stats_group)
		stats_layout = QHBoxLayout()
		stats_group.setLayout(stats_layout)

		self.unit_box = QComboBox()
		self.unit_box.addItems(["Mb", "Kb"])

		self.ns_box = QComboBox()
		self.ns_box.addItems(["exclude", "include"])

		stats_layout.addWidget(QLabel("Unit"))
		stats_layout.addWidget(self.unit_box, 1)
		stats_layout.addWidget(QLabel("Ns"))
		stats_layout.addWidget(self.ns_box, 1)


		main_layout = QVBoxLayout()
		main_layout.addWidget(ssr_group)
		main_layout.addWidget(cssr_group)
		main_layout.addWidget(itr_group)
		main_layout.addWidget(vntr_group)
		main_layout.addLayout(other_layout)
		self.setLayout(main_layout)

		self._mappings = {
			'SSR/mono': self.mono_box,
			'SSR/di': self.di_box,
			'SSR/tri': self.tri_box,
			'SSR/tetra': self.tetra_box,
			'SSR/penta': self.penta_box,
			'SSR/hexa': self.hexa_box,
			'CSSR/dmax': self.dmax_box,
			'VNTR/minmotif': self.minmotif_box,
			'VNTR/maxmotif': self.maxmotif_box,
			'VNTR/minrep': self.minrep_box,
			#'ITR/minmsize': self.minmsize_box,
			#'ITR/maxmsize': self.maxmsize_box,
			'ISSR/minsrep': self.minsrep_box,
			'ISSR/minslen': self.minslen_box,
			'ISSR/maxerr': self.maxerr_box,
			'ISSR/subpena': self.subpena_box,
			'ISSR/inspena': self.inspena_box,
			'ISSR/delpena': self.delpena_box,
			'ISSR/matratio': self.matratio_box,
			'ISSR/maxextend': self.maxextend_box,
			'STR/level': self.level_box,
			'STR/flank': self.flank_box,
			'STAT/unit': self.unit_box,
			'STAT/unkown': self.ns_box
		}

		self.read_settings()

	def read_settings(self):
		for param in self._mappings:
			box = self._mappings[param]
			default, func = KRAIT_PARAMETERS[param]

			if isinstance(box, QComboBox):
				box.setCurrentIndex(self.settings.value(param, default, func))
			else:
				box.setValue(self.settings.value(param, default, func))

	def write_settings(self):
		for param in self._mappings:
			box = self._mappings[param]

			if isinstance(box, QComboBox):
				self.settings.setValue(param, box.currentIndex())
			else:
				self.settings.setValue(param, box.value())

class PreferenceDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
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

		#spacer = QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

		layout = QVBoxLayout()
		layout.addWidget(self.tab_widget)
		#layout.addItem(spacer)
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
