# Share4AI — دليل المهام التجريبية | Job pilot guide

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

**للمطورين فقط:** خطوات الطرفية هنا اختبار داخلي للبروتوكول، وليست تجربة عميل أو مزود معتمدة. المستخدم النهائي يحصل على مثبت ويكمل الإعداد داخل التطبيق. التسجيل المبسط بخدمة المشاركة العامة لم يكتمل بعد.

### ما الذي تغير؟

يحتوي تطبيق المزود الآن على عامل مهام يتصل بالخادم اتصالًا صادرًا. يرسل العميل النص إلى خادم التحكم التجريبي، ويستعلم المزود عن مهمة واحدة موقعة، ثم تعود أجزاء الرد عبر خادم التحكم باستخدام SSE. لا يحتاج المزود إلى منفذ اتصال وارد. لا يدخل نص العميل في سجل Local AI أو أحداث الواجهة أو السجلات التشغيلية.

يتطلب Start Sharing محركًا يعمل واختبار أداء ناجحًا وبيانات اعتماد للمزود. وتتطلب حالة AVAILABLE أيضًا قياسات تؤهل الجهاز وعامل مهام فعالًا. يعطّل Stop Sharing قبول المهام أولًا ويلغي الاستدلال الشبكي الجاري. إذا توقفت قراءة الاستدلال عن الاستجابة، يُنهى محرك التشغيل الذي يديره التطبيق؛ **أعد تشغيل Local AI واختبار الأداء بعد الإلغاء قبل المشاركة مجددًا**. بدء المحادثة المحلية يوقف المشاركة أولًا، فصاحب الجهاز له الأولوية.

هذه **تجربة لمزود واحد موثوق، تعمل على الجهاز المحلي فقط وبذاكرة مؤقتة**، وليست موجّه الإنتاج الدائم. يظل `dev_control_plane.py` أداة للتسجيل فقط؛ استخدم الخادم التجريبي الجديد للمهام. لا تعرض أيًا من الخادمين للإنترنت.

### اختبار Windows على الجهاز الذي يحتوي النموذج

استخدم Python 3.11 أو أحدث مع Tcl/Tk. لا تحتاج حزمًا إضافية أو LM Studio. من مجلد Share4AI داخل PowerShell، اختر قيمتين سريتين طويلتين وعشوائيتين ومختلفتين لهذه التجربة. استخدم سر المزود للخادم وتطبيق المزود فقط، وسر العميل للخادم وعميل الاختبار فقط. لا تضع الأسرار في Git ولا ترسلها في المحادثة.

**الطرفية 1 — خادم التحكم**

```powershell
$env:SHARE4AI_PROVIDER_TOKEN = Read-Host 'Provider test secret'
$env:SHARE4AI_CLIENT_TOKEN = Read-Host 'Different client test secret'
py -3 -m tools.pilot_control_plane
```

**الطرفية 2 — المزود**

```powershell
$env:SHARE4AI_PROVIDER_TOKEN = Read-Host 'Same provider test secret'
py -3 -m provider
```

اتبع: فحص الجهاز → التنزيل والتحقق → تشغيل الذكاء المحلي → اختبار الأداء. اضبط عنوان خادم التحكم على `http://127.0.0.1:8000`. ابدأ المشاركة بعد نجاح الاختبار. لا نؤهل الأجهزة البطيئة أو المعتمدة على CPU فقط لمجرد إظهار تجربة ناجحة.

**الطرفية 3 — العميل**

```powershell
$env:SHARE4AI_CLIENT_TOKEN = Read-Host 'Same client test secret'
py -3 -m tools.pilot_chat
```

يقرأ العميل بصمة النموذج المثبت تلقائيًا على الجهاز نفسه، ويطلب رسالة، ثم يعرض الرد المتدفق. إذا استخدم المزود مجلد بيانات مخصصًا، مرّر `--state-dir PATH`؛ أو مرّر `--model-sha256 HASH` من سجل التثبيت.

اضغط Stop Sharing في تطبيق المزود أثناء توليد الرد. يجب أن يتلقى العميل خطأ ينهي المهمة، لا إجابة جزئية تُعرض بوصفها نجاحًا. لإعادة المحاولة بعد الإلغاء، شغّل المحرك واختبار الأداء وفعّل المشاركة مجددًا. إغلاق العميل يلغي مهمته أيضًا؛ يُكتشف ذلك عادة ضمن فترات الإبقاء على الاتصال والاستعلام، مضافًا إليها مهلة الشبكة.

### البروتوكول والحدود

