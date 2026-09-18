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
Settings|الإعدادات'''
TEXT = dict(line.split('|', 1) for line in _ROWS.splitlines())
