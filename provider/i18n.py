"""Arabic/English presentation only; never apply to chat content or wire payloads."""
import re
import argparse
import sys

# English source | Arabic translation. Runtime identifiers remain unchanged.
_ROWS = '''Share4AI Provider 1.1 — Community-powered AI|Share4AI Provider 1.1 — ذكاء اصطناعي يدعمه المجتمع
Share4AI  /  Community-powered AI|Share4AI / ذكاء اصطناعي يدعمه المجتمع
Windows pilot • Local AI first • Authenticated outbound sharing|تجربة Windows • أولوية للذكاء المحلي • مشاركة صادرة موثقة
Device & Setup|الجهاز والإعداد
Local AI|الذكاء الاصطناعي المحلي
Settings|الإعدادات
Scan your device to find a suitable model.|افحص جهازك للعثور على نموذج مناسب.
No recommendation yet|لا توجد توصية بعد
Ready to scan|جاهز للفحص
OFFLINE|غير متصل
AVAILABLE|متاح
LIMITED|المشاركة مقيدة
BUSY|مشغول
CONTROL PLANE OFFLINE|خادم التحكم غير متصل
1. Scan|1. فحص الجهاز
2. Download & Verify|2. تنزيل وتحقق
3. Start Local AI|3. تشغيل الذكاء المحلي
4. Benchmark|4. اختبار الأداء
Sharing connection|اتصال المشاركة
Start Sharing|بدء المشاركة
Stop Sharing|إيقاف المشاركة
Send|إرسال
Clear conversation|مسح المحادثة
Local conversation stays in memory and is not saved to history.|تبقى المحادثة المحلية في الذاكرة ولا تُحفظ في السجل.
Control Plane address|عنوان خادم التحكم
Max GPU Usage (%)|الحد الأعلى لاستخدام معالج الرسوميات (%)
Enter a whole number from 0 to 100|أدخل عددًا صحيحًا من 0 إلى 100
Save Settings|حفظ الإعدادات
Cancel / Stop AI|إلغاء / إيقاف الذكاء
No supported NVIDIA GPU|لا يوجد معالج رسوميات NVIDIA مدعوم
No suitable model|لا يوجد نموذج مناسب
You:|أنت:
AI:|الذكاء الاصطناعي:
Operation failed; check device and settings, then retry|فشلت العملية؛ تحقق من الجهاز والإعدادات ثم أعد المحاولة
Install first|ثبّت النموذج ومحرك التشغيل أولًا
Local AI ready|الذكاء الاصطناعي المحلي جاهز
Verifying installed files|جارٍ التحقق من الملفات المثبتة
Start cancelled|أُلغي التشغيل
Starting local model|جارٍ تشغيل النموذج المحلي
Local AI ready — benchmark required for sharing|الذكاء المحلي جاهز — يلزم اختبار الأداء للمشاركة
Benchmark: warmup + three Arabic/English samples|اختبار الأداء: تهيئة ثم ثلاث عينات بالعربية والإنجليزية
Job worker not running|مُنفّذ المهام لا يعمل
Start Local AI and pass benchmark before sharing|شغّل الذكاء المحلي واجتز اختبار الأداء قبل المشاركة
Sharing started; jobs run only while device is eligible|بدأت المشاركة؛ تُنفّذ المهام فقط عندما يستوفي الجهاز الشروط
Settings saved; sharing stopped|حُفظت الإعدادات وأُوقفت المشاركة
Stopped|تم الإيقاف
Invalid maximum|الحد الأعلى غير صالح
This alpha supports Windows x64 only|هذه النسخة الأولية تدعم Windows x64 فقط
Fits available memory with reserve; benchmark still required|يناسب الذاكرة المتاحة مع احتياطي؛ ما زال اختبار الأداء مطلوبًا
CPU local trial; network sharing requires GPU telemetry and benchmark|تجربة محلية بالمعالج المركزي؛ المشاركة تتطلب قياسات معالج الرسوميات واختبار الأداء
Not enough free memory or disk; close other workloads and scan again|الذاكرة أو مساحة القرص المتاحة غير كافية؛ أغلق البرامج الأخرى وأعد الفحص
Downloading and verifying runtime|جارٍ تنزيل محرك التشغيل والتحقق منه
Installed and SHA256 verified|اكتمل التثبيت والتحقق من SHA256
No suitable model recommended|لم يُوصَ بنموذج مناسب
Install cancelled|أُلغي التثبيت
Install cancelled before activation|أُلغي التثبيت قبل التفعيل
Invalid installed path|مسار التثبيت غير صالح
Installed manifest is not in the approved catalog|بيان التثبيت غير موجود في الكتالوج المعتمد
Installed model was modified; reinstall|عُدّل النموذج المثبت؛ أعد التثبيت
Runtime inventory missing executable|ملف التشغيل غير موجود في سجل ملفات المحرك
Runtime directory contents changed; reinstall|تغيّرت محتويات مجلد المحرك؛ أعد التثبيت
Installed runtime was modified; reinstall|عُدّل محرك التشغيل المثبت؛ أعد التثبيت
Untrusted artifact URL|رابط ملف التنزيل غير موثوق
Unsupported required signature|التوقيع المطلوب غير مدعوم
Signature verification failed|فشل التحقق من التوقيع
Invalid artifact metadata|بيانات ملف التنزيل غير صالحة
Insufficient disk space|مساحة القرص غير كافية
Download cancelled; retry is safe|أُلغي التنزيل؛ يمكن إعادة المحاولة بأمان
Artifact exceeds expected size|يتجاوز الملف الحجم المتوقع
SHA256 or size mismatch; artifact not activated|عدم تطابق SHA256 أو الحجم؛ لم يُفعّل الملف
Runtime destination must be new|يجب أن تكون وجهة محرك التشغيل جديدة
Unsafe runtime archive path|مسار غير آمن داخل أرشيف المحرك
Duplicate runtime archive path|مسار مكرر داخل أرشيف المحرك
Runtime archive exceeds extraction limit|يتجاوز أرشيف المحرك حد فك الضغط
Insufficient extraction space|المساحة غير كافية لفك الضغط
Expected one llama-server.exe|يجب وجود ملف llama-server.exe واحد
Ambiguous runtime dependency|ملفات اعتماد محرك التشغيل ملتبسة
Benchmark requires content and actual runtime token usage|يتطلب اختبار الأداء نصًا وقياس عدد الرموز الفعلي من المحرك
Invalid benchmark timing|توقيت اختبار الأداء غير صالح
Control Plane redirects are not allowed|إعادة التوجيه من خادم التحكم غير مسموحة
Invalid Control Plane address|عنوان خادم التحكم غير صالح
HTTP is allowed only for local development|يُسمح بـHTTP للتطوير المحلي فقط
A provider credential is required for remote registration|يلزم اعتماد مزود للتسجيل عن بُعد
Control Plane response too large|استجابة خادم التحكم أكبر من الحد
Invalid registration acknowledgment|تأكيد التسجيل غير صالح
Control Plane rejected request|رفض خادم التحكم الطلب
Control Plane unavailable|خادم التحكم غير متاح
Max GPU Usage must be an integer from 0 to 100|يجب أن يكون حد استخدام معالج الرسوميات عددًا صحيحًا من 0 إلى 100
Runtime not ready|محرك التشغيل غير جاهز
Local AI has priority|الأولوية للذكاء الاصطناعي المحلي
Benchmark has not passed|لم يجتز الجهاز اختبار الأداء
Owner limit is zero|الحد الذي حدده صاحب الجهاز يساوي صفرًا
GPU telemetry unavailable|قياسات معالج الرسوميات غير متاحة
Invalid GPU telemetry|قياسات معالج الرسوميات غير صالحة
Owner resource limit reached|تم بلوغ حد الموارد الذي حدده صاحب الجهاز
Resource checks passed|اجتاز الجهاز فحص الموارد
RAM telemetry unavailable|قياسات ذاكرة RAM غير متاحة
NVIDIA telemetry unavailable|قياسات NVIDIA غير متاحة
No supported NVIDIA telemetry; CPU local mode only|لا تتوفر قياسات NVIDIA مدعومة؛ الوضع المحلي بالمعالج المركزي فقط
Invalid output limit|حد المخرجات غير صالح
Invalid messages|الرسائل غير صالحة
Text messages only|الرسائل النصية فقط
Context limit exceeded|تم تجاوز حد السياق
Missing job authorization|تفويض المهمة مفقود
Invalid job authorization|تفويض المهمة غير صالح
Invalid job schema|بنية المهمة غير صالحة
Job audience or model mismatch|المزود المستهدف أو النموذج لا يطابق المهمة
Expired or invalid job deadline|انتهت مهلة المهمة أو أنها غير صالحة
Invalid job identity|هوية المهمة غير صالحة
Provider credential required for jobs|يلزم اعتماد مزود لتنفيذ المهام
Replayed job|مهمة مكررة مرفوضة
Job cancelled|أُلغيت المهمة
Runtime event too large|حدث محرك التشغيل أكبر من الحد
Runtime stream interrupted|انقطع البث من محرك التشغيل
Runtime rejected request|رفض محرك التشغيل الطلب
Runtime start cancelled|أُلغي بدء محرك التشغيل
Invalid context size|حجم السياق غير صالح
Runtime already started; stop before changing model|المحرك يعمل بالفعل؛ أوقفه قبل تغيير النموذج
Install runtime and model first|ثبّت المحرك والنموذج أولًا
Runtime exited; check compatible hardware and runtime package|توقف المحرك؛ تحقق من توافق العتاد وحزمة التشغيل
Runtime startup timed out|انتهت مهلة بدء محرك التشغيل
Invalid inference limits|حدود الاستدلال غير صالحة
Only text messages are supported|الرسائل النصية فقط مدعومة
Conversation too long; start a new chat|المحادثة طويلة جدًا؛ ابدأ محادثة جديدة
Runtime busy|محرك التشغيل مشغول
Inference cancelled or timed out|أُلغي الاستدلال أو انتهت مهلته
Runtime connection failed|فشل الاتصال بمحرك التشغيل
Share4AI Provider|مزود Share4AI
Read-only hardware report|تقرير العتاد للقراءة فقط
Share4AI pilot client|عميل Share4AI التجريبي
Set SHARE4AI_CLIENT_TOKEN in this terminal|عيّن SHARE4AI_CLIENT_TOKEN في هذه الطرفية
Install a model first or provide --model-sha256|ثبّت نموذجًا أولًا أو مرّر --model-sha256
Your message:|رسالتك:
Request stopped. Retry after checking provider readiness.|توقف الطلب. أعد المحاولة بعد التحقق من جاهزية المزود.
Connection interrupted; response is incomplete.|انقطع الاتصال؛ الاستجابة غير مكتملة.
Request interrupted.|انقطع الطلب.
Provider token is required|رمز اعتماد المزود مطلوب
Exact model SHA256 required|يلزم SHA256 مطابق تمامًا للنموذج
No eligible provider for this model|لا يوجد مزود مستوفٍ للشروط لهذا النموذج
Provider busy; retry later|المزود مشغول؛ أعد المحاولة لاحقًا
Two distinct nonempty credentials are required|يلزم اعتمادان مختلفان وغير فارغين
Share4AI local protocol fixture: http://127.0.0.1:8000 (no jobs, no persistence)|خادم اختبار بروتوكول Share4AI المحلي: http://127.0.0.1:8000 (بلا مهام أو تخزين دائم)
Share4AI authenticated local pilot on 127.0.0.1:8000; one trusted provider; memory only|تجربة Share4AI المحلية الموثقة على 127.0.0.1:8000؛ مزود موثوق واحد؛ تخزين في الذاكرة فقط'''
TEXT = dict(line.split('|', 1) for line in _ROWS.splitlines())
TEXT.update({
    'Sharing activation is not available in this trial. You can use Local AI.': 'تفعيل المشاركة غير متاح في هذه التجربة. يمكنك استخدام الذكاء المحلي.',
    'Advanced settings (internal testing)': 'إعدادات متقدمة (للاختبار الداخلي)',
    'Sharing pauses when resource usage or temperature is high. This setting does not impose a hard GPU limit. Public sharing activation is coming later.': 'تُعلّق المشاركة عند ارتفاع استخدام الموارد أو الحرارة. هذا الإعداد لا يفرض سقفًا صارمًا على معالج الرسوميات. تفعيل المشاركة العامة سيُتاح لاحقًا.',
    'Unsupported language': 'اللغة غير مدعومة',
    'Scan, download, start, then test performance.': 'افحص الجهاز، ثم نزّل النموذج وشغّله واختبر الأداء.',
    'Could not save language; check folder access.': 'تعذر حفظ اللغة؛ تحقق من صلاحية الوصول إلى المجلد.',
    'Download complete. Start Local AI, then test performance.': 'اكتمل التنزيل. شغّل الذكاء المحلي ثم اختبر الأداء.',
    'Local AI is ready. Test performance before sharing.': 'الذكاء المحلي جاهز. اختبر الأداء قبل المشاركة.',
    'Stopped. Start Local AI when you are ready.': 'تم الإيقاف. شغّل الذكاء المحلي عندما تكون جاهزًا.',
    'Model selected. Download and verify its files.': 'تم اختيار النموذج. نزّل ملفاته وتحقق منها.',
    'Free memory or disk space, then scan again.': 'وفّر ذاكرة أو مساحة على القرص، ثم أعد الفحص.',
    'Performance passed. Use Local AI or configure sharing.': 'اجتاز الجهاز اختبار الأداء. استخدم الذكاء المحلي أو اضبط المشاركة.',
    'Use Local AI. Performance is below the sharing target.': 'يمكنك استخدام الذكاء المحلي. الأداء أقل من متطلبات المشاركة.',
    'Downloads: Qwen 4B ≈ 2.7 GB / 9B ≈ 5.7 GB plus runtime.\nModels use published SHA256 checks. Retry restarts an interrupted download.':
        'التنزيلات: Qwen 4B نحو 2.7 GB / 9B نحو 5.7 GB إضافةً إلى المحرك.\nيُتحقق من النماذج باستخدام SHA256 المنشور. تبدأ إعادة المحاولة التنزيل المنقطع من جديد.',
    'Sharing requires a passing benchmark and a provider credential. Stop Sharing cancels the current network job. Local AI stops sharing first.':
        'تتطلب المشاركة اجتياز اختبار الأداء واعتماد مزود. إيقاف المشاركة يلغي المهمة الشبكية الحالية. استخدام الذكاء المحلي يوقف المشاركة أولًا.',
    'Operational sharing threshold, not a hard GPU utilization cap.\nHigh usage, heat or missing telemetry prevents availability.\nRemote registration requires HTTPS and SHARE4AI_PROVIDER_TOKEN.':
        'عتبة تشغيل للمشاركة وليست سقفًا صارمًا لاستخدام معالج الرسوميات.\nارتفاع الاستخدام أو الحرارة أو غياب القياسات يمنع إتاحة الجهاز.\nيتطلب التسجيل عن بُعد HTTPS وSHARE4AI_PROVIDER_TOKEN.',
    'Runtime {percent}%': 'محرك التشغيل {percent}%',
    'Model {percent}%': 'النموذج {percent}%',
    'Downloading and verifying {model}': 'جارٍ تنزيل {model} والتحقق منه',
    'Detected display: {names}': 'معالج العرض المكتشف: {names}',
    'RAM {ram} GB • Available {available} GB • Free disk {disk} GB': 'ذاكرة RAM ‏{ram} GB • المتاح {available} GB • مساحة القرص الحرة {disk} GB',
    'Benchmark PASSED • Worst TTFT {ttft}s • Slowest {speed} tokens/s': 'اجتاز اختبار الأداء • أطول زمن لأول رمز {ttft} ثانية • أبطأ سرعة {speed} رمز/ثانية',
    'Benchmark below sharing target • Worst TTFT {ttft}s • Slowest {speed} tokens/s': 'الأداء أقل من هدف المشاركة • أطول زمن لأول رمز {ttft} ثانية • أبطأ سرعة {speed} رمز/ثانية',
    'Request rejected ({code}). Check credentials, model and provider availability.': 'رُفض الطلب ({code}). تحقق من الاعتمادات والنموذج وتوفر المزود.',
})