- رمزا اعتماد المزود والعميل منفصلان. يربط الخادم التجريبي اعتماد المزود بأول عقدة مسجلة حتى إعادة تشغيل الخادم. يحتاج الإنتاج إلى تسجيل مزودين ومفاتيح لكل عقدة وإبطالها وإنهاء اتصال TLS بأمان.
- `POST /v1/chat/stream`: تفويض العميل؛ رسائل نصية وبصمة `model_sha256` دقيقة و`max_tokens`. تعيد العقدة الغائبة أو غير المؤهلة أو المشغولة بالطلب الوحيد الحالة 409 قبل بدء التدفق.
- `POST /v1/jobs/poll`: يسحب المزود الموثق مهمة محجوزة له؛ لا يمكن استلام المهمة مرتين.
- غلاف المهمة: HMAC-SHA256 مع بادئة تميّز هذا الاستخدام، فوق تمثيل JSON موحد للمهمة كاملة. يشمل هوية العقدة وبصمة النموذج وهوية المهمة وتوقيتي الإصدار والانتهاء والرسائل وحد الإخراج. يتحقق العامل قبل التنفيذ. هذا **تفويض للمهمة**، منفصل عن توقيع الحزم أو التطبيق.
- `POST /v1/jobs/event`: عقدة موثقة وتوقيع المهمة وتسلسل متزايد للأحداث. الأنواع `token` أو `done` أو `error`. تُرفض الأحداث المكررة، والتفويضات الخاطئة، والأحداث بعد إغلاق المهمة. لا إعادة محاولة غير آمنة عند غموض نجاح إرسال حدث؛ تفشل المهمة بدل تكرار النص.
- `POST /v1/jobs/status`: مراقبة الإلغاء والمهلة. الحجز المجهول أو تعطل الشبكة أو الإلغاء يوقف الاستدلال. يستمر heartbeat الخاص بالتسجيل بصورة منفصلة أثناء التنفيذ.
- مهلة التجربة 120 ثانية؛ الحد الأقصى المقبول للتحقق 180 ثانية؛ عمر حالة العقدة 20 ثانية؛ مهمة نشطة واحدة؛ 40 رسالة أو 12,000 حرف؛ حتى 1,024 token للإخراج؛ طلب بحجم 64KiB؛ و512 حدث تدفق أو مخزن رد بحجم 256KiB. تجاوز سعة التخزين أثناء ضغط التدفق يلغي المهمة.
- لا تحويل تلقائي إلى مزود آخر بعد رد جزئي؛ الخطأ صريح. لا دمج صامت لإجابتين ولا ادعاءات فوترة.
- تُحذف المدخلات عند انتهاء المهام، وتُزال مخازن الرد عند خروج مستهلك التدفق. لا حفظ دائم أو استعادة بعد إعادة تشغيل الخادم. لا يُضمن المسح الكامل لذاكرة Python أو GPU.

### التحقق

تغطي الاختبارات استعلام المزود عبر HTTP وتدفق SSE إلى العميل فعليًا مع محرك اختبار حتمي: رد كامل، وإيقاف أثناء التدفق، وفقدان حجز المهمة، وفصل الاعتمادات، وتعديل حمولة موقعة، وانتهاء صلاحيتها، وعقدة أو نموذج خاطئ، وإعادة الإرسال، وترتيب الأحداث، وحالة مزود قديمة، وتنظيف المدخلات. تثبت هذه الاختبارات إدارة المسار، **ولا تثبت استدلال Qwen أو أداء GPU**. ما زالت قيود العتاد وTcl السابقة قائمة في بيئة التنفيذ الحالية.

شغّل `py -3 -m unittest discover -s tests -v`. اختبار القبول التالي على العتاد: رد Qwen فعلي، والإيقاف أثناء معالجة المدخلات والتوليد، وانقطاع العميل، وإيقاف الخادم وإعادة تشغيله، واستخدام المالك للذكاء المحلي. التوجيه متعدد العقد والتخزين الإنتاجي والتحكم الأوسع بالحمل وتوزيع Windows الموقّع مراحل لاحقة.

---

<a id="en"></a>

## English

**Developers only:** terminal steps here are internal protocol tests, not an approved client/provider experience. End users receive an installer and complete setup inside the app. Simple public sharing enrollment is not complete yet.

### What changed

The Provider App now contains an outbound job worker. A client submits text to the pilot Control Plane, the provider polls for one signed task, and tokens return through the Control Plane as SSE. No inbound port on the provider. Customer text does not enter Local AI history, desktop events or logs.

