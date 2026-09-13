# المكونات المضمنة | Bundled components

يضم التطبيق Python ومكتباته القياسية وTcl/Tk ومحمّل PyInstaller. يوجد ترخيص Python في Python.txt، وتراخيص Tcl/Tk ضمن مجلدات بياناتهما في الحزمة. لا يُضمّن النموذج أو llama.cpp في المثبت؛ ينزلهما التطبيق بعد اختيار المستخدم. راجع مصادرهما وتراخيصهما المرتبطة في كتالوج التطبيق.

The app bundles Python and its standard library, Tcl/Tk and the PyInstaller bootloader. Python's license is in Python.txt; Tcl/Tk licenses are included in their bundled data directories. Models and llama.cpp are not embedded in the installer and are downloaded after user selection; see the sources and licenses linked in the app catalog.

- Python: https://docs.python.org/3/license.html
- Tcl/Tk: https://www.tcl-lang.org/software/tcltk/license.html
- PyInstaller: GPL with a bootloader exception permitting distribution of bundled applications. https://pyinstaller.org/en/stable/license.html
- Inno Setup generates the installer: https://jrsoftware.org/isinfo.php
