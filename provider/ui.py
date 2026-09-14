from provider.i18n import tr as translate, display_message as translate_message, TEXT
from .preferences import load_language, save_language
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
    window.geometry('1120x820')
    window.minsize(980, 720)
    window.configure(bg='#111318')
    style = ttk.Style(window)
    style.theme_use('clam')
    ink, paper, mute, line, lift = '#ececf1', '#111318', '#9aa0ab', '#2a2e36', '#1c2028'
    style.configure('.', background=paper, foreground=ink)
    style.configure('TFrame', background=paper)
    style.configure('Card.TFrame', background=lift)
    style.configure('TLabel', background=paper, foreground=ink, padding=4)
    style.configure('Mute.TLabel', background=paper, foreground=mute)
    style.configure('Banner.TLabel', background=lift, foreground=ink, padding=8)
    style.configure('TButton', padding=10, background='#2a2e36', foreground=ink)
    style.map('TButton', background=[('active', '#3a404c'), ('disabled', '#1a1d24')],
              foreground=[('disabled', mute)])
    style.configure('Accent.TButton', background=ink, foreground=paper)
    style.map('Accent.TButton', background=[('active', '#ffffff'), ('disabled', '#1a1d24')])
    style.configure('TNotebook', background=paper, borderwidth=0)
    style.configure('TNotebook.Tab', padding=(18, 10), background=lift, foreground=mute)
    style.map('TNotebook.Tab', background=[('selected', paper)], foreground=[('selected', ink)])
    style.configure('TProgressbar', troughcolor=lift, background=ink)
    style.configure('TSeparator', background=line)
    style.configure('TEntry', fieldbackground=lift, foreground=ink)
    style.configure('TSpinbox', fieldbackground=lift, foreground=ink)

    header = ttk.Frame(window)
    header.pack(fill='x', padx=22, pady=(16, 8))
    titles = ttk.Frame(header)
    titles.pack(side='left', fill='x', expand=True)
    ttk.Label(titles, text=tr('Share4AI  /  Community-powered AI'), font=('Segoe UI', 20, 'bold')).pack(anchor='w')
    ttk.Label(titles, text=tr('Windows pilot • Local AI first • Authenticated outbound sharing'),
              style='Mute.TLabel').pack(anchor='w')
    tools = ttk.Frame(header)
    tools.pack(side='right')

    banner = ttk.Frame(window, style='Card.TFrame')
    banner.pack(fill='x', padx=22, pady=(0, 8))
    status = tk.StringVar(value=tr('Ready to scan'))
    next_step = tk.StringVar(value=tr('Scan, download, start, then test performance.'))
    ttk.Label(banner, textvariable=next_step, style='Banner.TLabel', font=('Segoe UI', 11, 'bold')).pack(fill='x', padx=8, pady=(8, 0))
    status_label = ttk.Label(banner, textvariable=status, style='Banner.TLabel', wraplength=1040)
    status_label.pack(fill='x', padx=8, pady=(0, 4))
    progress = ttk.Progressbar(banner, maximum=100, mode='determinate')
    progress.pack(fill='x', padx=12, pady=(0, 12))

    def resize_banner(event):
        status_label.configure(wraplength=max(360, event.width - 48))
    window.bind('<Configure>', resize_banner)

    tabs = ttk.Notebook(window)
    tabs.pack(fill='both', expand=True, padx=22, pady=(0, 8))
    setup_tab, chat, settings = (ttk.Frame(tabs, padding=8) for _ in range(3))
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
        for widget in setup.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.configure(wraplength=max(280, event.width - 24))
    canvas.bind('<Configure>', resize_setup)
    for frame, name in [(setup_tab, tr('Device & Setup')), (chat, tr('Local AI')), (settings, tr('Settings'))]:
        tabs.add(frame, text=name)

    device = tk.StringVar(value=tr('Scan your device to find a suitable model.'))
    recommendation = tk.StringVar(value=tr('No recommendation yet'))
    network = tk.StringVar(value=tr('OFFLINE'))
    ttk.Label(setup, textvariable=device, font=('Segoe UI', 13, 'bold')).pack(anchor='w', pady=(4, 8))
    ttk.Label(setup, text=tr('Sizes in gigabytes'), style='Mute.TLabel').pack(anchor='w')
    resource_rows = ttk.Frame(setup)
    resource_rows.pack(fill='x', pady=8)
    numbers = {}
    number_labels = []
    for index, key in enumerate(('Installed memory', 'Free memory', 'Free disk space (not required space)',
                                 'Free memory required by this version', 'Disk space required including reserve')):
        ttk.Label(resource_rows, text=tr(key), style='Mute.TLabel').grid(row=index, column=1, sticky='ew', padx=8, pady=3)
        numbers[key] = tk.StringVar(value='—')
        label = ttk.Label(resource_rows, textvariable=numbers[key], width=14, anchor='w', font=('Segoe UI', 12, 'bold'))
        label.grid(row=index, column=0, sticky='w', padx=8, pady=3)
        number_labels.append(label)
    resource_rows.columnconfigure(1, weight=1)
    ttk.Label(setup, textvariable=recommendation, wraplength=820).pack(anchor='w', pady=10)

    buttons = []
    row = ttk.Frame(setup)
    row.pack(fill='x', pady=10)
    def provision_if_ready():
        if not app.recommendation or not app.recommendation.model:
            status.set(tr('Download unavailable until device requirements are met. See the reason above.'))
            return
        app.submit(app.provision)
    actions = [(tr('1. Scan'), app.scan_device), (tr('2. Download & Verify'), app.provision),
               (tr('3. Start Local AI'), app.start_local), (tr('4. Benchmark'), app.run_benchmark)]
    for index, (label, action) in enumerate(actions):
        kind = 'Accent.TButton' if index == 0 else 'TButton'
        button = ttk.Button(row, text=label, style=kind, command=lambda a=action: app.submit(a))
        button.pack(fill='x', pady=3)
        buttons.append(button)
    buttons[1].configure(command=provision_if_ready, state='disabled')
    ttk.Label(setup, text=tr('Download sizes'), style='Mute.TLabel').pack(anchor='w', pady=(12, 0))
    sizes_label = ttk.Label(setup, text='Qwen3.8 27B: 15.3 GB', anchor='w', justify='left')
    sizes_label.pack(anchor='w')
    number_labels.append(sizes_label)
    ttk.Label(setup, text=tr('The app also downloads its runtime and verifies the files automatically.'),
              wraplength=800, style='Mute.TLabel').pack(anchor='w')
    ttk.Separator(setup).pack(fill='x', pady=16)
    ttk.Label(setup, text=tr('Sharing connection'), font=('Segoe UI', 12, 'bold')).pack(anchor='w')
    ttk.Label(setup, textvariable=network, style='Mute.TLabel').pack(anchor='w')
    ttk.Label(setup, text=tr('Sharing requires a passing benchmark and a provider credential. Stop Sharing cancels the current network job. Local AI stops sharing first.'),
              wraplength=800, style='Mute.TLabel').pack(anchor='w')
    share = ttk.Frame(setup)
    share.pack(anchor='w', pady=8)
    def start_share():
        if not os.environ.get('SHARE4AI_PROVIDER_TOKEN'):
            status.set(tr('Sharing activation is not available in this trial. You can use Local AI.'))
            return
        app.submit(app.start_sharing)
    button = ttk.Button(share, text=tr('Start Sharing'), command=start_share)
    button.pack(side='left', padx=3)
    buttons.append(button)
    ttk.Button(share, text=tr('Stop Sharing'),
               command=lambda: threading.Thread(target=app.stop_sharing, daemon=True).start()).pack(side='left', padx=3)

    transcript = tk.Text(chat, wrap='word', font=('Segoe UI', 12), state='disabled',
                         bg=lift, fg=ink, insertbackground=ink, relief='flat', padx=12, pady=12)
    transcript.pack(fill='both', expand=True)
    entry = tk.Text(chat, height=3, wrap='word', font=('Segoe UI', 12),
                    bg=lift, fg=ink, insertbackground=ink, relief='flat', padx=10, pady=8)
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
    ttk.Label(settings, text=tr('Max GPU Usage (%)')).pack(anchor='w', pady=(18, 0))
    ttk.Spinbox(settings, from_=0, to=100, textvariable=maximum, width=8).pack(anchor='w')
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
        for widget in resource_rows.winfo_children():
            is_number = widget in number_labels
            widget.grid_configure(column=(0 if is_number else 1) if rtl else (1 if is_number else 0))
        resource_rows.columnconfigure(0, weight=0 if rtl else 1)
        resource_rows.columnconfigure(1, weight=1 if rtl else 0)
        selected = tabs.select()
        ordered = (settings, chat, setup_tab) if rtl else (setup_tab, chat, settings)
        for index, tab in enumerate(ordered):
            tabs.insert(index, tab)
        tabs.select(selected)
        scrollbar.pack_configure(side='left' if rtl else 'right')
        for frame in (share, chatrow):
            for widget in frame.winfo_children():
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
        for variable in (device, recommendation, status, network, next_step):
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
            gpu = ', '.join(g.name for g in value.gpus) or tr('No supported NVIDIA GPU')
            device.set(gpu)
            for key, amount in (('Installed memory', value.ram_mb), ('Free memory', value.available_ram_mb),
                                ('Free disk space (not required space)', value.disk_free_mb)):
                numbers[key].set(gb(amount))
        elif kind == 'recommendation':
            recommendation.set((value.model['id'] if value.model else tr('No suitable model')) + '\n' + display_message(value.reason))
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
