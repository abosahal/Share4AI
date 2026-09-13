# تجربة Windows | Windows trial

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

**[تنزيل ملف التثبيت](https://github.com/abosahal/Share4AI/releases/download/windows-preview-1-1/Share4AI-Setup-1.1.0-windows-x64.exe)**

نزّل **Share4AI-Setup-1.1.0-windows-x64.exe** وافتحه ثم اضغط **تثبيت**. افتح Share4AI من الاختصار بعد الانتهاء. لا تحتاج Python أو الطرفية أو فك ضغط ملفات. لا تبدأ بتنزيل نموذج إذا لم يوصِ التطبيق بنموذج مناسب لجهازك. المثبت التجريبي غير موقع رقميًا، وقد يظهر تحذير ناشر غير معروف؛ لا تعطّل حماية Windows.

1. تأكد أن الواجهة تبدأ بالعربية، وأن النصوص والأزرار كاملة عند حجم نافذة صغير. مرّر صفحة الإعداد عند الحاجة.
2. اضغط English ثم العربية. اكتب مسودة في المحادثة وبدّل اللغة: يجب بقاء المسودة. أغلق التطبيق وافتحه وتأكد من حفظ اللغة المختارة. لا تُحفظ المحادثة بعد الإغلاق.
3. افحص الجهاز، ثم نزّل النموذج وتحقق من ظهور نسبة التقدم. اختبر الإلغاء وإعادة المحاولة؛ تبدأ المحاولة الجديدة التنزيل من البداية.
4. شغّل الذكاء المحلي. جرّب: «اشرح لطفل كيف يتكون المطر»، ثم «وش الفرق بين الذاكرة والتخزين؟»، ثم نصًا مختلطًا مثل «لدي GPU بذاكرة 8 GB». افحص اتصال الحروف وترتيب الأرقام والأقواس ومكان مؤشر الكتابة والنسخ واللصق. سجّل جودة الإجابات منفصلة عن سرعة الأداء.
5. شغّل اختبار الأداء وسجّل الزمن لأول رمز والرموز في الثانية. النجاح في الاختبار لا يكفي وحده لإتاحة المشاركة؛ يلزم اعتماد مزود وقياسات موارد مناسبة.
6. اختبار المشاركة حاليًا داخلي للمطورين وفق [دليل المهام المحلية](PILOT_JOBS.md). لن نطلب منك تشغيل خادم أو إدخال أوامر. التسجيل المبسط بخدمة المشاركة العامة لم يكتمل بعد.

أرسل إصدار Windows، ونوع GPU وحجم الذاكرة، والخطوة التي فشلت، ورسالة الخطأ، ولقطة للشاشة إن كانت المشكلة بصرية. لا تُرفق رموز الاعتماد أو محادثات خاصة. إذا تعذر فتح التطبيق، أعد تثبيته من ملف التنزيل؛ لا تثبّت أدوات تطوير لإصلاحه. للإزالة افتح إعدادات Windows ثم التطبيقات واختر Share4AI. تبقى النماذج والإعدادات محفوظة لإعادة الاستخدام.

التحقق الآلي لا يغني عن هذه التجربة. عرض RTL الكامل وتشغيل Qwen على GPU لم يُعتمدا بعد. اترك طلب المراجعة مسودة حتى اكتمال التحقق.

<a id="en"></a>

## English

**[Download the installer](https://github.com/abosahal/Share4AI/releases/download/windows-preview-1-1/Share4AI-Setup-1.1.0-windows-x64.exe)**

Download **Share4AI-Setup-1.1.0-windows-x64.exe**, open it and select **Install**, then open Share4AI from its shortcut. No Python, terminal or archive extraction is required. Do not download a model unless the app recommends one for your device. The trial installer is unsigned and Windows may show an unknown-publisher warning; do not disable Windows protection.

1. Confirm Arabic is the default and text/buttons remain visible in a smaller window. Scroll the setup page when needed.
2. Switch to English and back to Arabic. Type a chat draft and switch languages: the draft must remain. Close and reopen the app to confirm the selected language persists. Conversation content is not retained after closing.
3. Scan, download the model and check percentage progress. Test cancellation and retry; retry starts the download again from the beginning.
4. Start Local AI. Try Arabic explanations, a common dialect question and mixed Arabic/English text with numbers, such as GPU and 8 GB. Inspect shaping, number/bracket order, caret movement and copy/paste. Record answer quality separately from speed.
5. Run the benchmark and record time to first token and tokens per second. A passing benchmark alone does not enable sharing; provider credentials and suitable resource telemetry are also required.
6. Sharing tests are currently internal developer work under the [local job guide](PILOT_JOBS.md). Users are not asked to run servers or commands. Simple public sharing enrollment remains incomplete.

Report the Windows version, GPU and memory, failed step, error message and a screenshot for visual issues. Do not include credentials or private conversations. If startup fails, reinstall using the downloaded installer; do not install development tools to repair it. Uninstall through Windows Settings → Apps → Share4AI. Models and preferences are retained for reuse.

Automated checks do not replace this trial. Full RTL rendering and Qwen GPU inference are not yet validated. Keep the pull request in draft until validation is complete.
