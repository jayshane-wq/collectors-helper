import streamlit as st
import pandas as pd

st.set_page_config(page_title="Collectors Helper", layout="wide")


def money(x):
    return f"${x:,.2f}"


def pmt(rate_annual, n_months, principal):
    if n_months <= 0:
        return 0.0
    r = rate_annual / 12 / 100
    if abs(r) < 1e-12:
        return principal / n_months
    return (principal * r) / (1 - (1 + r) ** (-n_months))


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "form_version" not in st.session_state:
    st.session_state.form_version = 0

if "show_results" not in st.session_state:
    st.session_state.show_results = False


def field_key(name: str) -> str:
    return f"{name}_{st.session_state.form_version}"


# --------------------------------------------------
# TITLE
# --------------------------------------------------
st.title("📞 Collectors Helper")
st.caption("Guided collections conversation + affordability review + recommended workout path")


# --------------------------------------------------
# KPI DASHBOARD
# --------------------------------------------------
st.markdown("## 📊 Portfolio KPI Dashboard")

total_loans = 13152
current_loans = 11945
d_0_30 = 709
d_30_plus = 297
d_60_plus = 112
d_90_plus = 74
d_120_plus = 15

delinquent_total = total_loans - current_loans
severe_total = d_60_plus + d_90_plus + d_120_plus

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Loans", f"{total_loans:,}")
k2.metric("Current %", f"{(current_loans / total_loans) * 100:.2f}%")
k3.metric("Delinquency %", f"{(delinquent_total / total_loans) * 100:.2f}%")
k4.metric("Severe Delinquency %", f"{(severe_total / total_loans) * 100:.2f}%")

k5, k6, k7 = st.columns(3)
k5.metric("0–30", f"{d_0_30:,} ({(d_0_30 / total_loans) * 100:.2f}%)")
k6.metric("30+", f"{d_30_plus:,} ({(d_30_plus / total_loans) * 100:.2f}%)")
k7.metric("60+ Aggregate", f"{severe_total:,} ({(severe_total / total_loans) * 100:.2f}%)")

st.markdown("---")


# --------------------------------------------------
# SIDEBAR / POLICY CONTROLS
# --------------------------------------------------
with st.sidebar:
    st.header("Policy Controls")
    st.caption("Leadership demo controls only. These would not be collector-editable in production.")

    repayment_months = st.slider(
        "Repayment cure window (months)",
        min_value=1,
        max_value=6,
        value=3,
        step=1
    )

    max_repayment_multiple = st.slider(
        "Max repayment multiple of current payment",
        min_value=1.0,
        max_value=3.0,
        value=2.0,
        step=0.1
    )

    mod_rate_options = [round(x * 0.125, 3) for x in range(0, 161)]  # 0.000 to 20.000 by 0.125
    mod_rate = st.select_slider(
        "Illustrative modification rate (%)",
        options=mod_rate_options,
        value=6.0,
        format_func=lambda x: f"{x:.3f}"
    )

    max_mod_term = st.slider(
        "Maximum modified term (months)",
        min_value=12,
        max_value=120,
        value=72,
        step=6
    )

    household_buffer_per_person = st.number_input(
        "Household living expense buffer per person",
        min_value=0.0,
        value=200.0,
        step=25.0
    )


# --------------------------------------------------
# SECTION 1 - HARDSHIP
# --------------------------------------------------
st.markdown("### 1) Hardship Review")
left, right = st.columns(2)

with left:
    hardship_type = st.radio(
        "Hardship Type",
        ["Temporary", "Permanent"],
        horizontal=True,
        key=field_key("hardship_type")
    )

    hardship_reason = st.selectbox(
        "Reason for Default / Delinquency",
        [
            "Medical",
            "Job Loss",
            "Reduced Income",
            "Disability (Temporary)",
            "Disability (Permanent)",
            "Death of spouse",
            "Divorce / Separation",
            "Unexpected expenses",
            "Other"
        ],
        key=field_key("hardship_reason")
    )

with right:
    currently_employed = st.toggle(
        "Currently Employed",
        value=True,
        key=field_key("currently_employed")
    )

    months_to_reemployment = None
    if not currently_employed:
        months_to_reemployment = st.number_input(
            "Expected Months to Return to Work",
            min_value=0,
            max_value=24,
            value=2,
            step=1,
            key=field_key("months_to_reemployment")
        )

    hardship_notes = st.text_area(
        "Collector Notes",
        height=100,
        key=field_key("hardship_notes")
    )


# --------------------------------------------------
# SECTION 2 - LOAN INPUTS
# --------------------------------------------------
st.markdown("### 2) Loan Inputs")
l1, l2 = st.columns(2)

with l1:
    balance = st.number_input(
        "Outstanding Loan Balance",
        min_value=0.0,
        value=12000.0,
        step=100.0,
        key=field_key("balance")
    )

    rate = st.number_input(
        "Current Interest Rate (%)",
        min_value=0.0,
        value=18.0,
        step=0.25,
        key=field_key("rate")
    )

    remaining_term = st.number_input(
        "Remaining Months on Loan",
        min_value=1,
        value=36,
        step=1,
        key=field_key("remaining_term")
    )

