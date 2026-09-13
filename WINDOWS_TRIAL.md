# تجربة Windows | Windows trial

[العربية](#ar) | [English](#en)

<a id="ar"></a>

## العربية

هذه حزمة مصدر تجريبية تحتاج Python 3.11 أو أحدث مع Tcl/Tk. ليست مثبتًا مستقلًا. فك الضغط في مجلد تملكه ثم افتح `run_windows.bat`. لا تبدأ بتنزيل نموذج إذا لم يوصِ التطبيق بنموذج مناسب لجهازك.

1. تأكد أن الواجهة تبدأ بالعربية، وأن النصوص والأزرار كاملة عند حجم نافذة صغير. مرّر صفحة الإعداد عند الحاجة.
2. اضغط English ثم العربية. اكتب مسودة في المحادثة وبدّل اللغة: يجب بقاء المسودة. أغلق التطبيق وافتحه وتأكد من حفظ اللغة المختارة. لا تُحفظ المحادثة بعد الإغلاق.
3. افحص الجهاز، ثم نزّل النموذج وتحقق من ظهور نسبة التقدم. اختبر الإلغاء وإعادة المحاولة؛ تبدأ المحاولة الجديدة التنزيل من البداية.
4. شغّل الذكاء المحلي. جرّب: «اشرح لطفل كيف يتكون المطر»، ثم «وش الفرق بين الذاكرة والتخزين؟»، ثم نصًا مختلطًا مثل «لدي GPU بذاكرة 8 GB». افحص اتصال الحروف وترتيب الأرقام والأقواس ومكان مؤشر الكتابة والنسخ واللصق. سجّل جودة الإجابات منفصلة عن سرعة الأداء.
5. شغّل اختبار الأداء وسجّل الزمن لأول رمز والرموز في الثانية. النجاح في الاختبار لا يكفي وحده لإتاحة المشاركة؛ يلزم اعتماد مزود وقياسات موارد مناسبة.
6. لاختبار المشاركة، اتبع [دليل المهام المحلية](PILOT_JOBS.md). ابدأ مهمة ثم أوقف المشاركة وتحقق من توقفها. استخدام المحادثة المحلية يجب أن يوقف المشاركة أولًا.

أرسل إصدار Windows، ونوع GPU وحجم الذاكرة، والخطوة التي فشلت، ورسالة الخطأ، ولقطة للشاشة إن كانت المشكلة بصرية. لا تُرفق رموز الاعتماد أو محادثات خاصة. إذا ظهر خطأ `init.tcl`، أصلح تثبيت Python مع Tcl/Tk وأعد التشغيل.

التحقق الآلي لا يغني عن هذه التجربة. عرض RTL الكامل وتشغيل Qwen على GPU لم يُعتمدا بعد. اترك طلب المراجعة مسودة حتى اكتمال التحقق.

<a id="en"></a>

## English

This source trial package requires Python 3.11 or later with Tcl/Tk. It is not a standalone installer. Extract it to a folder you own and open `run_windows.bat`. Do not download a model unless the app recommends one for your device.

1. Confirm Arabic is the default and text/buttons remain visible in a smaller window. Scroll the setup page when needed.
2. Switch to English and back to Arabic. Type a chat draft and switch languages: the draft must remain. Close and reopen the app to confirm the selected language persists. Conversation content is not retained after closing.
3. Scan, download the model and check percentage progress. Test cancellation and retry; retry starts the download again from the beginning.
4. Start Local AI. Try Arabic explanations, a common dialect question and mixed Arabic/English text with numbers, such as GPU and 8 GB. Inspect shaping, number/bracket order, caret movement and copy/paste. Record answer quality separately from speed.
5. Run the benchmark and record time to first token and tokens per second. A passing benchmark alone does not enable sharing; provider credentials and suitable resource telemetry are also required.
6. Follow the [local job guide](PILOT_JOBS.md) to test sharing. Start a task, stop sharing and confirm cancellation. Starting a local conversation must stop sharing first.

Report the Windows version, GPU and memory, failed step, error message and a screenshot for visual issues. Do not include credentials or private conversations. For an `init.tcl` error, repair the Python installation with Tcl/Tk and retry.

Automated checks do not replace this trial. Full RTL rendering and Qwen GPU inference are not yet validated. Keep the pull request in draft until validation is complete.
