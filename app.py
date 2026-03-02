"""
FIRE Calculator — Free Web Tool by ClearMetric
https://clearmetric.gumroad.com

A comprehensive Financial Independence, Retire Early calculator with
Monte Carlo simulation, multiple withdrawal strategies, and scenario analysis.
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FIRE Calculator — ClearMetric",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .main .block-container { padding-top: 2rem; max-width: 1200px; }
    .stMetric { background: #f8f9fa; border-radius: 8px; padding: 12px; border-left: 4px solid #1a5276; }
    h1 { color: #1a5276; }
    h2, h3 { color: #2c3e50; }
    .fire-number { font-size: 2.5rem; font-weight: bold; color: #e74c3c; text-align: center; }
    .success-high { color: #27ae60; font-weight: bold; }
    .success-med { color: #f39c12; font-weight: bold; }
    .success-low { color: #e74c3c; font-weight: bold; }
    .cta-box {
        background: linear-gradient(135deg, #1a5276 0%, #2e86c1 100%);
        color: white; padding: 24px; border-radius: 12px; text-align: center;
        margin: 20px 0;
    }
    .cta-box a { color: #f0d78c; text-decoration: none; font-weight: bold; font-size: 1.1rem; }
    div[data-testid="stSidebar"] { background: #f8f9fa; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("# 🔥 FIRE Calculator")
st.markdown("**Financial Independence, Retire Early** — Find your number, test your plan, see your odds.")
st.markdown("---")

# ---------------------------------------------------------------------------
# Sidebar — User inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## Your Financial Profile")
    st.button("🔄 Update Results", use_container_width=True)

    st.markdown("### Age & Timeline")
    current_age = st.number_input("Current Age", value=30, min_value=18, max_value=70, step=1)
    target_retire_age = st.number_input("Target Retirement Age", value=45, min_value=25, max_value=80, step=1)
    life_expectancy = st.number_input("Life Expectancy", value=90, min_value=60, max_value=100, step=1)

    if current_age >= target_retire_age:
        st.warning("⚠️ Current age must be below retirement age. Results assume a 1-year minimum horizon.")
    if life_expectancy <= target_retire_age:
        st.warning("⚠️ Life expectancy should be above retirement age for meaningful results.")

    st.markdown("### Income & Expenses")
    annual_income = st.number_input("Annual Gross Income ($)", value=100_000, min_value=0, step=5_000)
    tax_rate = st.slider("Effective Tax Rate (%)", 0, 50, 25)
    monthly_expenses = st.number_input("Monthly Expenses ($)", value=4_000, min_value=0, step=250)

    st.markdown("### Current Savings")
    current_savings = st.number_input("Current Invested Assets ($)", value=150_000, min_value=0, step=10_000)
    monthly_investment = st.number_input("Monthly Investment ($)", value=2_500, min_value=0, step=250)

    st.markdown("### Investment Assumptions")
    investment_style = st.selectbox(
        "Investment Style",
        ["Aggressive (90/10 stocks/bonds)", "Moderate (70/30)", "Conservative (50/50)", "Custom"],
    )

    equity_pct_map = {"Aggressive (90/10 stocks/bonds)": 90, "Moderate (70/30)": 70, "Conservative (50/50)": 50, "Custom": 70}
    if investment_style == "Custom":
        equity_pct = st.slider("Stock Allocation (%)", 0, 100, 70)
    else:
        equity_pct = equity_pct_map[investment_style]

    inflation = st.slider("Expected Inflation (%)", 1.0, 6.0, 3.0, 0.5)
    income_growth = st.slider("Annual Income Growth (%)", 0, 15, 3)

    st.markdown("### Withdrawal Strategy")
    withdrawal_strategy = st.selectbox(
        "Withdrawal Strategy",
        ["4% Rule (Traditional)", "3.5% Rule (Conservative)", "Variable Percentage", "Guardrails"],
    )

    swr_map = {"4% Rule (Traditional)": 4.0, "3.5% Rule (Conservative)": 3.5, "Variable Percentage": 4.0, "Guardrails": 4.0}
    swr = swr_map[withdrawal_strategy]

    social_security = st.checkbox("Include Social Security / Pension?")
    ss_monthly = 0
    ss_start_age = 67
    if social_security:
        ss_monthly = st.number_input("Monthly SS/Pension ($)", value=2_000, min_value=0, step=100)
        ss_start_age = st.number_input("Starting Age", value=67, min_value=55, max_value=75)

# ---------------------------------------------------------------------------
# Core calculations
# ---------------------------------------------------------------------------
years_to_fire = max(target_retire_age - current_age, 1)
years_in_retirement = max(life_expectancy - target_retire_age, 1)
inflation_rate = inflation / 100
swr_rate = swr / 100
equity_frac = equity_pct / 100
bond_frac = 1 - equity_frac
income_growth_rate = income_growth / 100

EQUITY_RETURN = 0.10  # long-term US equity nominal
EQUITY_STD = 0.16
BOND_RETURN = 0.05
BOND_STD = 0.04

nominal_return = equity_frac * EQUITY_RETURN + bond_frac * BOND_RETURN
real_return = nominal_return - inflation_rate
monthly_real = (1 + real_return) ** (1/12) - 1

annual_expenses = monthly_expenses * 12
expenses_at_retirement = annual_expenses * (1 + inflation_rate) ** years_to_fire
fire_number = expenses_at_retirement / swr_rate if swr_rate > 0 else 0

# Projected corpus at retirement
fv_current = current_savings * (1 + real_return) ** years_to_fire
fv_investments = 0
monthly_inv = monthly_investment
for year in range(years_to_fire):
    for month in range(12):
        months_left = (years_to_fire - year) * 12 - month
        fv_investments += monthly_inv * (1 + monthly_real) ** months_left
    monthly_inv *= (1 + income_growth_rate)

projected_corpus = fv_current + fv_investments
gap = fire_number - projected_corpus
on_track = projected_corpus >= fire_number

# Years to FIRE at current pace
def calc_years_to_fire():
    corpus = current_savings
    mi = monthly_investment
    for yr in range(100):
        for _ in range(12):
            corpus = corpus * (1 + monthly_real) + mi
        if corpus >= fire_number:
            return yr + 1
        mi *= (1 + income_growth_rate)
    return None

actual_fire_years = calc_years_to_fire()
actual_fire_age = current_age + actual_fire_years if actual_fire_years else None

# Additional monthly investment needed
def calc_additional_monthly():
    if on_track:
        return 0
    months = years_to_fire * 12
    if monthly_real == 0:
        return gap / months
    return gap * monthly_real / ((1 + monthly_real) ** months - 1)

extra_monthly = calc_additional_monthly()

# After-tax income
net_annual_income = annual_income * (1 - tax_rate / 100)
savings_rate = (monthly_investment * 12) / net_annual_income * 100 if net_annual_income > 0 else 0

# ---------------------------------------------------------------------------
# Monte Carlo simulation
# ---------------------------------------------------------------------------
NUM_SIMS = 2000

def run_monte_carlo(
    n_sims, yrs, current, monthly, inc_growth, eq_frac, bnd_frac, infl, swr_r, expense_retire,
    ss_monthly_val, ss_age, retire_age, life_exp
):
    rng = np.random.default_rng(42)
    blended_mean = eq_frac * EQUITY_RETURN + bnd_frac * BOND_RETURN - infl
    blended_std = np.sqrt((eq_frac * EQUITY_STD) ** 2 + (bnd_frac * BOND_STD) ** 2)

    final_corpus = np.zeros(n_sims)
    all_paths = np.zeros((n_sims, yrs + 1))

    for sim in range(n_sims):
        corpus = current
        mi = monthly
        all_paths[sim, 0] = corpus

        for yr in range(yrs):
            annual_r = rng.normal(blended_mean, blended_std)
            corpus += mi * 12
            corpus *= (1 + annual_r)
            mi *= (1 + inc_growth)
            all_paths[sim, yr + 1] = corpus

        final_corpus[sim] = corpus

    target = expense_retire / swr_r
    success_rate = np.mean(final_corpus >= target) * 100

    # Survival analysis: simulate 30 years of withdrawals
    retire_years = life_exp - retire_age
    survived = np.zeros(n_sims, dtype=bool)
    for sim in range(n_sims):
        c = final_corpus[sim]
        annual_withdraw = expense_retire
        for yr in range(retire_years):
            annual_r = rng.normal(blended_mean * 0.8, blended_std)  # slightly lower in retirement
            age_now = retire_age + yr
            ss_income = ss_monthly_val * 12 if age_now >= ss_age else 0
            c = c * (1 + annual_r) - annual_withdraw + ss_income
            annual_withdraw *= (1 + infl)
            if c <= 0:
                break
        survived[sim] = c > 0

    survival_rate = np.mean(survived) * 100

    return {
        "final_corpus": final_corpus,
        "all_paths": all_paths,
        "target": target,
        "success_rate": success_rate,
        "survival_rate": survival_rate,
        "median": np.median(final_corpus),
        "p10": np.percentile(final_corpus, 10),
        "p25": np.percentile(final_corpus, 25),
        "p75": np.percentile(final_corpus, 75),
        "p90": np.percentile(final_corpus, 90),
    }

mc = run_monte_carlo(
    NUM_SIMS, years_to_fire, current_savings, monthly_investment,
    income_growth_rate, equity_frac, bond_frac, inflation_rate, swr_rate,
    expenses_at_retirement, ss_monthly, ss_start_age, target_retire_age, life_expectancy,
)

# ---------------------------------------------------------------------------
# Display — Key Metrics
# ---------------------------------------------------------------------------
st.markdown("## Your FIRE Numbers")

c1, c2, c3, c4 = st.columns(4)
c1.metric("🎯 FIRE Number", f"${fire_number:,.0f}", help="The portfolio size needed to sustain your lifestyle in retirement")
c2.metric("📈 Projected Portfolio", f"${projected_corpus:,.0f}",
          delta="On Track ✅" if on_track else f"Gap: ${abs(gap):,.0f}")
c3.metric("🔥 FIRE Age", f"{actual_fire_age}" if actual_fire_age else "Not reachable",
          delta=f"{actual_fire_years} years" if actual_fire_years else None)
c4.metric("💰 Savings Rate", f"{savings_rate:.1f}%",
          delta="Great!" if savings_rate >= 50 else ("Good" if savings_rate >= 25 else "Needs work"))

st.markdown("---")

# ---------------------------------------------------------------------------
# Display — Monte Carlo Results
# ---------------------------------------------------------------------------
st.markdown("## Monte Carlo Simulation")
st.caption(f"{NUM_SIMS:,} randomized scenarios based on historical market volatility")

mc_c1, mc_c2, mc_c3, mc_c4 = st.columns(4)

success_class = "success-high" if mc["success_rate"] >= 80 else ("success-med" if mc["success_rate"] >= 50 else "success-low")
mc_c1.metric("Accumulation Success", f"{mc['success_rate']:.0f}%", help="% of simulations that reach your FIRE number")
mc_c2.metric("Survival Rate (lifetime)", f"{mc['survival_rate']:.0f}%", help="% of simulations where money lasts through retirement")
mc_c3.metric("Median Portfolio", f"${mc['median']:,.0f}")
mc_c4.metric("Worst Case (10th %ile)", f"${mc['p10']:,.0f}")

# Percentile bar chart
fig_pct = go.Figure()
percentiles = ["10th\n(Bad luck)", "25th", "50th\n(Median)", "75th", "90th\n(Good luck)"]
values = [mc["p10"], mc["p25"], mc["median"], mc["p75"], mc["p90"]]
colors = ["#e74c3c", "#f39c12", "#2e86c1", "#27ae60", "#1a8c3b"]

fig_pct.add_trace(go.Bar(
    x=percentiles, y=values,
    text=[f"${v:,.0f}" for v in values],
    textposition="outside",
    marker_color=colors,
))
fig_pct.add_hline(y=mc["target"], line_dash="dash", line_color="#e74c3c", line_width=2,
                  annotation_text=f"FIRE Target: ${mc['target']:,.0f}", annotation_position="top left")
fig_pct.update_layout(
    title="Portfolio Outcomes by Percentile",
    yaxis_title="Portfolio Value ($)", yaxis_tickformat="$,.0f",
    height=400, template="plotly_white",
    margin=dict(t=60, b=40),
)
st.plotly_chart(fig_pct, use_container_width=True)

# ---------------------------------------------------------------------------
# Display — Projected Net Worth Growth
# ---------------------------------------------------------------------------
st.markdown("## Projected Net Worth Over Time")

ages = list(range(current_age, current_age + years_to_fire + 1))

# Deterministic path
det_path = [current_savings]
c_det = current_savings
mi_det = monthly_investment
for yr in range(years_to_fire):
    c_det = c_det * (1 + real_return) + mi_det * 12
    mi_det *= (1 + income_growth_rate)
    det_path.append(c_det)

# Monte Carlo fan chart
p10_path = np.percentile(mc["all_paths"], 10, axis=0)
p25_path = np.percentile(mc["all_paths"], 25, axis=0)
p50_path = np.percentile(mc["all_paths"], 50, axis=0)
p75_path = np.percentile(mc["all_paths"], 75, axis=0)
p90_path = np.percentile(mc["all_paths"], 90, axis=0)

fig_growth = go.Figure()

fig_growth.add_trace(go.Scatter(
    x=ages, y=p90_path, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
))
fig_growth.add_trace(go.Scatter(
    x=ages, y=p10_path, fill="tonexty", mode="lines", line=dict(width=0),
    fillcolor="rgba(46, 134, 193, 0.15)", name="10th–90th percentile",
))
fig_growth.add_trace(go.Scatter(
    x=ages, y=p75_path, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
))
fig_growth.add_trace(go.Scatter(
    x=ages, y=p25_path, fill="tonexty", mode="lines", line=dict(width=0),
    fillcolor="rgba(46, 134, 193, 0.3)", name="25th–75th percentile",
))
fig_growth.add_trace(go.Scatter(
    x=ages, y=p50_path, mode="lines", line=dict(color="#1a5276", width=3), name="Median path",
))
fig_growth.add_trace(go.Scatter(
    x=ages, y=det_path, mode="lines", line=dict(color="#2e86c1", width=2, dash="dot"), name="Deterministic",
))

fig_growth.add_hline(y=fire_number, line_dash="dash", line_color="#e74c3c", line_width=2,
                     annotation_text=f"FIRE Number: ${fire_number:,.0f}")

fig_growth.update_layout(
    title="Portfolio Growth — Monte Carlo Fan Chart",
    xaxis_title="Age", yaxis_title="Portfolio Value ($)", yaxis_tickformat="$,.0f",
    height=450, template="plotly_white",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=80, b=40),
)
st.plotly_chart(fig_growth, use_container_width=True)

# ---------------------------------------------------------------------------
# Display — Year-by-Year Table
# ---------------------------------------------------------------------------
with st.expander("📊 Year-by-Year Projection (Deterministic)", expanded=False):
    rows = []
    c_table = current_savings
    mi_table = monthly_investment
    annual_inc = annual_income
    for yr in range(years_to_fire + 1):
        age_yr = current_age + yr
        annual_invest = mi_table * 12
        growth = c_table * real_return if yr > 0 else 0
        rows.append({
            "Age": age_yr,
            "Year": yr,
            "Portfolio": c_table,
            "Annual Investment": annual_invest,
            "Investment Growth": growth,
            "Annual Income": annual_inc,
            "Annual Expenses": monthly_expenses * 12 * (1 + inflation_rate) ** yr,
            "FIRE Number": fire_number,
            "% of FIRE": c_table / fire_number * 100 if fire_number > 0 else 0,
        })
        if yr < years_to_fire:
            c_table = c_table * (1 + real_return) + mi_table * 12
            mi_table *= (1 + income_growth_rate)
            annual_inc *= (1 + income_growth_rate)

    df = pd.DataFrame(rows)
    st.dataframe(
        df.style.format({
            "Portfolio": "${:,.0f}",
            "Annual Investment": "${:,.0f}",
            "Investment Growth": "${:,.0f}",
            "Annual Income": "${:,.0f}",
            "Annual Expenses": "${:,.0f}",
            "FIRE Number": "${:,.0f}",
            "% of FIRE": "{:.1f}%",
        }),
        use_container_width=True,
        height=400,
    )

# ---------------------------------------------------------------------------
# Display — Action Items
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("## Your Action Plan")

if on_track:
    st.success(f"""
    **You're on track to reach FIRE by age {actual_fire_age}!**

    With ${monthly_investment:,}/month invested and a {savings_rate:.0f}% savings rate,
    your portfolio should reach ${fire_number:,.0f} in about {actual_fire_years} years.

    Monte Carlo survival rate: **{mc['survival_rate']:.0f}%** — your money has a
    {mc['survival_rate']:.0f}% chance of lasting through age {life_expectancy}.
    """)
else:
    fire_age_msg = f"**age {actual_fire_age}**" if actual_fire_age else "an unreachable target"
    st.warning(f"""
    **You're ${abs(gap):,.0f} short of your FIRE number at age {target_retire_age}.**

    To close the gap, you could:
    - Invest **${extra_monthly:,.0f}/month more** (total: ${monthly_investment + extra_monthly:,.0f}/month)
    - Push retirement to {fire_age_msg} at your current savings rate
    - Reduce expenses by **${(gap * swr_rate / 12):,.0f}/month** to lower your FIRE number
    """)

# Savings rate context
st.markdown("### How You Compare")
savings_tiers = [
    (70, "Extreme FIRE", "~8-12 years to FI", "#1a8c3b"),
    (50, "Aggressive FIRE", "~12-17 years to FI", "#27ae60"),
    (30, "Standard FIRE", "~20-28 years to FI", "#2e86c1"),
    (15, "Comfortable", "~35-45 years to FI", "#f39c12"),
    (0, "Living paycheck to paycheck", "FI is very far away", "#e74c3c"),
]

for threshold, label, timeline, color in savings_tiers:
    marker = " ← **YOU**" if threshold <= savings_rate < (savings_tiers[savings_tiers.index((threshold, label, timeline, color)) - 1][0] if savings_tiers.index((threshold, label, timeline, color)) > 0 else 101) else ""
    bar_width = min(threshold, 100)
    st.markdown(f"**{threshold}%+** {label} ({timeline}){marker}")

# ---------------------------------------------------------------------------
# CTA — Paid Product
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div class="cta-box">
    <h3 style="color: white; margin: 0 0 8px 0;">Want the Full FIRE Planning Spreadsheet?</h3>
    <p style="margin: 0 0 16px 0;">
        Get the <strong>ClearMetric FIRE Calculator Pro</strong> — a downloadable Excel template with:<br>
        ✓ 3-scenario comparison side by side<br>
        ✓ Year-by-year projection table (pre-built, editable)<br>
        ✓ Coast FIRE & Barista FIRE calculators<br>
        ✓ Social Security integration<br>
        ✓ Print-ready retirement roadmap<br>
    </p>
    <a href="https://clearmetric.gumroad.com/l/fire-calculator" target="_blank">
        Get It on Gumroad — $14.99 →
    </a>
</div>
""", unsafe_allow_html=True)

# Cross-sell
st.markdown("### More from ClearMetric")
cx1, cx2, cx3 = st.columns(3)
with cx1:
    st.markdown("""
    **📊 Budget Planner** — $13.99
    Track income, expenses, savings with the 50/30/20 framework.
    [Get it →](https://clearmetric.gumroad.com/l/budget-planner)
    """)
with cx2:
    st.markdown("""
    **📈 Stock Portfolio Tracker** — $17.99
    Track 20 stocks, dividends, sector allocation, performance.
    [Get it →](https://clearmetric.gumroad.com/l/stock-portfolio-tracker)
    """)
with cx3:
    st.markdown("""
    **🏠 Rental Property Analyzer** — $19.99
    12+ metrics, 5-year projection, 4-property comparison.
    [Get it →](https://clearmetric.gumroad.com/l/rental-property-analyzer)
    """)

# Footer
st.markdown("---")
st.caption("© 2026 ClearMetric | [clearmetric.gumroad.com](https://clearmetric.gumroad.com) | "
           "This tool is for educational purposes only. Not financial advice. Consult a qualified financial advisor.")
