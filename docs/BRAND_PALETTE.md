# NYC Street Lights &mdash; Brand Palette

Authoritative color reference for the dashboard. Use this when regenerating Napkin.ai graphics, building new visuals, or adding UI components so everything stays visually coherent.

---

## Quick-reference chips

```
PRIMARY      #00b4d8   teal                  (headlines, key bars, accent strokes)
PRIMARY 2    #48bfe3   light teal            (hover states, gradient highlights)
PRIMARY DK   #0077b6   deep teal             (bar end-caps, pressed states)
PRIMARY LT   #8ab4f8   sky blue              (progress bars, soft accents)

POSITIVE     #2ec4b6   cyan-green            (good metrics, "closed on time" bars)
POSITIVE 2   #72efdd   mint                  (positive callout backgrounds)

WARNING      #ffb703   amber                 (pending states, medium priority)
WARNING 2    #ffd166   light amber           (caution highlights)

DANGER       #e63946   red                   (worst performer, high priority)
DANGER 2     #ff6b76   coral                 (inline text highlights on dark)

BG BASE      #0f1923   near-black            (page background)
BG CANVAS    #0d1b2a   dark slate            (card / chart canvas)
BG CARD      #1a2a3a   slate                 (raised cards)
BG CARD 2    #16253a   slate blue            (About-section gradient top)
BG DIVIDER   #223344   border                (card borders, dividers)
BG DIVIDER 2 #334455   stronger border       (inputs, focus outlines)

TEXT HIGH    #ffffff   pure white            (headlines)
TEXT PRIMARY #e0e0e0   off-white             (body copy)
TEXT SECOND  #c8d8e8   soft blue-grey        (secondary copy, chart values)
TEXT MUTED   #8899aa   muted blue-grey       (captions, axis labels)
TEXT DIM     #556677   dim grey              (disabled, timestamps)
TEXT DIMMER  #667788   slightly brighter dim (disclaimer italics)
```

---

## 1. Primary teal family &mdash; the signature color

Use for headlines, key data points, the "accent" in any chart, focus rings, hover states, and CTAs.

| Name | Hex | RGB | HSL | Use |
|---|---|---|---|---|
| Primary | `#00b4d8` | `0, 180, 216` | `191°, 100%, 42%` | Headlines, key bars, accent strokes |
| Primary Light | `#48bfe3` | `72, 191, 227` | `194°, 73%, 59%` | Hover states, gradient highlights |
| Primary Dark | `#0077b6` | `0, 119, 182` | `200°, 100%, 36%` | Bar end-caps, pressed states |
| Sky Blue | `#8ab4f8` | `138, 180, 248` | `217°, 89%, 76%` | Progress bar fills, soft accents |

**Gradient example** (page CTA buttons): `linear-gradient(135deg, #00b4d8 0%, #48bfe3 100%)`

---

## 2. Semantic accents

| Role | Name | Hex | Use |
|---|---|---|---|
| Positive | Cyan-green | `#2ec4b6` | Closed tickets, good performance, "on time" bars |
| Positive 2 | Mint | `#72efdd` | Positive callout backgrounds, soft highlights |
| Warning | Amber | `#ffb703` | Pending status, medium-priority complaints, caution bars |
| Warning 2 | Light Amber | `#ffd166` | Warning highlights, caution tints |
| Danger | Red | `#e63946` | Worst-performing borough, high-priority tickets, unresolved callouts |
| Danger 2 | Coral | `#ff6b76` | Inline text emphasis on dark backgrounds (the "1 in 3" callout) |

**Rule of thumb:** use semantic colors sparingly. One red bar in a chart of five teal bars is far more effective than five different colors.

---

## 3. Neutral backgrounds

| Name | Hex | Use |
|---|---|---|
| BG Base | `#0f1923` | Page background, outer frame |
| BG Canvas | `#0d1b2a` | Chart canvas, input fields, deepest surface |
| BG Card | `#1a2a3a` | Raised cards (classification, vendor, similar panels) |
| BG Card 2 | `#16253a` | About-section gradient top |
| BG Divider | `#223344` | Card borders, table grid lines |
| BG Divider 2 | `#334455` | Input borders, focus outlines |
| BG Deeper | `#0a1320` | Deepest canvas for code / pre blocks |

Always layer surfaces: page `0f1923` &rarr; card `1a2a3a` &rarr; chart `0d1b2a`. This creates visible depth without heavy borders.

---

## 4. Text colors

| Name | Hex | Use |
|---|---|---|
| Text High | `#ffffff` | Section headlines, hero numbers |
| Text Primary | `#e0e0e0` | Body copy, card content |
| Text Secondary | `#c8d8e8` | Longer prose, chart value labels |
| Text Muted | `#8899aa` | Captions, axis labels, timestamps |
| Text Dim | `#556677` | Disabled states, placeholders |
| Text Dimmer | `#667788` | Disclaimer italics, tertiary notes |

---

## 5. Chart palette &mdash; for Napkin.ai

Use these specific color sequences when feeding Napkin.ai. Napkin lets you override theme colors; if it doesn't accept exact hex values, pick its closest equivalents.

### 5a. Single-series bar charts (Graphic 1 / 2)

Order bars by value and color them as follows:

| Rank | Color | Purpose |
|---|---|---|
| Best / leader | `#2ec4b6` (cyan-green) | Celebrate the top performer |
| Middle bars | `#00b4d8` (teal) | Neutral primary |
| Worst / outlier | `#e63946` (red) | Flag the laggard |

