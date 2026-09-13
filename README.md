# Share4AI — دليل المشروع | Project guide

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

العربية هي لغة الواجهة الافتراضية، مع زر English للتبديل الفوري وحفظ الاختيار. تُحاذى عناصر العربية إلى اليمين ويُعكس ترتيب أزرار الإعداد؛ تبقى الوثائق وأدوات الطرفية ثنائية اللغة. تظهر نسبة التنزيل وإرشادات الخطوة التالية، ويمكن تمرير صفحة الإعداد على الشاشات الصغيرة. تبقى أسماء الأوامر وحقول البروتوكول ومحتويات المحادثة كما هي. يتطلب التحقق البصري من اتصال الحروف العربية واتجاهها ومؤشر الكتابة جهاز Windows يعمل عليه Tcl/Tk؛ المحاذاة وحدها لا تثبت دعم RTL الكامل. اتبع [دليل التجربة](WINDOWS_TRIAL.md).

**ذكاء اصطناعي مدعوم من المجتمع — Community-powered AI** — نسخة ألفا من تطبيق المزود v1.1 على Windows.

توثيق المشروع وبداية Sprint 1. يعمل التطبيق مع llama.cpp دون LM Studio. هذه نسخة تطوير محلية وليست خدمة عامة جاهزة.

### البدء السريع — Windows x64

1. نزّل ملف **Share4AI-Setup-1.1.0-windows-x64.exe** المرفق بالنسخة التجريبية وافتحه ثم اضغط **تثبيت**. يتضمن متطلبات التشغيل؛ لا تحتاج Python أو الطرفية.
2. افتح **Share4AI** من اختصار سطح المكتب أو قائمة ابدأ. واجهة التثبيت والتطبيق تبدأ بالعربية.
3. اتبع: **فحص الجهاز → التنزيل والتحقق → تشغيل الذكاء المحلي → اختبار الأداء**.
4. استخدم تبويب **Local AI — الذكاء المحلي**. تنزيل Qwen يبلغ نحو 2.7GB لحجم 4B أو 5.7GB لحجم 9B؛ يختار التطبيق بحسب الذاكرة المتاحة. تضيف حزم تشغيل CUDA نحو 646MB. أغلق التطبيقات الأخرى التي تستهلك ذاكرة كبيرة أولًا.
5. زر **Cancel / Stop AI — إلغاء / إيقاف الذكاء المحلي** يلغي العمل ويوقف محرك التشغيل الذي يديره التطبيق. إعادة المحاولة تبدأ التنزيل المقطوع من جديد؛ استئناف التنزيل من آخر بايت لم يُنفذ بعد.

التشغيل على CPU مخصص لتجارب الذكاء المحلي. أهلية مشاركة NVIDIA تتطلب قياسات حية واجتياز اختبار الأداء. يعرض التطبيق تفسيرًا عند عدم دعم العتاد أو نقص الذاكرة، ولا يُظهر نجاح إعداد غير حقيقي.

### ما يعمل في هذه المرحلة

- اكتشاف CPU وRAM والقرص في Windows، وبطاقة NVIDIA وVRAM واستخدامها وحرارتها.
- كتالوج مثبت لـQwen3.5 بحجمي 4B و9B وتكميم Q4_K_M، وحزم llama.cpp b10868 للـCPU وCUDA 12.4، بما فيها مكتبات CUDA DLL.
- تنزيل عبر HTTPS، وفحص الحجم وSHA256، واستخراج مرحلي آمن، وإلغاء وإعادة محاولة آمنان، ودعم اختياري للتحقق من Authenticode وفق هوية ناشر مثبتة.
- RuntimeAdapter ومحرك llama-server محلي يديره التطبيق، مع مفتاح API خاص بكل عملية، ومحادثة محلية متدفقة واختبار أداء بعد الإحماء يستخدم أعداد tokens الفعلية.
- واجهة للإعداد والمحادثة والإعدادات، وحد موارد يحدده صاحب الجهاز، وهوية عقدة ثابتة، وتسجيل وheartbeat وإعادة تسجيل عبر اتصال صادر، وإيقاف المشاركة.

### حدود نسخة ألفا

