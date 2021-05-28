import sys
import apsw
import stria
import primer3
import pyfastx
import PySide6

__all__ = ['KRAIT_VERSION', 'KRAIT_BUILD', 'KRAIT_ABOUT']

KRAIT_VERSION = "0.1.0"

KRAIT_BUILD = "20210528"

KRAIT_CITATION = """
Du L, Zhang C, Liu Q, Zhang X, Yue B (2018)
Krait: an ultrafast tool for genome-wide survey of microsatellites and primer design.
Bioinformatics. 34(4):681-683
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
		<td>stria</td>
		<td>v{stria}</td>
		<td>
			<a href="https://github.com/lmdu/stria">
				https://github.com/lmdu/stria
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
		<td>SQLite3</td>
		<td>v{sqlite}</td>
		<td>
			<a href="https://www.sqlite.org/index.html">
				https://www.sqlite.org/index.html
			</a>
		<td>
	</tr>
	<tr>
		<td>primer3</td>
		<td>v2.3.7</td>
		<td>
			<a href="https://primer3.org/">
				https://primer3.org
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
		<td>cgranges</td>
		<td>v0.1.0</td>
		<td>
			<a href="https://github.com/lh3/cgranges">
				https://github.com/lh3/cgranges
			</a>
		<td>
	</tr>
	<tr>
		<td>plotly.js</td>
		<td>v1.58.4</td>
		<td>
			<a href="https://plotly.com/javascript/">
				https://plotly.com/javascript
			</a>
		<td>
	</tr>
	<tr>
		<td>DataTables</td>
		<td>v1.10.24</td>
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
	stria = stria.version(),
	pyfastx = pyfastx.version(),
	apsw = apsw.apswversion(),
	sqlite = apsw.sqlitelibversion(),
	primerpy = primer3.__version__
)
