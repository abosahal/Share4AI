# Sprint 01 — Provider App v1.1

## تحديث 2026-09-10 — مسار المهام

اكتمل تنفيذ JobWorker داخل التطبيق وControl Plane محلي لمزود واحد وأداة عميل streaming. يدعم التحقق من توقيع HMAC للمهمة وهوية المزود وبصمة النموذج والمهلة، ومنع إعادة التنفيذ، والإلغاء عند Stop أو فقدان lease/الاتصال، وأولوية Local AI. لا يظهر محتوى العملاء في أحداث واجهة المزود. هذه الإضافة تتقدم على عبارة «لا Jobs» في سجل التسليم التاريخي أدناه.

النتيجة: **32 اختبارًا ناجحًا**، مع compileall وgit diff --check. الاختبارات تستخدم HTTP فعليًا مع runtime بديل للاختبار؛ لا تثبت أداء Qwen. تعليمات التشغيل والحدود في [PILOT_JOBS.md](PILOT_JOBS.md). نجح إنشاء فرع GitHub في محاولة 2026-09-10؛ فشل 403 أدناه توثيق للمحاولة السابقة.

بدأ 2026-09-09. الهدف: بداية تنفيذ قابلة للاختبار على Windows دون LM Studio. لا يساوي هذا إعلان اكتمال MVP.

## Deliverables and acceptance

| ID | المرحلة الصغيرة | قبول |
|---|---|---|
| S1-00 | الوثائق الخمس | فصل القرارات المعتمدة والمقترحات وحالة الإثبات |
| S1-01 | RuntimeAdapter + hardware + recommendation | GPU غائب/متعدد وRAM/VRAM قليلة دون crash |
| S1-02 | تنزيل وتحقق | SHA256، staging، إلغاء، رفض unsafe ZIP/URL؛ لا قبول signature غير متحقق |
| S1-03 | llama.cpp + Local AI | start/health/stream/stop، تشغيل loopback دون LM Studio |
| S1-04 | benchmark | warmup + قياسات متكررة، tokens من runtime، قبول صريح |
| S1-05 | sharing state + control client | Start/Stop وMax GPU، register/heartbeat/re-register، offline fail closed |
| S1-06 | Windows UI + launcher | scan/install/benchmark/chat/settings، عدم تجميد الواجهة |
| S1-07 | validation and handoff | unit/integration + تشغيل فعلي إن سمح العتاد، توثيق المتبقي |

## Test plan

Offline tests تستخدم transports/runtime مؤقتة لتغطية النجاح والفشل: digest mismatch، إلغاء وتنزيل جزئي، extraction path escape، نقص الموارد، runtime crash/timeout، stream usage/TTFT، no content logging، رفض المشاركة دون benchmark أو مع telemetry مجهولة، Stop أثناء الاتصال، heartbeat 404/reconnect، سياسة Max GPU عند 0/100 وحدود غير صحيحة.

Real Windows validation: scan على الجهاز الحالي؛ runtime مثبت يمكن تشغيل `--version`؛ نموذج فعلي إذا توفر RAM/VRAM ومساحة ملائمة. لا تنزيل متعدد gigabytes لمجرد اختبارات unit. يجب تسجيل ما لم يُختبر، خصوصًا GPU performance وinstaller على جهاز نظيف وشبكة ثلاثة أجهزة.

## Delivery status — 2026-09-09

| ID | الحالة |
|---|---|
| S1-00 | مكتمل: الوثائق الخمس مع القرارات والتعارضات |
| S1-01 | منفذ ومختبر: hardware/recommendation وRuntimeAdapter |
| S1-02 | منفذ ومختبر: تنزيل وحماية archive وSHA256 وإلغاء؛ runtime CPU حقيقي جرى تنزيله والتحقق منه |
| S1-03 | منفذ مع اختبارات contract/lifecycle؛ تشغيل binary فعلي ناجح؛ inference بـQwen غير متحقق على هذا الجهاز |
| S1-04 | منفذ ومختبر ببيانات runtime اصطناعية؛ القياس الحقيقي على GPU مناسب ما زال مطلوبًا |
| S1-05 | منفذ: register/heartbeat/404 re-register/Stop وresource admission؛ لا Jobs، لذلك accepts_jobs=false وLIMITED |
| S1-06 | واجهة Windows وlauncher منفذان؛ الاختبار البصري لم يكتمل بسبب فشل Tcl initialization في Python المرفق ببيئة التنفيذ |
| S1-07 | 21 اختبارًا ناجحًا + compileall + diff check؛ Sprint ما زال مفتوحًا للاختبارات الفعلية المتبقية |

