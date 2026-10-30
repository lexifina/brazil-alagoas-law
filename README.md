# Alagoas: law history in git

The law of the State of Alagoas (Estado de Alagoas) (Brazil) as a git history: one file per Artigo, one paragraph per line, so `git blame`, `git log` and `git diff` work line by line. The text is Portuguese, the only official language.

It follows the shared design of [lexifina/global-law](https://github.com/lexifina/global-law).

## What this repository holds

| Folder | Act | Versions |
| --- | --- | ---: |
| `constituicao/` | Constituição do Estado de Alagoas (5 October 1989), text in force as compiled by the Assembly up to Emenda Constitucional nº 52/2024 | 1 |
| `lc-<year>-<number>/` | 36 Leis Complementares (1991-2026) from the PDFs the Assembly's SAPL holds | 1 each |

The Constituição is given **only as its text in force**, credited to the Assembly as the oldest version available: the wordings in between are not reconstructed yet, so no earlier version is shown rather than a wrong one. Every Lei Complementar is given **as enacted**, credited to itself, and only when nothing later in the record amends it. Left out: 15 Leis Complementares whose PDFs are scans without a text layer, 17 that a later Lei Complementar amends, repeals or cites next to such words, 2 compiled texts whose notes cite no date, and 2 whose tables the second PDF reader reads in a different order. Ordinary Leis, decrees and the Emendas Constitucionais as acts are not included yet.

## Source

[Assembleia Legislativa do Estado de Alagoas (site and SAPL)](https://www.al.al.leg.br), published by the Assembleia Legislativa do Estado de Alagoas. Each version names the page it was taken from and that page's sha256, in `data/versions.json`.

## Dates

The compiled Constituição is dated by the date the last Emenda it includes prints (Emenda Constitucional nº 52/2024, Sala das Sessões, Maceió, 15 October 2024; it takes effect on publication). Commits are at noon in Maceió. A Lei Complementar as enacted is dated by its publication in the Diário Oficial do Estado as SAPL records it (or its date when SAPL records none).

## How it is built

Lexifina reads the sources listed here and records each act's dated versions, and the laws that made each change, in one corpus file. `tools/build.py` writes this repository from that file, and the same corpus always gives the same commit hashes; `REPRODUCE.md` gives the details and the checks. A model (Claude) wrote Lexifina's code; it wrote no legal text, and no model runs when the history is built.

The Assembly's compiled edition is a PDF with a text layer (from its SAPL: `constituicao_de_alagoas_ate_emenda_52.pdf`). It prints the text in force in body type (Arial 10.5 pt) and every superseded wording ("REDAÇÃO ORIGINAL: ...") and editorial note ("NOTA: ...") in small grey italics; only the body type is kept. The parenthetical notes the body type itself carries, such as "(Redação dada pela Emenda Constitucional nº 23/2001)", are kept as printed. Lines are joined into paragraphs at the first-line indent. Each article becomes one file (`art-*`; the Ato das Disposições Constitucionais Transitórias `adt-*`); headings of the Títulos, Capítulos, Seções and Subseções stand above the first article under them. The index, front matter and the Emendas printed after the text are left out. A second PDF reader (xpdf pdftotext) checks every letter and digit of the record against the PDF, passing over only the small-italic notes.

## How it is checked

Every version is read back from git on the day it took effect (`tools/check_repo.py`) and must match the corpus; an independent letters-and-digits comparison of every version against the source page must show no difference. Results are in `REPRODUCE.md`.

## What "author" means

The author of each commit is the law that made the text, or, for a consolidated text, the publisher, with an e-mail address that cannot exist; the committer is always Lexifina.

## Limits

Not a complete history: the Constituição starts at its text in force. The text is not the official version: only the Diário Oficial do Estado is authoritative. The edition has no preamble in its text layer. Article 63 is printed "Ar. 63." and kept as printed. No Emenda after nº 52/2024 is in the Assembly's SAPL for 2025 or 2026 (checked 30 October 2026). A Lei Complementar is checked for later amendments only against the other Leis Complementares (their texts, or for scans the SAPL summary): an amendment made by an ordinary Lei would not be seen.

## Licence

See [LICENSE](LICENSE): Brazilian law texts are not protected by copyright (Lei 9.610/1998, art. 8, IV). Fonte: Assembleia Legislativa do Estado de Alagoas (site and SAPL), Assembleia Legislativa do Estado de Alagoas.
