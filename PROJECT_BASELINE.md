# Share4AI — مرجع المشروع | Project baseline

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

الإصدار 1.1 · 2026-09-09 · ذكاء اصطناعي يدعمه المجتمع

### المرجع وحالة المشروع

مصدر الحقيقة للكود: https://github.com/abosahal/Share4AI . نقطة البداية المسترجعة: `272971f60f3b54e391a01b6fa9a44a9ca30e8bab`؛ يحتوي المستودع على README فقط. لم تتوفر ملفات ZIP السابقة في مساحة المشروع. لذلك هذا تنفيذ جديد متوافق مع القرارات، وليس تعديلًا على كود v1 المستعاد.

المصدر التاريخي: محادثة «مشاركة الذكاء الاصطناعي»، ID `6a8e9c67-add4-83eb-9d9f-57bdb7e1a4d4`، راجعت صفحاتها حتى البداية. المرفقات القديمة غير المسترجعة لا تُعد كودًا متحققًا منه. أحدث تعليمات المستخدم تتقدم على المقترحات القديمة. هذه الوثائق تجمع القرارات؛ لا تنقل توقعات السوق أو الأرباح كحقائق.

### الرؤية والجمهور

مساعد AI منخفض التكلفة للاستخدام اليومي بالعربية والإنجليزية، يبدأ بالسعودية ويتهيأ للتوسع. يستفيد من قدرة أجهزة المجتمع الخاملة. يحصل المزود على AI محلي مفيد أولًا، ثم يختار مشاركة جهازه. لا توجد إعادة بيع لحسابات أو أرصدة خدمات AI. الاستخدام AI inference؛ لا rendering أو mining أو تشغيل كود العملاء.

العميل: Web App/PWA أولًا، تجربة بسيطة بلا تفاصيل GPU والعقد. المزود: تطبيق Desktop، Windows أولًا، ثم Linux وMac لاحقًا؛ أجهزة PlayStation خارج النطاق. الهوية المعتمدة: **Share4AI / Community-powered AI**. الإعلان عن المرحلة التجريبية والطابع المجتمعي واضح، بلا ضمان دخل أو تكافؤ مثبت مع ChatGPT.

### القرارات المعتمدة

| المجال | القرار |
|---|---|
| الأولوية | تجربة العميل وسرعة الاستجابة فوق قبول أكبر عدد من الأجهزة |
| رحلة المزود | Install → Scan → Recommend → Download/Verify → Benchmark → Ready → Share |
| Runtime | RuntimeAdapter؛ llama.cpp أولًا؛ LM Studio أداة اختبار اختيارية وليست متطلبًا؛ vLLM لاحقًا |
| النماذج | Qwen3.5 family؛ 4B و9B مضغوطة أولًا؛ الأكبر بعد القياس؛ لا تنزيل جميع الأحجام |
| القبول | العتاد يرشح، benchmark يقرر؛ VRAM الفعلية والحرارة والحمل أهم من اسم البطاقة |
| Local AI | يعمل محليًا بعد التنزيل دون اتصال بالمنصة؛ أولوية صاحب الجهاز |
| المشاركة | موافقة صريحة Start/Stop؛ الافتراضي متوقف؛ المنصة تدير الحمل تحت الحد الذي يحدده المزود |
| الحمل | مراقبة GPU/VRAM/الحرارة؛ تعليق عند الحمل أو اللعب؛ جدولة وخمول أكثر دقة لاحقًا |
| التوجيه | أهلية وتوافق النموذج أولًا، ثم الأداء والحمل وlatency والثقة؛ المدينة ترجيح وليست شرطًا |
| الجلسات | Session affinity ما دامت العقدة مناسبة؛ failover عند الحاجة |
| الخصوصية | لا تدريب ولا prompts/responses في logs؛ عدم عرض محتوى العملاء أو هوياتهم للمزود |
| البيانات | History اختياري، تشفير، Export/Delete من متطلبات MVP المستخدم |
| الشبكة | اتصال المزود بالخادم outbound؛ لا مطالبة المستخدم بفتح منفذ منزلي |

### ما تم إثباته سابقًا وما لم يُثبت