كود v1 القديم غير موجود في GitHub؛ العقد الجديد ليس ادعاء backward compatibility مع payload مفقود.

### Evidence

- `python -W error::ResourceWarning -m unittest discover -s tests -v`: **21 passed**؛ تغطي HTTP loopback حقيقي، token خاطئ، إعادة تسجيل بعد reset، TTL، stop ordering، lifecycle/crash/timeout، إلغاء العمليات المنتظرة، مصادر غير موثوقة وZIP وتجزئة، token usage وSSE المقطوع.
- `python -m compileall -q provider tools tests`: passed.
- `git diff --check`: passed.
- الحزمة `llama-b10868-bin-win-cpu-x64.zip` نُزلت فعليًا من المصدر المثبت، وطابقت SHA256، واستُخرجت بأمان. `llama-server.exe --version` أعاد exit 0: `0.4.0-dev (build 10868, commit 304665fe7)`؛ flags المستخدمة موجودة في `--help`.
- العتاد المكتشف: Windows x64، 8 logical CPUs، RAM نحو 7.84GiB والمتاح نحو 1.8GiB، دون NVIDIA telemetry مدعومة. لا يكفي لتوصية Qwen 4B/9B؛ لم يُنزّل نموذج ضخم أو يُزعم نجاح benchmark حقيقي.
- Python المرفق يستطيع import tkinter لكنه يفشل عند إنشاء نافذة بـ`Can't find a usable init.tcl`. تمت محاولة مسار Tcl مستقل أيضًا ولم تنجح؛ يلزم Python Windows سليم مع Tcl/Tk للتحقق البصري. لا screenshot مصطنعة.
- GitHub: القراءة والclone نجحا، لكن إنشاء الفرع عبر الموصل أعاد `403 Resource not accessible by integration`. git push لم يجد اعتماد تسجيل دخول محليًا. لا تغييرات رفعت إلى المستودع البعيد. المصدر محفوظ محليًا في فرع `sprint-01-provider-v1.1` مع إيداعات منفصلة وحزمة Git قابلة للنقل.

### Next concrete slice

1. تشغيل الواجهة على Python Windows مع Tcl/Tk سليم؛ اختبار resize/error/cancel/close.
2. تشغيل Qwen 4B ثم 9B على جهاز مناسب؛ تحقق CUDA DLLs وstartup/stream/benchmark والذاكرة والحرارة. لا قَبول مشاركة لمجرد install ناجح.
3. تنفيذ outbound job worker داخل التطبيق مع tokens قصيرة العمر وstream/cancel؛ بعدها فقط تمكين accepts_jobs وAVAILABLE واختبار عميل → مزود.
4. استعادة صلاحية كتابة GitHub ثم push للإيداعات وفتح draft PR؛ لا حاجة لإرسال token في المحادثة.

### Known limitations

Max GPU Usage حد admission وليس hard cap. لا gaming detection أو تعليق inference تلقائي أثناء الحمل بعد. استئناف تنزيل byte-range مؤجل؛ retry يبدأ من جديد ويحافظ على الملفات المتحققة. توزيع EXE/installer موقع، Windows Credential Manager، Postgres/Redis، routing متعدد العقد، حسابات/ملفات/دفع جميعها غير منفذة. التوقيعات للartifacts الحالية غير منشورة؛ لا ندعي تحقق signature. سجل inventory المحلي يكشف التغيير العارض ولا يحمي من Administrator يعدل البرنامج والmanifest معًا.

## Completion rule

كل دفعة commit مستقل؛ الاختبارات قبل إيداعها. يبقى Sprint مفتوحًا إذا لم تنجح رحلة runtime/model فعلية على جهاز Windows مناسب. Deliverable هذه المهمة يشمل بدء التنفيذ العملي وتسليم المراحل المنجزة مع المتبقي بدقة.
