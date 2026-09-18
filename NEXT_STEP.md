# الخطوة التالية: تثبيت تجربة الجهاز الآخر | Next step: stabilize the second-device experience

> تحديث بتوجيه المستخدم: مشكلة التنزيل والواجهة محلولة بواسطة جروك؛ الأولوية أصبحت الوصول إلى MVP. نُفذت واجهة محادثة المستخدم وتجربة المشاركة من زر واحد في 1.1.4، والاستضافة مؤجلة باختيار المستخدم. راجع [MVP_TRIAL.md](MVP_TRIAL.md) للمسار الحالي. القائمة أدناه سجل مراجعة سابق وليست ترتيب العمل الحالي.
>
> User-directed update: download/UI issues were resolved by Grok; the priority is MVP delivery. Version 1.1.4 implements browser customer chat and a one-click sharing trial. Hosting is deferred by user choice. See [MVP_TRIAL.md](MVP_TRIAL.md) for current delivery/next steps. The following list is prior review history, not the current execution order.

Baseline reviewed: `0af3fcc5535460977198d98ba9fc9dcd523686cc` (2026-09-17).
Status: prepared; implementation and device acceptance pending.
الحالة: جاهزة للتنفيذ؛ الإصلاح واختبار الجهاز الآخر لم يكتملَا بعد.

## الهدف | Goal
من ملف تثبيت واحد إلى أول إجابة عربية على الجهاز الآخر، مع تفسير واضح لأي عائق. لا طرفية ولا أدوات تطوير للمستخدم. تؤجل توسعة multi-node حتى تثبت دورة التنزيل والتشغيل.
One installer through the first Arabic answer on the second computer, with actionable failure messages. No terminal/developer tools for users. Multi-node expansion follows a verified download/start path.

## دفعات التنفيذ | Implementation slices

1. **إصلاح تشغيل النموذج | Repair model startup.**
   مرر ngl الموثق من التوصية إلى RuntimeAdapter ثم llama.cpp، مع حدود صحيحة وCPU=0 وتوافق السجلات القديمة. أضف اختبارًا عند حد تشغيل العملية يثبت وصول 28 بدل 99 لحالة offload. تحقق من وجود ملف النموذج وSHA256 المنشور وتوافق المحرك قبل تنزيل تجربة كبيرة.
   Pass validated ngl through the controller and adapter into the process, with CPU=0 and old-record compatibility. Test the actual launch arguments for offload=28. Verify upstream artifact/digest and pinned-runtime compatibility before a large trial download.

2. **استعادة تجربة الترقية | Preserve upgrade usability.**
   لا تُجبر الأجهزة العاملة على 27B دون مسار ترقية. جهز اختيارًا تلقائيًا مناسبًا وخيار نموذج أخف موثوق عند الحاجة، واختبر ترقية تثبيت 4B/9B دون فقد البيانات. لا تُحذف النماذج تلقائيًا.
   Avoid a mandatory 27B replacement without migration. Provide an appropriate automatic recommendation and a trusted smaller fallback when needed; test upgrades from existing 4B/9B installations without data loss. Do not automatically delete models.

3. **تنزيل مفهوم وقابل للاستعادة | Make download status actionable.**
   أظهر الاتصال، والبيانات المنزلة/الإجمالي، والسرعة، والتحقق كحالات مستقلة. افصل أخطاء الشبكة عن المحرك مع إعادة المحاولة وزمن إلغاء محدد. اختبر فشل الاتصال وانقطاع القراءة والإلغاء وSHA256 دون تنزيل نموذج كامل. وضح أن إعادة المحاولة تبدأ من جديد ما لم يُنفذ استكمال آمن.
   Show connecting, bytes/total, speed and verification separately. Add network-specific Arabic/English recovery messages and bounded cancellation. Test connection/read failures, cancellation and integrity without full model downloads. State restart behavior until safe resume is implemented.

4. **هوية إصدار موحدة | Align release identity.**
   اعرض رقم الإصدار ومعرف البناء في التطبيق مع زر نسخ تشخيص مختصر بلا أسرار أو محادثات. حدّث README ودليل التجربة وملاحظات الإصدار ووصف PR للكتالوج الفعلي ورابط مثبت واحد محدد. ثم ابنِ إصدار تجربة جديدًا.
   Display version/build ID and a copyable minimal diagnostic without secrets or chats. Align README, trial guide, release notes and PR with the actual catalog and one exact installer link. Build a new trial.

5. **قبول على الجهاز الآخر | Second-device acceptance.**
   اختبر RTX 3060 Ti الظاهر بالصورة مع قراءة جديدة للذاكرة المتاحة؛ القيم بالصورة قديمة. تحقق من التنزيل وSHA256 والتشغيل وأول إجابة عربية وbenchmark، ثم إعادة الفتح والإلغاء وإعادة المحاولة. اختبر دقة العربية والنص المختلط والتكبير 100% و125% و150%، والتثبيت/التحديث/الإزالة وخيار سطح المكتب على Windows بلا Python.
   Retest the pictured RTX 3060 Ti with fresh available-memory measurements. Validate download, SHA256, startup, first Arabic answer, benchmark, restart and recovery. Check Arabic/mixed text at 100/125/150% scaling and install/upgrade/uninstall/desktop-shortcut behavior on Windows without Python.

## شرط الانتقال | Exit gate
نجاح الاختبارات الآلية وبناء المثبت لا يكفي؛ يلزم تسجيل تجربة نموذج حقيقي على الجهاز الآخر برقم البناء ونتائج الأداء. بعدها نجهز تفعيل المشاركة من داخل الواجهة وتجربة مزود واحد قبل multi-node. البحث عبر الويب يبقى غير مفعل حتى اكتمال حماية الوجهات واختيار المستخدم.
Unit tests and installer CI alone are insufficient. Record real second-device inference with build ID and performance results. Then implement in-app sharing enrollment and a one-provider trial before multi-node. Keep web research disconnected until destination protection and user opt-in are complete.
