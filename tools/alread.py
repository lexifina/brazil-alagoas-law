"""Alagoas Assembly compiled Constituição (CorelDRAW PDF, one column) -> body lines in reading order. Private.

pymupdf spans, grouped by baseline (span origin) and sorted top to bottom (the PDF's own block order is not the reading
order). Body type is Arial 10.5 pt in ink 0x231f20; the superseded wordings ("REDAÇÃO ORIGINAL: ...") and the
publisher's notes ("NOTA: ...") are Arial Italic 9 pt in grey: they are returned apart, as notes. Page numbers
(9 pt, black) are dropped.
"""
import re
import unicodedata

import pymupdf

BODY_INK = 0x231f20


def clean(s):
    s = unicodedata.normalize('NFC', s.replace('ﬁ', 'fi').replace('ﬂ', 'fl').replace('\xa0', ' ').replace('­', '').replace('\t', ' '))
    return re.sub(r' {2,}', ' ', s)


def page_lines(page):
    spans = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            for s in l['spans']:
                if not s['text'].strip():
                    continue
                spans.append((round(s['origin'][1], 1), s['bbox'][0], s['bbox'][2], s))
    spans.sort(key=lambda t: (t[0], t[1]))
    rows = []
    for t in spans:
        if rows and abs(rows[-1][0][0] - t[0]) < 1.5:
            rows[-1].append(t)
        else:
            rows.append([t])
    out = []
    for r in rows:
        r.sort(key=lambda t: t[1])
        text = ''
        for i, t in enumerate(r):
            if i and t[1] - r[i - 1][2] > 1.2 and not text.endswith(' '):
                text += ' '
            text += t[3]['text']
        sizes = {round(t[3]['size'], 1) for t in r}
        inks = {t[3]['color'] for t in r}
        if inks == {0} and re.fullmatch(r'\s*\d{1,3}\s*', text):
            continue  # page number
        body = all(t[3]['size'] >= 10 and t[3]['color'] == BODY_INK for t in r)
        note = all(t[3]['size'] < 10 for t in r)
        if not (body or note):
            raise ValueError(f'mixed line p{page.number} y{r[0][0]}: {text[:80]!r} {sizes} {inks}')
        out.append({'y': r[0][0], 'x0': r[0][1], 'x1': r[-1][2], 'text': clean(text).strip(), 'body': body,
                    'bold': all('Bold' in t[3]['font'] for t in r),
                    'bold_start': 'Bold' in r[0][3]['font'], 'page': page.number})
    return out


def lines(path, first, last):
    d = pymupdf.open(path)
    out = []
    for pno in range(first, last + 1):
        out += page_lines(d[pno])
    return out


def lc_lines(path, body_min=9.5):
    """A Lei Complementar PDF (Word export, one column) -> lines in reading order, each with 'body' (type of at least
    body_min pt; the superseded wordings "REDAÇÃO ORIGINAL: ..." are 8 pt), 'bold', 'x0', 'y', 'page', 'gap_before'
    (vertical distance from the line above on the same page, None at a page top). Fragments on one baseline are
    joined with a space, or with " | " across a wide gap (table cells). The running header (the lines that open
    the first page and repeat at the same height on later pages) is dropped from later pages."""
    d = pymupdf.open(path)
    pages = []
    for page in d:
        spans = []
        for b in page.get_text('dict')['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    if s['text'].strip():
                        spans.append((round(s['origin'][1], 1), s['bbox'][0], s['bbox'][2], s))
        spans.sort(key=lambda t: (t[0], t[1]))
        rows = []
        for t in spans:
            if rows and abs(rows[-1][0][0] - t[0]) < 1.5:
                rows[-1].append(t)
            else:
                rows.append([t])
        out = []
        for r in rows:
            r.sort(key=lambda t: t[1])
            text = ''
            for i, t in enumerate(r):
                gap = t[1] - r[i - 1][2] if i else 0
                if i and gap > 30:
                    text = text.rstrip() + ' | '
                elif i and gap > 1.2 and not text.endswith(' '):
                    text += ' '
                text += t[3]['text']
            out.append({'y': r[0][0], 'x0': r[0][1], 'x1': r[-1][2], 'text': clean(text).strip(),
                        'body': all(t[3]['size'] >= body_min for t in r),
                        'small': all(t[3]['size'] < body_min for t in r),
                        'bold': all('Bold' in t[3]['font'] or t[3]['flags'] & 16 for t in r),
                        'page': page.number})
        pages.append(out)
    head = {(round(l['y']), l['text']) for l in pages[0][:4]} if pages and pages[0] else set()
    res, dropped = [], []
    for pno, out in enumerate(pages):
        prev = None
        for l in out:
            if pno and (round(l['y']), l['text']) in head:
                dropped.append(l)
                continue
            if re.fullmatch(r'\d{1,3}', l['text']) and l is out[-1]:
                dropped.append(l)
                continue  # a page number at the foot
            l['gap_before'] = None if prev is None else l['y'] - prev['y']
            res.append(l)
            prev = l
    return res, dropped, d
