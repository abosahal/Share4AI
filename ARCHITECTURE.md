# Share4AI — المعمارية | Architecture

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

### المعمارية المستهدفة

User Web/PWA → API/Auth/Fair Use → Router → Job Queue/Lease → outbound Provider worker → RuntimeAdapter → llama.cpp → GPU. Streaming يرجع عبر نفس مسار المهمة. لا فتح منافذ منزلية ولا اتصال العميل مباشرة بالGPU.

Control Plane يملك الهوية والجدولة وسياسة الجودة وسجل العمل. Provider يملك حق رفض/إيقاف العمل لحماية صاحبه. Runtime يعرف inference فقط. ملفات العملاء تعالج في خدمة استخراج محدودة الموارد قبل إرسال الأجزاء اللازمة.

### خيارات تنفيذ المرحلة الأولى

هذه اختيارات تنفيذ جديدة وليست stack مسترجعًا من ZIP: Python 3.11+ وTkinter على Windows لتطبيق خفيف قابل للاختبار دون تبعيات pip إلزامية. فصل domain/runtime/download/network عن UI. stdlib HTTP client، عملية llama-server مستقلة مملوكة للتطبيق، state directory للمستخدم. منصة الإنتاج المقترحة FastAPI/Postgres/Redis تأتي لاحقًا؛ لا نستنتج توافق payload قديم لم يتوفر كوده.

Modules: hardware → catalog/recommendation → artifacts → runtime → benchmark → provider/control plane → UI. يُحقن runtime/transport/clock في الاختبارات. العمليات الطويلة خارج خيط الواجهة؛ أحداث العرض عبر queue، لا تحديث Tk من worker.

### عقد محرك التشغيل

`start(model, gpu_layers, context)`، `health()`، `stream(messages, max_tokens)`، `stop()`. أحداث stream تحتوي النص وusage النهائي؛ benchmark يقيس زمن أول content ومدة التوليد، ويقرأ عدد tokens من runtime. نموذج محمل واحد وسعة واحدة مبدئيًا. Local AI لا يمر بالControl Plane.

llama-server مربوط فقط بـ127.0.0.1، API key عشوائي لكل عملية؛ لا shell ولا أوامر من job. timeout للصحة، اكتشاف crash، terminate/kill للعملية المملوكة فقط. model/runtime versions والhashes مثبتة في كتالوج موزع مع المصدر. لا اعتماد على latest أثناء تشغيل التطبيق.

### الحالات وأولوية صاحب الجهاز

Setup: NOT_READY → DOWNLOADING → VERIFYING → STARTING → BENCHMARKING → READY؛ أي خطأ يمنع إظهار نجاح وهمي. Sharing intent منفصل عن runtime health: OFFLINE / AVAILABLE / BUSY / LIMITED. لا AVAILABLE بدون runtime سليم، benchmark مقبول، telemetry مناسبة، ومشاركة مفعلة. Stop يوقف قبول العمل فورًا؛ المهام الحالية تلغى في مرحلة Jobs. Local AI يمنع إسناد عمل شبكة متزامن.

Max GPU Usage في الأساس حد admission ومراقبة تعلّق المشاركة عند تجاوزه، وليس power cap أو partition صلب. GPU layers يحدد offload وليس نسبة utilization. يجب ألا تزعم الواجهة خلاف ذلك. انعدام telemetry يمنع المشاركة، ويسمح بتجربة Local AI على CPU. تبريد/لعب وتحكم أثناء inference يحتاجان اختبارات مرحلة 3.

### عقد خادم التحكم v1.1

مساران مسترجعان من التجربة: `POST /v1/nodes/register` و`POST /v1/nodes/heartbeat`. تعريف payload الجديد الموثق هنا يحتاج migration إن استُعيد backend القديم.

Register: node_id ثابت عشوائي، protocol_version، app_version، capabilities (runtime/model/hash/context/max_concurrency)، benchmark، device metadata. Heartbeat: node_id، state، sharing_enabled، max_gpu_usage، telemetry، capabilities. الخادم يصدر acknowledgment ولا يستنتج disponibilité من مجرد التسجيل. heartbeat كل 5s، lease/TTL مقترح 20s؛ 404 يعيد التسجيل، فشل الاتصال يمنع إظهار AVAILABLE في الواجهة، retries محدودة بتأخير.

تحديث 2026-09-10: أُضيف JobWorker outbound داخل التطبيق. تعلن النسخة `accepts_jobs=true` فقط مع worker فعال؛ AVAILABLE يحتاج runtime وbenchmark وtelemetry مناسبة. `tools/pilot_control_plane.py` يوجّه مهمة واحدة إلى مزود موثوق محليًا مع HMAC وتحقق audience/model/deadline وتسلسل أحداث، ويرجع SSE للعميل. المرجع القديم `tools/dev_control_plane.py` يظل registration-only. كلا المخزنين مؤقتان للاختبار. عقد المسارات والحدود وإلغاء المهمة في PILOT_JOBS.md.

Production: TLS وcredential منفصل لكل مزود، لا token داخل logs أو URL. مرجع محلي للاختبار فقط يمكن أن يستخدم HTTP loopback. لا إطلاق عام لهذا المرجع.

### الاستعداد لتعدد المزودين

