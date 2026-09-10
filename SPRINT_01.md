# Sprint 01 — Provider App v1.1

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

## Initial status

S1-00 موثق. S1-01 إلى S1-07 قيد التنفيذ. ستضاف نتيجة التحقق والحدود في نهاية Sprint قبل التسليم. كود v1 القديم غير موجود في GitHub؛ العقد الجديد ليس ادعاء backward compatibility مع payload مفقود.

## Completion rule

كل دفعة commit مستقل؛ الاختبارات قبل إيداعها. يبقى Sprint مفتوحًا إذا لم تنجح رحلة runtime/model فعلية على جهاز Windows مناسب. Deliverable هذه المهمة يشمل بدء التنفيذ العملي وتسليم المراحل المنجزة مع المتبقي بدقة.
