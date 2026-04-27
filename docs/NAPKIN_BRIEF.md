# Napkin.ai Input Brief — About Page Graphics

**How to use this file:** Paste each section (one at a time) into Napkin.ai's text-to-graphic input. The style hints at the top apply to every graphic so the final set looks cohesive when dropped onto the About page.

---

## Global style hints (apply to all graphics)

- **Theme:** Dark background, high-contrast text. The site uses `#0f1923` (near-black) and `#1a2a3a` (slate) as canvas colors.
- **Primary accent:** Teal `#00b4d8` (headline values, bars, key callouts).
- **Secondary accent:** Cyan-green `#2ec4b6` (positive metric / "good" bars like fastest borough).
- **Warning accent:** Amber `#ffb703` (caution).
- **Danger accent:** Red `#e63946` (worst-performing bar / long-unresolved callout).
- **Text:** Off-white `#e0e0e0` for values, muted `#8899aa` for captions and axis labels.
- **Typography:** Clean sans-serif (Segoe UI / Inter vibe — no serifs, no script fonts).
- **Aspect ratio:** 16:9 landscape for standalone graphics, 1:1 square for the callout tile.
- **Export:** PNG at 2x (for retina) or SVG if available.

File-naming convention when you save them: `public/img/about/g1-volume.png`, `g2-closure.png`, `g3-revenue.png`, `g4-callout.png`.

---

## GRAPHIC 1 — "NYC Street Light Complaints, 2024"

**Type:** Horizontal bar chart, sorted descending.
**Headline:** `30,881 complaints filed to 311 in 2024`
**Subhead:** `Street Light Condition — by borough`

**Data:**

| Borough | Complaints |
|---|---|
| Brooklyn | 8,639 |
| Queens | 8,571 |
| Bronx | 6,184 |
| Manhattan | 4,962 |
| Staten Island | 2,318 |

**Styling notes:**
- Bars use teal `#00b4d8`.
- Show the numeric value at the end of each bar in off-white.
- No gridlines; let the bars breathe.
- Small caption at the bottom: `Source: NYC OpenData, dataset erm2-nwe9, complaint_type = "Street Light Condition", 2024 calendar year.`

---

## GRAPHIC 2 — "Speed of Resolution by Borough, 2024"

**Type:** Horizontal bar chart, sorted descending.
**Headline:** `% of 2024 complaints closed within 30 days`
**Subhead:** `Brooklyn and Staten Island tied at the top; Manhattan trails`

**Data:**

| Borough | % Closed ≤ 30 days |
|---|---|
| Brooklyn | 80.4% |
| Staten Island | 80.4% |
| Bronx | 78.3% |
| Queens | 76.3% |
| Manhattan | 67.4% |

**Styling notes:**
- Use cyan-green `#2ec4b6` for the top two bars (Brooklyn and Staten Island) to emphasize the leaders.
- Middle bars (Bronx, Queens) use teal `#00b4d8`.
- Manhattan's bar uses red `#e63946` to highlight the outlier.
- Add a faint vertical dashed line at 80% labeled `"80% benchmark"` in muted grey.
- Caption: `Source: NYC OpenData erm2-nwe9, Street Light Condition complaints filed in calendar year 2024.`

---

## GRAPHIC 2B (optional) — "Rapid Resolution: Closed Within 7 Days, 2024"

**Type:** Horizontal bar chart, sorted descending. Complements Graphic 2 by showing same-week response.
**Headline:** `% of 2024 complaints closed within 7 days`
**Subhead:** `More than half of all complaints are resolved in a week`

**Data:**

| Borough | % Closed ≤ 7 days |
|---|---|
| Brooklyn | 63.3% |
| Manhattan | 61.3% |
| Bronx | 56.9% |
| Queens | 53.8% |
| Staten Island | 47.1% |

**Styling notes:**
- All bars teal `#00b4d8`.
- Caption: `Source: NYC OpenData erm2-nwe9, 2024 calendar year.`
- Interesting finding: Manhattan is second-fastest on same-week closures yet worst on the 30-day metric — its problem is the long tail, not the first response.

---

## GRAPHIC 3 — "Local Vendor Revenue Opportunity, Annualized"

**Type:** Grouped horizontal bar chart (three bars per borough — Low / Mid / High scenario).
**Headline:** `$6.2M – $15.4M annual local-vendor revenue potential`
**Subhead:** `2024 311 volume × NYC electrical service-call rates`

**Data (values in millions USD):**

| Borough | Low ($200/repair) | Mid ($350/repair) | High ($500/repair) |
|---|---|---|---|
| Brooklyn | $1.73M | $3.02M | $4.32M |
| Queens | $1.71M | $3.00M | $4.29M |
| Bronx | $1.24M | $2.16M | $3.09M |
| Manhattan | $0.99M | $1.74M | $2.48M |
| Staten Island | $0.46M | $0.81M | $1.16M |
| **NYC Total** | **$6.18M** | **$10.81M** | **$15.44M** |

**Styling notes:**
- Three bar colors per borough group: muted teal `#48bfe3` (Low), primary teal `#00b4d8` (Mid), deep teal `#0077b6` (High).
- Legend at top right: `Low $200  ·  Mid $350  ·  High $500  per repair`.
- Label each bar with its dollar value.
- **Disclaimer line beneath the chart (important — do not omit):**
  > *Revenue estimates derived from published NYC electrical service-call market rates and 2024 311 complaint volumes. Not NYC DOT contract data.*
- Caption source line: `Volume: NYC OpenData erm2-nwe9 · Rates: Homeyou, industry sources (see Sources page)`

---

## GRAPHIC 4 — Callout Tile

**Type:** Single big-number callout, 1:1 square, poster-style.
**Primary number:** `1 in 3`
**Primary text:** `Manhattan street-light complaints still unresolved 30 days after being filed.`
**Accent color:** Red `#e63946` for the "1 in 3" figure.
**Small subtext:** `32.6% of Manhattan's 2024 complaints remain open, pending, or take longer than a month to close — the worst rate of any borough.`
**Caption:** `Source: NYC OpenData erm2-nwe9, 2024 calendar year.`

---

## GRAPHIC 5 (optional) — Infrastructure Scale Tile

**Type:** Three-column "by the numbers" tile, landscape.
**Columns (each big number over a short label):**

| Number | Label |
|---|---|
| 250,000 | Streetlamps maintained by NYC DOT citywide |
| 30,881 | 311 complaints filed in 2024 |
| 4 hrs | Required emergency response window under DOT contract |

**Styling notes:**
- Numbers in teal `#00b4d8`, labels in muted `#8899aa`.
- Thin vertical dividers between the three columns.
- Caption: `Sources: NYC DOT, amNY, NYC OpenData.`

---

## Reminders

- When you export, save the files into `public/img/about/` in the project so the build process can reference them.
- If Napkin.ai doesn't let you set exact hex values, match as closely as possible — I'll do a visual pass and can correct minor color drift via a CSS overlay if needed.
- If any graphic comes back with a different layout than described, that's fine — the data is the important part, and I'll fit whatever Napkin produces to the page.
