from provider.i18n import tr as translate, display_message as translate_message, TEXT
from .preferences import load_language, save_language
from .readiness import diagnostic_text, gpu_fields, mode_label, selected_gpu, verdict
import re
import os
import threading
import tkinter as tk
from tkinter import ttk
from .app import ProviderApp


def launch(state_dir=None, on_ready=None):
    app = ProviderApp(state_dir)
    language = load_language(app.root)

    def tr(source, **values):
        return translate(source, language=language, **values)

    def display_message(source):
        return '\n'.join(translate_message(line, language=language) for line in source.split('\n'))

    window = tk.Tk()
    window.title(tr('Share4AI Provider 1.1 — Community-powered AI'))
    window.geometry('1180x860')
    window.minsize(1040, 760)
    paper, lift, ink, mute, line, ok = '#0b0c0e', '#16181d', '#f2f3f5', '#9aa0ab', '#2a2e36', '#8fbf9f'
    window.configure(bg=paper)
    style = ttk.Style(window)
    style.theme_use('clam')
    style.configure('.', background=paper, foreground=ink)
    style.configure('TFrame', background=paper)
    style.configure('Card.TFrame', background=lift)
    style.configure('TLabel', background=paper, foreground=ink, padding=2)
    style.configure('Mute.TLabel', background=paper, foreground=mute)
    style.configure('Card.TLabel', background=lift, foreground=ink)
    style.configure('CardMute.TLabel', background=lift, foreground=mute)
    style.configure('Ok.TLabel', background=lift, foreground=ok)
    style.configure('Banner.TLabel', background=lift, foreground=ink, padding=6)
    style.configure('TButton', padding=(12, 10), background='#2a2e36', foreground=ink)
    style.map('TButton', background=[('active', '#3a404c'), ('disabled', '#1a1d24')],
              foreground=[('disabled', mute)])
    style.configure('Accent.TButton', background=ink, foreground=paper, padding=(12, 11))
    style.map('Accent.TButton', background=[('active', '#ffffff'), ('disabled', '#1a1d24')],
              foreground=[('disabled', mute)])
    style.configure('TNotebook', background=paper, borderwidth=0)
    style.configure('TNotebook.Tab', padding=(20, 11), background=lift, foreground=mute)
    style.map('TNotebook.Tab', background=[('selected', paper)], foreground=[('selected', ink)])
    style.configure('TProgressbar', troughcolor='#1a1d24', background=ink)
    style.configure('Gpu.Horizontal.TProgressbar', troughcolor='#1a1d24', background=ok)
    style.configure('TSeparator', background=line)
    style.configure('TEntry', fieldbackground=lift, foreground=ink)
    style.configure('TSpinbox', fieldbackground=lift, foreground=ink)

    header = ttk.Frame(window)
    header.pack(fill='x', padx=24, pady=(18, 10))
    titles = ttk.Frame(header)
    titles.pack(side='left', fill='x', expand=True)
    ttk.Label(titles, text=tr('Share4AI  /  Community-powered AI'), font=('Segoe UI', 22, 'bold')).pack(anchor='w')
    ttk.Label(titles, text=tr('Windows pilot • Local AI first • Authenticated outbound sharing'),
              style='Mute.TLabel').pack(anchor='w')
    tools = ttk.Frame(header)
    tools.pack(side='right')

    banner = ttk.Frame(window, style='Card.TFrame')
    banner.pack(fill='x', padx=24, pady=(0, 10))
    status = tk.StringVar(value=tr('Ready to scan'))
    next_step = tk.StringVar(value=tr('Scan, download, start, then test performance.'))
    ttk.Label(banner, text=tr('Next action'), style='CardMute.TLabel').pack(fill='x', padx=14, pady=(10, 0))
    ttk.Label(banner, textvariable=next_step, style='Banner.TLabel', font=('Segoe UI', 12, 'bold')).pack(fill='x', padx=8)
    status_label = ttk.Label(banner, textvariable=status, style='Banner.TLabel', wraplength=1080)
    status_label.pack(fill='x', padx=8, pady=(0, 2))
    progress = ttk.Progressbar(banner, maximum=100, mode='determinate')
    progress.pack(fill='x', padx=14, pady=(0, 14))

    def resize_banner(event):
        status_label.configure(wraplength=max(360, event.width - 56))
    window.bind('<Configure>', resize_banner)

    tabs = ttk.Notebook(window)
    tabs.pack(fill='both', expand=True, padx=24, pady=(0, 8))
    setup_tab, chat, settings = (ttk.Frame(tabs, padding=4) for _ in range(3))
    canvas = tk.Canvas(setup_tab, highlightthickness=0, bg=paper, bd=0)
    scrollbar = ttk.Scrollbar(setup_tab, orient='vertical', command=canvas.yview)
    scrollbar.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True)
    canvas.configure(yscrollcommand=scrollbar.set)
    setup = ttk.Frame(canvas)
    setup_item = canvas.create_window((0, 0), window=setup, anchor='nw')
    setup.bind('<Configure>', lambda event: canvas.configure(scrollregion=canvas.bbox('all')))

    def resize_setup(event):
        canvas.itemconfigure(setup_item, width=event.width)

    for frame, name in [(setup_tab, tr('Device & Setup')), (chat, tr('Local AI')), (settings, tr('Settings'))]:
        tabs.add(frame, text=name)

    body = ttk.Frame(setup)
    body.pack(fill='both', expand=True)
    main = ttk.Frame(body)
    rail = ttk.Frame(body, style='Card.TFrame')
    main.pack(side='left', fill='both', expand=True, padx=(0, 12))
    rail.pack(side='right', fill='y', ipadx=8)

    device = tk.StringVar(value=tr('Scan your device to find a suitable model.'))
    recommendation = tk.StringVar(value=tr('No recommendation yet'))
    readiness = tk.StringVar(value=tr('Ready to scan'))
    mode = tk.StringVar(value='—')
    notes = tk.StringVar(value='')
    network = tk.StringVar(value=tr('OFFLINE'))
    gpu_load = tk.IntVar(value=0)

    hero = ttk.Frame(main, style='Card.TFrame')
    hero.pack(fill='x', pady=(0, 12))
    ttk.Label(hero, text=tr('This computer'), style='CardMute.TLabel').pack(anchor='w', padx=14, pady=(12, 0))
    ttk.Label(hero, textvariable=device, style='Card.TLabel', font=('Segoe UI', 18, 'bold')).pack(anchor='w', padx=14, pady=(2, 0))
    ttk.Label(hero, textvariable=readiness, style='Ok.TLabel', font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=14, pady=(4, 0))
    ttk.Label(hero, textvariable=mode, style='CardMute.TLabel').pack(anchor='w', padx=14, pady=(0, 8))
    gpu_bar = ttk.Progressbar(hero, maximum=100, mode='determinate', variable=gpu_load, style='Gpu.Horizontal.TProgressbar')
    gpu_bar.pack(fill='x', padx=14, pady=(0, 14))

    resource_rows = ttk.Frame(main)
    resource_rows.pack(fill='x', pady=(0, 12))
    numbers = {}
    number_labels = []
    metric_keys = (
        'Graphics card', 'GPU memory', 'Free GPU memory', 'GPU usage now', 'GPU temperature',
        'Processor', 'Installed memory', 'Free memory', 'Free disk space (not required space)',
        'Free memory required by this version', 'Disk space required including reserve',
    )
    for index, key in enumerate(metric_keys):
        cell = ttk.Frame(resource_rows, style='Card.TFrame')
        row, column = divmod(index, 2)
        cell.grid(row=row, column=column, sticky='nsew', padx=4, pady=4)
        ttk.Label(cell, text=tr(key), style='CardMute.TLabel').pack(anchor='w', padx=12, pady=(10, 0))
        numbers[key] = tk.StringVar(value='—')
        label = ttk.Label(cell, textvariable=numbers[key], style='Card.TLabel', font=('Segoe UI', 13, 'bold'))
        label.pack(anchor='w', padx=12, pady=(2, 10))
        number_labels.append(label)
    resource_rows.columnconfigure(0, weight=1)
    resource_rows.columnconfigure(1, weight=1)

    model_card = ttk.Frame(main, style='Card.TFrame')
    model_card.pack(fill='x', pady=(0, 12))
    ttk.Label(model_card, text=tr('Recommended model'), style='CardMute.TLabel').pack(anchor='w', padx=14, pady=(12, 0))
    ttk.Label(model_card, textvariable=recommendation, style='Card.TLabel', wraplength=640).pack(anchor='w', padx=14, pady=(2, 6))
    reason_label = ttk.Label(model_card, text=tr('Qwen3.8 27B: 15.3 GB plus runtime'), style='CardMute.TLabel', wraplength=640)
    reason_label.pack(anchor='w', padx=14, pady=(0, 4))
    notes_label = ttk.Label(model_card, textvariable=notes, style='CardMute.TLabel', wraplength=640)
    notes_label.pack(anchor='w', padx=14, pady=(0, 12))

    buttons = []

    def provision_if_ready():
        if not app.recommendation or not app.recommendation.model:
            status.set(tr('Download unavailable until device requirements are met. See the reason above.'))
            return
        app.submit(app.provision)

    ttk.Label(rail, text=tr('Device & Setup'), style='Card.TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=12, pady=(12, 8))
    actions = [(tr('1. Scan'), app.scan_device), (tr('2. Download & Verify'), app.provision),
               (tr('3. Start Local AI'), app.start_local), (tr('4. Benchmark'), app.run_benchmark)]
    for index, (label, action) in enumerate(actions):
        kind = 'Accent.TButton' if index == 0 else 'TButton'
        button = ttk.Button(rail, text=label, style=kind, command=lambda a=action: app.submit(a))
        button.pack(fill='x', padx=12, pady=3)
        buttons.append(button)
    buttons[1].configure(command=provision_if_ready, state='disabled')

    def copy_report():
        try:
            report = diagnostic_text(app.hardware, app.recommendation)
            window.clipboard_clear()
            window.clipboard_append(report)
            status.set(tr('Device report copied'))
        except tk.TclError:
            status.set(tr('Could not copy device report'))

    ttk.Button(rail, text=tr('Copy device report'), command=copy_report).pack(fill='x', padx=12, pady=(10, 4))
    sizes_label = ttk.Label(rail, text=tr('Qwen3.8 27B: 15.3 GB plus runtime'), style='CardMute.TLabel', wraplength=240)
    sizes_label.pack(anchor='w', padx=12, pady=(4, 2))
    ttk.Label(rail, text=tr('The app also downloads its runtime and verifies the files automatically.'),
              style='CardMute.TLabel', wraplength=240).pack(anchor='w', padx=12, pady=(0, 12))

    ttk.Separator(rail).pack(fill='x', padx=12, pady=4)
    ttk.Label(rail, text=tr('Sharing connection'), style='Card.TLabel', font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=12, pady=(8, 0))
    ttk.Label(rail, textvariable=network, style='CardMute.TLabel').pack(anchor='w', padx=12)
    share_hint = ttk.Label(rail, text=tr('Sharing requires a passing benchmark and a provider credential. Stop Sharing cancels the current network job. Local AI stops sharing first.'),
                           style='CardMute.TLabel', wraplength=240)
    share_hint.pack(anchor='w', padx=12, pady=(4, 8))
    share = ttk.Frame(rail, style='Card.TFrame')
    share.pack(fill='x', padx=8, pady=(0, 12))

    def start_share():
        if not app.trial_client and not os.environ.get('SHARE4AI_PROVIDER_TOKEN'):
            status.set(tr('Sharing activation is not available in this trial. You can use Local AI.'))
            return
        app.submit(app.start_sharing)

    button = ttk.Button(share, text=tr('Start Sharing'), command=start_share)
    button.pack(fill='x', pady=3)
    buttons.append(button)
    trial_button = ttk.Button(share, text=tr('Try customer chat on this computer'),
                              command=lambda: app.submit(app.start_browser_trial))
    trial_button.pack(fill='x', pady=3)
    buttons.append(trial_button)
    ttk.Button(share, text=tr('Stop Sharing'),
               command=lambda: threading.Thread(target=app.stop_sharing, daemon=True).start()).pack(fill='x', pady=3)

    def resize_setup(event):
        canvas.itemconfigure(setup_item, width=event.width)
        wrap = max(240, event.width - 340)
        for widget in (reason_label, notes_label, share_hint, sizes_label):
            widget.configure(wraplength=wrap)
    canvas.bind('<Configure>', resize_setup)

    transcript = tk.Text(chat, wrap='word', font=('Segoe UI', 12), state='disabled',
                         bg=lift, fg=ink, insertbackground=ink, relief='flat', padx=16, pady=16)
    transcript.pack(fill='both', expand=True)
    entry = tk.Text(chat, height=3, wrap='word', font=('Segoe UI', 12),
                    bg=lift, fg=ink, insertbackground=ink, relief='flat', padx=12, pady=10)
    entry.pack(fill='x', pady=8)
    messages = []

    def append(text):
        transcript.configure(state='normal')
        transcript.insert('end', text, 'direction')
        transcript.see('end')
        transcript.configure(state='disabled')

    def send():
        content = entry.get('1.0', 'end').strip()
        if not content:
            return
        entry.delete('1.0', 'end')
        messages.append(dict(role='user', content=content))
        append('\n' + tr('You:') + ' ' + content + '\n' + tr('AI:') + ' ')
        snapshot = [dict(m) for m in messages]
        app.submit(lambda: app.chat(snapshot))

    chatrow = ttk.Frame(chat)
    chatrow.pack(fill='x')
    sendbutton = ttk.Button(chatrow, text=tr('Send'), style='Accent.TButton', command=send)
    sendbutton.pack(side='left')
    buttons.append(sendbutton)

    def clear():
        messages.clear()
        transcript.configure(state='normal')
        transcript.delete('1.0', 'end')
        transcript.configure(state='disabled')

    clearbutton = ttk.Button(chatrow, text=tr('Clear conversation'), command=clear)
    clearbutton.pack(side='left', padx=6)
    buttons.append(clearbutton)
    ttk.Label(chat, text=tr('Local conversation stays in memory and is not saved to history.'),
              style='Mute.TLabel').pack(anchor='w', pady=(6, 0))

    address = tk.StringVar(value=app.settings['control_plane'])
    maximum = tk.IntVar(value=app.settings['maximum'])
    advanced = ttk.Frame(settings)

    def toggle_advanced():
        if advanced.winfo_manager():
            advanced.pack_forget()
        else:
            advanced.pack(fill='x', pady=8)

    ttk.Button(settings, text=tr('Advanced settings (internal testing)'), command=toggle_advanced).pack(anchor='w')
    ttk.Label(advanced, text=tr('Control Plane address')).pack(anchor='w')
    ttk.Entry(advanced, textvariable=address, width=65).pack(anchor='w', pady=6)
    ttk.Label(settings, text=tr('Max GPU Usage (%)'), font=('Segoe UI', 12, 'bold')).pack(anchor='w', pady=(18, 0))
    ttk.Spinbox(settings, from_=0, to=100, textvariable=maximum, width=8).pack(anchor='w', pady=6)
    ttk.Label(settings, text=tr('Sharing pauses when resource usage or temperature is high. This setting does not impose a hard GPU limit. Public sharing activation is coming later.'),
              wraplength=800, style='Mute.TLabel').pack(anchor='w', pady=12)

    def save():
        try:
            value = maximum.get()
        except tk.TclError:
            status.set(tr('Enter a whole number from 0 to 100'))
            return
        url = address.get().strip()
        app.submit(lambda: app.save_settings(url, value))

    savebutton = ttk.Button(settings, text=tr('Save Settings'), command=save)
    savebutton.pack(anchor='w')
    buttons.append(savebutton)

    ttk.Button(tools, text=tr('Cancel / Stop AI'),
               command=lambda: threading.Thread(target=app.stop_all, daemon=True).start()).pack(side='right')

    latest = {}
    working = False

    def sync_buttons():
        for b in buttons:
            b.configure(state='disabled' if working else 'normal')
        if working or not app.recommendation or not app.recommendation.model:
            buttons[1].configure(state='disabled')

    def orient():
        rtl = language == 'ar'
        anchor, justify, side = ('e', 'right', 'right') if rtl else ('w', 'left', 'left')

        def visit(widget):
            if isinstance(widget, ttk.Label):
                widget.configure(anchor=anchor, justify=justify)
            if widget.winfo_manager() == 'pack':
                info = widget.pack_info()
                if str(info.get('anchor')) in ('w', 'e'):
                    widget.pack_configure(anchor=anchor)
            for child in widget.winfo_children():
                visit(child)
        visit(window)
        for label in number_labels:
            label.configure(anchor='w', justify='left')
        main.pack_configure(side='right' if rtl else 'left')
        rail.pack_configure(side='left' if rtl else 'right')
        selected = tabs.select()
        ordered = (settings, chat, setup_tab) if rtl else (setup_tab, chat, settings)
        for index, tab in enumerate(ordered):
            tabs.insert(index, tab)
        tabs.select(selected)
        scrollbar.pack_configure(side='left' if rtl else 'right')
        for widget in chatrow.winfo_children():
            widget.pack_configure(side=side)
        transcript.tag_configure('direction', justify=justify)
        transcript.tag_add('direction', '1.0', 'end')
        entry.tag_configure('direction', justify=justify)
        entry.tag_add('direction', '1.0', 'end')
        entry.configure(insertwidth=2)

    def change_language():
        nonlocal language
        old = language
        target = 'en' if old == 'ar' else 'ar'
        try:
            save_language(app.root, target)
        except OSError:
            status.set(tr('Could not save language; check folder access.'))
            return
        replacements = {translate(key, language=old): translate(key, language=target)
                        for key in TEXT if '{' not in key}
        language = target

        def update(widget):
            if 'text' in widget.keys():
                current = str(widget.cget('text'))
                if current in replacements:
                    widget.configure(text=replacements[current])
            for child in widget.winfo_children():
                update(child)
        update(window)
        window.title(tr('Share4AI Provider 1.1 — Community-powered AI'))
        for tab, key in ((setup_tab, 'Device & Setup'), (chat, 'Local AI'), (settings, 'Settings')):
            tabs.tab(tab, text=tr(key))
        for variable in (device, recommendation, status, network, next_step, readiness, mode, notes):
            if variable.get() in replacements:
                variable.set(replacements[variable.get()])
        language_button.configure(text='English' if language == 'ar' else 'العربية')
        guidance = next_step.get()
        for kind, value in list(latest.items()):
            render(kind, value)
        next_step.set(guidance)
        orient()

    language_button = ttk.Button(tools, text='English' if language == 'ar' else 'العربية', command=change_language)
    language_button.pack(side='right', padx=8)
    entry.bind('<KeyRelease>', lambda event: entry.tag_add('direction', '1.0', 'end'))

    def gb(amount):
        return f'{amount / 1024:.1f} GB'

    def apply_gpu(hw, rec):
        gpu = selected_gpu(hw, rec) if hw else None
        device.set(gpu.name if gpu else tr('No supported NVIDIA GPU'))
        fields = gpu_fields(gpu)
        numbers['Graphics card'].set(fields['name'] or '—')
        numbers['GPU memory'].set(fields['vram'])
        numbers['Free GPU memory'].set(fields['free_vram'])
        numbers['GPU usage now'].set(fields['utilization'])
        numbers['GPU temperature'].set(fields['temperature'])
        match = re.fullmatch(r'(\d+)%', fields['utilization'] or '')
        gpu_load.set(int(match[1]) if match else 0)

    def render(kind, value):
        nonlocal working
        if kind in ('status', 'hardware', 'recommendation', 'sharing', 'benchmark'):
            if kind in ('status', 'benchmark'):
                latest.pop('status', None)
                latest.pop('benchmark', None)
            latest[kind] = value
        if kind == 'status':
            status.set(display_message(value))
            match = re.fullmatch(r'(Runtime|Model) (\d+)%', value)
            progress.configure(value=min(100, int(match[2])) if match else 0)
            if value == 'Installed and SHA256 verified':
                next_step.set(tr('Download complete. Start Local AI, then test performance.'))
            elif value.startswith('Local AI ready'):
                next_step.set(tr('Local AI is ready. Test performance before sharing.'))
            elif value == 'Stopped':
                next_step.set(tr('Stopped. Start Local AI when you are ready.'))
        elif kind == 'working':
            working = bool(value)
            sync_buttons()
        elif kind == 'hardware':
            apply_gpu(value, app.recommendation)
            numbers['Processor'].set(f'{value.cores}')
            for key, amount in (('Installed memory', value.ram_mb), ('Free memory', value.available_ram_mb),
                                ('Free disk space (not required space)', value.disk_free_mb)):
                numbers[key].set(gb(amount))
            notes.set('\n'.join(display_message(item) for item in value.warnings) if value.warnings else '')
        elif kind == 'recommendation':
            recommendation.set((value.model['id'] if value.model else tr('No suitable model')) + '\n' + display_message(value.reason))
            readiness.set(tr(verdict(value)))
            mode.set(tr(mode_label(value)))
            if app.hardware:
                apply_gpu(app.hardware, value)
            for key, amount in (('Free memory required by this version', value.required_free_ram_mb),
                                ('Disk space required including reserve', value.required_disk_mb)):
                numbers[key].set(gb(amount) if amount else '—')
            next_step.set(tr('Model selected. Download and verify its files.') if value.model else tr('Download unavailable until device requirements are met. See the reason above.'))
            sync_buttons()
        elif kind == 'sharing':
            network.set(display_message(value))
        elif kind == 'token':
            append(value)
        elif kind == 'answer':
            messages.append(dict(role='assistant', content=value))
            append('\n')
        elif kind == 'benchmark':
            status.set(tr('Benchmark ' + ('PASSED' if value.passed else 'below sharing target') + ' • Worst TTFT {ttft}s • Slowest {speed} tokens/s',
                          ttft=f'{value.max_ttft_seconds:.2f}', speed=f'{value.min_tokens_per_second:.1f}'))
            next_step.set(tr('Performance passed. Use Local AI or configure sharing.') if value.passed else tr('Use Local AI. Performance is below the sharing target.'))

    def pump():
        while not app.events.empty():
            kind, value = app.events.get_nowait()
            render(kind, value)
        if not app.closed:
            window.after(100, pump)

    def close():
        window.withdraw()

        def cleanup():
            app.close()
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()

        def finish():
            if thread.is_alive():
                window.after(100, finish)
            else:
                window.destroy()
        finish()

    window.protocol('WM_DELETE_WINDOW', close)
    orient()
    if on_ready is None:
        app.submit(app.scan_device)
    else:
        on_ready(window, close, app)
    pump()
    window.mainloop()
