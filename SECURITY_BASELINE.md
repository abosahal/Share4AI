# Share4AI — Security baseline

## Security promise

لا تدريب على المحادثات، لا محتوى عملاء في logs أو لوحة المزود، وتقليل الاحتفاظ والصلاحيات. نقل الإنتاج مشفر، وتخزين history المستقبلي مشفر مع KMS منفصل. Local AI بعد provisioning لا يرسل المحادثة إلى المنصة.

هذه متطلبات تُختبر وليست شهادة أن النظام آمن للإطلاق العام. لا E2EE بمعنى إخفاء plaintext عن جهاز inference؛ Administrator على جهاز مجتمع قد يقرأ ذاكرة العملية. توقيع التطبيق وDocker لا يزيلان هذا الخطر. البيانات الحساسة لا تستخدم community pool قبل اعتماد سياسة ثقة مناسبة. Trusted pools/attestation اتجاه لاحق، غير منفذ هنا.

## Threat model and controls

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

## Artifact trust

SHA256 يثبت تطابق الملف مع metadata؛ لا يثبت وحده هوية ناشر مستقل إذا اختُرق المصدر نفسه. الكتالوج جزء من إصدار Share4AI المراجع؛ ثبّت URLs/revisions/digests. يُسجل مصدر digest وحالة signature بشكل صريح. إن لم تتوفر signature، لا ندعي أنها تحققت. وجود signature مطلوب في manifest مع عدم القدرة على تحققها يفشل مغلقًا. Authenticode يتحقق من سلسلة الثقة ومن هوية ناشر مثبتة، لا من عبارة Valid وحدها.

التوزيع العام يحتاج توقيع installer والتحديثات بمفتاح Share4AI وإدارة rollback/revocation وقائمة مكونات/تراخيص. لا شهادة متاحة في هذه المرحلة. لا تحديث صامت إلى latest.

## Data boundaries

Sprint 1 لا يحفظ chat history أو prompts في settings/benchmark. يُحفظ فقط catalog/settings/node ID/نتائج قياس غير محتوية للنص. تجنب أسماء المستخدم ومسارات المنزل وأرقام hardware التسلسلية في telemetry. لا mouse/keyboard content؛ أي idle detection لاحقًا زمن خمول فقط. لا credentials في المستودع؛ استخدم متغير بيئة للاختبار وWindows Credential Manager في التوزيع لاحقًا.

الإنتاج: TLS 1.3 مستهدف، mTLS بين المنصة والعقد لاحقًا؛ AES-256-GCM للhistory مع مفاتيح مغلفة خارج قاعدة البيانات، deletion/export وretention للنسخ الاحتياطية. مسح ذاكرة Python/GPU بصورة مضمونة ليس ادعاء مدعومًا؛ إنهاء العملية وتقليل العمر والاحتفاظ يخففان الخطر فقط.

## Release gates

لا public jobs قبل auth لكل مزود وتفويض jobs/replay protection، TLS، مراجعة privacy، isolation/cancellation، signing، abuse response، اختبارات محتوى logs. لا نشر تلقائي لمنافذ أو بيانات شخصية. المرجع المحلي للاختبار لا يُعرض للإنترنت. راجع ROADMAP لخطوات استكمال هذه الضوابط.