أقر المستخدم بنجاح Local AI وظهور AVAILABLE بعد التسجيل/heartbeat في v1، وبنجاح مسار Browser → Control Plane → Provider → LM Studio → Qwen على جهاز تجريبي. وردت قياسات تقريبية RTX 3060 Ti 8GB: TTFT نحو 18 ثانية و13 tokens/sec؛ ليست نتائج لهذه النسخة ولا دليل بلوغ الجودة المستهدفة. طلب المستخدم اعتبار المبدأ ناجحًا والانتقال؛ اختبار failover على ثلاثة أجهزة واستقرار الإنتاج لا يزال مطلوبًا.

هدف الأداء: TTFT نحو 1–2.5 ثانية، و25–40 tokens/sec أو أكثر، تقييم بشري ≥4/5 للمهام اليومية. هذه أهداف قبول تجريبية وليست SLA. القياس يتضمن cold/warm، العربية والإنجليزية، السياق، الإصدار، tokens من runtime، الحرارة والاستقرار. لا نحسب chunks أو الكلمات بوصفها tokens.

### نطاق MVP ومراحله

Sprint 1 يبدأ بتطبيق Windows قابل للتجربة: اكتشاف عتاد، كتالوج مثبت، تنزيل موثق، runtime مملوك للتطبيق، benchmark، Local AI، مشاركة وتسجيل وheartbeat، وعقد قدرات يمهد للتوجيه. تنفيذ Jobs/streaming داخل التطبيق بدل provider-node المنفصل جزء من طريق MVP.

بعد أساس المزود: Postgres للحفظ، Redis للطابور/الحالة عند الحاجة، router متعدد العقد، affinity/failover، Experience Score يجمع TTFT والسرعة والlatency والحمل والموثوقية والحرارة. لا يكفي Compute Score النظري.

MVP المستخدم: حسابات ومحادثة streaming، History اختياري، تصدير JSON/Markdown/TXT وحذف، تحليل صور ومستندات PDF/DOCX/TXT وجداول CSV/XLSX. الحدود المعتمدة 10MB مجاني و50MB مدفوع، مع حدود استخراج وصفحات/tokens إضافية. parsing وفحص الملفات ثم retrieval للأجزاء المهمة. لا توليد صور أو فيديو. الملفات ليست ضمن Sprint 1 النصي.

لا IDE أو Coding Mode مستقل الآن؛ يمكن للنموذج الإجابة عن الأسئلة البرمجية داخل المحادثة. لا تشغيل آلي للكود على أجهزة المزودين. Hermes/OpenClaw ألغيا؛ Cursor/Grok أدوات تطوير اختيارية وليسا اعتماد تشغيل. Lovable غير مطلوب.

### التشغيل والاقتصاد

- Free: حوسبة فائضة بعد المشتركين؛ دون عدد ثابت مصطنع، مع سياسة Fair Use ومكافحة إساءة؛ تفضيل الأضعف **القادر على الجودة المطلوبة**.
- Basic: السعر المقترح الأحدث نحو $2.5 شهريًا؛ أولوية أعلى واستخدام واسع وفق Fair Use. مبلغ 9 ريال تقدير مبكر وليس سعر تحويل ثابتًا.
- Supporter: $20، أعلى أولوية، وصول مبكر ودعم أولوية ولوحة شرف اختيارية؛ الفوترة مؤجلة.
- التعويض حسب العمل الحاسوبي المتحقق منه، الزمن × الجهد × العمل المنجز والموثوقية، بغض النظر عن نوع العميل. لا دفع لمجرد uptime.
- لا نسبة معلنة مضمونة؛ التوجه الداخلي نحو نصف صافي الأرباح حسب الدخل والمصروفات والاستدامة. المزود يتحمل كهرباءه وإنترنت جهازه وتكاليفه.
- البداية ثلاثة أجهزة موثوقة، ثم فتح التسجيل للمؤهلين بعد التحقق من الأمان والاستقرار والمحاسبة. فحص عشوائي، تعليق للتحقيق عند الاشتباه، إنذار للمخالفة الأولى وإلغاء عند التكرار.
- تحديد المسؤوليات وشروط الاستخدام يحتاج مراجعة قبل الإطلاق؛ عبارة الإعفاء المطلق لم تُعتمد كضمان قابل للتنفيذ.

### التعارضات المحسومة والأسئلة المفتوحة

