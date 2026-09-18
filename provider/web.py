"""Outbound HTTPS lookup used by local chat. The model weights stay offline."""
from datetime import datetime
from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
import xml.etree.ElementTree as ET
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = 'Share4AI-Provider/1.1 (local research)'
MAX_BODY = 400_000
TIMEOUT = 8
ARABIC_DAYS = ('الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد')
ARABIC_MONTHS = ('يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر')


class WebError(RuntimeError):
    pass


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'noscript'):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'noscript') and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            text = ' '.join(data.split())
            if text:
                self.parts.append(text)


def _opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _public_https(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise WebError('Untrusted artifact URL')
    if parsed.port not in (None, 443):
        raise WebError('Untrusted artifact URL')
    host = parsed.hostname
    if host.lower() in ('localhost', 'localhost.localdomain'):
        raise WebError('Untrusted artifact URL')
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as error:
        raise WebError('Control Plane unavailable') from error
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise WebError('Untrusted artifact URL')
    return parsed.geturl()


def _get(url, accept='application/json'):
    safe = _public_https(url)
    req = urllib.request.Request(safe, headers={'User-Agent': USER_AGENT, 'Accept': accept})
    try:
        with _opener().open(req, timeout=TIMEOUT) as response:
            data = response.read(MAX_BODY + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise WebError('Control Plane unavailable') from error
    if len(data) > MAX_BODY:
        raise WebError('Control Plane response too large')
    return data


NEWS_RE = re.compile(
    r'(أخبار|اخبار|خبر|عاجل|صحافة|ابحث|news|latest|headline|breaking|search)',
    re.I,
)


def _clean_query(query):
    query = ' '.join((query or '').split())
    query = re.sub(
        r'^(?:please\s+)?(?:ابحث(?:ي)?(?:\s+عن)?|search(?:\s+for)?|find|look up)\s+',
        '',
        query,
        flags=re.I,
    )
    return query[:200]


def _wikipedia_lang(text):
    return 'ar' if re.search(r'[\u0600-\u06FF]', text or '') else 'en'


def search_news(query, opener=None):
    query = _clean_query(query)
    if len(query) < 2:
        return []
    lang = _wikipedia_lang(query)
    hl, gl, ceid = ('ar', 'SA', 'SA:ar') if lang == 'ar' else ('en', 'US', 'US:en')
    url = (
        'https://news.google.com/rss/search?q=' + urllib.parse.quote(query)
        + f'&hl={hl}&gl={gl}&ceid={ceid}'
    )
    try:
        raw = _get(url, accept='application/rss+xml,application/xml,text/xml') if opener is None else opener(url)
        root = ET.fromstring(raw)
    except (WebError, ValueError, OSError, ET.ParseError):
        return []
    results = []
    for item in root.iter('item'):
        title = ' '.join((item.findtext('title') or '').split())
        link = (item.findtext('link') or '').strip()
        source = ' '.join((item.findtext('source') or '').split())
        published = ' '.join((item.findtext('pubDate') or '').split())
        if not title:
            continue
        snippet = ' — '.join(part for part in (source, published) if part)[:280]
        results.append({'title': title, 'url': link, 'snippet': snippet})
        if len(results) >= 6:
            break
    return results


def search_web(query, opener=None):
    query = _clean_query(query)
    if len(query) < 2:
        return []
    results = []
    if NEWS_RE.search(query):
        results.extend(search_news(query, opener=opener))
        if results:
            return results[:6]
    lang = _wikipedia_lang(query)
    encoded = urllib.parse.quote(query)
    wiki = (
        f'https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}'
        '&srlimit=3&format=json&utf8=1'
    )
    try:
        raw = _get(wiki) if opener is None else opener(wiki)
        payload = json.loads(raw.decode('utf-8', errors='replace'))
    except (WebError, ValueError, OSError):
        payload = {}
    for item in payload.get('query', {}).get('search', [])[:3]:
        title = item.get('title') or ''
        snippet = re.sub(r'<[^>]+>', '', item.get('snippet') or '')
        if title:
            results.append({
                'title': title,
                'url': f'https://{lang}.wikipedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_')),
                'snippet': ' '.join(snippet.split())[:280],
            })
    ddg = f'https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&no_redirect=1&skip_disambig=1'
    try:
        raw = _get(ddg) if opener is None else opener(ddg)
        instant = json.loads(raw.decode('utf-8', errors='replace'))
    except (WebError, ValueError, OSError):
        instant = {}
    abstract = (instant.get('AbstractText') or '')[:400]
    source = instant.get('AbstractURL') or ''
    if abstract:
        results.insert(0, {'title': instant.get('Heading') or query, 'url': source, 'snippet': abstract})
    return results[:6]