**يدعم Start Sharing الآن مهام موثقة عبر اتصال صادر في تجربة محلية.** يتطلب نموذجًا يعمل، واختبار أداء ناجحًا، وقياسات تؤهل الجهاز، وبيانات اعتماد للمزود. يلغي Stop Sharing العمل الشبكي الحالي؛ واستخدام Local AI يوقف المشاركة أولًا. اتبع [PILOT_JOBS.md](PILOT_JOBS.md) لتشغيل خادم التحكم وعميل التجربة المتدفق. Max GPU Usage عتبة لقبول العمل، **وليس سقفًا صارمًا لنسبة استخدام البطاقة**. ما زال اكتشاف الألعاب الكامل، وإيقاف العمل تلقائيًا عند ضغط الموارد، وخادم التحكم الدائم للإنتاج، والتوجيه متعدد العقد، والمثبّت الموقّع ضمن خطة العمل.

تنشر الحزم المثبتة بصمات SHA256؛ لم تُرفق توقيعات منفصلة في الكتالوج. التحقق من البصمة منفذ؛ لا ندعي التحقق من توقيع لم يُنشر. توفر Unsloth نسخ GGUF المكممة من نماذج Qwen الأصلية؛ وليست مستودع GGUF رسميًا تابعًا لـQwen. احتفظ بإشعارات المصادر الأصلية عند التوزيع.

يبقى محتوى المحادثة المحلية في ذاكرة العملية. لا استدلال سحابي ولا API مدفوع إلزامي. لا تستخدم نسخة ألفا هذه لمهام مجتمعية حساسة. راجع SECURITY_BASELINE.md لفهم حدود الخصوصية على جهاز يملكه المزود.

### اختبار بروتوكول خادم التحكم المحلي

لتنفيذ المهام، استخدم `py -3 -m tools.pilot_control_plane` و`py -3 -m tools.pilot_chat` مع بيانات اعتماد مختلفة للمزود والعميل كما يوضح PILOT_JOBS.md. يظل `tools/dev_control_plane.py` أداة اختبار للتسجيل فقط، ولا يرسل مهام. يستمع الخادمان على الجهاز المحلي فقط، ولا يملكان تخزينًا دائمًا. أي نقطة اتصال بعيدة تتطلب HTTPS و`SHARE4AI_PROVIDER_TOKEN`؛ أما التسجيل الإنتاجي وإدارة دورة حياة مفاتيح كل مزود فما زالا عملًا لاحقًا.