1. نص فقط مقابل تحليل صور: الصور والملفات معتمدة في MVP لاحق؛ Sprint 1 نصي. لا توليد بصري.
2. مواصفات 16/24GB القديمة كانت أمثلة؛ لا أجهزة مملوكة مفترضة. توصية أحدث 8GB VRAM/16GB RAM تجريبية، والقرار للbenchmark.
3. اختيار أكبر نموذج مقابل السرعة: أصغر نموذج يحقق جودة المهمة وسرعتها مع هامش ذاكرة.
4. History: المؤكد اختياري؛ ذُكر افتراضي off ثم اقتراح on. لم يُحسم نهائيًا؛ هذه النسخة لا تحفظ محتوى. حسم الافتراضي قبل Web MVP.
5. السرية المطلقة ضد Administrator على جهاز مجتمع غير ممكنة بهذا الأساس. Trusted/Secure pool وattestation اتجاهات مقترحة، ليست حماية منفذة؛ لا تسويق E2EE أو ضمان عدم القراءة المطلق.
6. التوقيع الرسمي وشهادة Windows، هوية المزود وإصدار job tokens، سياسة الاحتفاظ والنسخ الاحتياطية، معادلة المكافآت النهائية وحدود الاستخدام تحتاج إعدادًا قبل الإطلاق العام.

### معايير الاكتمال

كل مرحلة: كود + اختبارات ملائمة + نتيجة موثقة + commit. لا يساوي مرور اختبارات mock نجاح GPU. لإغلاق Sprint 1 يلزم اختبار Windows نظيف دون LM Studio، تنزيل سليم وفاسد ومقطوع، تشغيل Qwen فعلي، benchmark دقيق، إيقاف المشاركة أثناء العمل، offline/reconnect، وعدم تسرب محتوى. لإغلاق MVP: ثلاثة أجهزة وفشل عقدة، auth/tokens/TLS، حفظ آمن وحقوق البيانات، تجربة مستخدم وجودة ومحاسبة مثبتة. تفاصيل التنفيذ والحالة في SPRINT_01.md.

---

<a id="en"></a>

## English

Version 1.1 · 2026-09-09 · Community-powered AI

### Reference and project status

Code source of truth: https://github.com/abosahal/Share4AI . The recovered starting commit was `272971f60f3b54e391a01b6fa9a44a9ca30e8bab`, containing only a README. Earlier ZIP files were unavailable in the workspace. This is therefore a new implementation consistent with the decisions, not an edit of recovered v1 code.

Historical source: the conversation “مشاركة الذكاء الاصطناعي” (AI sharing), ID `6a8e9c67-add4-83eb-9d9f-57bdb7e1a4d4`, reviewed back to its beginning. Unrecovered attachments are not verified code. The user's latest instructions supersede earlier proposals. These documents consolidate decisions; market and earnings forecasts are not presented as facts.

### Vision and audience

A low-cost AI assistant for everyday Arabic and English use, starting in Saudi Arabia and preparing to expand. It uses idle community computing capacity. Providers receive useful local AI first, then choose whether to share their devices. No resale of AI accounts or service credits. The workload is AI inference, not rendering, mining or execution of customer code.

Customers: Web App/PWA first, with a simple experience that hides GPU and node details. Providers: desktop app, Windows first, then Linux and Mac; PlayStation is out of scope. Approved identity: **Share4AI / Community-powered AI**. Clearly describe the experimental, community-supported nature without guaranteed income or claims of proven parity with ChatGPT.

### Approved decisions

| Area | Decision |
|---|---|
| Priority | Customer experience and responsiveness take precedence over accepting more devices |
| Provider journey | Install → Scan → Recommend → Download/Verify → Benchmark → Ready → Share |
| Runtime | RuntimeAdapter; llama.cpp first; LM Studio is an optional testing tool, not a requirement; vLLM later |
| Models | Qwen3.5 family; quantized 4B and 9B first; larger models after measurement; do not download every size |
| Admission | Hardware suggests; benchmark decides. Actual VRAM, temperature and load matter more than GPU name |
| Local AI | Runs locally after downloading, without a platform connection; owner priority |
| Sharing | Explicit Start/Stop; off by default; platform manages load below the owner's selected limit |
| Load | GPU/VRAM/temperature monitoring; suspend for load or gaming; more precise scheduling and idle detection later |
| Routing | Eligibility and model compatibility first, then performance, load, latency and trust; city is a preference, not a requirement |
| Sessions | Session affinity while the node remains suitable; failover when needed |
| Privacy | No training or prompt/response logs; no customer content or identity shown to providers |
| Data | Optional history, encryption, export/delete are requirements of the customer MVP |
| Network | Provider connects outbound; no request to open a home network port |

