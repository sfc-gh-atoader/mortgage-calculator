import streamlit as st
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import altair as alt

st.set_page_config(page_title="Mortgage Calculator", page_icon="🏠", layout="wide")

# Row 1: Title
st.title("🏠 Mortgage Calculator")
st.write("Calculate your monthly mortgage payment and total loan costs")

# Currency selector (will be set in input column)
currency_options = {
    "EUR (€)": "€",
    "USD ($)": "$",
    "GBP (£)": "£",
    "JPY (¥)": "¥",
    "CHF (Fr)": "Fr"
}

# Row 2: Get all inputs first (in a form-like structure)
col_input, col_output = st.columns([1, 1])

with col_input:
    st.header("Loan Details")
    
    # Currency selector in input column
    selected_currency = st.selectbox(
        "Currency",
        options=list(currency_options.keys()),
        index=0  # Default to EUR
    )
    currency_symbol = currency_options[selected_currency]
    
    # Home value input
    home_value = st.number_input(
        f"Home Value ({currency_symbol})",
        min_value=0.0,
        value=100000.0,
        step=10000.0,
        format="%.2f"
    )
    
    # Downpayment input with toggle between percentage and amount
    downpayment_type = st.radio(
        "Downpayment Type",
        ["Percentage", "Amount"],
        horizontal=True
    )
    
    if downpayment_type == "Percentage":
        downpayment_pct = st.slider(
            "Downpayment (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5
        )
        downpayment_amount = home_value * (downpayment_pct / 100)
    else:
        downpayment_amount = st.number_input(
            f"Downpayment Amount ({currency_symbol})",
            min_value=0.0,
            max_value=home_value,
            value=0.0,
            step=5000.0,
            format="%.2f"
        )
        downpayment_pct = (downpayment_amount / home_value * 100) if home_value > 0 else 0
    
    # Loan amount (calculated or manual override)
    calculated_loan = home_value - downpayment_amount
    loan_amount = st.number_input(
        f"Loan Amount ({currency_symbol})",
        min_value=0.0,
        value=calculated_loan,
        step=10000.0,
        format="%.2f",
        help="Automatically calculated as Home Value - Downpayment, but can be adjusted"
    )
    
    # Interest rate
    interest_rate = st.number_input(
        "Annual Interest Rate (%)",
        min_value=0.0,
        max_value=20.0,
        value=6.5,
        step=0.1,
        format="%.2f"
    )
    
    # Loan term
    loan_term_years = st.number_input(
        "Loan Term (Years)",
        min_value=1,
        max_value=50,
        value=30,
        step=1
    )
    
    # Start date
    start_date = st.date_input(
        "Loan Start Date",
        value=datetime.now().date(),
        min_value=datetime(2000, 1, 1).date(),
        max_value=datetime(2100, 12, 31).date()
    )
    
    # Payment deferral period
    deferral_months = st.number_input(
        "Payment Deferral Period (Months)",
        min_value=0,
        max_value=120,
        value=0,
        step=1,
        help="Number of months to defer payments while still accruing interest"
    )

