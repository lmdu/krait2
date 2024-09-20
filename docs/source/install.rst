Installation
============

Krait2 is a standalone desktop software designed to run on Windows, Linux and MacOS. You don't need to install any dependencies to easily run and use it.

Krait2 download: `https://github.com/lmdu/krait2/releases <https://github.com/lmdu/krait2/releases>`_

中国镜像下载地址: `https://big.cdu.edu.cn/software/krait2 <https://big.cdu.edu.cn/software/krait2>`_

On Windows
----------

#. Go to `https://github.com/lmdu/krait2/releases <https://github.com/lmdu/krait2/releases>`_ page, click on ``krait-2.x.x-win64.exe`` to download it. Then double click the downloaded installer to install the program following the on-screen instructions.

#. Or, you can click on ``Krait-2.x.x-win64.7z`` to download the portable version. Then uncompress the 7z file using `7-zip <https://www.7-zip.org/>`_ and double click the Krait.exe to run it.

On Linux
--------

#. Go to `https://github.com/lmdu/krait2/releases <https://github.com/lmdu/krait2/releases>`_ page, click on ``krait-2.x.x-ubuntu.deb`` to download it. Then double click the downloaded installer to install the program following the on-screen instructions.

#. You can also install Krait2 using command line tool like this:

	.. code:: shell

		sudo dpkg -i Krait-2.x.x-ubuntu.deb

#. Or, you can click on ``Krait-2.x.x-ubuntu.AppImage`` to download the portable version. Just run it like this:

	.. code:: shell

		chmod +x Krait-2.x.x-ubuntu.AppImage
		./Krait-2.x.x-ubuntu.AppImage

	You can also double click the .AppImage file to run it.

#. Or, you can click on ``Krait-2.x.x-ubuntu.tar.gz`` to download the compressed package, and then uncompress it to run Krait:

.. code:: shell

	tar xzvf Krait-2.x.x-ubuntu.tar.gz
	cd Krait
	./Krait

.. note::
	
	Currently, we only tested Krait2 on Ubuntu systems. It may also support other Linux systems based on Debian, for example, Deepin.

	The installation file with ``ubuntu20.04`` can only run on Ubuntu 20.04, while file with ``ubuntu22.04`` can run on Ubuntu >= 22.04.

On MacOS
--------

Because the Krait2 is unsigned application which can not be installed from apple store, the gatekeeper of MacOS will prevent the installation and running of Krait2. So, before installation, you should disable gatekeeper from command line in MacOS.

To disable gatekeeper, following these steps:

#. Launch **Terminal** from **Applications** > **Utilities**.

#. Enter the following command:

	.. code:: shell

		sudo spctl --master-disable

#. Press **Enter** and type your admin password.

#. Press **Enter** again.

Now, the Anywhere option should be available under the **Allow apps downloaded from** section of **System Preferences** > **Security & Privacy** > **General**.

.. note::

	If you want to re-enable gatekeeper, you can do with a simple command:

	.. code:: shell

		sudo spclt --master-enable

Then, go to `https://github.com/lmdu/krait2/releases <https://github.com/lmdu/krait2/releases>`_ page, click on ``Krait-2.x.x-macos.dmg`` to download it. Then double click the downloaded installer to install the program following the on-screen instructions.

After installation, you should set the permissions as following:

.. code:: shell

	sudo xattr -r -d com.apple.quarantine /Applications/Krait.app
