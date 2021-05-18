import os
import sys
import multiprocessing

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from widgets import *

if __name__ == '__main__':
	multiprocessing.freeze_support()

	QCoreApplication.setOrganizationName("Krait")
	QCoreApplication.setOrganizationDomain("krait2.readthedocs.io")
	QCoreApplication.setApplicationName("Kriat2")

	QSettings.setDefaultFormat(QSettings.IniFormat)

	app = QApplication(sys.argv)
	win = KraitMainWindow()
	win.show()
	sys.exit(app.exec_())