# Calculate mortgage details (outside column context)
if loan_amount > 0 and interest_rate > 0:
    # Monthly interest rate
    monthly_rate = interest_rate / 100 / 12
    
    # Total number of payments
    total_payments = loan_term_years * 12
    
    # Calculate interest accrued during deferral period
    if deferral_months > 0:
        # Simple interest accrual during deferral
        deferred_interest = loan_amount * monthly_rate * deferral_months
        adjusted_principal = loan_amount + deferred_interest
    else:
        deferred_interest = 0
        adjusted_principal = loan_amount
    
    # Calculate monthly payment using the mortgage formula
    # M = P * [r(1+r)^n] / [(1+r)^n - 1]
    if monthly_rate > 0:
        monthly_payment = adjusted_principal * (
            monthly_rate * (1 + monthly_rate) ** total_payments
        ) / ((1 + monthly_rate) ** total_payments - 1)
    else:
        monthly_payment = adjusted_principal / total_payments
    
    # Calculate total amount paid
    total_amount_paid = monthly_payment * total_payments
    
    # Calculate total interest
    total_interest = total_amount_paid - loan_amount
    
    # Calculate payoff date
    first_payment_date = datetime.combine(start_date, datetime.min.time()) + relativedelta(months=deferral_months)
    payoff_date = first_payment_date + relativedelta(months=total_payments)
    
    # Generate amortization schedule
    schedule_data = []
    balance = adjusted_principal
    cumulative_interest = 0
    cumulative_principal = 0
    
    for month in range(1, total_payments + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        cumulative_interest += interest_payment
        cumulative_principal += principal_payment
        
        # Store every month for detailed chart, but we can sample for very long loans
        if total_payments <= 360 or month % max(1, total_payments // 360) == 0 or month == total_payments:
            payment_date = first_payment_date + relativedelta(months=month-1)
            schedule_data.append({
                "Month": month,
                "Date": payment_date,
                "Balance": max(0, balance),  # Ensure no negative balance due to rounding
                "Principal": cumulative_principal,
                "Interest": cumulative_interest
            })
    
    amortization_df = pd.DataFrame(schedule_data)

# Row 1 (continued): Display chart after title
if loan_amount > 0 and interest_rate > 0:
    st.subheader("Loan Amortization Over Time")
    
    # Create chart data in long format for Altair
    chart_data = pd.DataFrame({
        "Date": amortization_df["Date"].tolist() * 3,
        "Amount": (
            amortization_df["Balance"].tolist() + 
            amortization_df["Principal"].tolist() + 
            amortization_df["Interest"].tolist()
        ),
        "Type": (
            ["Balance"] * len(amortization_df) + 
            ["Principal Paid"] * len(amortization_df) + 
            ["Interest Paid"] * len(amortization_df)
        )
    })
    
    # Create interactive bar chart with Altair
    chart = alt.Chart(chart_data).mark_bar(size=20).encode(
        x=alt.X("Date:T", title="Date", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("Amount:Q", title="Amount ($)"),
        color=alt.Color("Type:N", title="Category"),
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%B %Y"),
            alt.Tooltip("Type:N", title="Category"),
            alt.Tooltip("Amount:Q", title="Amount", format=",.2f")
        ]
    ).properties(
        height=400
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)

# Row 2: Right column - Output metrics (reuse the col_output from above)
with col_output:
    st.header("Calculation Results")
    
    if loan_amount > 0 and interest_rate > 0:
        st.metric(
            "Monthly Payment",
            f"{currency_symbol}{monthly_payment:,.2f}"
        )
        
        st.metric(
            "First Payment Date",
            first_payment_date.strftime("%B %d, %Y")
        )
        
        st.metric(
            "Loan Payoff Date",
            payoff_date.strftime("%B %d, %Y")
        )
        
        st.metric(
            "Total Interest Paid",
            f"{currency_symbol}{total_interest:,.2f}"
        )
        
        st.metric(
            "Total Amount Paid",
            f"{currency_symbol}{total_amount_paid:,.2f}"
        )
        
        # Additional summary
        st.divider()
        st.subheader("Summary")
        
        summary_data = {
            "Item": [
                "Home Value",
                "Downpayment",
                "Downpayment %",
                "Loan Amount",
                "Interest Rate",
                "Loan Term",
                "Deferral Period",
                "Interest During Deferral",
                "Adjusted Principal"
            ],
            "Value": [
                f"{currency_symbol}{home_value:,.2f}",
                f"{currency_symbol}{downpayment_amount:,.2f}",
                f"{downpayment_pct:.2f}%",
                f"{currency_symbol}{loan_amount:,.2f}",
                f"{interest_rate:.2f}%",
                f"{loan_term_years} years",
                f"{deferral_months} months",
                f"{currency_symbol}{deferred_interest:,.2f}",
                f"{currency_symbol}{adjusted_principal:,.2f}"
            ]
        }
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
    else:
        st.warning("Please enter valid loan amount and interest rate to calculate mortgage details.")
