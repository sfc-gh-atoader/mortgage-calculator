import streamlit as st
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd

st.set_page_config(page_title="Mortgage Calculator", page_icon="🏠", layout="wide")

st.title("🏠 Mortgage Calculator")
st.write("Calculate your monthly mortgage payment and total loan costs")

# Create two columns for input and output
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Loan Details")
    
    # Home value input
    home_value = st.number_input(
        "Home Value ($)",
        min_value=0.0,
        value=500000.0,
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
            value=20.0,
            step=0.5
        )
        downpayment_amount = home_value * (downpayment_pct / 100)
    else:
        downpayment_amount = st.number_input(
            "Downpayment Amount ($)",
            min_value=0.0,
            max_value=home_value,
            value=home_value * 0.20,
            step=5000.0,
            format="%.2f"
        )
        downpayment_pct = (downpayment_amount / home_value * 100) if home_value > 0 else 0
    
    # Loan amount (calculated or manual override)
    calculated_loan = home_value - downpayment_amount
    loan_amount = st.number_input(
        "Loan Amount ($)",
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

# Calculate mortgage details
with col2:
    st.header("Calculation Results")
    
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
        
        # Display results in metric cards
        st.metric(
            "Monthly Payment",
            f"${monthly_payment:,.2f}"
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
            f"${total_interest:,.2f}"
        )
        
        st.metric(
            "Total Amount Paid",
            f"${total_amount_paid:,.2f}"
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
                f"${home_value:,.2f}",
                f"${downpayment_amount:,.2f}",
                f"{downpayment_pct:.2f}%",
                f"${loan_amount:,.2f}",
                f"{interest_rate:.2f}%",
                f"{loan_term_years} years",
                f"{deferral_months} months",
                f"${deferred_interest:,.2f}",
                f"${adjusted_principal:,.2f}"
            ]
        }
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
    else:
        st.warning("Please enter valid loan amount and interest rate to calculate mortgage details.")