def fetch_page(url, opener=None):
    raw = _get(url, accept='text/html,application/xhtml+xml') if opener is None else opener(url)
    parser = _TextExtractor()
    parser.feed(raw.decode('utf-8', errors='replace'))
    return ' '.join(parser.parts)[:2500]


def clock_context(now=None):
    now = now or datetime.now().astimezone()
    iso = now.strftime('%Y-%m-%d')
    clock = now.strftime('%H:%M')
    offset = now.strftime('%z')
    weekday_en = now.strftime('%A')
    weekday_ar = ARABIC_DAYS[now.weekday()]
    month_ar = ARABIC_MONTHS[now.month - 1]
    return (
        f'The current local date and time is {weekday_en} {iso} {clock} (UTC{offset}). '
        f'Today is {iso}. For "today", "now", or the current date, use this clock. '
        f'Do not use a training-cutoff date. '
        f'اليوم هو {weekday_ar} {now.day} {month_ar} {now.year}، الساعة {clock}.'
    )


ANSWER_RULES = (
    'You already have the current clock and, when present, live web headlines. '
    'Answer from those facts. Cite source titles and URLs. '
    'Never say you cannot access the internet, never tell the user to visit other news sites instead of answering, '
    'and never refuse because of a training cutoff. '
    'If live research is missing, say the search returned nothing. Reply in the user language.'
)


def context_for_messages(messages, search=search_web, fetch=fetch_page):
    user = next((m.get('content', '') for m in reversed(messages or []) if m.get('role') == 'user'), '')
    if len(user.strip()) < 4:
        return ''
    blocks = []
    urls = re.findall(r'https://[^\s<>"\']+', user)[:2]
    try:
        hits = search(user)
    except (WebError, ValueError, OSError):
        hits = []
    for hit in hits:
        line = f"- {hit.get('title', '')}: {hit.get('snippet', '')}"
        if hit.get('url'):
            line += f" ({hit['url']})"
        blocks.append(line)
    for url in urls:
        try:
            blocks.append(f"Page {url}: {fetch(url)}")
        except (WebError, ValueError, OSError):
            continue
    if not blocks:
        return ''
    return (
        'Live web research for this question. These are current headlines and snippets. '
        'Summarize them. Do not send the user away to look this up. '
        'Cite titles and URLs.\n' + '\n'.join(blocks)
    )[:3500]


def _fit(payload, limit=11000):
    while sum(len(m['content']) for m in payload) > limit and len(payload) > 3:
        for index, message in enumerate(payload):
            if message['role'] != 'system':
                del payload[index]
                break
        else:
            break
    total = sum(len(m['content']) for m in payload)
    if total > limit and payload:
        extra = total - limit
        payload[-1] = dict(payload[-1], content=payload[-1]['content'][extra:] if extra < len(payload[-1]['content']) else payload[-1]['content'][:limit])
    return payload


def augment_messages(messages, now=None, search=search_web, fetch=fetch_page):
    payload = [
        {'role': 'system', 'content': clock_context(now)},
        {'role': 'system', 'content': ANSWER_RULES},
    ]
    web = context_for_messages(messages, search=search, fetch=fetch)
    if web:
        payload.append({'role': 'system', 'content': web})
    payload.extend(dict(role=item['role'], content=item['content']) for item in messages or [])
    return _fit(payload)