### Previously demonstrated and still unproven

The user confirmed Local AI success, AVAILABLE after registration/heartbeat in v1, and Browser → Control Plane → Provider → LM Studio → Qwen on a test machine. Approximate RTX 3060 Ti 8GB measurements were 18 seconds TTFT and 13 tokens/sec. These are not results of this version or evidence that the quality target was reached. The user asked to consider the principle proven and move on; three-device failover and production stability still require testing.

Performance targets: approximately 1–2.5 seconds TTFT, 25–40 tokens/sec or more, and human evaluation ≥4/5 for everyday tasks. These are experimental admission goals, not an SLA. Measurements cover cold/warm runs, Arabic/English, context, version, runtime token counts, heat and stability. Chunks or words must not be counted as tokens.

### MVP scope and phases

Sprint 1 starts with a testable Windows app: hardware discovery, pinned catalog, documented downloads, an owned runtime, benchmark, Local AI, sharing/registration/heartbeat, and a capability contract that prepares for routing. Jobs and streaming inside the app, replacing a separate provider-node, are part of the MVP path.

After the provider foundation: Postgres persistence, Redis for queue/state when needed, multi-node routing, affinity/failover, and an Experience Score combining TTFT, speed, latency, load, reliability and temperature. A theoretical Compute Score alone is insufficient.

Customer MVP: accounts, streaming chat, optional history, JSON/Markdown/TXT export and deletion, image analysis, PDF/DOCX/TXT documents and CSV/XLSX spreadsheets. Approved limits are 10MB free and 50MB paid, plus extraction/page/token limits. Parse and scan files, then retrieve relevant parts. No image or video generation. Files are outside text-only Sprint 1.

No standalone IDE or Coding Mode now; the model can answer coding questions in chat. No automatic code execution on provider devices. Hermes/OpenClaw were removed; Cursor/Grok are optional development tools, not runtime dependencies. Lovable is not required.

### Operations and economics

- Free: surplus capacity after subscribers, no artificial fixed count, with Fair Use and abuse prevention; prefer the weakest device **capable of the required quality**.
- Basic: latest proposed price approximately $2.5/month; higher priority and broad usage under Fair Use. SAR 9 was an early estimate, not a fixed conversion rate.
- Supporter: $20, highest priority, early access, priority support and an optional supporter honor board; billing deferred.
- Compensation follows verified computing work: time × effort × work completed and reliability, regardless of customer type. No payment merely for uptime.
- No guaranteed public revenue share. Internal direction is around half of net profits, subject to income, expenses and sustainability. Providers pay their own electricity, Internet and device costs.
- Start with three trusted devices, then admit qualified providers after security, stability and accounting validation. Random checks, suspension for investigation upon suspicion, a warning for the first violation and termination for repetition.
- Responsibilities and terms require review before launch; a blanket liability exemption was not adopted as an enforceable guarantee.

### Resolved conflicts and open questions

1. Text-only versus image analysis: images/files are approved for a later customer MVP; Sprint 1 is text-only. No visual generation.
2. Earlier 16/24GB hardware specifications were examples, not assumed owned devices. The more recent 8GB VRAM/16GB RAM guidance is experimental; benchmark decides.
3. Largest model versus speed: choose the smallest model that meets task quality and speed, with memory reserve.
4. History is definitely optional. Off by default was followed by a proposal for on by default; no final resolution. This version stores no content. Decide the default before the Web MVP.
5. Absolute confidentiality against an Administrator on a community device is not possible on this foundation. Trusted/Secure pools and attestation are proposed directions, not implemented protection. Do not market E2EE or absolute inability to read content.
6. Official signing/Windows certificate, provider identity and job token issuance, retention/backups, final rewards formula and usage limits require preparation before public launch.

### Definition of Done

Each stage: code + appropriate tests + documented result + commit. Mock tests passing do not mean GPU success. Closing Sprint 1 requires a clean Windows trial without LM Studio; valid, corrupt and interrupted downloads; real Qwen operation; accurate benchmark; Stop during work; offline/reconnect; and no content leakage. Closing the MVP requires three devices and node failure, auth/tokens/TLS, secure storage and data rights, and demonstrated user experience, quality and accounting. Implementation details and status are in SPRINT_01.md.