Start Sharing requires a live runtime, passing benchmark and provider credential. AVAILABLE additionally requires eligible telemetry and an active worker. Stop Sharing disables admission first and cancels active network inference. A blocked inference read is interrupted by terminating the owned runtime; **restart Local AI and rerun benchmark after cancellation before sharing again**. Opening Local AI chat stops sharing first so the owner has priority.

This is an **in-memory, loopback-only, one-trusted-provider pilot**, not the persistent production router. The existing `dev_control_plane.py` remains a registration-only fixture; use the new pilot for jobs. Do not expose either server to the Internet.

### Windows test on the machine with the model

Use Python 3.11+ with Tcl/Tk. No extra packages or LM Studio required. In PowerShell, from the Share4AI directory, choose two different long random secrets for this test. Use the provider secret only for the server and Provider App, and the client secret only for the server and test client. Do not commit or send these secrets in chat.

**Terminal 1 — Control Plane**

```powershell
$env:SHARE4AI_PROVIDER_TOKEN = Read-Host 'Provider test secret'
$env:SHARE4AI_CLIENT_TOKEN = Read-Host 'Different client test secret'
py -3 -m tools.pilot_control_plane
```

**Terminal 2 — Provider**

```powershell
$env:SHARE4AI_PROVIDER_TOKEN = Read-Host 'Same provider test secret'
py -3 -m provider
```

Use Scan → Download & Verify → Start Local AI → Benchmark. Set Control Plane to `http://127.0.0.1:8000`. Start Sharing after benchmark passes. CPU-only or slow devices are not made eligible merely to force a successful demo.

**Terminal 3 — Client**

```powershell
$env:SHARE4AI_CLIENT_TOKEN = Read-Host 'Same client test secret'
py -3 -m tools.pilot_chat
```

The client reads the installed model fingerprint automatically on the same machine, asks for a message, and displays streamed output. If the provider uses a custom data directory, pass `--state-dir PATH`; alternatively pass `--model-sha256 HASH` from its installed manifest.

While a response is being generated, press Stop Sharing in the provider. The client must receive a terminal error, not a successful partial answer. To retry after cancellation, start the runtime, run benchmark, and enable sharing again. Closing the client also cancels its task; detection is normally within the keepalive/poll intervals plus network timeout.

### Protocol and limits

- Provider bearer and client bearer are separate. The pilot binds its provider credential to the first registered node until server restart. Production needs enrollment, per-node keys, revocation and TLS termination.
- `POST /v1/chat/stream`: client authorization; text messages, exact `model_sha256`, and `max_tokens`. Missing/ineligible node or full single slot returns 409 before streaming.
- `POST /v1/jobs/poll`: authenticated provider pulls one lease; no job can be claimed twice.
- Envelope: HMAC-SHA256 with a domain prefix over the entire canonical JSON job. Includes node ID, exact model SHA256, job ID, issue/expiry, messages and output limit. The worker verifies before executing. This is **job authorization**, separate from artifact/application signing.
- `POST /v1/jobs/event`: authenticated node + job signature + monotonically ordered sequence. `token`, `done` or `error`. Duplicates, wrong job authorization and events after closure are rejected. No unsafe retry after an ambiguous event write; job fails instead of duplicating text.
- `POST /v1/jobs/status`: cancellation/deadline monitoring. Unknown lease, network failure or cancellation stops inference. Separate registration heartbeat continues during execution.
- Pilot deadline 120 seconds, verifier maximum 180 seconds, node TTL 20 seconds, one active job, 40 messages / 12,000 characters, maximum 1,024 output tokens, 64KiB request, 512 stream events / 256KiB response buffer. Backpressure overflow cancels the job.
- No automatic failover after partial output; error is explicit. No silent merging of two answers and no billing claims.
- Prompts are erased when jobs finish and buffers removed when the streaming consumer exits. No persistence/recovery on server restart. Python/GPU memory wiping is not guaranteed.

### Validation

Automated tests cover real HTTP provider polling and client SSE against the broker, with a deterministic test runtime: complete response, mid-stream Stop, lost lease, auth separation, signed payload tampering, expiry, wrong node/model, replay, ordering, stale provider and prompt cleanup. These demonstrate orchestration, **not Qwen inference or GPU performance**. Earlier hardware/Tcl limitations still apply to this execution environment.

Run `py -3 -m unittest discover -s tests -v`. Next hardware acceptance: real Qwen response, Stop during prefill and generation, client disconnect, server shutdown/restart, and owner Local AI use. Multi-node routing, production persistence, broader live load control and signed Windows distribution remain future milestones.
