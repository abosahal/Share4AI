# بناء المثبّت | Installer build

## العربية

هذه التعليمات للمطورين فقط. قاعدة المنتج في ../AGENTS.md تمنع اشتراط الطرفية أو أدوات التطوير على العميل والمزود. ملف التسليم هو Share4AI-Setup-1.1.0-windows-x64.exe؛ حزمة الكود السابقة ليست مسار تسليم المستخدم.

للبناء استخدم Windows x64 وPython 3.12 مع Tcl/Tk وInno Setup 6.7.3. نفّذ الأوامر أدناه من جذر المستودع. يفحص البناء الواجهة المجمّعة وتبديل اللغة والكتالوج قبل إنتاج المثبّت. tools/test_installer.ps1 يفحص التثبيت وإعادته والإزالة داخل مجلد اختبار، ويرفض استبدال أي تثبيت أو اختصار موجود. لا يحذف المثبت نماذج المستخدم وإعداداته.

## English

These instructions are for maintainers only. ../AGENTS.md forbids requiring terminals or developer tools from clients/providers. Deliver Share4AI-Setup-1.1.0-windows-x64.exe; the previous source package is not the end-user delivery path.

Build on Windows x64 with Python 3.12, Tcl/Tk and Inno Setup 6.7.3. Run these commands from the repository root. The build checks packaged UI startup, language switching and the catalog before producing the installer. tools/test_installer.ps1 checks install/reinstall/uninstall in a test folder and refuses to overwrite any existing installation or shortcut. Uninstall preserves user models and preferences.

```powershell
python -m pip install -r packaging/requirements-build.txt
python -m unittest discover -s tests -q
python tools/build_windows.py --iscc 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
./tools/test_installer.ps1
```

GitHub Actions builds and publishes a prerelease on packaging changes to the development branch or main. This automated run must succeed before advertising a release download. The SHA256 file checks integrity; it does not replace a publisher signature. A code-signing certificate, clean-machine validation without Python, full Arabic visual checks and actual GPU inference remain release gates.

يبني GitHub Actions إصدارًا تجريبيًا وينشره عند تغيير ملفات التغليف في فرع التطوير أو main. يجب نجاح التشغيل قبل إعلان رابط الإصدار. ملف SHA256 للتحقق من السلامة وليس بديلًا عن توقيع الناشر. تظل شهادة توقيع التطبيق واختبار جهاز نظيف دون Python والفحص البصري للعربية وتشغيل النموذج على GPU شروطًا قبل الاعتماد.

Build references: [PyInstaller bundling](https://pyinstaller.org/en/stable/operating-mode.html), [external process DLL handling](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html), [Inno per-user install](https://jrsoftware.org/ishelp/topic_setup_privilegesrequired.htm).
