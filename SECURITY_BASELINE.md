# Share4AI — مرجع الأمان | Security baseline

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

### تحديث تجربة المهام — 2026-09-10

تدعم التجربة المحلية الآن اعتمادَي وصول منفصلين للعميل والمزود، ومهام موقعة بـHMAC ومقيدة بالمزود، والتحقق من الجهاز والنموذج والمهلة، ورفض إعادة التشغيل، وترتيب أحداث النتائج والإلغاء. لا ترث عمليات المحرك اعتمادات SHARE4AI. لا يدخل محتوى مهام العملاء إلى أحداث محادثة سطح المكتب. التفاصيل والقيود في PILOT_JOBS.md. هذه تجربة لمزود موثوق واحد عبر loopback، ولا تستبدل TLS الإنتاجي أو تسجيل الأجهزة وإلغاء اعتمادها أو التخزين الدائم أو التنفيذ السري.

### التزام الأمان

لا تدريب على المحادثات، لا محتوى عملاء في logs أو لوحة المزود، وتقليل الاحتفاظ والصلاحيات. نقل الإنتاج مشفر، وتخزين history المستقبلي مشفر مع KMS منفصل. Local AI بعد provisioning لا يرسل المحادثة إلى المنصة.

هذه متطلبات تُختبر وليست شهادة أن النظام آمن للإطلاق العام. لا E2EE بمعنى إخفاء plaintext عن جهاز inference؛ Administrator على جهاز مجتمع قد يقرأ ذاكرة العملية. توقيع التطبيق وDocker لا يزيلان هذا الخطر. البيانات الحساسة لا تستخدم community pool قبل اعتماد سياسة ثقة مناسبة. Trusted pools/attestation اتجاه لاحق، غير منفذ هنا.

### التهديدات وضوابط الحماية

| التهديد | التحكم المطلوب | التحقق |
|---|---|---|
| تنزيل runtime/model معدل | HTTPS، إصدارات ثابتة، SHA256 منشور؛ تحقق signature إن وجد ورفض غير الصحيح | hash mismatch لا يفعّل الملف |
| ZIP traversal / zip bomb | منع absolute/.. / symlink/Windows ADS، حد استخراج وحجم، staging | archive ضار لا يكتب خارج cache |
| خلط تحديث جزئي | `.part` ثم تحقق ثم استبدال ذري، تثبيت في إصدار منفصل | قطع التنزيل يحافظ على السليم |
| مصدر/redirect غير موثوق | allowlist لمصادر الكتالوج والتنزيل، TLS verification | HTTP وhost غريب مرفوضان |
| تشغيل أوامر المستخدم | لا shell، args ثابتة ومحدودة، لا execute tools/macros | رسائل نموذج لا تصبح أوامر |
| كشف runtime للشبكة | loopback فقط، API key للعملية، تعطيل logs المحتوى | عدم bind على 0.0.0.0 |
| انتحال مزود / replay | auth خاص بالمزود؛ job tokens TTL وaudience/nonce في مرحلة Jobs | رفض token غائب/خاطئ/منتهي |
| تسرب في diagnostics | رموز أخطاء وmetadata فقط؛ تجاهل stdout/stderr النموذج | لا طباعة bodies أو prompts أو credentials |
| DoS / حرارة / ذاكرة | حدود تنزيل/context/output/concurrency، telemetry، Stop، timeouts | فشل موارد/حرارة يمنع admission |
| مزود يكذب بالمحاسبة | قياسات من الخادم وتحديات عشوائية وledger | اختبارات duplicate attempts لاحقًا |
| خلط مستأجرين | فصل job/session والذاكرة المؤقتة وعدم عرض jobs في Local AI | اختبار tenant isolation قبل شبكة عامة |

### الثقة بملفات التنزيل

SHA256 يثبت تطابق الملف مع metadata؛ لا يثبت وحده هوية ناشر مستقل إذا اختُرق المصدر نفسه. الكتالوج جزء من إصدار Share4AI المراجع؛ ثبّت URLs/revisions/digests. يُسجل مصدر digest وحالة signature بشكل صريح. إن لم تتوفر signature، لا ندعي أنها تحققت. وجود signature مطلوب في manifest مع عدم القدرة على تحققها يفشل مغلقًا. Authenticode يتحقق من سلسلة الثقة ومن هوية ناشر مثبتة، لا من عبارة Valid وحدها.

التوزيع العام يحتاج توقيع installer والتحديثات بمفتاح Share4AI وإدارة rollback/revocation وقائمة مكونات/تراخيص. لا شهادة متاحة في هذه المرحلة. لا تحديث صامت إلى latest.

### حدود البيانات

Sprint 1 لا يحفظ chat history أو prompts في settings/benchmark. يُحفظ فقط catalog/settings/node ID/نتائج قياس غير محتوية للنص. تجنب أسماء المستخدم ومسارات المنزل وأرقام hardware التسلسلية في telemetry. لا mouse/keyboard content؛ أي idle detection لاحقًا زمن خمول فقط. لا credentials في المستودع؛ استخدم متغير بيئة للاختبار وWindows Credential Manager في التوزيع لاحقًا.

