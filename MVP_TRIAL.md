# تجربة MVP الأولى | First MVP trial

## العربية
هذه الدفعة تضيف محادثة المستخدم في المتصفح فوق مسار المشاركة الحقيقي داخل تطبيق المزود. الاستضافة مؤجلة بناءً على قرار المستخدم؛ التجربة الحالية على جهاز واحد ولا تفتح منفذًا للشبكة العامة.

1. ثبّت النسخة 1.1.4 وافتح التطبيق.
2. شغّل الذكاء المحلي ثم اختبر الأداء. يلزم نجاح الاختبار للمشاركة.
3. اضغط **تجربة محادثة المستخدم على هذا الجهاز**. يفتح المتصفح تلقائيًا دون كتابة أوامر أو نسخ مفاتيح.
4. انتظر «جاهز للمحادثة»، واكتب رسالتك. يظهر الرد تدريجيًا. يمكنك الإيقاف أو بدء محادثة جديدة أو تبديل اللغة.
5. إيقاف المشاركة يوقف استقبال الطلبات. **إلغاء / إيقاف الذكاء** أو إغلاق التطبيق ينهي جلسة التجربة. لتجربة جديدة شغّل النموذج واختبر الأداء مجددًا.
6. إذا أعدت تحميل صفحة المتصفح، افتح التجربة من زر التطبيق مجددًا؛ رمز الوصول مؤقت ولا يُحفظ في المتصفح.

لا يعرض العميل أسماء العقد أو بصمة النموذج أو رموز الوصول. المحادثة في ذاكرة الصفحة فقط؛ الخدمة تمحو محتوى الطلب عند انتهائه وتمحو أحداثه عند إغلاق الاتصال. لا يوجد حساب أو سجل دائم في هذه الدفعة.

### التحقق
نجح 52 اختبارًا، منها وصول الرد عبر HTTP من واجهة العميل إلى العامل داخل تطبيق المزود، واختيار النموذج دون إدخال البصمة، ورفض أصل/مضيف غير مسموح، وفصل صلاحيات المزود والعميل، وتنظيف الجلسة، وتمرير طبقات GPU. نجح فحص JavaScript وتجربة الرد العربي والتبديل للإنجليزية في متصفح فعلي باستخدام نموذج محاكى. لا يمثل ذلك قياس سرعة أو جودة نموذج حقيقي.

### الدفعة التالية
بعد نجاح التجربة على جهاز المزود الحقيقي: تجهيز خدمة HTTPS مستضافة، وتفعيل المزود داخل التطبيق، ورابط عميل يعمل من جهاز آخر. يلزم تخزين هوية وصلاحيات دائم ومراقبة جاهزية الخدمة. يبقى خادم التجربة الحالي مقيدًا بالجهاز؛ لا تنشره كما هو على الإنترنت.

## English
This slice adds browser chat over the provider app's actual job-sharing path. Hosting is deferred by user choice. The current trial runs on one computer and exposes no public network listener.

1. Install version 1.1.4 and open the app.
2. Start Local AI and pass the benchmark.
3. Select **Try customer chat on this computer**. The browser opens automatically; no commands or copied credentials.
4. Wait for “Ready to chat” and send a message. Replies stream progressively; Stop, New chat and language switching are available.
5. Stop Sharing stops new jobs. Cancel / Stop AI or closing the app ends the trial session. Restart the model and rerun the benchmark for a new session.
6. After a browser refresh, reopen the trial through the app button; the temporary credential is not stored in the browser.

The customer never enters node names, model hashes or credentials. Chat stays in page memory. The broker clears prompts when jobs terminate and removes events when the consuming connection ends. Accounts and durable history are outside this slice.

### Validation
52 tests passed, including HTTP customer-to-provider streaming, automatic model selection, origin/host rejection, provider/client authorization separation, session cleanup and GPU-layer forwarding. JavaScript syntax and Arabic reply/language switching passed in a real browser using a simulated runtime. This is not evidence of real-model speed or quality.

### Next slice
After a successful real-provider trial: hosted HTTPS service, in-app provider enrollment and a customer link usable from another device, with durable identity/credentials and service readiness monitoring. The current broker remains loopback-only and must not be deployed publicly as-is.

