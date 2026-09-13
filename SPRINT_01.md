# Share4AI — المرحلة الأولى | Sprint 01 — Provider App v1.1

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

### تحديث اللغتين — 2026-09-13

أضيف قسم عربي وآخر إنجليزي إلى الوثائق السبع، ونصوص ثنائية اللغة إلى واجهة المزود ورسائل التنزيل والتشغيل وأدوات التجربة المحلية. بقيت رموز البروتوكول ومحتويات المحادثات كما هي. أضيفت اختبارات لتغطية الأخطاء وقوالب الرسائل ومساعدة الطرفية والحفاظ على نص النموذج أثناء البث. التحقق البصري على Windows ما زال معلقًا بسبب تعذر تهيئة Tcl/Tk في بيئة التنفيذ.

### تحديث 2026-09-10 — مسار المهام

اكتمل تنفيذ JobWorker داخل التطبيق وControl Plane محلي لمزود واحد وأداة عميل streaming. يدعم التحقق من توقيع HMAC للمهمة وهوية المزود وبصمة النموذج والمهلة، ومنع إعادة التنفيذ، والإلغاء عند Stop أو فقدان lease/الاتصال، وأولوية Local AI. لا يظهر محتوى العملاء في أحداث واجهة المزود. هذه الإضافة تتقدم على عبارة «لا Jobs» في سجل التسليم التاريخي أدناه.

النتيجة: **32 اختبارًا ناجحًا**، مع compileall وgit diff --check. الاختبارات تستخدم HTTP فعليًا مع runtime بديل للاختبار؛ لا تثبت أداء Qwen. تعليمات التشغيل والحدود في [PILOT_JOBS.md](PILOT_JOBS.md). نجح إنشاء فرع GitHub في محاولة 2026-09-10؛ فشل 403 أدناه توثيق للمحاولة السابقة.

بدأ 2026-09-09. الهدف: بداية تنفيذ قابلة للاختبار على Windows دون LM Studio. لا يساوي هذا إعلان اكتمال MVP.

### المخرجات ومعايير القبول

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

### خطة الاختبار

Offline tests تستخدم transports/runtime مؤقتة لتغطية النجاح والفشل: digest mismatch، إلغاء وتنزيل جزئي، extraction path escape، نقص الموارد، runtime crash/timeout، stream usage/TTFT، no content logging، رفض المشاركة دون benchmark أو مع telemetry مجهولة، Stop أثناء الاتصال، heartbeat 404/reconnect، سياسة Max GPU عند 0/100 وحدود غير صحيحة.

Real Windows validation: scan على الجهاز الحالي؛ runtime مثبت يمكن تشغيل `--version`؛ نموذج فعلي إذا توفر RAM/VRAM ومساحة ملائمة. لا تنزيل متعدد gigabytes لمجرد اختبارات unit. يجب تسجيل ما لم يُختبر، خصوصًا GPU performance وinstaller على جهاز نظيف وشبكة ثلاثة أجهزة.

### حالة التسليم — 2026-09-09

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

#### أدلة التحقق

- `python -W error::ResourceWarning -m unittest discover -s tests -v`: **21 passed**؛ تغطي HTTP loopback حقيقي، token خاطئ، إعادة تسجيل بعد reset، TTL، stop ordering، lifecycle/crash/timeout، إلغاء العمليات المنتظرة، مصادر غير موثوقة وZIP وتجزئة، token usage وSSE المقطوع.
- `python -m compileall -q provider tools tests`: passed.
- `git diff --check`: passed.
- الحزمة `llama-b10868-bin-win-cpu-x64.zip` نُزلت فعليًا من المصدر المثبت، وطابقت SHA256، واستُخرجت بأمان. `llama-server.exe --version` أعاد exit 0: `0.4.0-dev (build 10868, commit 304665fe7)`؛ flags المستخدمة موجودة في `--help`.
- العتاد المكتشف: Windows x64، 8 logical CPUs، RAM نحو 7.84GiB والمتاح نحو 1.8GiB، دون NVIDIA telemetry مدعومة. لا يكفي لتوصية Qwen 4B/9B؛ لم يُنزّل نموذج ضخم أو يُزعم نجاح benchmark حقيقي.
- Python المرفق يستطيع import tkinter لكنه يفشل عند إنشاء نافذة بـ`Can't find a usable init.tcl`. تمت محاولة مسار Tcl مستقل أيضًا ولم تنجح؛ يلزم Python Windows سليم مع Tcl/Tk للتحقق البصري. لا screenshot مصطنعة.
- GitHub: القراءة والclone نجحا، لكن إنشاء الفرع عبر الموصل أعاد `403 Resource not accessible by integration`. git push لم يجد اعتماد تسجيل دخول محليًا. لا تغييرات رفعت إلى المستودع البعيد. المصدر محفوظ محليًا في فرع `sprint-01-provider-v1.1` مع إيداعات منفصلة وحزمة Git قابلة للنقل.