الإنتاج: TLS 1.3 مستهدف، mTLS بين المنصة والعقد لاحقًا؛ AES-256-GCM للhistory مع مفاتيح مغلفة خارج قاعدة البيانات، deletion/export وretention للنسخ الاحتياطية. مسح ذاكرة Python/GPU بصورة مضمونة ليس ادعاء مدعومًا؛ إنهاء العملية وتقليل العمر والاحتفاظ يخففان الخطر فقط.

### شروط الإصدار

لا public jobs قبل auth لكل مزود وتفويض jobs/replay protection، TLS، مراجعة privacy، isolation/cancellation، signing، abuse response، اختبارات محتوى logs. لا نشر تلقائي لمنافذ أو بيانات شخصية. المرجع المحلي للاختبار لا يُعرض للإنترنت. راجع ROADMAP لخطوات استكمال هذه الضوابط.

---

<a id="en"></a>

## English

### Job pilot update — 2026-09-10

The local pilot now implements separate client/provider bearer credentials, provider-bound HMAC task envelopes, node/model/deadline verification, replay rejection, ordered result events and cancellation. Runtime subprocesses do not inherit SHARE4AI credentials. Client task content never enters desktop chat events. Details and limits are in PILOT_JOBS.md. This is one trusted provider on loopback, not a replacement for production TLS, per-node enrollment/revocation, persistence or confidential execution.

### Security promise

No training on conversations, no customer content in logs or the provider dashboard, and minimized retention/permissions. Production transport is encrypted; future history storage is encrypted with separate KMS. After provisioning, Local AI does not send the conversation to the platform.

These are requirements to test, not certification that the system is safe for public launch. No E2EE claim that plaintext is hidden from the inference device; an Administrator on a community device may read process memory. App signing and Docker do not remove that risk. Sensitive data must not use a community pool before an appropriate trust policy is approved. Trusted pools/attestation are later directions, not implemented here.

### Threat model and controls

| Threat | Required control | Verification |
|---|---|---|
| Modified runtime/model download | HTTPS, pinned versions, published SHA256; verify signatures when available and reject invalid ones | Hash mismatch never activates file |
| ZIP traversal / zip bomb | Reject absolute/.. / symlink/Windows ADS, extraction/size limits, staging | Malicious archive cannot write outside cache |
| Mixed partial update | `.part`, then verification and atomic replacement; install to separate version | Interrupted download preserves valid installation |
| Untrusted origin/redirect | Catalog/download origin allowlist, TLS verification | Reject HTTP and unknown hosts |
| Customer command execution | No shell, fixed bounded arguments, no execution of tools/macros | Model messages never become commands |
| Runtime exposed to network | Loopback only, per-process API key, no content logs | Never bind to 0.0.0.0 |
| Provider impersonation / replay | Provider authentication; job token TTL and audience/nonce in Jobs stage | Reject absent/wrong/expired token |
| Diagnostic leakage | Error codes/metadata only; discard model stdout/stderr | Never print bodies, prompts or credentials |
| DoS / heat / memory | Download/context/output/concurrency limits, telemetry, Stop, timeouts | Resource/heat failures block admission |
| Provider accounting fraud | Server-side measurement, random challenges, ledger | Duplicate-attempt tests later |
| Tenant mixing | Isolate job/session/temp memory; no jobs shown in Local AI | Tenant isolation tests before public network |

### Artifact trust

SHA256 proves a file matches metadata; by itself it does not independently establish publisher identity if the source is compromised. The catalog is part of the reviewed Share4AI release; pin URLs/revisions/digests. Record digest provenance and signature status explicitly. Do not claim signature verification when no signature exists. If a manifest requires a signature and verification is unavailable, fail closed. Authenticode must validate the trust chain and pinned publisher identity, not just a Valid status.

Public distribution needs installer/update signing with a Share4AI key, rollback/revocation management and component/license inventory. No certificate is available at this stage. No silent update to latest.

### Data boundaries

Sprint 1 stores no chat history or prompts in settings/benchmark. Persist only catalog/settings/node ID and content-free measurements. Avoid usernames, home paths and hardware serial numbers in telemetry. No mouse/keyboard content; future idle detection only records time since activity. No credentials in the repository; use environment variables for tests and Windows Credential Manager for later distribution.

Production: target TLS 1.3, later mTLS between platform and nodes; AES-256-GCM history with wrapped keys outside the database, deletion/export and backup retention. Guaranteed Python/GPU memory erasure is not a supported claim; process termination and minimizing lifetime/retention only reduce risk.

### Release gates

No public jobs before per-provider authentication and job authorization/replay protection, TLS, privacy review, isolation/cancellation, signing, abuse response and content-log tests. No automatic public ports or personal-data publication. The local test reference must not be exposed to the Internet. See ROADMAP for completing these controls.
