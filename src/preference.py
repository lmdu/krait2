from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

__all__ = ['PreferenceDialog']

class PrimerTagLabel(QLabel):
	base_url = "https://primer3.org/manual.html#{}"

	def __init__(self, tag, parent=None):
		super(PrimerTagLabel, self).__init__(parent)
		#self.setOpenExternalLinks(True)
		self.tag = tag
		self.setText('<a href="#{}">{}</a>'.format(self.tag, self.tag))
		self.linkActivated.connect(self.openLink)

	def openLink(self, link):
		url = QUrl(self.base_url.format(self.tag))
		QDesktopServices.openUrl(url)

class PrimerParameterPanel(QWidget):
	def __init__(self, parent=None):
		super(PrimerParameterPanel, self).__init__(parent)
		self.settings = QSettings()
		
		self.product_size = QLineEdit()
		self.primer_num_return = QSpinBox()
		self.repeat_library = QComboBox()
		self.repeat_library.addItems(['None', 'Human', 'Rodent', 'Rodent and Simple', 'Drosophila'])

		product_size_group = QGroupBox(self.tr('General Settings'))
		product_size_layout = QGridLayout()

		product_size_layout.addWidget(PrimerTagLabel('PRIMER_PRODUCT_SIZE_RANGE'), 0, 0)
		product_size_layout.addWidget(self.product_size, 0, 1, 1, 3)
		product_size_layout.addWidget(PrimerTagLabel('PRIMER_MISPRIMING_LIBRARY'), 1, 0)
		product_size_layout.addWidget(self.repeat_library, 1, 1)
		product_size_layout.addWidget(PrimerTagLabel("PRIMER_NUM_RETURN"), 1, 2)
		product_size_layout.addWidget(self.primer_num_return, 1, 3)
		
		product_size_group.setLayout(product_size_layout)

		primer_size_group = QGroupBox(self.tr("Primer Size and GC content"))
		primer_size_layout = QGridLayout()
		self.primer_size_min = QSpinBox()
		self.primer_size_opt = QSpinBox()
		self.primer_size_max = QSpinBox()
		self.primer_gc_min = QDoubleSpinBox()
		self.primer_gc_max = QDoubleSpinBox()
		self.primer_gc_clamp = QSpinBox()
		primer_size_layout.addWidget(PrimerTagLabel("PRIMER_MIN_SIZE"), 0, 0)
		primer_size_layout.addWidget(self.primer_size_min, 0, 1)
		primer_size_layout.addWidget(PrimerTagLabel("PRIMER_OPT_SIZE"), 0, 2)
		primer_size_layout.addWidget(self.primer_size_opt, 0, 3)
		primer_size_layout.addWidget(PrimerTagLabel("PRIMER_MAX_SIZE"), 0, 4)
		primer_size_layout.addWidget(self.primer_size_max, 0, 5)
		primer_size_layout.addWidget(PrimerTagLabel("PRIMER_MIN_GC"), 1, 0)
		primer_size_layout.addWidget(self.primer_gc_min, 1, 1)
		primer_size_layout.addWidget(PrimerTagLabel("PRIMER_MAX_GC"), 1, 2)
		primer_size_layout.addWidget(self.primer_gc_max, 1, 3)
		primer_size_layout.addWidget(PrimerTagLabel("PRIMER_GC_CLAMP"), 1, 4)
		primer_size_layout.addWidget(self.primer_gc_clamp, 1, 5)
		primer_size_group.setLayout(primer_size_layout)

		primer_tm_group = QGroupBox(self.tr("Primer Melting Temperature"))
		primer_tm_layout = QGridLayout()
		self.primer_tm_min = QDoubleSpinBox()
		self.primer_tm_opt = QDoubleSpinBox()
		self.primer_tm_max = QDoubleSpinBox()
		self.primer_tm_pair = QDoubleSpinBox()
		self.primer_tm_pair.setMaximum(1000)
		primer_tm_layout.addWidget(PrimerTagLabel("PRIMER_MIN_TM"), 0, 0)
		primer_tm_layout.addWidget(self.primer_tm_min, 0, 1)
		primer_tm_layout.addWidget(PrimerTagLabel("PRIMER_OPT_TM"), 0, 2)
		primer_tm_layout.addWidget(self.primer_tm_opt, 0, 3)
		primer_tm_layout.addWidget(PrimerTagLabel("PRIMER_MAX_TM"), 0, 4)
		primer_tm_layout.addWidget(self.primer_tm_max, 0, 5)
		primer_tm_group.setLayout(primer_tm_layout)

		primer_bind_group = QGroupBox(self.tr("Self-binding (primer-dimer and hairpins)"))
		primer_bind_layout = QGridLayout()
		self.primer_max_self_any = QDoubleSpinBox()
		self.primer_max_self_any.setMaximum(1000000)
		self.primer_pair_max_compl_any = QDoubleSpinBox()
		self.primer_pair_max_compl_any.setMaximum(10000)
		self.primer_max_self_end = QDoubleSpinBox()
		self.primer_max_self_end.setMaximum(10000)
		self.primer_pair_max_compl_end = QDoubleSpinBox()
		self.primer_pair_max_compl_end.setMaximum(10000)
		self.primer_max_hairpin = QDoubleSpinBox()
		primer_bind_layout.addWidget(PrimerTagLabel("PRIMER_MAX_SELF_ANY_TH"), 0, 0)
		primer_bind_layout.addWidget(self.primer_max_self_any, 0, 1)
		primer_bind_layout.addWidget(PrimerTagLabel("PRIMER_PAIR_MAX_COMPL_ANY_TH"), 0, 2)
		primer_bind_layout.addWidget(self.primer_pair_max_compl_any, 0, 3)
		primer_bind_layout.addWidget(PrimerTagLabel("PRIMER_MAX_SELF_END_TH"), 1, 0)
		primer_bind_layout.addWidget(self.primer_max_self_end, 1, 1)
		primer_bind_layout.addWidget(PrimerTagLabel("PRIMER_PAIR_MAX_COMPL_END_TH"), 1, 2)
		primer_bind_layout.addWidget(self.primer_pair_max_compl_end, 1, 3)
		primer_bind_layout.addWidget(PrimerTagLabel("PRIMER_MAX_HAIRPIN_TH"), 2, 0)
		primer_bind_layout.addWidget(self.primer_max_hairpin, 2, 1)
		primer_bind_group.setLayout(primer_bind_layout)

		primer_other_group = QGroupBox(self.tr("PolyX and Other"))
		primer_other_layout = QGridLayout()
		self.primer_max_end_stability = QDoubleSpinBox()
		self.primer_max_end_stability.setMaximum(1000)
		self.primer_max_ns_accepted = QSpinBox()
		self.primer_max_poly_x = QSpinBox()
		primer_other_layout.addWidget(PrimerTagLabel("PRIMER_MAX_END_STABILITY"), 0, 0)
		primer_other_layout.addWidget(self.primer_max_end_stability, 0, 1)
		primer_other_layout.addWidget(PrimerTagLabel("PRIMER_MAX_POLY_X"), 0, 2)
		primer_other_layout.addWidget(self.primer_max_poly_x, 0, 3)
		primer_other_layout.addWidget(PrimerTagLabel("PRIMER_MAX_NS_ACCEPTED"), 1, 0)
		primer_other_layout.addWidget(self.primer_max_ns_accepted, 1, 1)
		primer_other_layout.addWidget(PrimerTagLabel("PRIMER_PAIR_MAX_DIFF_TM"), 1, 2)
		primer_other_layout.addWidget(self.primer_tm_pair, 1, 3)
		primer_other_group.setLayout(primer_other_layout)

		mainLayout = QVBoxLayout()
		mainLayout.addWidget(product_size_group)
		mainLayout.addWidget(primer_size_group)
		mainLayout.addWidget(primer_tm_group)
		mainLayout.addWidget(primer_bind_group)
		mainLayout.addWidget(primer_other_group)

		self.setLayout(mainLayout)
		self.getSettings()

	def getSettings(self):
		self.product_size.setText(self.settings.value('primer/PRIMER_PRODUCT_SIZE_RANGE', '100-300'))
		self.primer_size_min.setValue(int(self.settings.value('primer/PRIMER_MIN_SIZE', 18)))
		self.primer_size_opt.setValue(int(self.settings.value('primer/PRIMER_OPT_SIZE', 20)))
		self.primer_size_max.setValue(int(self.settings.value('primer/PRIMER_MAX_SIZE', 27)))
		self.primer_tm_min.setValue(int(self.settings.value('primer/PRIMER_MIN_TM', 58)))
		self.primer_tm_opt.setValue(int(self.settings.value('primer/PRIMER_OPT_TM', 60)))
		self.primer_tm_max.setValue(int(self.settings.value('primer/PRIMER_MAX_TM', 65)))
		self.primer_gc_min.setValue(int(self.settings.value('primer/PRIMER_MIN_GC', 30)))
		self.primer_gc_max.setValue(int(self.settings.value('primer/PRIMER_MAX_GC', 80)))
		self.primer_gc_clamp.setValue(int(self.settings.value('primer/PRIMER_GC_CLAMP', 2)))
		self.primer_tm_pair.setValue(int(self.settings.value('primer/PRIMER_PAIR_MAX_DIFF_TM', 2)))
		self.primer_max_self_any.setValue(int(self.settings.value('primer/PRIMER_MAX_SELF_ANY_TH', 47)))
		self.primer_pair_max_compl_any.setValue(int(self.settings.value('primer/PRIMER_PAIR_MAX_COMPL_ANY_TH', 47)))
		self.primer_max_self_end.setValue(int(self.settings.value('primer/PRIMER_MAX_SELF_END_TH', 47)))
		self.primer_pair_max_compl_end.setValue(int(self.settings.value('primer/PRIMER_PAIR_MAX_COMPL_END_TH', 47)))
		self.primer_max_hairpin.setValue(int(self.settings.value('primer/PRIMER_MAX_HAIRPIN_TH', 47)))
		self.primer_max_end_stability.setValue(int(self.settings.value('primer/PRIMER_MAX_END_STABILITY', 100)))
		self.primer_max_ns_accepted.setValue(int(self.settings.value('primer/PRIMER_MAX_POLY_X', 5)))
		self.primer_max_poly_x.setValue(int(self.settings.value('primer/PRIMER_MAX_NS_ACCEPTED', 0)))
		self.primer_num_return.setValue(int(self.settings.value('primer/PRIMER_NUM_RETURN', 1)))
		self.repeat_library.setCurrentIndex(int(self.settings.value('primer/PRIMER_MISPRIMING_LIBRARY', 0)))


	def saveSettings(self):
		self.settings.setValue('primer/PRIMER_PRODUCT_SIZE_RANGE', self.product_size.text())
		self.settings.setValue('primer/PRIMER_MIN_SIZE', self.primer_size_min.value())
		self.settings.setValue('primer/PRIMER_OPT_SIZE', self.primer_size_opt.value())
		self.settings.setValue('primer/PRIMER_MAX_SIZE', self.primer_size_max.value())
		self.settings.setValue('primer/PRIMER_MIN_TM', self.primer_tm_min.value())
		self.settings.setValue('primer/PRIMER_OPT_TM', self.primer_tm_opt.value())
		self.settings.setValue('primer/PRIMER_MAX_TM', self.primer_tm_max.value())
		self.settings.setValue('primer/PRIMER_MIN_GC', self.primer_gc_min.value())
		self.settings.setValue('primer/PRIMER_MAX_GC', self.primer_gc_max.value())
		self.settings.setValue('primer/PRIMER_GC_CLAMP', self.primer_gc_clamp.value())
		self.settings.setValue('primer/PRIMER_PAIR_MAX_DIFF_TM', self.primer_tm_pair.value())
		self.settings.setValue('primer/PRIMER_MAX_SELF_ANY_TH', self.primer_max_self_any.value())
		self.settings.setValue('primer/PRIMER_PAIR_MAX_COMPL_ANY_TH', self.primer_pair_max_compl_any.value())
		self.settings.setValue('primer/PRIMER_MAX_SELF_END_TH', self.primer_max_self_end.value())
		self.settings.setValue('primer/PRIMER_PAIR_MAX_COMPL_END_TH', self.primer_pair_max_compl_end.value())
		self.settings.setValue('primer/PRIMER_MAX_HAIRPIN_TH', self.primer_max_hairpin.value())
		self.settings.setValue('primer/PRIMER_MAX_END_STABILITY', self.primer_max_end_stability.value())
		self.settings.setValue('primer/PRIMER_MAX_POLY_X', self.primer_max_ns_accepted.value())
		self.settings.setValue('primer/PRIMER_MAX_NS_ACCEPTED', self.primer_max_poly_x.value())
		self.settings.setValue('primer/PRIMER_NUM_RETURN', self.primer_num_return.value())
		self.settings.setValue('primer/PRIMER_MISPRIMING_LIBRARY', self.repeat_library.currentIndex())

