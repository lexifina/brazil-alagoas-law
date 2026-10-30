"""Independent letters-and-digits check of a part against the source PDF, read by a second engine (xpdf pdftotext).

    python -X utf8 check_letters.py corpus.d/10-constituicao.json [...]

Private. For each version, the units (the "## " heading marks taken off) reduced to letters and digits must be found,
in order and without a gap, in the PDF's text as xpdf reads it (pdftotext -simple, pages FIRST..LAST), reduced the
same way. Source text may be passed over only where it is made up entirely of lines that alread.py (pymupdf) read
as notes, i.e. not body type: the superseded wordings ("REDAÇÃO ORIGINAL: ...") and editorial notes ("NOTA: ..."),
and page numbers. Anything else is a mismatch: a word in the record that is not in the PDF, words out of order, or
body text left out. The check also requires the record to start at the PDF's first body word and end at its last.
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import alread  # noqa: E402  (only to know which lines are not body type)
import parse  # noqa: E402  (page range and URLs)


def ld(s):
    s = s.replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    return ''.join(ch for ch in s if ch.isalnum())


def source(pdf, first, last):
    out = subprocess.run(['pdftotext', '-simple', '-enc', 'UTF-8', '-f', str(first + 1), '-l', str(last + 1), str(pdf), '-'],
                         capture_output=True, check=True).stdout
    import unicodedata
    pages = unicodedata.normalize('NFC', out.decode('utf-8', 'replace')).split('\f')
    # a line that is only the page's own number (the folio) is not text
    return ''.join(ld('\n'.join(l for l in pg.splitlines() if l.strip() != str(first + k + 1)))
                   for k, pg in enumerate(pages))


def aside_of(pdf, first, last):
    import pymupdf
    d = pymupdf.open(str(pdf))
    a = []
    for pno in range(first, last + 1):
        for l in alread.page_lines(d[pno]):
            if not l['body']:
                a.append(ld(l['text']))
    return a


END = [0]


def align(U, S, aside):
    pool = {}
    for x in aside:
        if x:
            pool[x] = pool.get(x, 0) + 1
    i = j = 0
    gaps = 0
    while i < len(U):
        if j < len(S) and S[j] == U[i]:
            i += 1; j += 1
            continue
        # the record's next letters, in shorter and shorter windows (a note may sit right after a heading), at the
        # first place from which everything passed over is set-aside text
        hit = None
        for n in (24, 16, 10, 6):
            pos = S.find(U[i:i + n], j)
            tries = 0
            while pos >= 0 and tries < 5:
                ok, used = gap_ok(S[j:pos], pool)
                if ok:
                    hit = (pos, used)
                    break
                pos = S.find(U[i:i + n], pos + 1)
                tries += 1
            if hit:
                break
        if hit is None:
            return False, f'record text not found after set-aside text only: {U[i:i + 70]!r} (source: {S[j:j + 120]!r})'
        pos, used = hit
        for x in used:
            pool[x] -= 1
        gaps += 1
        j = pos
    END[0] = j
    return True, f'{gaps} set-aside stretches passed over'


def gap_ok(rest, pool):
    """Is rest a concatenation of set-aside lines? (any order; each line at most as often as the pool holds it;
    searched over all ways of splitting, so one line that is a prefix of another does not mislead it)."""
    cands = [x for x, n in pool.items() if n > 0]
    back = {0: None}
    todo = [0]
    while todo:
        k = todo.pop()
        if k == len(rest):
            used, q = [], k
            while back[q] is not None:
                q, x = back[q]
                used.append(x)
            return True, used
        for x in cands:
            e = k + len(x)
            if e not in back and rest.startswith(x, k):
                back[e] = (k, x)
                todo.append(e)
    return False, []


def main(paths):
    bad = 0
    failed = {}
    for p in paths:
        c = json.load(open(p, encoding='utf-8'))
        for a in c['acts']:
            for v in a['versions']:
                pdf = HERE / '.cache' / 'raw' / hashlib.sha256(v['source_url'].encode()).hexdigest()
                assert hashlib.sha256(pdf.read_bytes()).hexdigest() == v['sha256'], 'sha256 differs'
                first, last = (parse.FIRST, parse.LAST) if a['slug'] == 'constituicao' else (0, None)
                if last is None:
                    import pymupdf
                    last = pymupdf.open(str(pdf)).page_count - 1
                S = source(pdf, first, last)
                if a['slug'] == 'constituicao':
                    aside = aside_of(pdf, first, last)
                else:  # a Lei Complementar: the lines alread.lc_lines dropped or read as small type
                    kept, dropped, _ = alread.lc_lines(str(pdf))
                    aside = [ld(l['text']) for l in dropped + [k for k in kept if not k['body']]]
                U = ''.join(ld(re.sub(r'(?m)^#+ ', '', u['text'])) for u in v['units'].values())
                # leading/trailing source text outside the record must be set-aside text too
                start = S.find(U[:40])
                lead_ok = start >= 0 and gap_ok(S[:start], {x: 99 for x in aside if x})[0]
                ok, msg = align(U, S[start:] if start >= 0 else S, aside)
                if ok:
                    tail = S[max(start, 0) + END[0]:]  # where the alignment ended
                    ok = gap_ok(tail, {x: 99 for x in aside if x})[0]
                    msg += '' if ok else f'; source text after the record: {tail[:100]!r}'
                ok = ok and lead_ok
                bad += not ok
                if not ok:
                    failed[a['slug']] = 'the second PDF reader (xpdf) does not give the same letters and digits in the same order: ' + msg[:160]
                print('OK  ' if ok else 'FAIL', a['slug'], v['from'], len(U), 'letters;', msg,
                      '' if lead_ok else f'; source before the record: {S[:max(start, 0)][:100]!r}')
    print('versions failing:', bad)
    if LEFT_OUT:
        Path(LEFT_OUT).write_text(json.dumps(failed, ensure_ascii=False, indent=1), encoding='utf-8')
    return bad


LEFT_OUT = None
if __name__ == '__main__':
    if '--left-out' in sys.argv:  # write the slugs that fail, with the reason, to this file (parse.py leaves them out)
        k = sys.argv.index('--left-out')
        LEFT_OUT = sys.argv[k + 1]
        del sys.argv[k:k + 2]
    sys.exit(1 if main(sys.argv[1:] or sorted(str(p) for p in (HERE / 'corpus.d').glob('*.json'))) else 0)