with l2:
    entered_payment = st.number_input(
        "Current Monthly Payment (leave 0 to auto-calc)",
        min_value=0.0,
        value=0.0,
        step=25.0,
        key=field_key("entered_payment")
    )

    current_payment = entered_payment if entered_payment > 0 else pmt(rate, remaining_term, balance)

    payments_past_due = st.number_input(
        "Payments Past Due",
        min_value=0,
        value=2,
        step=1,
        key=field_key("payments_past_due")
    )

    manual_past_due_amount = st.number_input(
        "Past Due Amount Override (optional)",
        min_value=0.0,
        value=0.0,
        step=25.0,
        key=field_key("manual_past_due_amount")
    )

    arrears = manual_past_due_amount if manual_past_due_amount > 0 else current_payment * payments_past_due


# --------------------------------------------------
# SECTION 3 - INCOME / EXPENSE
# --------------------------------------------------
st.markdown("### 3) Income & Expense Review")
c1, c2, c3 = st.columns(3)

with c1:
    income = st.number_input(
        "Total Household Income",
        min_value=0.0,
        value=4500.0,
        step=50.0,
        key=field_key("income")
    )
    housing = st.number_input(
        "Housing",
        min_value=0.0,
        value=1200.0,
        step=25.0,
        key=field_key("housing")
    )
    utilities = st.number_input(
        "Utilities",
        min_value=0.0,
        value=250.0,
        step=25.0,
        key=field_key("utilities")
    )

with c2:
    food = st.number_input(
        "Food",
        min_value=0.0,
        value=700.0,
        step=25.0,
        key=field_key("food")
    )
    car = st.number_input(
        "Car / Transportation",
        min_value=0.0,
        value=400.0,
        step=25.0,
        key=field_key("car")
    )
    phone = st.number_input(
        "Phone",
        min_value=0.0,
        value=120.0,
        step=10.0,
        key=field_key("phone")
    )

with c3:
    internet = st.number_input(
        "Internet",
        min_value=0.0,
        value=80.0,
        step=10.0,
        key=field_key("internet")
    )
    other = st.number_input(
        "Other Expenses",
        min_value=0.0,
        value=300.0,
        step=25.0,
        key=field_key("other")
    )
    household_size = st.number_input(
        "Household Size",
        min_value=1,
        value=3,
        step=1,
        key=field_key("household_size")
    )

household_buffer = household_size * household_buffer_per_person
living_expenses = housing + utilities + food + car + phone + internet + other + household_buffer

# cash available before any loan payment
cash_available = income - living_expenses

# affordability after current payment
current_affordability = cash_available - current_payment


# --------------------------------------------------
# SECTION 4 - BUTTONS
# --------------------------------------------------
st.markdown("### 4) Decisioning")
b1, b2, b3 = st.columns(3)

with b1:
    if st.button("Calculate Recommendation", type="primary", use_container_width=True):
        st.session_state.show_results = True

with b2:
    if st.button("Clear Results", use_container_width=True):
        st.session_state.show_results = False
        st.rerun()

with b3:
    if st.button("Reset Full Form", use_container_width=True):
        st.session_state.form_version += 1
        st.session_state.show_results = False
        st.rerun()


