"""Outbound HTTPS lookup used by local chat. The model weights stay offline."""
from html.parser import HTMLParser
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = 'Share4AI-Provider/1.1 (local research)'
MAX_BODY = 400_000
TIMEOUT = 8


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
        raise WebError('Only public HTTPS URLs are allowed')
    if parsed.port not in (None, 443):
        raise WebError('Only public HTTPS URLs are allowed')
    host = parsed.hostname
    if host.lower() in ('localhost', 'localhost.localdomain'):
        raise WebError('Private addresses are blocked')
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError as error:
        raise WebError('Could not resolve host') from error
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise WebError('Private addresses are blocked')
    return parsed.geturl()


def _get(url, accept='application/json'):
    safe = _public_https(url)
    req = urllib.request.Request(safe, headers={'User-Agent': USER_AGENT, 'Accept': accept})
    try:
        with _opener().open(req, timeout=TIMEOUT) as response:
            data = response.read(MAX_BODY + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise WebError('Web source unavailable') from error
    if len(data) > MAX_BODY:
        raise WebError('Web page too large')
    return data


def _wikipedia_lang(text):
    return 'ar' if re.search(r'[\u0600-\u06FF]', text or '') else 'en'


def search_web(query, opener=None):
    query = ' '.join((query or '').split())[:200]
    if len(query) < 2:
        return []
    lang = _wikipedia_lang(query)
    encoded = urllib.parse.quote(query)
    results = []
    wiki = (
        f'https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={encoded}'
        '&srlimit=3&format=json&utf8=1'
    )
    raw = _get(wiki) if opener is None else opener(wiki)
    payload = json.loads(raw.decode('utf-8', errors='replace'))
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
    except (WebError, ValueError):
        instant = {}
    abstract = (instant.get('AbstractText') or '')[:400]
    source = instant.get('AbstractURL') or ''
    if abstract:
        results.insert(0, {'title': instant.get('Heading') or query, 'url': source, 'snippet': abstract})
    return results[:4]


def fetch_page(url, opener=None):
    raw = _get(url, accept='text/html,application/xhtml+xml') if opener is None else opener(url)
    parser = _TextExtractor()
    parser.feed(raw.decode('utf-8', errors='replace'))
    text = ' '.join(parser.parts)
    return text[:2500]


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
        'Live web research for this question. Prefer these sources over training memory. '
        'Cite URLs when you use them.\n' + '\n'.join(blocks)
    )[:2500]