هوية ثابتة + نسخة بروتوكول + model revision/hash + context + capacity + benchmark + حالة واضحة. المستقبل يضيف trusted node identity، observed network latency، server-derived reliability، lease ID، job ID، attempt ID، deadline، tenant/session، trust pool. لا يعتمد router على client self-reported score وحده. affinity مفتاح session مع TTL، يعاد فحص الأهلية لكل طلب؛ المدينة اختيارية دون GPS دقيق.

Postgres: nodes، capabilities، sessions، jobs، attempts، usage ledger؛ محتوى history في تخزين مشفر منفصل. Redis: queue/leases/cache قابل للاستعادة؛ لا مصدر حقيقة للأموال. مهام retries idempotent، ولا replay بعد partial stream بلا سياسة واضحة. توزيع الطلبات بين أجهزة كاملة، لا تقسيم طبقات النموذج بين أجهزة gamers في Sprint 1.

---

<a id="en"></a>

## English

### Target

User Web/PWA → API/Auth/Fair Use → Router → Job Queue/Lease → outbound Provider worker → RuntimeAdapter → llama.cpp → GPU. Streaming returns along the same job path. No home network ports or direct customer-to-GPU connections.

The Control Plane owns identity, scheduling, quality policy and work records. The Provider retains the right to reject/stop work to protect its owner. The runtime handles inference only. Customer files pass through a resource-limited extraction service before relevant parts are sent.

### Sprint 1 implementation choices

These are new implementation choices, not a stack recovered from ZIP: Python 3.11+ and Tkinter on Windows for a lightweight testable app with no mandatory pip dependencies. Separate domain/runtime/download/network from UI. Standard-library HTTP client, an independent owned llama-server process, and a user state directory. Proposed production FastAPI/Postgres/Redis come later; do not infer compatibility with unavailable legacy payload code.

Modules: hardware → catalog/recommendation → artifacts → runtime → benchmark → provider/control plane → UI. Tests inject runtime/transport/clock. Long operations run outside the UI thread; display events travel through a queue, with no worker updating Tk directly.

### Runtime contract

`start(model, gpu_layers, context)`, `health()`, `stream(messages, max_tokens)`, `stop()`. Stream events carry text and final usage; benchmark measures first-content time and generation duration, reading actual token counts from the runtime. Initially one loaded model and one slot. Local AI bypasses the Control Plane.

llama-server binds only 127.0.0.1, with a random API key per process; no shell or job-provided commands. Health timeout, crash detection and terminate/kill target only the owned process. Model/runtime versions and hashes are pinned in the source-distributed catalog. No latest-version dependency during app operation.

### States and ownership

Setup: NOT_READY → DOWNLOADING → VERIFYING → STARTING → BENCHMARKING → READY; errors must not appear as false success. Sharing intent is separate from runtime health: OFFLINE / AVAILABLE / BUSY / LIMITED. AVAILABLE requires healthy runtime, acceptable benchmark, suitable telemetry and enabled sharing. Stop immediately prevents new work; current tasks are cancelled in the Jobs stage. Local AI prevents concurrent network assignment.

Max GPU Usage is initially an admission/monitoring threshold that suspends sharing when exceeded, not a power cap or hard partition. GPU layers controls offload, not utilization percentage. The UI must not claim otherwise. Missing telemetry blocks sharing but permits CPU Local AI trials. Cooling/gaming and control during inference need stage 3 tests.

### Control Plane contract v1.1

Two paths recovered from the prototype: `POST /v1/nodes/register` and `POST /v1/nodes/heartbeat`. The new documented payload requires migration if the old backend is recovered.

Register: persistent random node_id, protocol_version, app_version, capabilities (runtime/model/hash/context/max_concurrency), benchmark and device metadata. Heartbeat: node_id, state, sharing_enabled, max_gpu_usage, telemetry and capabilities. The server acknowledges registration without inferring availability from registration alone. Heartbeat every 5s; proposed lease/TTL 20s; 404 triggers registration; connection failure prevents AVAILABLE in the UI; retries use bounded delays.

2026-09-10 update: an outbound JobWorker was added inside the app. `accepts_jobs=true` is advertised only with an active worker; AVAILABLE requires suitable runtime, benchmark and telemetry. `tools/pilot_control_plane.py` routes one task to a local trusted provider, using HMAC and audience/model/deadline checks plus ordered events, and returns SSE to the client. The older `tools/dev_control_plane.py` remains registration-only. Both stores are temporary test stores. Path contracts, limits and cancellation are in PILOT_JOBS.md.

Production requires TLS and a separate credential per provider; no token in logs or URLs. The local test reference may use HTTP loopback. It must not be publicly launched.

### Multi-node readiness

Persistent identity + protocol version + model revision/hash + context + capacity + benchmark + explicit state. Later: trusted node identity, observed network latency, server-derived reliability, lease ID, job ID, attempt ID, deadline, tenant/session and trust pool. The router must not trust self-reported scores alone. Affinity uses a session key with TTL; eligibility is checked for each request. City is optional, with no precise GPS.

Postgres: nodes, capabilities, sessions, jobs, attempts and usage ledger; history content in separate encrypted storage. Redis: recoverable queue/leases/cache, never the financial source of truth. Retries are idempotent, with no replay after partial streaming without a clear policy. Route requests among complete devices; do not split model layers across gamers' computers in Sprint 1.
