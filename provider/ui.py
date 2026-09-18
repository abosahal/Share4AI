from provider.i18n import tr as translate, display_message as translate_message, TEXT
from .preferences import load_language, save_language
from .readiness import diagnostic_text, gpu_fields, mode_label, selected_gpu, verdict
import re
import os
import threading
import tkinter as tk
from tkinter import ttk
from .app import ProviderApp
from .documents import DocumentError, MAX_FILES, read_document


def launch(state_dir=None, on_ready=None):
    app = ProviderApp(state_dir)
    language = load_language(app.root)

    def tr(source, **values):
        return translate(source, language=language, **values)

    def display_message(source):
        return '\n'.join(translate_message(line, language=language) for line in source.split('\n'))

    paper, lift, ink, mute, line, ok = '#101114', '#1b1e24', '#f4f5f7', '#a7adb8', '#2e333c', '#8fbf9f'
    window = tk.Tk()
    window.title(tr('Share4AI Provider 1.1 — Community-powered AI'))
    window.geometry('1100x780')
    window.minsize(900, 680)
    window.configure(bg=paper)
    style = ttk.Style(window)
    style.theme_use('clam')
    style.configure('.', background=paper, foreground=ink, font=('Segoe UI', 10))
    style.configure('TFrame', background=paper)
    style.configure('Card.TFrame', background=lift)
    style.configure('TLabel', background=paper, foreground=ink)
    style.configure('Mute.TLabel', background=paper, foreground=mute)
    style.configure('Card.TLabel', background=lift, foreground=ink)
    style.configure('CardMute.TLabel', background=lift, foreground=mute)
    style.configure('Ok.TLabel', background=lift, foreground=ok)
    style.configure('TButton', padding=(10, 8), background='#2c313a', foreground=ink)
    style.map('TButton', background=[('active', '#3c4350'), ('disabled', '#1a1d24')],
              foreground=[('disabled', mute)])
    style.configure('Accent.TButton', background=ink, foreground=paper, padding=(10, 9))
    style.map('Accent.TButton', background=[('active', '#ffffff'), ('disabled', '#1a1d24')],
              foreground=[('disabled', mute)])
    style.configure('TNotebook', background=paper, borderwidth=0)
    style.configure('TNotebook.Tab', padding=(16, 8), background=lift, foreground=mute)
    style.map('TNotebook.Tab', background=[('selected', paper)], foreground=[('selected', ink)])
    style.configure('TProgressbar', troughcolor='#1a1d24', background=ink)
    style.configure('TEntry', fieldbackground=lift, foreground=ink)
    style.configure('TSpinbox', fieldbackground=lift, foreground=ink)

    header = ttk.Frame(window)
    header.pack(fill='x', padx=16, pady=(12, 8))
    header.columnconfigure(0, weight=1)
    titles = ttk.Frame(header)
    titles.grid(row=0, column=0, sticky='ew')
    ttk.Label(titles, text='Share4AI', font=('Segoe UI', 16, 'bold')).pack(anchor='w')
    ttk.Label(titles, text=tr('Windows pilot • Local AI first • Authenticated outbound sharing'),
              style='Mute.TLabel').pack(anchor='w')
    tools = ttk.Frame(header)
    tools.grid(row=0, column=1, sticky='e', padx=(12, 0))

    banner = ttk.Frame(window, style='Card.TFrame')
    banner.pack(fill='x', padx=16, pady=(0, 8))
    status = tk.StringVar(value=tr('Ready to scan'))
    next_step = tk.StringVar(value=tr('Scan, download, start, then test performance.'))
    ttk.Label(banner, textvariable=next_step, style='Card.TLabel', font=('Segoe UI', 11, 'bold')).pack(
        fill='x', padx=12, pady=(10, 2))
    status_label = ttk.Label(banner, textvariable=status, style='CardMute.TLabel', wraplength=1000)
    status_label.pack(fill='x', padx=12)
    progress = ttk.Progressbar(banner, maximum=100, mode='determinate')
    progress.pack(fill='x', padx=12, pady=(6, 10))

    def resize_banner(event):
        status_label.configure(wraplength=max(400, event.width - 48))
    banner.bind('<Configure>', resize_banner)

    tabs = ttk.Notebook(window)
    tabs.pack(fill='both', expand=True, padx=16, pady=(0, 12))
    setup, chat, settings = ttk.Frame(tabs), ttk.Frame(tabs), ttk.Frame(tabs)
    for frame, name in ((setup, tr('Device & Setup')), (chat, tr('Local AI')), (settings, tr('Settings'))):
        tabs.add(frame, text=name)

    device = tk.StringVar(value=tr('Scan your device to find a suitable model.'))
    recommendation = tk.StringVar(value=tr('No recommendation yet'))
    readiness = tk.StringVar(value=tr('Ready to scan'))
    mode = tk.StringVar(value='—')
    notes = tk.StringVar(value='')
    network = tk.StringVar(value=tr('OFFLINE'))

    actions = ttk.Frame(setup)
    actions.pack(side='bottom', fill='x', padx=8, pady=8)
    content = ttk.Frame(setup)
    content.pack(fill='both', expand=True, padx=8, pady=(8, 0))

    hero = ttk.Frame(content, style='Card.TFrame')
    hero.pack(fill='x', pady=(0, 8))
    ttk.Label(hero, textvariable=device, style='Card.TLabel', font=('Segoe UI', 14, 'bold')).pack(
        anchor='w', padx=12, pady=(10, 0))
    ttk.Label(hero, textvariable=readiness, style='Ok.TLabel').pack(anchor='w', padx=12, pady=2)
    ttk.Label(hero, textvariable=mode, style='CardMute.TLabel').pack(anchor='w', padx=12, pady=(0, 10))

    resource_rows = ttk.Frame(content)
    resource_rows.pack(fill='x')
    numbers, number_labels = {}, []
    metric_keys = (
        'Graphics card', 'GPU memory', 'Free GPU memory', 'GPU usage now', 'GPU temperature',
        'Processor', 'Installed memory', 'Free memory', 'Free disk space (not required space)',
        'Free memory required by this version', 'Disk space required including reserve',
    )
    for index, key in enumerate(metric_keys):
        cell = ttk.Frame(resource_rows, style='Card.TFrame')
        row, column = divmod(index, 2)
        cell.grid(row=row, column=column, sticky='nsew', padx=3, pady=3)
        ttk.Label(cell, text=tr(key), style='CardMute.TLabel').pack(anchor='w', padx=10, pady=(8, 0))
        numbers[key] = tk.StringVar(value='—')
        label = ttk.Label(cell, textvariable=numbers[key], style='Card.TLabel', font=('Segoe UI', 12, 'bold'))
        label.pack(anchor='w', padx=10, pady=(0, 8))
        number_labels.append(label)
    resource_rows.columnconfigure(0, weight=1)
    resource_rows.columnconfigure(1, weight=1)

    model_card = ttk.Frame(content, style='Card.TFrame')
    model_card.pack(fill='x', pady=8)
    ttk.Label(model_card, textvariable=recommendation, style='Card.TLabel', wraplength=820).pack(
        anchor='w', padx=12, pady=(10, 2))
    notes_label = ttk.Label(model_card, textvariable=notes, style='CardMute.TLabel', wraplength=820)
    notes_label.pack(anchor='w', padx=12, pady=(0, 10))
    ttk.Label(content, text=tr('Qwen3.8 27B: 15.3 GB plus runtime'), style='Mute.TLabel').pack(anchor='w')
    ttk.Label(content, textvariable=network, style='Mute.TLabel').pack(anchor='w', pady=(0, 4))

    buttons = []

    def provision_if_ready():
        if not app.recommendation or not app.recommendation.model:
            status.set(tr('Download unavailable until device requirements are met. See the reason above.'))
            return
        app.submit(app.provision)

    step_row = ttk.Frame(actions)
    step_row.pack(fill='x')
    step_defs = [
        (tr('1. Scan'), lambda: app.submit(app.scan_device), 'Accent.TButton'),
        (tr('2. Download & Verify'), provision_if_ready, 'TButton'),
        (tr('3. Start Local AI'), lambda: app.submit(app.start_local), 'Accent.TButton'),
        (tr('4. Benchmark'), lambda: app.submit(app.run_benchmark), 'TButton'),
    ]
    for index, (label, command, kind) in enumerate(step_defs):
        button = ttk.Button(step_row, text=label, style=kind, command=command)
        button.grid(row=index // 2, column=index % 2, sticky='ew', padx=3, pady=3)
        buttons.append(button)
    step_row.columnconfigure(0, weight=1)
    step_row.columnconfigure(1, weight=1)
    buttons[1].configure(state='disabled')

    extra = ttk.Frame(actions)
    extra.pack(fill='x', pady=(4, 0))

    def copy_report():
        try:
            window.clipboard_clear()
            window.clipboard_append(diagnostic_text(app.hardware, app.recommendation))
            status.set(tr('Device report copied'))
        except tk.TclError:
            status.set(tr('Could not copy device report'))

    def start_share():
        if not app.trial_client and not os.environ.get('SHARE4AI_PROVIDER_TOKEN'):
            status.set(tr('Sharing activation is not available in this trial. You can use Local AI.'))
            return
        app.submit(app.start_sharing)

    ttk.Button(extra, text=tr('Copy device report'), command=copy_report).pack(side='left', padx=3)
    share_button = ttk.Button(extra, text=tr('Start Sharing'), command=start_share)
    share_button.pack(side='left', padx=3)
    buttons.append(share_button)
    trial_button = ttk.Button(extra, text=tr('Try customer chat on this computer'),
                              command=lambda: app.submit(app.start_browser_trial))
    trial_button.pack(side='left', padx=3)
    buttons.append(trial_button)
    ttk.Button(extra, text=tr('Stop Sharing'),
               command=lambda: threading.Thread(target=app.stop_sharing, daemon=True).start()).pack(side='left', padx=3)

    chat.rowconfigure(0, weight=1)
    chat.columnconfigure(0, weight=1)
    transcript = tk.Text(chat, wrap='word', font=('Segoe UI', 12), state='disabled',
                         bg=lift, fg=ink, insertbackground=ink, relief='flat', padx=12, pady=12)
    transcript.grid(row=0, column=0, sticky='nsew', padx=8, pady=(8, 4))
    composer = ttk.Frame(chat)
    composer.grid(row=1, column=0, sticky='ew', padx=8, pady=(0, 8))
    composer.columnconfigure(0, weight=1)
    composer.columnconfigure(1, weight=1)
    entry = tk.Text(composer, height=4, wrap='word', font=('Segoe UI', 12),
                    bg='#0c0d10', fg=ink, insertbackground=ink, relief='solid', bd=1,
                    highlightthickness=1, highlightbackground=line, highlightcolor=ink, padx=10, pady=8)
    entry.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 6))
    files = ttk.Frame(composer)
    files.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 6))
    messages, attachments = [], []

    def show_attachments():
        for child in files.winfo_children():
            child.destroy()
        for index, doc in enumerate(attachments):
            ttk.Label(files, text=tr('Attached') + ': ' + doc['name'], style='Mute.TLabel').grid(
                row=index // 2, column=(index % 2) * 2, sticky='w', padx=(0, 6))
            ttk.Button(files, text='×', width=3, command=lambda i=index: remove_attachment(i)).grid(
                row=index // 2, column=(index % 2) * 2 + 1, sticky='w')

    def remove_attachment(index):
        if 0 <= index < len(attachments):
            attachments.pop(index)
            show_attachments()

    def attach():
        from tkinter import filedialog
        selected = filedialog.askopenfilenames(
            parent=window, title=tr('Attach file'),
            filetypes=((tr('Documents'), '*.txt;*.md;*.pdf;*.docx;*.json;*.csv;*.log'),
                       (tr('All files'), '*.*')))
        for path in selected:
            if len(attachments) >= MAX_FILES:
                status.set(tr('Too many attached files'))
                break
            try:
                attachments.append(read_document(path))
            except DocumentError as error:
                status.set(display_message(str(error)))
                return
            except OSError:
                status.set(tr('Could not read this file'))
                return
        show_attachments()

    def append(text):
        transcript.configure(state='normal')
        transcript.insert('end', text, 'direction')
        transcript.see('end')
        transcript.configure(state='disabled')

    def send():
        content = entry.get('1.0', 'end').strip()
        if not content and not attachments:
            return
        entry.delete('1.0', 'end')
        shown, payload = content, content
        for doc in attachments:
            shown = (shown + '\n' if shown else '') + tr('Attached') + ': ' + doc['name']
            payload = (payload + '\n' if payload else '') + f"Attached file {doc['name']}:\n{doc['text']}"
        attachments.clear()
        show_attachments()
        messages.append(dict(role='user', content=payload))
        append('\n' + tr('You:') + ' ' + shown + '\n' + tr('AI:') + ' ')
        snapshot = [dict(item) for item in messages]
        app.submit(lambda: app.chat(snapshot))

    sendbutton = ttk.Button(composer, text=tr('Send'), style='Accent.TButton', command=send)
    sendbutton.grid(row=2, column=0, sticky='ew', padx=(0, 4), pady=2)
    buttons.append(sendbutton)
    attachbutton = ttk.Button(composer, text=tr('Attach file'), command=attach)
    attachbutton.grid(row=2, column=1, sticky='ew', pady=2)
    buttons.append(attachbutton)

    def copy_chat():
        text = transcript.get('1.0', 'end').strip()
        if not text:
            status.set(tr('Nothing to copy'))
            return
        try:
            window.clipboard_clear()
            window.clipboard_append(text)
            status.set(tr('Conversation copied'))
        except tk.TclError:
            status.set(tr('Could not copy conversation'))

    ttk.Button(composer, text=tr('Copy conversation'), command=copy_chat).grid(
        row=3, column=0, sticky='ew', padx=(0, 4), pady=2)

    def clear():
        messages.clear()
        attachments.clear()
        show_attachments()
        transcript.configure(state='normal')
        transcript.delete('1.0', 'end')
        transcript.configure(state='disabled')

    ttk.Button(composer, text=tr('Clear conversation'), command=clear).grid(
        row=3, column=1, sticky='ew', pady=2)
    ttk.Label(chat, text=tr("Uses this computer's clock and live web lookup for current facts."),
              style='Mute.TLabel').grid(row=2, column=0, sticky='ew', padx=8, pady=(0, 8))

    address = tk.StringVar(value=app.settings['control_plane'])
    maximum = tk.IntVar(value=app.settings['maximum'])
    advanced = ttk.Frame(settings)

    def toggle_advanced():
        if advanced.winfo_manager():
            advanced.pack_forget()
        else:
            advanced.pack(fill='x', pady=8, padx=8)

    ttk.Button(settings, text=tr('Advanced settings (internal testing)'), command=toggle_advanced).pack(
        anchor='w', padx=8, pady=8)
    ttk.Label(advanced, text=tr('Control Plane address')).pack(anchor='w')
    ttk.Entry(advanced, textvariable=address, width=65).pack(anchor='w', pady=6)
    ttk.Label(settings, text=tr('Max GPU Usage (%)'), font=('Segoe UI', 12, 'bold')).pack(anchor='w', padx=8, pady=(8, 0))
    ttk.Spinbox(settings, from_=0, to=100, textvariable=maximum, width=8).pack(anchor='w', padx=8, pady=6)
    ttk.Label(settings, text=tr('Sharing pauses when resource usage or temperature is high. This setting does not impose a hard GPU limit. Public sharing activation is coming later.'),
              wraplength=760, style='Mute.TLabel').pack(anchor='w', padx=8, pady=8)

    def save():
        try:
            value = maximum.get()
        except tk.TclError:
            status.set(tr('Enter a whole number from 0 to 100'))
            return
        app.submit(lambda: app.save_settings(address.get().strip(), value))

    savebutton = ttk.Button(settings, text=tr('Save Settings'), command=save)
    savebutton.pack(anchor='w', padx=8)
    buttons.append(savebutton)

    ttk.Button(tools, text=tr('Cancel / Stop AI'),
               command=lambda: threading.Thread(target=app.stop_all, daemon=True).start()).pack(side='right')

    latest, working = {}, False

    def sync_buttons():
        for b in buttons:
            b.configure(state='disabled' if working else 'normal')
        if working or not app.recommendation or not app.recommendation.model:
            buttons[1].configure(state='disabled')

    def orient():
        rtl = language == 'ar'
        justify = 'right' if rtl else 'left'
        anchor = 'e' if rtl else 'w'

        def visit(widget):
            if isinstance(widget, ttk.Label):
                widget.configure(anchor=anchor, justify=justify)
            for child in widget.winfo_children():
                visit(child)
        visit(window)
        for label in number_labels:
            label.configure(anchor='w', justify='left')
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
        for tab, key in ((setup, 'Device & Setup'), (chat, 'Local AI'), (settings, 'Settings')):
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
    entry.bind('<Control-Return>', lambda event: send())

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
            progress.configure(value=min(100, int(match[2])) if match else (100 if value == 'Installed and SHA256 verified' else progress['value']))
            if value == 'Installed and SHA256 verified':
                next_step.set(tr('Download complete. Start Local AI, then test performance.'))
                progress.configure(value=100)
                tabs.select(setup)
            elif value.startswith('Local AI ready'):
                next_step.set(tr('Local AI is ready. Test performance before sharing.'))
                tabs.select(chat)
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