def tr(source, language='both', **values):
    """Translate a known presentation template, retaining its English source."""
    if language == 'en':
        return source.format(**values)
    if language == 'ar':
        return TEXT[source].format(**values)
    return TEXT[source].format(**values) + ' | ' + source.format(**values)


def display_message(source, language='both'):
    """Render owned diagnostic text. Unknown text passes through unchanged."""
    if source in TEXT:
        return tr(source, language=language)
    for label in ('Runtime', 'Model'):
        match = re.fullmatch(label + r' (\d+)%', source)
        if match:
            return tr(label + ' {percent}%', language=language, percent=match[1])
    for prefix, template, key in (
        ('Downloading and verifying ', 'Downloading and verifying {model}', 'model'),
        ('Detected display: ', 'Detected display: {names}', 'names'),
    ):
        if source.startswith(prefix):
            return tr(template, language=language, **{key: source[len(prefix):]})
    return source


class BilingualParser(argparse.ArgumentParser):
    """Bilingual CLI chrome without changing option names or parsed values."""
    def __init__(self, *args, **kwargs):
        kwargs['add_help'] = False
        kwargs.setdefault('usage', '%(prog)s [خيارات / options]')
        super().__init__(*args, **kwargs)
        self._positionals.title = 'المعاملات / positional arguments'
        self._optionals.title = 'الخيارات / options'
        self.add_argument('-h', '--help', action='help', help='عرض المساعدة والخروج / show help and exit')

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f'{self.prog}: خطأ في المدخلات / input error: {display_message(message)}\n')
