## العربية

الإصدار 1.1.2 يضيف خيار «إنشاء اختصار على سطح المكتب» أثناء التثبيت، محددًا افتراضيًا في التثبيت الجديد. يمكنك إلغاء تحديده؛ يظل التطبيق متاحًا في قائمة ابدأ. إلغاء الاختيار لا يحذف اختصارًا موجودًا من تثبيت سابق.

إصلاح 1.1.1: يعرض التطبيق سبب منع التنزيل بدقة، ويفصل إجمالي الذاكرة عن المتاح والمطلوب ومساحة القرص. يُعطل زر التنزيل عندما لا يوجد نموذج مناسب، ويعيد تفعيله بعد فحص ناجح. لا يغير هذا الإصلاح شروط تشغيل النماذج: جهاز بذاكرة إجمالية 7.8 GB دون بطاقة رسوميات مدعومة ما زال أقل من شرط هذه النسخة. فُصلت الأرقام عن النص العربي لتحسين العرض.

نزّل ملف Share4AI-Setup-1.1.2-windows-x64.exe وافتحه ثم اضغط تثبيت. بعد الانتهاء افتح Share4AI من الاختصار. لا تحتاج Python أو الطرفية. يختار التطبيق نموذجًا مناسبًا وينزله بعد موافقتك.

هذه نسخة تجريبية غير موقعة رقميًا؛ قد يعرض Windows تحذير ناشر غير معروف. لا نطلب تعطيل حماية Windows. اختُبر فتح الواجهة المجمّعة وتبديل اللغة آليًا؛ جودة عرض العربية والتشغيل الفعلي للنموذج على GPU والتجربة على Windows نظيف دون Python ما زالت تحتاج تحققًا. تفعيل المشاركة مع خدمة عامة من داخل التطبيق لم يكتمل؛ أدوات تجربة الشبكة الحالية داخلية للمطورين فقط.

## English

Version 1.1.2 adds a “Create a desktop shortcut” installer option, selected by default on fresh installs. You can uncheck it; the app remains available in Start. Unchecking does not delete a shortcut from a previous installation.

Fix 1.1.1: download blockers now distinguish total/free RAM and disk space, with separate available/required readings. Download is disabled without a suitable model and re-enabled after a successful scan. Model admission thresholds are unchanged: a 7.8 GB machine without a supported GPU remains below this version's requirement. Numeric values are separated from Arabic labels for clearer rendering.

Download Share4AI-Setup-1.1.2-windows-x64.exe, open it and select Install. Then open Share4AI from its shortcut. No Python or terminal is required. The app selects a suitable model and downloads it after your confirmation.

This trial is not digitally signed; Windows may show an unknown-publisher warning. Do not disable Windows protection. Packaged UI startup and language switching are automatically checked. Arabic rendering quality, real GPU model inference and a clean Windows machine without Python still need validation. In-app enrollment into a public sharing service is not complete; current network pilot tools are internal developer tools only.
