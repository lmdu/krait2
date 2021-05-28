import os
import sys
import ctypes
import multiprocessing

from PySide6.QtCore import *
from PySide6.QtWidgets import *

from widgets import *
from config import *

if __name__ == '__main__':
	multiprocessing.freeze_support()

	QCoreApplication.setOrganizationName("Krait")
	QCoreApplication.setOrganizationDomain("krait2.readthedocs.io")
	QCoreApplication.setApplicationName("Kriat2")

	QSettings.setDefaultFormat(QSettings.IniFormat)

	if os.name == 'nt':
		myappid = "BIG.Tandem.Krait2.{}".format(KRAIT_VERSION)
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

	app = QApplication(sys.argv)
	win = KraitMainWindow()
	win.show()
	sys.exit(app.exec_())