If a chart has no clear "best/worst" story, use all `#00b4d8` for every bar and let the values speak.

### 5b. Multi-series / grouped bar charts (Graphic 3)

Three-tier scenario palette (Low / Mid / High):

| Scenario | Color | Hex |
|---|---|---|
| Low | Light teal | `#48bfe3` |
| Mid | Primary teal | `#00b4d8` |
| High | Deep teal | `#0077b6` |

Monochromatic progression signals "same thing, more of it" far more clearly than three random colors.

### 5c. Donut / pie chart segments

| Order | Color | Hex |
|---|---|---|
| 1 | Primary teal | `#00b4d8` |
| 2 | Cyan-green | `#2ec4b6` |
| 3 | Amber | `#ffb703` |
| 4 | Coral | `#ff6b76` |
| 5 | Sky blue | `#8ab4f8` |

### 5d. Chart canvas / background

- Napkin default is a white tile &mdash; that's fine and contrasts well against our dark page.
- If you switch Napkin to dark mode, use canvas `#0d1b2a` and gridlines `#223344` (very faint, `stroke-width: 1`).
- Axis labels: `#8899aa`.
- Data-value labels sitting next to bars: `#e0e0e0`.

---

## 6. Borough color assignment (optional convention)

If a chart shows the same boroughs repeatedly and you want them visually consistent across the site, this is the suggested mapping. Use only when borough-specific color coding adds clarity &mdash; not for every chart.

| Borough | Color | Hex |
|---|---|---|
| Manhattan | Red | `#e63946` |
| Brooklyn | Primary teal | `#00b4d8` |
| Queens | Amber | `#ffb703` |
| Bronx | Cyan-green | `#2ec4b6` |
| Staten Island | Sky blue | `#8ab4f8` |

(This follows roughly the color associations used by NYC transit maps &mdash; the 7 train is Queens purple-red, Brooklyn is cool, Manhattan is bold. Feel free to override.)

---

## 7. Typography pairings (for reference)

Not a color, but usually paired with palette decisions:

- **Headlines:** Segoe UI / Inter, weight 700, `#ffffff`
- **Body:** Segoe UI / Inter, weight 400, `#c8d8e8`
- **Data labels in charts:** Segoe UI / Inter, weight 600, `#e0e0e0`
- **Captions:** Segoe UI / Inter, weight 400, `#8899aa`

Napkin.ai defaults to Georgia / Merriweather serif pairings &mdash; perfectly acceptable in charts because the contrast with our sans-serif body copy actually adds a nice editorial feel. Leave the Napkin fonts alone unless you specifically want them changed.

---

## 8. Copy-paste snippets

### CSS custom properties (add to `:root{}` in `build.py` CSS block if you want to refactor later)

```css
:root {
  --teal:        #00b4d8;
  --teal-light:  #48bfe3;
  --teal-dark:   #0077b6;
  --sky:         #8ab4f8;

  --green:       #2ec4b6;
  --mint:        #72efdd;
  --amber:       #ffb703;
  --amber-light: #ffd166;
  --red:         #e63946;
  --coral:       #ff6b76;

  --bg-base:     #0f1923;
  --bg-canvas:   #0d1b2a;
  --bg-card:     #1a2a3a;
  --bg-divider:  #223344;
  --bg-focus:    #334455;

  --text-high:   #ffffff;
  --text:        #e0e0e0;
  --text-2:      #c8d8e8;
  --text-muted:  #8899aa;
  --text-dim:    #556677;
}
```

### JSON (for Napkin.ai palette imports, if supported)

```json
{
  "name": "NYC Street Lights",
  "primary": "#00b4d8",
  "secondary": "#2ec4b6",
  "accent": "#ffb703",
  "danger": "#e63946",
  "background": "#0d1b2a",
  "surface": "#1a2a3a",
  "text": "#e0e0e0",
  "textMuted": "#8899aa",
  "chartPalette": ["#00b4d8", "#2ec4b6", "#ffb703", "#ff6b76", "#8ab4f8", "#0077b6"]
}
```

### Hex-only list (for tools that only accept flat arrays)

```
#00b4d8  #48bfe3  #0077b6  #8ab4f8
#2ec4b6  #72efdd  #ffb703  #ffd166
#e63946  #ff6b76
#0f1923  #0d1b2a  #1a2a3a  #223344  #334455
#ffffff  #e0e0e0  #c8d8e8  #8899aa  #556677
```

---

## 9. Updating the Napkin SVGs to match

When you re-export from Napkin.ai with updated colors, save over the existing files in `public/img/about/`:

- `g1-volume.svg`
- `g2-closure.svg`
- `g3-revenue.svg`

The About page will pick them up automatically on the next deploy &mdash; no code changes required.

**Alternative if Napkin.ai won't accept custom hex values:** edit the SVG files directly. Open each in a text editor and find-and-replace the Napkin default colors with our hex values. The three main colors Napkin currently uses are approximately:

| Napkin default | Replace with |
|---|---|
| `#4f91fc` (blue) | `#00b4d8` (teal) |
| `#43dd93` (green) | `#2ec4b6` (cyan-green) |
| `#ffe711` (yellow) | `#ffb703` (amber) |

I can do that SVG find-and-replace pass for you in one step if you'd rather not regenerate in Napkin &mdash; just say the word.
