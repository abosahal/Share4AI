# Share4AI — خارطة الطريق | Roadmap

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

2026-09-09. ترتيب تنفيذ قابل للتعديل وفق الاختبارات؛ لا وعود زمنية قديمة.

| المرحلة | العمل | معيار الخروج |
|---|---|---|
| 0 — Baseline | الوثائق الخمس وتسجيل مصدر القرارات والتعارضات | مراجعة اتساق النطاق وإيداع مستقل |
| 1A — Foundation | Windows discovery، RuntimeAdapter، توصية Qwen، سياسة الحمل | اختبارات عتاد غائب/متعدد/ذاكرة قليلة وحدود صحيحة |
| 1B — Provisioning | كتالوج إصدارات مثبتة، تنزيل runtime/model، SHA256/signatures عند توفرها، إلغاء وإعادة محاولة | ملف فاسد لا يُفعّل؛ استخراج آمن؛ لا كسر النسخة السليمة |
| 1C — Local AI | llama-server مملوك للتطبيق، loopback، health، streaming، benchmark | اختبار تشغيل فعلي دون LM Studio، readiness صادقة وإيقاف ينظف العملية |
| 1D — Sharing | تسجيل/heartbeat وإعادة تسجيل، Start/Stop، telemetry/capabilities | عدم الإعلان AVAILABLE إذا غير جاهز؛ TTL يستبعد غير المتصل |
| 2 — Jobs | تنفيذ داخل التطبيق، قناة outbound، token/job TTL، streaming/cancel | العميل يحصل على جواب عبر المزود دون provider-node مستقل؛ stop يمنع العمل الجديد |
| 3 — Owner first | خمول/لعب وجدولة، thermal cooldown، ضغط الموارد | تشغيل لعبة/انشغال يوقف المشاركة؛ قياس أثرها على الجهاز |
| 4 — Durable network | Postgres، queue/Redis، leases، router/affinity/failover، Experience Score | ثلاثة أجهزة؛ restart لا يفقد الهوية؛ فشل عقدة لا يكرر الفوترة أو يخلط الردود |
| 5 — User MVP | Web/PWA، auth، عربي/إنجليزي، history controls، export/delete | لا تفاصيل عقد للعميل؛ رحلة محادثة وحقوق بيانات كاملة |
| 6 — Files | استخراج/فحص/retrieval، صور، 10MB/50MB مع حدود موارد | ملفات خبيثة/ضخمة مرفوضة؛ لا تشغيل macros أو كود مستخدم |
| 7 — Economics | خطط/Fair Use، قياس موثق، مكافآت، دفع وثقة | ledger قابل للتدقيق؛ معادلة واعتماد مالي؛ لا مكافأة uptime فقط |
| 8 — Qualified public network | توقيع التطبيق والتحديث، تشفير/tokens/revocation، تحقق عشوائي، عمليات ودعم | اجتياز بوابة الأمان والجودة قبل قبول مزودين عامين |

### الاختبارات المشتركة

100–200 سؤال عربي/إنجليزي للكتابة والشرح والترجمة والتلخيص والتخطيط والأسئلة العامة؛ تقييم أعمى للجودة. قياس p50/p95 TTFT، tokens/sec حقيقية، الازدحام والlatency، حرارة وذاكرة وفشل. أهداف 1–2.5s و25–40 tokens/sec تخضع للتحقق وليست نتائج محققة.

Failover قبل أول token يسمح بإعادة محاولة محدودة. بعد بدء streaming لا نلصق ردًا من نموذج آخر؛ نعرض إعادة المحاولة بوضوح أو نستبدل المحاولة ككل، مع attempt ID وعدم احتساب العمل مرتين.

### مؤجل بوضوح

vLLM والتزامن المرتفع، Linux/Mac، mobile native، API عام، confidential computing/attestation، نماذج 27B+، تدريب/تقطير عربي-إنجليزي. لا PlayStation، Hermes/OpenClaw، IDE أو توليد صور/فيديو في النطاق الحالي.

### بوابة فتح التسجيل العام

تجربة ثلاثة أجهزة موثوقة، وقياس فعلي مقبول، وauth/TLS/job expiry/revocation، وتوقيع توزيع التطبيق، ومراقبة بلا محتوى، ومعالجة إساءة الاستخدام وسياسة بيانات وشروط تشغيل معتمدة. مصدر نمو الشبكة هو أهلية الجهاز لا اسمه أو وعد الإيراد.

---

<a id="en"></a>

## English

2026-09-09. Execution order may change based on tests; earlier timeline promises do not apply.

| Stage | Work | Exit criterion |
|---|---|---|
| 0 — Baseline | Five documents and provenance/conflict record | Consistent scope review and separate commit |
| 1A — Foundation | Windows discovery, RuntimeAdapter, Qwen recommendation, load policy | Missing/multiple GPU, low-memory and valid-limit tests |
| 1B — Provisioning | Pinned catalog, runtime/model downloads, SHA256/signatures when available, cancel/retry | Corrupt file never activated; safe extraction; good installation preserved |
| 1C — Local AI | Owned llama-server, loopback, health, streaming, benchmark | Real operation without LM Studio, honest readiness, process cleanup on Stop |
| 1D — Sharing | Registration/heartbeat/re-registration, Start/Stop, telemetry/capabilities | Never AVAILABLE when unready; TTL excludes disconnected nodes |
| 2 — Jobs | In-app execution, outbound channel, token/job TTL, streaming/cancel | Customer receives an answer through the provider without a separate provider-node; Stop prevents new work |
| 3 — Owner first | Idle/gaming/scheduling, thermal cooldown, resource pressure | Gaming/busy state stops sharing; measure impact on owner use |
| 4 — Durable network | Postgres, queue/Redis, leases, router/affinity/failover, Experience Score | Three devices; restart preserves identity; failure does not duplicate billing or mix responses |
| 5 — Customer MVP | Web/PWA, auth, Arabic/English, history controls, export/delete | No node details for customers; complete chat and data-rights journey |
| 6 — Files | Extract/scan/retrieve, images, 10MB/50MB with resource limits | Reject malicious/oversized files; never execute macros or customer code |
| 7 — Economics | Plans/Fair Use, verified metering, rewards, payment and trust | Auditable ledger and approved financial formula; no uptime-only rewards |
| 8 — Qualified public network | App/update signing, encryption/tokens/revocation, random checks, operations/support | Pass security and quality gates before admitting public providers |

### Shared testing

100–200 Arabic/English questions on writing, explanation, translation, summarization, planning and general knowledge; blind quality evaluation. Measure p50/p95 TTFT, real tokens/sec, congestion, latency, heat, memory and failures. Targets of 1–2.5s and 25–40 tokens/sec require validation and are not achieved results.

Failover before the first token permits a bounded retry. After streaming starts, do not append another model's answer; show the retry clearly or replace the whole attempt, with attempt ID and no double accounting.

### Explicitly deferred

vLLM/high concurrency, Linux/Mac, native mobile, public API, confidential computing/attestation, 27B+ models and Arabic-English training/distillation. PlayStation, Hermes/OpenClaw, IDE and image/video generation are outside current scope.

### Public enrollment gate

Three trusted-device trials, acceptable measured performance, auth/TLS/job expiry/revocation, signed app distribution, content-free monitoring, abuse response, approved data policy and operating terms. Network growth depends on device eligibility, not device name or earnings promises.
