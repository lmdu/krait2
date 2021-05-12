import os
import sys
import multiprocessing
from PySide6.QtWidgets import *

from widgets import *

if __name__ == '__main__':
	multiprocessing.freeze_support()

	app = QApplication(sys.argv)
	win = KraitMainWindow()
	win.show()
	sys.exit(app.exec_())