class KraitGroupBox(QGroupBox):
	def __init__(self, title):
		super(KraitGroupBox, self).__init__(title)
		self.setStyleSheet("QGroupBox{font-weight: bold;}")

class SearchParameterPanel(QWidget):
	def __init__(self, parent=None):
		super(SearchParameterPanel, self).__init__(parent)
		self.settings = QSettings()

		repeatsGroup = KraitGroupBox("Microsatellites (SSRs)")
		mrep_label = QLabel("Minimum repeats required for each type to form an SSR")
		monoLabel = QLabel("Mono")
		self.monoValue = QSpinBox(self)
		diLabel = QLabel("Di")
		self.diValue = QSpinBox(self)
		triLabel = QLabel("Tri")
		self.triValue = QSpinBox(self)
		tetraLabel = QLabel("Tetra")
		self.tetraValue = QSpinBox(self)
		pentaLabel = QLabel("Penta")
		self.pentaValue = QSpinBox(self)
		hexaLabel = QLabel("Hexa")
		self.hexaValue = QSpinBox(self)
		
		repeatLayout = QGridLayout()
		repeatLayout.setColumnStretch(1, 1)
		repeatLayout.setColumnStretch(3, 1)
		repeatLayout.setColumnStretch(5, 1)
		repeatLayout.addWidget(mrep_label, 0, 0, 1, 6)
		repeatLayout.addWidget(monoLabel, 1, 0)
		repeatLayout.addWidget(self.monoValue, 1, 1)
		repeatLayout.addWidget(diLabel, 1, 2)
		repeatLayout.addWidget(self.diValue, 1, 3)
		repeatLayout.addWidget(triLabel, 1, 4)
		repeatLayout.addWidget(self.triValue, 1, 5)
		repeatLayout.addWidget(tetraLabel, 2, 0)
		repeatLayout.addWidget(self.tetraValue, 2, 1)
		repeatLayout.addWidget(pentaLabel, 2, 2)
		repeatLayout.addWidget(self.pentaValue, 2, 3)
		repeatLayout.addWidget(hexaLabel, 2, 4)
		repeatLayout.addWidget(self.hexaValue, 2, 5)
		repeatsGroup.setLayout(repeatLayout)

		distanceGroup = KraitGroupBox("Compound microsatellites (cSSRs)")
		distanceLabel = QLabel("Maximum distance allowed between two adjacent SSRs (d<sub>MAX</sub>)")
		self.distanceValue = QSpinBox()
		self.distanceValue.setMaximum(1000)
		distanceLayout = QHBoxLayout()
		distanceLayout.addWidget(distanceLabel)
		distanceLayout.addWidget(self.distanceValue, 1)
		distanceGroup.setLayout(distanceLayout)

		satelliteGroup = QGroupBox("Minisatellites (VNTRs)")
		min_tandem_label = QLabel("Minimum motif size")
		self.min_tandem_motif = QSpinBox()
		self.min_tandem_motif.setMinimum(1)
		self.min_tandem_motif.setMaximum(1000)

		max_tandem_label = QLabel("Maximum motif size")
		self.max_tandem_motif = QSpinBox()
		self.max_tandem_motif.setMinimum(1)
		self.max_tandem_motif.setMaximum(1000)

		repeat_tandem_label = QLabel("Minimum repeats")
		self.min_tandem_repeat = QSpinBox()
		self.min_tandem_repeat.setMinimum(2)

		satelliteLayout = QGridLayout()
		satelliteLayout.addWidget(min_tandem_label, 0, 0)
		satelliteLayout.addWidget(max_tandem_label, 0, 1)
		satelliteLayout.addWidget(repeat_tandem_label, 0, 2)
		satelliteLayout.addWidget(self.min_tandem_motif, 1, 0)
		satelliteLayout.addWidget(self.max_tandem_motif, 1, 1)
		satelliteLayout.addWidget(self.min_tandem_repeat, 1, 2)
		satelliteGroup.setLayout(satelliteLayout)

		issrGroup = KraitGroupBox("Imperfect tandem repeats (ITRs)")
		min_motif_label = QLabel("Minimum motif size")
		self.min_motif_size = QSpinBox()
		self.min_motif_size.setMinimum(1)
		max_motif_label = QLabel("Maximum motif size")
		self.max_motif_size = QSpinBox()
		self.min_motif_size.setMinimum(1)
		seed_mrep_label = QLabel("Minimum seed repeats")
		self.seed_min_repeat = QSpinBox()
		self.seed_min_repeat.setMinimum(2)
		seed_mlen_label = QLabel("Minimum seed length")
		self.seed_min_length = QSpinBox()
		max_error_label = QLabel("Maximum continuous errors")
		self.max_error = QSpinBox()
		sub_penalty_label = QLabel("substitution penalty")
		self.sub_penalty = QDoubleSpinBox()
		ins_penalty_label = QLabel("insertion penalty")
		self.ins_penalty = QDoubleSpinBox()
		del_penalty_label = QLabel("deletion penalty")
		self.del_penalty = QDoubleSpinBox()
		math_ratio_label = QLabel("Minimum match ratio")
		self.match_ratio = QDoubleSpinBox()
		self.match_ratio.setMaximum(1)

		issrLayout = QGridLayout()
		issrLayout.addWidget(min_motif_label, 0, 0)
		issrLayout.addWidget(max_motif_label, 0, 1)
		issrLayout.addWidget(max_error_label, 0, 2)
		issrLayout.addWidget(self.min_motif_size, 1, 0)
		issrLayout.addWidget(self.max_motif_size, 1, 1)
		issrLayout.addWidget(self.max_error, 1, 2)

		issrLayout.addWidget(seed_mrep_label, 2, 0)
		issrLayout.addWidget(seed_mlen_label, 2, 1)
		issrLayout.addWidget(math_ratio_label, 2, 2)
		issrLayout.addWidget(self.seed_min_repeat, 3, 0)
		issrLayout.addWidget(self.seed_min_length, 3, 1)
		issrLayout.addWidget(self.match_ratio, 3, 2)

		issrLayout.addWidget(sub_penalty_label, 4, 0)
		issrLayout.addWidget(ins_penalty_label, 4, 1)
		issrLayout.addWidget(del_penalty_label, 4, 2)
		issrLayout.addWidget(self.sub_penalty, 5, 0)
		issrLayout.addWidget(self.ins_penalty, 5, 1)
		issrLayout.addWidget(self.del_penalty, 5, 2)

		issrGroup.setLayout(issrLayout)

		otherLayout = QHBoxLayout()

		level_group = KraitGroupBox("Motif standardization")
		level_label = QLabel("Level")
		self.level_select = QComboBox()

		standard_levels = [
			"Level 0",
			"Level 1",
			"Level 2",
			"Level 3",
			"Level 4"
		]
		self.level_select.addItems(standard_levels)
		level_layout = QHBoxLayout()
		level_layout.addWidget(level_label)
		level_layout.addWidget(self.level_select, 1)
		level_group.setLayout(level_layout)

		flank_group = KraitGroupBox("Flank sequence")
		flankLabel = QLabel("Length")
		self.flankValue = QSpinBox()
		self.flankValue.setMaximum(10000)
		flankLayout = QHBoxLayout()
		flankLayout.addWidget(flankLabel)
		flankLayout.addWidget(self.flankValue, 1)
		flank_group.setLayout(flankLayout)

		otherLayout.addWidget(level_group)
		otherLayout.addWidget(flank_group)
		
		mainLayout = QVBoxLayout()
		mainLayout.addWidget(repeatsGroup)
		mainLayout.addWidget(distanceGroup)
		mainLayout.addWidget(satelliteGroup)
		mainLayout.addWidget(issrGroup)
		mainLayout.addLayout(otherLayout)
		self.setLayout(mainLayout)
		#self.get_settings()

	def get_settings(self):
		self.monoValue.setValue(int(self.settings.value('SSR/mono', 12)))
		self.diValue.setValue(int(self.settings.value('SSR/di', 7)))
		self.triValue.setValue(int(self.settings.value('SSR/tri', 5)))
		self.tetraValue.setValue(int(self.settings.value('SSR/tetra', 4)))
		self.pentaValue.setValue(int(self.settings.value('SSR/penta', 4)))
		self.hexaValue.setValue(int(self.settings.value('SSR/hexa', 4)))

		self.distanceValue.setValue(int(self.settings.value('CSSR/dmax', 10)))

		self.min_tandem_motif.setValue(int(self.settings.value('VNTR/vmin', 7)))
		self.max_tandem_motif.setValue(int(self.settings.value('VNTR/vmax', 30)))
		self.min_tandem_repeat.setValue(int(self.settings.value('VNTR/vrep', 2)))

		self.seed_min_repeat.setValue(int(self.settings.value('ITR/srep', 3)))
		self.seed_min_length.setValue(int(self.settings.value('ITR/slen', 8)))
		self.max_error.setValue(int(self.settings.value('ITR/error', 3)))
		self.min_score.setValue(int(self.settings.value('ITR/score', 10)))
		self.mis_penalty.setValue(int(self.settings.value('ITR/mismatch', 1)))
		self.gap_penalty.setValue(int(self.settings.value('ITR/gap', 2)))

		self.flankValue.setValue(int(self.settings.value('STR/flank', 100)))
		self.level_select.setCurrentIndex(int(self.settings.value('STR/level', 3)))

	def save_settings(self):
		self.settings.setValue('SSR/mono', self.monoValue.value())
		self.settings.setValue('SSR/di', self.diValue.value())
		self.settings.setValue('SSR/tri', self.triValue.value())
		self.settings.setValue('SSR/tetra', self.tetraValue.value())
		self.settings.setValue('SSR/penta', self.pentaValue.value())
		self.settings.setValue('SSR/hexa', self.hexaValue.value())
		self.settings.setValue('CSSR/dmax', self.distanceValue.value())
		
		self.settings.setValue('VNTR/vmin', self.min_tandem_motif.value())
		self.settings.setValue('VNTR/vmax', self.max_tandem_motif.value())
		self.settings.setValue('VNTR/vrep', self.min_tandem_repeat.value())
		
		self.settings.setValue('ITR/srep', self.seed_min_repeat.value())
		self.settings.setValue('ITR/slen', self.seed_min_length.value())
		self.settings.setValue('ITR/error', self.max_error.value())
		self.settings.setValue('ITR/score', self.min_score.value())
		self.settings.setValue('ITR/mismatch', self.mis_penalty.value())
		self.settings.setValue('ITR/gap', self.gap_penalty.value())

		self.settings.setValue('STR/flank', self.flankValue.value())
		self.settings.setValue('STR/level', self.level_select.currentIndex())

