import sys
import apsw
import pytrf
import pygros
import primer3
import pyfastx
import PySide6

__all__ = ['KRAIT_VERSION', 'KRAIT_BUILD', 'KRAIT_ABOUT',
			'KRAIT_SEARCH_PARAMETERS', 'KRAIT_PRIMER_TAGS',
			'KRAIT_PRIMER_COMMONS']

KRAIT_VERSION = "2.0.1"

KRAIT_BUILD = "20241113"

KRAIT_CITATION = """

"""

KRAIT_ABOUT ="""
<p><b>Krait2 - Microsatellite Identification and Primer Design</b></p>
<p><b>Version</b> v{version} <b>Build</b> {build}<p>
<p>Krait2 is a robust and ultrafast tool that provides a user-friendly GUI for no computationally
skilled biologists to extract perfect, imperfect and compound microsatellites and VNTRs from fasta
formatted DNA sequences; and design primers; and perform statistical analysis.</p>
<p><b>Acknowledgements:</b></p>
<table cellspacing="5">
	<tr>
		<td>Python</td>
		<td>v{python}</td>
		<td>
			<a href="https://www.python.org/">
				https://www.python.org
			</a>
		<td>
	</tr>
	<tr>
		<td>PySide6</td>
		<td>v{pyside}</td>
		<td>
			<a href="https://wiki.qt.io/Qt_for_Python">
				https://wiki.qt.io/Qt_for_Python
			</a>
		<td>
	</tr>
	<tr>
		<td>pytrf</td>
		<td>v{pytrf}</td>
		<td>
			<a href="https://github.com/lmdu/pytrf">
				https://github.com/lmdu/pytrf
			</a>
		<td>
	</tr>
	<tr>
		<td>pyfastx</td>
		<td>v{pyfastx}</td>
		<td>
			<a href="https://github.com/lmdu/pyfastx">
				https://github.com/lmdu/pyfastx
			</a>
		<td>
	</tr>
	<tr>
		<td>apsw</td>
		<td>v{apsw}</td>
		<td>
			<a href="https://github.com/rogerbinns/apsw">
				https://github.com/rogerbinns/apsw
			</a>
		<td>
	</tr>
	<tr>
		<td>primer3-py</td>
		<td>v{primerpy}</td>
		<td>
			<a href="https://github.com/libnano/primer3-py">
				https://github.com/libnano/primer3-py
			</a>
		<td>
	</tr>
	<tr>
		<td>pygros</td>
		<td>v{pygros}</td>
		<td>
			<a href="https://github.com/lmdu/pygros">
				https://github.com/lmdu/pygros
			</a>
		<td>
	</tr>
	<tr>
		<td>cgranges</td>
		<td>v0.1.1</td>
		<td>
			<a href="https://github.com/lh3/cgranges">
				https://github.com/lh3/cgranges
			</a>
		<td>
	</tr>
	<tr>
		<td>plotly.js</td>
		<td>v2.35.0</td>
		<td>
			<a href="https://plotly.com/javascript/">
				https://plotly.com/javascript
			</a>
		<td>
	</tr>
	<tr>
		<td>DataTables</td>
		<td>v2.1.6</td>
		<td>
			<a href="https://datatables.net/">
				https://datatables.net
			</a>
		<td>
	</tr>
</table>
""".format(
	version = KRAIT_VERSION,
	build = KRAIT_BUILD,
	python = sys.version.split()[0],
	pyside = PySide6.__version__,
	pytrf = pytrf.__version__,
	pyfastx = pyfastx.__version__,
	pygros = pygros.__version__,
	apsw = apsw.apswversion(),
	primerpy = primer3.__version__
)

#default parameter and type for krait
KRAIT_SEARCH_PARAMETERS = {
	'SSR/mono': (12, int),
	'SSR/di': (7, int),
	'SSR/tri': (5, int),
	'SSR/tetra': (4, int),
	'SSR/penta': (4, int),
	'SSR/hexa': (4, int),
	'CSSR/dmax': (10, int),
	'GTR/minmotif': (7, int),
	'GTR/maxmotif': (30, int),
	'GTR/minrep': (3, int),
	'GTR/minlen': (10, int),
	#'ITR/minmsize': (1, int),
	#'ITR/maxmsize': (6, int),
	'ISSR/minsrep': (3, int),
	'ISSR/minslen': (10, int),
	'ISSR/maxerr': (3, int),
	'ISSR/identity': (70, float),
	'ISSR/maxextend': (2000, int),
	'STR/level': (3, int),
	'STR/flank': (50, int),
	'STAT/unit': (0, int),
	'STAT/unkown': (0, int)
}

