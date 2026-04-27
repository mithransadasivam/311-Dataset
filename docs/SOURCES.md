# Sources & Methodology — About Page Data

This document lists every source behind the statistics displayed on the About page, separates verified facts from range-based estimates, and records the methodology for anyone auditing our numbers.

---

## 1. Complaint volume — 2024 calendar year (verified)

| Borough | 2024 Street Light Complaints |
|---|---|
| Brooklyn | 8,639 |
| Queens | 8,571 |
| Bronx | 6,184 |
| Manhattan | 4,962 |
| Staten Island | 2,318 |
| Unspecified | 207 |
| **NYC Total** | **30,881** |

**Source:** [NYC OpenData — 311 Service Requests from 2010 to Present](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9), dataset ID `erm2-nwe9`, maintained by NYC 311 and updated daily.

**Methodology:** Live Socrata SoQL query:

```
SELECT borough, count(*)
WHERE complaint_type = 'Street Light Condition'
  AND created_date BETWEEN '2024-01-01T00:00:00' AND '2024-12-31T23:59:59'
GROUP BY borough
```

Executed against the Socrata endpoint `data.cityofnewyork.us/resource/erm2-nwe9.json`.

---

## 2. Resolution-speed percentages — 2024 (verified, live-queried)

| Borough | Closed ≤ 7 days | Closed ≤ 30 days | Still unresolved at 30d |
|---|---|---|---|
| Brooklyn | 63.3% | 80.4% | 19.6% |
| Staten Island | 47.1% | 80.4% | 19.6% |
| Bronx | 56.9% | 78.3% | 21.7% |
| Queens | 53.8% | 76.3% | 23.7% |
| Manhattan | 61.3% | 67.4% | **32.6%** |
| **Citywide** | **57.7%** | **76.7%** | **23.3%** |

**Source:** Same dataset as §1 — [NYC OpenData `erm2-nwe9`](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9).

**Methodology:** Three live Socrata SoQL queries executed against `data.cityofnewyork.us/resource/erm2-nwe9.json`:

```
-- Denominator: total 2024 complaints by borough
SELECT borough, count(*)
WHERE complaint_type = 'Street Light Condition'
  AND created_date BETWEEN '2024-01-01T00:00:00' AND '2024-12-31T23:59:59'
GROUP BY borough

-- Numerator: closed within 30 days
SELECT borough, count(*)
WHERE complaint_type = 'Street Light Condition'
  AND status = 'Closed'
  AND created_date BETWEEN '2024-01-01T00:00:00' AND '2024-12-31T23:59:59'
  AND closed_date IS NOT NULL
  AND date_diff_d(closed_date, created_date) <= 30
GROUP BY borough

-- Same as above with `<= 7` for the rapid-response metric.
```

"Still unresolved at 30 days" = 1 − (closed_within_30d / total_filed). This includes tickets still `Open`, `Pending`, or `Assigned` at query time, plus tickets that eventually closed but took longer than 30 days.

**Noteworthy finding:** Manhattan has the **second-fastest same-week response** (61.3% closed within 7 days) yet the **worst 30-day rate** (67.4%). Its problem isn't first response — it's the long tail of tickets that slip into multi-month backlogs.

---

## 3. Infrastructure scale (verified)