class PreferenceDialog(QDialog):
	def __init__(self, parent=None):
		super(PreferenceDialog, self).__init__(parent)
		self.settings = QSettings()
		self.setWindowTitle(self.tr("Preferences"))
		#self.setMinimumWidth(500)

		self.search_tab = SearchParameterPanel(self)
		self.primer_tab = PrimerParameterPanel(self)

		self.tabWidget = QTabWidget()
		self.tabWidget.addTab(self.search_tab, 'Search')
		self.tabWidget.addTab(self.primer_tab, 'Primer')

		buttonBox = QDialogButtonBox(QDialogButtonBox.RestoreDefaults | QDialogButtonBox.Save | QDialogButtonBox.Cancel)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
		buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restore_settings)

		spacerItem = QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)

		mainLayout = QVBoxLayout()
		mainLayout.addWidget(self.tabWidget)
		mainLayout.addItem(spacerItem)
		mainLayout.addWidget(buttonBox)

		self.setLayout(mainLayout)

	def save_settings(self):
		self.search_tab.save_settings()
		self.primer_tab.save_settings()

	def restore_settings(self):
		self.settings.clear()
		self.search_tab.get_settings()
		self.primer_tab.get_settings()
		self.save_settings()

	def goto_primer_panel(self):
		self.tabWidget.setCurrentIndex(1)