#default parameter and type for primer3
KRAIT_PRIMER_TAGS = {
	'PRIMER_FLANK_LENGTH': (100, int),
	'PRIMER_PICK_LEFT_PRIMER': (1, int),
	'PRIMER_PICK_INTERNAL_OLIGO': (0, int),
	'PRIMER_PICK_RIGHT_PRIMER': (1, int),
	'PRIMER_NUM_RETURN': (1, int),
	'PRIMER_MIN_5_PRIME_OVERLAP_OF_JUNCTION': (5, int),
	'PRIMER_PRODUCT_SIZE_RANGE': ('100-300', str),
	'PRIMER_PRODUCT_OPT_SIZE': (0, int),
	'PRIMER_PAIR_WT_PRODUCT_SIZE_LT': (0.0, float),
	'PRIMER_PAIR_WT_PRODUCT_SIZE_GT': (0.0, float),
	'PRIMER_MIN_SIZE': (18, int),
	'PRIMER_INTERNAL_MIN_SIZE': (18, int),
	'PRIMER_OPT_SIZE': (20, int),
	'PRIMER_INTERNAL_OPT_SIZE': (20, int),
	'PRIMER_MAX_SIZE': (27, int),
	'PRIMER_INTERNAL_MAX_SIZE': (27, int),
	'PRIMER_WT_SIZE_LT': (1.0, float),
	'PRIMER_INTERNAL_WT_SIZE_LT': (1.0, float),
	'PRIMER_WT_SIZE_GT': (1.0, float),
	'PRIMER_INTERNAL_WT_SIZE_GT': (1.0, float),
	'PRIMER_MIN_GC': (20.0, float),
	'PRIMER_INTERNAL_MIN_GC': (20.0, float),
	'PRIMER_OPT_GC_PERCENT': (50.0, float),
	'PRIMER_MAX_GC': (80.0, float),
	'PRIMER_INTERNAL_MAX_GC': (80.0, float),
	'PRIMER_WT_GC_PERCENT_LT': (0.0, float),
	'PRIMER_INTERNAL_WT_GC_PERCENT_LT': (0.0, float),
	'PRIMER_WT_GC_PERCENT_GT': (0.0, float),
	'PRIMER_INTERNAL_WT_GC_PERCENT_GT': (0.0, float),
	'PRIMER_GC_CLAMP': (2, int),
	'PRIMER_MAX_END_GC': (5, int),
	'PRIMER_MIN_TM': (57.0, float),
	'PRIMER_INTERNAL_MIN_TM': (57.0, float),
	'PRIMER_OPT_TM': (60.0, float),
	'PRIMER_INTERNAL_OPT_TM': (60.0, float),
	'PRIMER_MAX_TM': (63.0, float),
	'PRIMER_INTERNAL_MAX_TM': (63.0, float),
	'PRIMER_PAIR_MAX_DIFF_TM': (100.0, float),
	'PRIMER_WT_TM_LT': (1.0, float),
	'PRIMER_INTERNAL_WT_TM_LT': (1.0, float),
	'PRIMER_WT_TM_GT': (1.0, float),
	'PRIMER_INTERNAL_WT_TM_GT': (1.0, float),
	'PRIMER_PAIR_WT_DIFF_TM': (0.0, float),
	'PRIMER_PRODUCT_MIN_TM': (-1000000.0, float),
	'PRIMER_PRODUCT_OPT_TM': (0.0, float),
	'PRIMER_PRODUCT_MAX_TM': (1000000.0, float),
	'PRIMER_PAIR_WT_PRODUCT_TM_LT': (0.0, float),
	'PRIMER_PAIR_WT_PRODUCT_TM_GT': (0.0, float),
	'PRIMER_TM_FORMULA': (0, int),
	'PRIMER_SALT_MONOVALENT': (50.0, float),
	'PRIMER_INTERNAL_SALT_MONOVALENT': (50.0, float),
	'PRIMER_SALT_DIVALENT': (0.0, float),
	'PRIMER_INTERNAL_SALT_DIVALENT': (0.0, float),
	'PRIMER_DNTP_CONC': (0.0, float),
	'PRIMER_INTERNAL_DNTP_CONC': (0.0, float),
	'PRIMER_SALT_CORRECTIONS': (0, int),
	'PRIMER_DNA_CONC': (50.0, float),
	'PRIMER_INTERNAL_DNA_CONC': (50.0, float),
	'PRIMER_MAX_SELF_ANY': (8.00, float),
	'PRIMER_INTERNAL_MAX_SELF_ANY': (12.00, float),
	'PRIMER_PAIR_MAX_COMPL_ANY': (8.00, float),
	'PRIMER_WT_SELF_ANY': (0.0, float),
	'PRIMER_INTERNAL_WT_SELF_ANY': (0.0, float),
	'PRIMER_PAIR_WT_COMPL_ANY': (0.0, float),
	'PRIMER_MAX_SELF_END': (3.00, float),
	'PRIMER_INTERNAL_MAX_SELF_END': (12.00, float),
	'PRIMER_PAIR_MAX_COMPL_END': (3.00, float),
	'PRIMER_WT_SELF_END': (0.0, float),
	'PRIMER_INTERNAL_WT_SELF_END': (0.0, float),
	'PRIMER_PAIR_WT_COMPL_END': (0.0, float),
	'PRIMER_MAX_END_STABILITY': (100.0, float),
	'PRIMER_WT_END_STABILITY': (0.0, float),
	'PRIMER_MAX_NS_ACCEPTED': (5, int),
	'PRIMER_INTERNAL_MAX_NS_ACCEPTED': (0, int),
	'PRIMER_WT_NUM_NS': (0.0, float),
	'PRIMER_INTERNAL_WT_NUM_NS': (0.0, float),
	'PRIMER_MAX_POLY_X': (0, int),
	'PRIMER_INTERNAL_MAX_POLY_X': (5, int),
	'PRIMER_MIN_THREE_PRIME_DISTANCE': (-1, int),
	'PRIMER_PICK_ANYWAY': (0, int),
	'PRIMER_LOWERCASE_MASKING': (0, int),
	'PRIMER_EXPLAIN_FLAG': (0, int),
	'PRIMER_LIBERAL_BASE': (0, int),
	'PRIMER_FIRST_BASE_INDEX': (0, int),
	'PRIMER_MAX_TEMPLATE_MISPRIMING': (-1.00, float),
	'PRIMER_PAIR_MAX_TEMPLATE_MISPRIMING': (-1.00, float),
	'PRIMER_WT_TEMPLATE_MISPRIMING': (0.0, float),
	'PRIMER_PAIR_WT_TEMPLATE_MISPRIMING': (0.0, float),
	'PRIMER_LIB_AMBIGUITY_CODES_CONSENSUS': (1, int),
	'PRIMER_MAX_LIBRARY_MISPRIMING': (12.00, float),
	'PRIMER_INTERNAL_MAX_LIBRARY_MISHYB': (12.00, float),
	'PRIMER_PAIR_MAX_LIBRARY_MISPRIMING': (24.00, float),
	'PRIMER_WT_LIBRARY_MISPRIMING': (0.0, float),
	'PRIMER_INTERNAL_WT_LIBRARY_MISHYB': (0.0, float),
	'PRIMER_PAIR_WT_LIBRARY_MISPRIMING': (0.0, float),
	'PRIMER_MIN_QUALITY': (0, int),
	'PRIMER_INTERNAL_MIN_QUALITY': (0, int),
	'PRIMER_MIN_END_QUALITY': (0, int),
	'PRIMER_QUALITY_RANGE_MIN': (0, int),
	'PRIMER_QUALITY_RANGE_MAX': (100, int),
	'PRIMER_WT_SEQ_QUAL': (0.0, float),
	'PRIMER_INTERNAL_WT_SEQ_QUAL': (0.0, float),
	'PRIMER_PAIR_WT_PR_PENALTY': (1.0, float),
	'PRIMER_PAIR_WT_IO_PENALTY': (0.0, float),
	'PRIMER_INSIDE_PENALTY': (-1.0, float),
	'PRIMER_OUTSIDE_PENALTY': (0.0, float),
	'PRIMER_WT_POS_PENALTY': (1.0, float),
	'PRIMER_SEQUENCING_LEAD': (50, int),
	'PRIMER_SEQUENCING_SPACING': (500, int),
	'PRIMER_SEQUENCING_INTERVAL': (250, int),
	'PRIMER_SEQUENCING_ACCURACY': (20, int),
	'PRIMER_WT_END_QUAL': (0.0, float),
	'PRIMER_INTERNAL_WT_END_QUAL': (0.0, float)
}

KRAIT_PRIMER_COMMONS = [
	'PRIMER_PRODUCT_SIZE_RANGE',
	'PRIMER_NUM_RETURN',
	'PRIMER_MIN_SIZE',
	'PRIMER_OPT_SIZE',
	'PRIMER_MAX_SIZE',
	'PRIMER_MIN_GC',
	'PRIMER_OPT_GC_PERCENT',
	'PRIMER_MAX_GC',
	'PRIMER_MIN_TM',
	'PRIMER_OPT_TM',
	'PRIMER_MAX_TM',
	'PRIMER_MAX_NS_ACCEPTED',
	'PRIMER_GC_CLAMP',
	'PRIMER_PAIR_MAX_DIFF_TM',
	'PRIMER_MAX_END_STABILITY'
]
