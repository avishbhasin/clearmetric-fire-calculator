# FIRE Calculator — Tiny Bet #1

ClearMetric's first micro-app: a free web-based FIRE calculator + paid Excel template.

## Products

| Product | Type | Price | Status |
|---------|------|-------|--------|
| FIRE Calculator (web) | Streamlit app | Free | Built |
| FIRE Calculator Pro | Excel template | $14.99 | Built |

## Quick Start

### Run the free web tool
```bash
cd projects/tiny-bets/fire-calculator
streamlit run app.py
```

### Build the paid Excel template
```bash
python3 build_excel.py
# Output: output/ClearMetric-FIRE-Calculator-Pro.xlsx
```

## Files

```
app.py           — Streamlit web app (free FIRE calculator)
build_excel.py   — Generates the paid Excel template
listing.md       — Gumroad product listing copy + tags
requirements.txt — Python dependencies
output/          — Generated Excel files
```

## Distribution Strategy

1. Deploy web app to Streamlit Cloud (free hosting)
2. List Excel template on Gumroad ($14.99)
3. Web app CTAs drive traffic to Gumroad product
4. Cross-promote with existing ClearMetric products
5. Reddit posts to r/financialindependence, r/FIRE, r/leanfire, r/fatFIRE

## Tech Stack

- Python 3.10+
- Streamlit (web app)
- Plotly (interactive charts)
- NumPy (Monte Carlo simulation)
- openpyxl (Excel template generation)
