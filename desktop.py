"""Windowed packaged entry point. No terminal is required by end users."""
import ctypes
import json
import os
from pathlib import Path
import sys
import tempfile


def main():
    # Import native modules before restoring the DLL search path for external
    # NVIDIA tools and llama.cpp; see PyInstaller's subprocess guidance.
    from provider.ui import launch
    from provider.catalog import load_catalog
    if getattr(sys, 'frozen', False) and os.name == 'nt':
        ctypes.windll.kernel32.SetDllDirectoryW(None)
    if len(sys.argv) == 3 and sys.argv[1] == '--smoke-test':
        report = Path(sys.argv[2]).resolve()
        with tempfile.TemporaryDirectory(prefix='share4ai-package-test-') as directory:
            def check(window, close):
                window.withdraw()
                from tkinter import ttk
                def widgets(parent):
                    for child in parent.winfo_children():
                        yield child
                        yield from widgets(child)
                before = list(widgets(window))
                switch = next(w for w in before if isinstance(w, ttk.Button) and w.cget('text') == 'English')
                switch.invoke()
                assert switch.cget('text') == 'العربية'
                switch.invoke()
                assert switch.cget('text') == 'English'
                assert load_catalog()['models']
                report.write_text(json.dumps({'ok': True, 'catalog': True,
                    'tk': window.tk.eval('info patchlevel'), 'language_switch': True}), encoding='utf-8')
                window.after(50, close)
            launch(Path(directory), on_ready=check)
    else:
        launch()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if '--smoke-test' in sys.argv:
            raise
        # Never expose paths, customer content or credentials in startup errors.
        ctypes.windll.user32.MessageBoxW(None,
            'تعذر فتح Share4AI. أعد تشغيل التطبيق أو أعد تثبيته من ملف التنزيل.\n'
            'Share4AI could not start. Restart the app or reinstall it from the download.',
            'Share4AI', 0x10 | 0x00100000 | 0x00080000)
        sys.exit(1)
