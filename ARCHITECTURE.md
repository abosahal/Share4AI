# Share4AI — Architecture

## Target

User Web/PWA → API/Auth/Fair Use → Router → Job Queue/Lease → outbound Provider worker → RuntimeAdapter → llama.cpp → GPU. Streaming يرجع عبر نفس مسار المهمة. لا فتح منافذ منزلية ولا اتصال العميل مباشرة بالGPU.

Control Plane يملك الهوية والجدولة وسياسة الجودة وسجل العمل. Provider يملك حق رفض/إيقاف العمل لحماية صاحبه. Runtime يعرف inference فقط. ملفات العملاء تعالج في خدمة استخراج محدودة الموارد قبل إرسال الأجزاء اللازمة.

## Sprint 1 implementation choices

هذه اختيارات تنفيذ جديدة وليست stack مسترجعًا من ZIP: Python 3.11+ وTkinter على Windows لتطبيق خفيف قابل للاختبار دون تبعيات pip إلزامية. فصل domain/runtime/download/network عن UI. stdlib HTTP client، عملية llama-server مستقلة مملوكة للتطبيق، state directory للمستخدم. منصة الإنتاج المقترحة FastAPI/Postgres/Redis تأتي لاحقًا؛ لا نستنتج توافق payload قديم لم يتوفر كوده.

Modules: hardware → catalog/recommendation → artifacts → runtime → benchmark → provider/control plane → UI. يُحقن runtime/transport/clock في الاختبارات. العمليات الطويلة خارج خيط الواجهة؛ أحداث العرض عبر queue، لا تحديث Tk من worker.

## Runtime contract

`start(model, gpu_layers, context)`، `health()`، `stream(messages, max_tokens)`، `stop()`. أحداث stream تحتوي النص وusage النهائي؛ benchmark يقيس زمن أول content ومدة التوليد، ويقرأ عدد tokens من runtime. نموذج محمل واحد وسعة واحدة مبدئيًا. Local AI لا يمر بالControl Plane.

llama-server مربوط فقط بـ127.0.0.1، API key عشوائي لكل عملية؛ لا shell ولا أوامر من job. timeout للصحة، اكتشاف crash، terminate/kill للعملية المملوكة فقط. model/runtime versions والhashes مثبتة في كتالوج موزع مع المصدر. لا اعتماد على latest أثناء تشغيل التطبيق.

## States and ownership

Setup: NOT_READY → DOWNLOADING → VERIFYING → STARTING → BENCHMARKING → READY؛ أي خطأ يمنع إظهار نجاح وهمي. Sharing intent منفصل عن runtime health: OFFLINE / AVAILABLE / BUSY / LIMITED. لا AVAILABLE بدون runtime سليم، benchmark مقبول، telemetry مناسبة، ومشاركة مفعلة. Stop يوقف قبول العمل فورًا؛ المهام الحالية تلغى في مرحلة Jobs. Local AI يمنع إسناد عمل شبكة متزامن.

Max GPU Usage في الأساس حد admission ومراقبة تعلّق المشاركة عند تجاوزه، وليس power cap أو partition صلب. GPU layers يحدد offload وليس نسبة utilization. يجب ألا تزعم الواجهة خلاف ذلك. انعدام telemetry يمنع المشاركة، ويسمح بتجربة Local AI على CPU. تبريد/لعب وتحكم أثناء inference يحتاجان اختبارات مرحلة 3.

## Control Plane contract v1.1

مساران مسترجعان من التجربة: `POST /v1/nodes/register` و`POST /v1/nodes/heartbeat`. تعريف payload الجديد الموثق هنا يحتاج migration إن استُعيد backend القديم.

Register: node_id ثابت عشوائي، protocol_version، app_version، capabilities (runtime/model/hash/context/max_concurrency)، benchmark، device metadata. Heartbeat: node_id، state، sharing_enabled، max_gpu_usage، telemetry، capabilities. الخادم يصدر acknowledgment ولا يستنتج disponibilité من مجرد التسجيل. heartbeat كل 5s، lease/TTL مقترح 20s؛ 404 يعيد التسجيل، فشل الاتصال يمنع إظهار AVAILABLE في الواجهة، retries محدودة بتأخير.

النسخة المنفذة الآن تعلن `accepts_jobs=false` وحالة LIMITED حتى لو نجحت أهلية الموارد. Start Sharing يفعّل التسجيل والheartbeat فقط. الإعلان AVAILABLE مؤجل إلى أن توجد قناة Jobs فعالة ومختبرة. المرجع `tools/dev_control_plane.py` يفرض LIMITED ولا يوجه مهام؛ مخزنه مؤقت للاختبار فقط.

Production: TLS وcredential منفصل لكل مزود، لا token داخل logs أو URL. مرجع محلي للاختبار فقط يمكن أن يستخدم HTTP loopback. لا إطلاق عام لهذا المرجع.

## Multi-node readiness

هوية ثابتة + نسخة بروتوكول + model revision/hash + context + capacity + benchmark + حالة واضحة. المستقبل يضيف trusted node identity، observed network latency، server-derived reliability، lease ID، job ID، attempt ID، deadline، tenant/session، trust pool. لا يعتمد router على client self-reported score وحده. affinity مفتاح session مع TTL، يعاد فحص الأهلية لكل طلب؛ المدينة اختيارية دون GPS دقيق.

Postgres: nodes، capabilities، sessions، jobs، attempts، usage ledger؛ محتوى history في تخزين مشفر منفصل. Redis: queue/leases/cache قابل للاستعادة؛ لا مصدر حقيقة للأموال. مهام retries idempotent، ولا replay بعد partial stream بلا سياسة واضحة. توزيع الطلبات بين أجهزة كاملة، لا تقسيم طبقات النموذج بين أجهزة gamers في Sprint 1.
