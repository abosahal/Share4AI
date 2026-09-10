import threading
import tkinter as tk
from tkinter import ttk
from .app import ProviderApp


def launch(state_dir=None):
    app = ProviderApp(state_dir)
    window = tk.Tk()
    window.title('Share4AI Provider 1.1 — Community-powered AI')
    window.geometry('940x740')
    window.minsize(780, 620)
    style = ttk.Style(window)
    style.theme_use('clam')
    style.configure('TButton', padding=8)
    style.configure('TLabel', padding=4)
    ttk.Label(window, text='Share4AI  /  Community-powered AI', font=('Segoe UI', 19, 'bold')).pack(anchor='w', padx=18, pady=(14, 2))
    ttk.Label(window, text='Windows pilot • Local AI first • Authenticated outbound sharing').pack(anchor='w', padx=18)
    tabs = ttk.Notebook(window)
    tabs.pack(fill='both', expand=True, padx=18, pady=12)
    setup, chat, settings = (ttk.Frame(tabs, padding=14) for _ in range(3))
    for frame, name in [(setup, 'Device & Setup'), (chat, 'Local AI'), (settings, 'Settings')]:
        tabs.add(frame, text=name)
    device = tk.StringVar(value='Scan your device to find a suitable model.')
    recommendation = tk.StringVar(value='No recommendation yet')
    status = tk.StringVar(value='Ready to scan')
    network = tk.StringVar(value='OFFLINE')
    ttk.Label(setup, textvariable=device, wraplength=810).pack(anchor='w')
    ttk.Label(setup, textvariable=recommendation, wraplength=810).pack(anchor='w', pady=10)
    buttons = []
    row = ttk.Frame(setup); row.pack(anchor='w', pady=10)
    for label, action in [('1. Scan', app.scan_device), ('2. Download & Verify', app.provision),
                          ('3. Start Local AI', app.start_local), ('4. Benchmark', app.run_benchmark)]:
        button = ttk.Button(row, text=label, command=lambda a=action: app.submit(a))
        button.pack(side='left', padx=3); buttons.append(button)
    ttk.Label(setup, text='Downloads: Qwen 4B ≈ 2.7 GB / 9B ≈ 5.7 GB plus runtime.\nModels use published SHA256 checks. Retry restarts an interrupted download.', wraplength=800).pack(anchor='w')
    ttk.Separator(setup).pack(fill='x', pady=18)
    ttk.Label(setup, text='Sharing connection', font=('Segoe UI', 13, 'bold')).pack(anchor='w')
    ttk.Label(setup, textvariable=network).pack(anchor='w')
    ttk.Label(setup, text='Sharing requires a passing benchmark and a provider credential. Stop Sharing cancels the current network job. Local AI stops sharing first.', wraplength=800).pack(anchor='w')
    share = ttk.Frame(setup); share.pack(anchor='w', pady=8)
    button = ttk.Button(share, text='Start Sharing', command=lambda: app.submit(app.start_sharing))
    button.pack(side='left', padx=3); buttons.append(button)
    ttk.Button(share, text='Stop Sharing', command=lambda: threading.Thread(target=app.stop_sharing, daemon=True).start()).pack(side='left', padx=3)
    transcript = tk.Text(chat, wrap='word', font=('Segoe UI', 11), state='disabled')
    transcript.pack(fill='both', expand=True)
    entry = tk.Text(chat, height=3, wrap='word', font=('Segoe UI', 11)); entry.pack(fill='x', pady=8)
    messages = []
    def append(text):
        transcript.configure(state='normal'); transcript.insert('end', text); transcript.see('end'); transcript.configure(state='disabled')
    def send():
        content = entry.get('1.0', 'end').strip()
        if not content:
            return
        entry.delete('1.0', 'end')
        messages.append(dict(role='user', content=content))
        append('\nYou: ' + content + '\nAI: ')
        snapshot = [dict(m) for m in messages]
        app.submit(lambda: app.chat(snapshot))
    chatrow = ttk.Frame(chat); chatrow.pack(fill='x')
    sendbutton = ttk.Button(chatrow, text='Send', command=send); sendbutton.pack(side='left'); buttons.append(sendbutton)
    def clear():
        messages.clear(); transcript.configure(state='normal'); transcript.delete('1.0', 'end'); transcript.configure(state='disabled')
    clearbutton = ttk.Button(chatrow, text='Clear conversation', command=clear); clearbutton.pack(side='left', padx=6); buttons.append(clearbutton)
    ttk.Label(chat, text='Local conversation stays in memory and is not saved to history.').pack(anchor='w')
    address = tk.StringVar(value=app.settings['control_plane'])
    maximum = tk.IntVar(value=app.settings['maximum'])
    ttk.Label(settings, text='Control Plane address').pack(anchor='w')
    ttk.Entry(settings, textvariable=address, width=65).pack(anchor='w', pady=6)
    ttk.Label(settings, text='Max GPU Usage (%)').pack(anchor='w', pady=(18, 0))
    ttk.Spinbox(settings, from_=0, to=100, textvariable=maximum, width=8).pack(anchor='w')
    ttk.Label(settings, text='Operational sharing threshold, not a hard GPU utilization cap.\nHigh usage, heat or missing telemetry prevents availability.\nRemote registration requires HTTPS and SHARE4AI_PROVIDER_TOKEN.', wraplength=800).pack(anchor='w', pady=12)
    def save():
        try:
            value = maximum.get()
        except tk.TclError:
            status.set('Enter a whole number from 0 to 100'); return
        url = address.get().strip()
        app.submit(lambda: app.save_settings(url, value))
    savebutton = ttk.Button(settings, text='Save Settings', command=save); savebutton.pack(anchor='w'); buttons.append(savebutton)
    bottom = ttk.Frame(window); bottom.pack(fill='x', padx=18, pady=(0, 14))
    ttk.Label(bottom, textvariable=status, wraplength=650).pack(side='left')
    ttk.Button(bottom, text='Cancel / Stop AI', command=lambda: threading.Thread(target=app.stop_all, daemon=True).start()).pack(side='right')
    def pump():
        while not app.events.empty():
            kind, value = app.events.get_nowait()
            if kind == 'status': status.set(value)
            elif kind == 'working':
                for b in buttons: b.configure(state='disabled' if value else 'normal')
            elif kind == 'hardware':
                gpu = ', '.join(g.name for g in value.gpus) or 'No supported NVIDIA GPU'
                device.set(f'{gpu}\nRAM {value.ram_mb / 1024:.1f} GB • Available {value.available_ram_mb / 1024:.1f} GB • Free disk {value.disk_free_mb / 1024:.1f} GB')
            elif kind == 'recommendation':
                recommendation.set((value.model['id'] if value.model else 'No suitable model') + '\n' + value.reason)
            elif kind == 'sharing': network.set(value)
            elif kind == 'token': append(value)
            elif kind == 'answer': messages.append(dict(role='assistant', content=value)); append('\n')
            elif kind == 'benchmark':
                status.set(f'Benchmark {"PASSED" if value.passed else "below sharing target"} • Worst TTFT {value.max_ttft_seconds:.2f}s • Slowest {value.min_tokens_per_second:.1f} tokens/s')
        if not app.closed:
            window.after(100, pump)
    def close():
        window.withdraw()
        def cleanup():
            app.close()
        thread = threading.Thread(target=cleanup, daemon=True); thread.start()
        def finish():
            if thread.is_alive(): window.after(100, finish)
            else: window.destroy()
        finish()
    window.protocol('WM_DELETE_WINDOW', close)
    app.submit(app.scan_device)
    pump()
    window.mainloop()
