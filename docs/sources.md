# Source check (Phase 0)

Checked 2026-11-18 and 2026-11-19 with the user agent in `config/config.toml`, from the author's network. Decisions are in `DECISIONS.md` (D-19 to D-23).

| Outlet | robots.txt | Terms | Discovery | Status |
|---|---|---|---|---|
| CityNews Toronto (`toronto.citynews.ca`) | Allows articles; `Crawl-delay: 10` | Rogers Media: personal, non-commercial use; no redistribution; no scraping clause found | WordPress post sitemaps (`sitemap-pt-post-pN.xml`) | Included, 10 s delay |
| CTV News Toronto (`www.ctvnews.ca/toronto/`) | Allows articles | Bell Media: personal, non-commercial use; no scraping clause found | Daily Arc sitemaps; dates before about 2025 return empty | Included, shorter window |
| Global News (`globalnews.ca`) | Allows articles | Corus: non-commercial use of individual pages; no scraping clause found | Numbered sitemaps with `lastmod`; national, so Toronto relevance is checked in the text | Included |
| CBC Toronto (`www.cbc.ca`) | Timed out | Not checked | Not checked | Retry during collection; excluded if unreachable |
| Toronto Sun (`torontosun.com`) | Allows articles | Postmedia: "Web Scraping shall not be permitted under any circumstance without the prior consent of Postmedia." | n/a | **Excluded** (terms) |
| blogTO (`www.blogto.com`) | 403 | n/a | n/a | **Excluded** (blocks scripted access) |
| Toronto Today (`www.torontotoday.ca`) | 403, Cloudflare challenge | n/a | n/a | **Excluded** (blocks scripted access) |
| Toronto Police (`tps.ca`) | 403, Cloudflare challenge | n/a | Wayback Machine CDX, sequential release IDs | Wayback copies only (author's decision); ~42% of 2023–2026 IDs archived |

Fetch rules: at least 2 s between requests to the same domain, or the site's crawl-delay if longer; robots.txt checked before every fetch; raw HTML kept in `data/raw/`, never committed.

## Comparison corpora (nice-to-haves, D-99 to D-101)

Collected into separate databases (`data/compare.sqlite`, `data/cities.sqlite`) under the same fetch rules.

| Outlet | robots.txt | Terms | Discovery | Status |
|---|---|---|---|---|
| Spacing Toronto (`spacing.ca/toronto`) | Allows articles | Copying for personal use only; no scraping clause found | WordPress post sitemaps | Included (urbanist) |
| The Local (`thelocal.to`) | Allows articles | No terms page found | WordPress post sitemap | Included (urbanist) |
| Canadian Cycling Magazine (`cyclingmagazine.ca`) | Allows articles | No terms page found | WordPress post sitemaps, slug filter | Included (urbanist) |
| CityNews Vancouver, Montreal | Allows articles; `Crawl-delay: 10` | Rogers Media, as for Toronto | Post sitemaps | Included, 10 s delay |
| CTV News Vancouver, Montreal | Allows articles | Bell Media, as for Toronto | Daily Arc sitemaps; 16 failed after retry | Included |
| Global News BC, Montreal | Allows articles | Corus, as for Toronto | Regional sections of the main crawl | Included |
| Radio-Canada (`ici.radio-canada.ca`) | Allows articles | No scraping or automated-access clause found | Wayback CDX index of article URLs; pages fetched live | Included (French, Montreal) |
| La Presse (`lapresse.ca`) | n/a | n/a | n/a | **Excluded** (405, blocks scripted access) |
| TVA Nouvelles, Journal de Montréal (Québecor) | n/a | Could not be confirmed | n/a | **Excluded** (terms) |
| Le Devoir, Métro | n/a | n/a | No historical sitemaps | **Excluded** (no discovery route) |