### التطوير والتحقق

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m provider --scan --state-dir .state
py -3 -m compileall -q provider tools tests
```

تُحفظ بيانات التطبيق افتراضيًا في `%LOCALAPPDATA%\Share4AI`؛ استخدم `--state-dir` لاختبار معزول. لا تحتوي الإعدادات على رمز اعتماد. لا تُدرج النماذج وأرشيفات محرك التشغيل في إيداعات Git. أداة `tools/pin_catalog.py` للمشرفين فقط، ويجب مراجعتها قبل تحديث الكتالوج؛ لا يتبع التطبيق أحدث إصدار تلقائيًا.

### وثائق المشروع

- [PROJECT_BASELINE.md](PROJECT_BASELINE.md): القرارات المعتمدة ومصادرها والنطاق والقرارات المفتوحة.
- [ARCHITECTURE.md](ARCHITECTURE.md): المكونات والحالات والبروتوكول.
- [SECURITY_BASELINE.md](SECURITY_BASELINE.md): حدود الثقة وشروط الإطلاق.
- [ROADMAP.md](ROADMAP.md): مراحل التنفيذ ومعايير القبول.
- [SPRINT_01.md](SPRINT_01.md): التقدم الحالي وحدود التحقق.

### المراجع الأصلية

- [إصدار llama.cpp المثبت](https://github.com/ggml-org/llama.cpp/releases/tag/b10868)
- [واجهة خادم llama.cpp](https://github.com/ggml-org/llama.cpp/blob/b10868/tools/server/README.md)
- [Qwen3.5 4B بصيغة GGUF](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF)
- [Qwen3.5 9B بصيغة GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)

لم تكن أرشيفات ZIP للنموذج الأولي الأصلي موجودة في المستودع. تفصل الوثيقة المرجعية بين النجاح السابق الذي أبلغ عنه المستخدم واختبارات هذا التنفيذ الجديد.

---

<a id="en"></a>

## English

The UI defaults to Arabic, with an English button for live switching and a saved preference. Arabic controls align right and setup buttons reverse order; documentation and CLI tools remain bilingual. Download percentages and next-step guidance are visible, with a scrollable setup page for smaller screens. Command names, protocol fields and conversation content remain unchanged. Arabic shaping, direction and caret behavior require visual validation on Windows with working Tcl/Tk; alignment alone does not establish full RTL support. Follow the [trial guide](WINDOWS_TRIAL.md).

**Community-powered AI** — Windows Provider App v1.1 alpha.

Project documentation and the start of Sprint 1. The app runs with llama.cpp without LM Studio. This is a local development build, not a ready public service.

### Quick start — Windows x64

1. Download **Share4AI-Setup-1.1.0-windows-x64.exe** attached to the trial build, open it and select **Install**. Runtime requirements are bundled; no Python or terminal is needed.
2. Open **Share4AI** from the desktop or Start menu shortcut. The installer and app default to Arabic.
3. **Scan → Download & Verify → Start Local AI → Benchmark**.
4. Use the **Local AI** tab. Qwen downloads are about 2.7GB (4B) or 5.7GB (9B); the app selects based on available memory. CUDA runtime packages add about 646MB. Close other memory-heavy applications first.
5. **Cancel / Stop AI** cancels work and stops the owned runtime. Retry restarts interrupted downloads; byte-range resume is not yet implemented.

CPU fallback is for Local AI trials. NVIDIA sharing eligibility requires live telemetry and a passing benchmark. Unsupported hardware or low memory produces an explanation rather than pretending setup succeeded.

### What works in this slice

- Windows CPU/RAM/disk discovery and NVIDIA GPU/VRAM/utilization/temperature detection.
- Pinned Qwen3.5 4B/9B Q4_K_M catalog and llama.cpp b10868 CPU/CUDA 12.4 packages, including CUDA DLLs.
- HTTPS downloads, size/SHA256 checks, safe staged extraction, cancellation and safe retry, optional pinned-publisher Authenticode verification.
- RuntimeAdapter, owned loopback llama-server with per-process API key, streaming Local AI and warm benchmark with real token usage.
- Desktop setup/chat/settings, owner resource threshold, persistent node ID, outbound registration/heartbeat/re-registration and Stop.

### Deliberate alpha limits

**Start Sharing now supports authenticated outbound jobs in a local pilot.** It requires a running model, passing benchmark, eligible telemetry and a provider credential. Stop Sharing cancels active network work; Local AI use stops sharing first. Follow [PILOT_JOBS.md](PILOT_JOBS.md) for the Control Plane and streaming test client. Max GPU Usage is an admission threshold, **not a hard percentage cap**. Full gaming detection, live resource preemption, persistent production Control Plane, multi-node routing and signed installer remain on the roadmap.

The pinned artifacts publish SHA256 digests; detached signatures were not supplied in the catalog. Hash verification is implemented; do not claim signature verification occurred when none was published. Unsloth supplies the GGUF quantizations of upstream Qwen models, rather than an official Qwen GGUF repository. Retain upstream notices when distributing.

Local chat content stays in process memory. No cloud inference or mandatory paid API. Do not use this alpha for sensitive community workloads. See SECURITY_BASELINE.md for the limits of privacy on a provider-owned computer.

### Local Control Plane protocol test

For job execution use `py -3 -m tools.pilot_control_plane` and `py -3 -m tools.pilot_chat` with separate provider/client credentials as described in PILOT_JOBS.md. The older `tools/dev_control_plane.py` remains a registration-only test fixture; it never dispatches jobs. Both bind loopback only and have no persistent storage. A remote endpoint must use HTTPS plus `SHARE4AI_PROVIDER_TOKEN`; production enrollment and per-provider key lifecycle remain future work.

### Development and checks

```powershell
py -3 -m unittest discover -s tests -v
py -3 -m provider --scan --state-dir .state
py -3 -m compileall -q provider tools tests
```

App data defaults to `%LOCALAPPDATA%\Share4AI`; use `--state-dir` for an isolated test. Settings contain no token. Models and runtime archives are never committed. `tools/pin_catalog.py` is maintainer-only and must be reviewed before a catalog update; the app never follows latest automatically.

### Project documents

- [PROJECT_BASELINE.md](PROJECT_BASELINE.md): accepted decisions, provenance, scope and open decisions.
- [ARCHITECTURE.md](ARCHITECTURE.md): components, state and protocol.
- [SECURITY_BASELINE.md](SECURITY_BASELINE.md): trust boundaries and release gates.
- [ROADMAP.md](ROADMAP.md): staged delivery and acceptance.
- [SPRINT_01.md](SPRINT_01.md): current progress and validation limitations.

### Upstream references

- [llama.cpp pinned release](https://github.com/ggml-org/llama.cpp/releases/tag/b10868)
- [llama.cpp server interface](https://github.com/ggml-org/llama.cpp/blob/b10868/tools/server/README.md)
- [Qwen3.5 4B GGUF](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF)
- [Qwen3.5 9B GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF)

Original prototype ZIPs were not present in the repository. The baseline records earlier user-reported success separately from tests of this new implementation.