#### الخطوة التنفيذية التالية

1. تشغيل الواجهة على Python Windows مع Tcl/Tk سليم؛ اختبار resize/error/cancel/close.
2. تشغيل Qwen 4B ثم 9B على جهاز مناسب؛ تحقق CUDA DLLs وstartup/stream/benchmark والذاكرة والحرارة. لا قَبول مشاركة لمجرد install ناجح.
3. تنفيذ outbound job worker داخل التطبيق مع tokens قصيرة العمر وstream/cancel؛ بعدها فقط تمكين accepts_jobs وAVAILABLE واختبار عميل → مزود.
4. استعادة صلاحية كتابة GitHub ثم push للإيداعات وفتح draft PR؛ لا حاجة لإرسال token في المحادثة.

#### القيود المعروفة

Max GPU Usage حد admission وليس hard cap. لا gaming detection أو تعليق inference تلقائي أثناء الحمل بعد. استئناف تنزيل byte-range مؤجل؛ retry يبدأ من جديد ويحافظ على الملفات المتحققة. توزيع EXE/installer موقع، Windows Credential Manager، Postgres/Redis، routing متعدد العقد، حسابات/ملفات/دفع جميعها غير منفذة. التوقيعات للartifacts الحالية غير منشورة؛ لا ندعي تحقق signature. سجل inventory المحلي يكشف التغيير العارض ولا يحمي من Administrator يعدل البرنامج والmanifest معًا.

### شرط الاكتمال

كل دفعة commit مستقل؛ الاختبارات قبل إيداعها. يبقى Sprint مفتوحًا إذا لم تنجح رحلة runtime/model فعلية على جهاز Windows مناسب. Deliverable هذه المهمة يشمل بدء التنفيذ العملي وتسليم المراحل المنجزة مع المتبقي بدقة.

---

<a id="en"></a>

## English

### Bilingual update — 2026-09-13

All seven documents now have Arabic and English sections. Provider UI, download and operational messages, and local pilot tools display both languages. Protocol codes and conversation content remain unchanged. Added checks cover error translations, message templates, CLI help and preservation of streamed model text. Windows visual validation remains outstanding because Tcl/Tk initialization fails in the execution environment.

### 2026-09-10 update — Job path

The in-app JobWorker, one-provider local Control Plane and streaming client are implemented. They verify the job HMAC, provider identity, model fingerprint and deadline; prevent repeated execution; cancel on Stop or lost lease/connection; and prioritize Local AI. Customer content never appears in provider desktop events. This update supersedes “no Jobs” in the historical delivery record below.

Result: **32 tests passed**, plus compileall and git diff --check. Tests use actual HTTP with a test runtime; they do not establish Qwen performance. Instructions and limits are in [PILOT_JOBS.md](PILOT_JOBS.md). GitHub branch creation succeeded on 2026-09-10; the 403 below records the earlier attempt.

Started 2026-09-09. Goal: a testable Windows implementation foundation without LM Studio. This does not announce MVP completion.

### Deliverables and acceptance

| ID | Small stage | Acceptance |
|---|---|---|
| S1-00 | Five documents | Separate accepted decisions, proposals and evidence status |
| S1-01 | RuntimeAdapter + hardware + recommendation | Missing/multiple GPU and low RAM/VRAM without crashes |
| S1-02 | Download and verification | SHA256, staging, cancellation, unsafe ZIP/URL rejection; no unverified signature acceptance |
| S1-03 | llama.cpp + Local AI | start/health/stream/stop, loopback without LM Studio |
| S1-04 | Benchmark | Warmup and repeated measurements, runtime token counts, explicit admission |
| S1-05 | Sharing state + control client | Start/Stop and Max GPU, register/heartbeat/re-register, fail closed offline |
| S1-06 | Windows UI + launcher | Scan/install/benchmark/chat/settings without freezing UI |
| S1-07 | Validation and handoff | Unit/integration plus real execution when hardware permits; document remaining work |