# --------------------------------------------------
# DECISION ENGINE
# --------------------------------------------------
if st.session_state.show_results:
    permanent_hardship = (
        hardship_type == "Permanent"
        or hardship_reason in [
            "Reduced Income",
            "Disability (Permanent)",
            "Death of spouse",
            "Divorce / Separation"
        ]
    )

    # candidate offer calculations
    repayment_payment = current_payment + (arrears / max(repayment_months, 1))
    deferral_payment = current_payment
    mod_principal = balance + arrears
    mod_term = max_mod_term
    mod_payment = pmt(mod_rate, mod_term, mod_principal)

    recommendation = None
    alternatives = []

    # 1) Temporary unemployment / expected back soon -> Forbearance
    if not currently_employed and months_to_reemployment is not None and months_to_reemployment <= 3:
        recommendation = {
            "plan": "Forbearance",
            "payment": 0.0,
            "approval": "Standard agent authority",
            "summary": "Borrower is currently unemployed but expects to return to work soon.",
            "details": f"Forbear {min(months_to_reemployment, payments_past_due)} payment(s) and re-evaluate upon return to work.",
            "script": "Because you are currently unemployed and expect to return to work soon, a short-term forbearance may be the best fit."
        }

    # 2) No income or no cash -> Charge-Off / Recovery
    elif income <= 0 or cash_available <= 0:
        recommendation = {
            "plan": "Charge-Off / Recovery",
            "payment": 0.0,
            "approval": "Manager / recovery workflow",
            "summary": "No income or no available cash to support a retention option.",
            "details": "Borrower has no available income to support repayment, deferral, or modification under current inputs.",
            "script": "Based on the information available today, I’m not seeing a sustainable payment solution. Let me explain the next steps and document your situation accurately."
        }

    # 3) Current payment not affordable -> test Modification
    elif current_affordability < 0:
        if cash_available >= mod_payment:
            recommendation = {
                "plan": "Modification",
                "payment": mod_payment,
                "approval": "Manager approval required",
                "summary": "Current payment is not affordable, but a modified payment restores affordability.",
                "details": f"Modified payment of {money(mod_payment)} at {mod_rate:.3f}% over {mod_term} months on a capitalized balance of {money(mod_principal)} fits within available cash.",
                "script": "The current payment appears unaffordable, but a modification may create a more sustainable payment structure."
            }
        else:
            recommendation = {
                "plan": "Charge-Off / Recovery",
                "payment": 0.0,
                "approval": "Manager / recovery workflow",
                "summary": "Current payment is not affordable and no viable modification was identified.",
                "details": "Available cash does not support the modified payment at the illustrative rate and maximum term.",
                "script": "Based on the information available today, I’m not seeing a sustainable payment solution. Let me explain the next steps and document your situation accurately."
            }

    # 4) Current payment affordable -> Repayment or Deferral
    else:
        repay_affordable = (
            cash_available >= repayment_payment
            and repayment_payment <= current_payment * max_repayment_multiple
        )

        if repay_affordable:
            recommendation = {
                "plan": "Repayment",
                "payment": repayment_payment,
                "approval": "Standard agent authority",
                "summary": "Borrower can cure delinquency within a short time frame.",
                "details": f"Estimated repayment payment is {money(repayment_payment)} for {repayment_months} month(s).",
                "script": "Based on your budget, it looks like you can support a short-term catch-up plan to bring the account current."
            }

            alternatives.append({
                "Plan": "Deferral",
                "Est. Payment": money(deferral_payment),
                "Approval Path": "Standard agent authority",
                "Summary": f"Alternative path: defer {money(arrears)} and resume the regular payment of {money(deferral_payment)}."
            })

            if permanent_hardship and cash_available >= mod_payment:
                alternatives.append({
                    "Plan": "Modification",
                    "Est. Payment": money(mod_payment),
                    "Approval Path": "Manager approval required",
                    "Summary": "Alternative path for long-term sustainability due to permanent hardship."
                })

        else:
            recommendation = {
                "plan": "Deferral",
                "payment": deferral_payment,
                "approval": "Standard agent authority",
                "summary": "Borrower can resume the regular payment but not a higher catch-up payment.",
                "details": f"Past due amount of {money(arrears)} would be deferred. Ongoing payment remains {money(deferral_payment)}.",
                "script": "You may be a fit for a deferral, where the past due balance is moved to the end while you resume the regular monthly payment."
            }

            if permanent_hardship and cash_available >= mod_payment:
                alternatives.append({
                    "Plan": "Modification",
                    "Est. Payment": money(mod_payment),
                    "Approval Path": "Manager approval required",
                    "Summary": "Alternative path for long-term sustainability due to permanent hardship."
                })

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------
    st.markdown("## Recommendation")

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Current Payment", money(current_payment))
    m2.metric("Past Due Amount", money(arrears))
    m3.metric("Living Expenses", money(living_expenses))
    m4.metric("Cash Available", money(cash_available))
    m5.metric("Current Affordability", money(current_affordability))
    m6.metric("Recommended Plan", recommendation["plan"])

    st.success(f"Recommended Plan: {recommendation['plan']}")
    st.write(recommendation["summary"])
    st.write(f"**Estimated Payment:** {money(recommendation['payment'])}")
    st.write(f"**Details:** {recommendation['details']}")
    st.write(f"**Approval Path:** {recommendation['approval']}")

    if recommendation["plan"] == "Modification":
        st.warning("Modification requires manager approval before offer presentation or finalization.")

    st.markdown("### Suggested Collector Language")
    st.info(recommendation["script"])

    if alternatives:
        st.markdown("### Alternative Options")
        alt_df = pd.DataFrame(alternatives)
        st.dataframe(alt_df, use_container_width=True, hide_index=True)

    st.markdown("### Case Summary")
    st.json({
        "Hardship Type": hardship_type,
        "Hardship Reason": hardship_reason,
        "Currently Employed": currently_employed,
        "Months to Re-employment": months_to_reemployment,
        "Outstanding Balance": money(balance),
        "Current Interest Rate": f"{rate:.3f}%",
        "Remaining Term": f"{remaining_term} months",
        "Current Payment": money(current_payment),
        "Payments Past Due": int(payments_past_due),
        "Past Due Amount": money(arrears),
        "Household Income": money(income),
        "Living Expenses": money(living_expenses),
        "Cash Available Before Loan Payment": money(cash_available),
        "Current Affordability": money(current_affordability),
        "Illustrative Mod Rate": f"{mod_rate:.3f}%",
        "Capitalized Mod Balance": money(mod_principal),
        "Illustrative Mod Term": f"{mod_term} months",
        "Illustrative Mod Payment": money(mod_payment),
        "Recommended Plan": recommendation["plan"],
        "Approval Required": recommendation["approval"]
    })