- **NYC DOT maintains ~250,000 streetlamps citywide.**
  Source: [amNY — "LED streetlight conversion in NYC more than 70%"](https://www.amny.com/news/led-streetlight-conversion-in-nyc-more-than-70-1-14280026/); cross-referenced in [Wikipedia — NYC Department of Transportation](https://en.wikipedia.org/wiki/New_York_City_Department_of_Transportation).

- **4-hour emergency-response requirement for DOT streetlight contractors.**
  Source: [NYC DOT — Streetlights](https://www.nyc.gov/html/dot/html/infrastructure/streetlights.shtml).

- **All repairs must be performed by a licensed NYC electrical contractor.**
  Source: [NYC DOT — Streetlights](https://www.nyc.gov/html/dot/html/infrastructure/streetlights.shtml); corroborated in [NYC Rules § 2-20 Street Light and Power](https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCrules/0-0-0-62948).

---

## 4. Per-repair cost range (published market rates — estimate)

These figures are U.S. market rates for streetlight service calls and electrical labor. They are **not NYC DOT contract rates**, which are not publicly disclosed.

| Component | Range | Source |
|---|---|---|
| NYC licensed electrician labor | $50–$200 / hr | [Homeyou — Electrician costs in NY](https://www.homeyou.com/ny/electrician-new-york-costs) |
| Bucket truck / aerial lift | $60–$150 / hr ($1,500–$2,000 / day) | [Lightwaytraffic](https://www.lightwaytraffic.com/how-much-does-a-street-light-cost/), industry aggregators |
| Simple fixture / bulb repair (non-NYC baseline) | $50–$120 total | [Ecosmart](https://www.ecosmartinc.com/how-much-does-a-street-light-cost/), [Lightwaytraffic](https://www.lightwaytraffic.com/how-much-does-a-street-light-cost/) |
| Full fixture or pole replacement | $1,000+ | Same as above |
| Annualized per-light maintenance cost (LA) | ~$200 / light / year | [Cost of Service and Street Light Assessment, City of LA](https://lalights.lacity.org/residents/cost_of_svc_and_stlighting_assessments.html) |

**NYC-adjusted service-call range used on this site: $200 – $500 per completed complaint.**

**Rationale:** The non-NYC floor of $50–$120 per repair is unrealistic in a union-heavy, high-cost-of-living market. We shift the floor to $200, anchor the midpoint at $350, and cap the ceiling at $500 — still well below the $1,000+ full-replacement benchmark. The range is deliberately conservative and error-bands toward underestimation rather than inflation.

---

## 5. Revenue opportunity (estimate — derived)

| Borough | Low ($200/ea) | Mid ($350/ea) | High ($500/ea) |
|---|---|---|---|
| Brooklyn | $1.73M | $3.02M | $4.32M |
| Queens | $1.71M | $3.00M | $4.29M |
| Bronx | $1.24M | $2.16M | $3.09M |
| Manhattan | $0.99M | $1.74M | $2.48M |
| Staten Island | $0.46M | $0.81M | $1.16M |
| **NYC Total** | **$6.18M** | **$10.81M** | **$15.44M** |

**Methodology:** `annual_revenue_borough = complaints_2024_borough × rate_per_repair`, for each of the three rate scenarios above.

**Disclaimer (appears on the About page next to the revenue graphic):**

> *Revenue estimates are derived from published NYC electrical service-call market rates and 2024 311 complaint volumes. They are **not** NYC DOT contract data and do not represent actual payments made to any current contractor.*

**What we do NOT claim:**
- These numbers are not NYC DOT's actual spend on street-light maintenance.
- They are not promised revenue to any specific vendor.
- They do not account for the share of current spend captured by prime contractors (e.g. Welsbach Electric Corp. historically), subcontracting arrangements, or non-repair costs like materials markup and administrative overhead.
- Actual vendor revenue would depend on contract structure, volume awarded, and competitive bidding.

---

## 6. Data freshness & update cadence

- **Live 311 feed (Socrata):** Browser-direct query executed on every complaint submission. Updated daily by NYC 311.
- **About-page statistics:** Pulled directly from NYC OpenData `erm2-nwe9` for calendar year 2024. To refresh, re-run the Socrata queries in §1 and §2 and update the numbers in `docs/NAPKIN_BRIEF.md` and the About page copy.
- **Baked historical sample (used for similar-complaint matching only):** 10,000 records, 2018–2019 snapshot. Regenerated at build time from `data/*.csv`. Powers the "similar past complaints" ranking on the results screen, not the About page.
- **Vendor directory:** NYC DOB master electrician license roster, filtered to exclude non-contractor institutions (universities, hospitals, city agencies). 1,853 active licensed vendors.

---

## 7. Full source list (in one place, for citation)

- [NYC OpenData — 311 Service Requests from 2010 to Present (erm2-nwe9)](https://data.cityofnewyork.us/Social-Services/311-Service-Requests-from-2010-to-Present/erm2-nwe9)
- [NYC OpenData — DOT Street Lights and Traffic Signals (311 Service Requests)](https://data.cityofnewyork.us/Transportation/DOT-Street-Lights-and-Traffic-Signals-311-Service-/jwvp-gyiq)
- [NYC DOT — Streetlights](https://www.nyc.gov/html/dot/html/infrastructure/streetlights.shtml)
- [NYC Rules § 2-20 Street Light and Power](https://codelibrary.amlegal.com/codes/newyorkcity/latest/NYCrules/0-0-0-62948)
- [NYC DOT Street Lighting Specifications PDF (NYSDOT mirror)](https://www.dot.ny.gov/main/business-center/designbuildproject55/repository/D900055%20NYCDOT%20Street%20Lighting%20Specifications%20-%2020220519.pdf)
- [amNY — LED streetlight conversion in NYC more than 70%](https://www.amny.com/news/led-streetlight-conversion-in-nyc-more-than-70-1-14280026/)
- [Wikipedia — New York City Department of Transportation](https://en.wikipedia.org/wiki/New_York_City_Department_of_Transportation)
- [Homeyou — Electrician costs in New York, NY](https://www.homeyou.com/ny/electrician-new-york-costs)
- [Ecosmart — How much does a street light cost?](https://www.ecosmartinc.com/how-much-does-a-street-light-cost/)
- [Lightwaytraffic — How much does a street light cost?](https://www.lightwaytraffic.com/how-much-does-a-street-light-cost/)
- [LA Lights — Cost of Service and Street Light Assessment](https://lalights.lacity.org/residents/cost_of_svc_and_stlighting_assessments.html)

---

## 8. How to audit or update these numbers

1. **To re-pull 2024 volume:** run the Socrata SoQL query above against `erm2-nwe9`. No API key required for low volume.
2. **To refresh the historical sample:** pull a fresh CSV per borough from the same dataset with a `created_date` range of your choice, drop into `data/*.csv`, and run `python build.py`.
3. **To refine the revenue estimate:** if NYC DOT publishes per-unit contract rates (e.g. via a FOIL response), replace the `$200–$500` range in `docs/NAPKIN_BRIEF.md` and in the About page copy, and refresh the Napkin graphic.
