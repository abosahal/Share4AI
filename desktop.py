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
            def check(window, close, app):
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
                from provider.hardware import Hardware
                from provider.catalog import recommend
                from provider.i18n import tr
                hardware = Hardware('Windows', 'AMD64', 'test', 4, 7.8 * 1024, 0.8 * 1024, 362.3 * 1024, [])
                app.recommendation = recommend(hardware)
                app.emit('hardware', hardware)
                app.emit('recommendation', app.recommendation)
                app.emit('working', False)
                def verify_blocked():
                    try:
                        download = next(w for w in widgets(window) if isinstance(w, ttk.Button)
                                        and w.cget('text') == tr('2. Download & Verify', language='ar'))
                        assert download.instate(['disabled'])
                        assert app.recommendation.blockers == ('total_ram',)
                        # Language toggling must not re-enable a blocked download.
                        switch.invoke(); switch.invoke()
                        assert download.instate(['disabled'])
                        hardware.available_ram_mb = 10 * 1024
                        hardware.ram_mb = 16 * 1024
                        app.recommendation = recommend(hardware)
                        app.emit('hardware', hardware)
                        app.emit('recommendation', app.recommendation)
                        app.emit('working', False)
                        window.after(150, lambda: verify_ready(download))
                    except Exception:
                        close()
                        raise
                def verify_ready(download):
                    try:
                        assert not download.instate(['disabled'])
                        report.write_text(json.dumps({'ok': True, 'catalog': True,
                            'tk': window.tk.eval('info patchlevel'), 'language_switch': True,
                            'low_memory_download_blocked': True, 'rescan_download_enabled': True}), encoding='utf-8')
                    finally:
                        close()
                window.after(150, verify_blocked)
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