### Test plan

Offline tests use temporary transports/runtime to cover success/failure: digest mismatch, cancellation/partial downloads, extraction escape, insufficient resources, runtime crash/timeout, stream usage/TTFT, no content logging, rejection without benchmark or with unknown telemetry, Stop during connection, heartbeat 404/reconnect, Max GPU at 0/100 and invalid limits.

Real Windows validation: scan current machine; run the pinned runtime's `--version`; use an actual model if RAM/VRAM/disk are adequate. Do not download multiple gigabytes just for unit tests. Record untested areas, especially GPU performance, clean-machine installer and three-device network.

### Delivery status — 2026-09-09

| ID | Status |
|---|---|
| S1-00 | Complete: five documents with decisions and conflicts |
| S1-01 | Implemented/tested: hardware/recommendation and RuntimeAdapter |
| S1-02 | Implemented/tested: downloads, archive protection, SHA256 and cancellation; real CPU runtime downloaded and verified |
| S1-03 | Implemented with contract/lifecycle tests; real binary execution succeeded; Qwen inference unverified on this machine |
| S1-04 | Implemented/tested with synthetic runtime data; real GPU measurement still required |
| S1-05 | Implemented: register/heartbeat/404 re-register/Stop and resource admission; no Jobs, so accepts_jobs=false and LIMITED |
| S1-06 | Windows UI/launcher implemented; visual testing incomplete because bundled Python failed Tcl initialization |
| S1-07 | 21 tests passed + compileall + diff check; Sprint remains open for remaining real-device tests |

Legacy v1 code is absent from GitHub; the new contract does not claim backward compatibility with unavailable payloads.

#### Evidence

- `python -W error::ResourceWarning -m unittest discover -s tests -v`: **21 passed**, covering real loopback HTTP, wrong tokens, re-registration after reset, TTL, stop ordering, lifecycle/crash/timeout, queued operation cancellation, untrusted origins, ZIP/hashing, token usage and interrupted SSE.
- `python -m compileall -q provider tools tests`: passed.
- `git diff --check`: passed.
- `llama-b10868-bin-win-cpu-x64.zip` was downloaded from its pinned source, matched SHA256 and extracted safely. `llama-server.exe --version` returned exit 0: `0.4.0-dev (build 10868, commit 304665fe7)`; the flags used appear in `--help`.
- Detected hardware: Windows x64, 8 logical CPUs, approximately 7.84GiB RAM with 1.8GiB available, no supported NVIDIA telemetry. Insufficient for Qwen 4B/9B recommendation; no huge model was downloaded and no real benchmark success claimed.
- Bundled Python imports tkinter but window creation fails with `Can't find a usable init.tcl`. A separate Tcl path was also tried unsuccessfully; visual verification needs a working Windows Python/Tcl/Tk installation. No fabricated screenshot.
- GitHub: reading/cloning succeeded, but connector branch creation returned `403 Resource not accessible by integration`. git push found no local login credential. No changes were uploaded at that time. Source was saved locally on `sprint-01-provider-v1.1`, with separate commits and a portable Git bundle.

#### Next concrete slice

1. Run the UI on Windows Python with working Tcl/Tk; test resize/error/cancel/close.
2. Run Qwen 4B then 9B on suitable hardware; verify CUDA DLLs, startup/stream/benchmark, memory and heat. Installation alone does not qualify a provider.
3. Implement an outbound job worker with short-lived tokens and stream/cancel; only then enable accepts_jobs/AVAILABLE and test customer → provider.
4. Restore GitHub write access, upload commits and open a draft PR; no need to send a token in chat.

#### Known limitations

Max GPU Usage is an admission threshold, not a hard cap. Gaming detection and automatic inference suspension under load are not yet implemented. Byte-range download resume is deferred; retry restarts safely and preserves verified files. Signed EXE/installer distribution, Windows Credential Manager, Postgres/Redis, multi-node routing, accounts/files/payment are unimplemented. Current artifact signatures are unpublished; no signature-verification claim. A local inventory detects accidental changes, not an Administrator modifying both program and manifest.

### Completion rule

Each batch gets a separate commit after tests. The Sprint stays open without a successful real runtime/model journey on suitable Windows hardware. This task's deliverable includes starting practical implementation and accurately handing off completed stages and remaining work.
