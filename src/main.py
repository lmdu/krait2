import os
import sys
import multiprocessing

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

import resources
from window import *
from config import *

class KraitApplication(QApplication):
	osx_open_with = Signal(str)

	def __init__(self, argv):
		super().__init__(argv)

	def event(self, event):
		if sys.platform == 'darwin':
			if isinstance(event, QFileOpenEvent):
				self.osx_open_with.emit(event.file())

		return super().event(event)

if __name__ == '__main__':
	multiprocessing.freeze_support()

	#fix taskbar icon display
	if os.name == 'nt':
		import ctypes
		myappid = "DuLab.Krait.Krait.{}".format(KRAIT_VERSION)
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

	QCoreApplication.setOrganizationName("DuLab")
	QCoreApplication.setOrganizationDomain("big.cdu.edu.cn")
	QCoreApplication.setApplicationName("Kriat")
	QCoreApplication.setApplicationVersion(KRAIT_VERSION)
	QSettings.setDefaultFormat(QSettings.IniFormat)

	app = KraitApplication(sys.argv)
	QFontDatabase.addApplicationFont(":/fonts/robotomono.ttf")
	win = KraitMainWindow()
	app.osx_open_with.connect(win.open_project)

	args = app.arguments()
	if len(args) > 1:
		if os.path.isfile(args[1]):
			win.open_project(args[1])

	sys.exit(app.exec())
