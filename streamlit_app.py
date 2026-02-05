import streamlit as st
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import altair as alt

st.set_page_config(page_title="Calculator Ipotecar", page_icon="🏠", layout="wide")

# Row 1: Title
st.title("🏠 Calculator Ipotecar")
st.write("Calculează plata lunară a creditului ipotecar și costurile totale ale creditului")

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
    st.header("Detalii credit")
    
    # Currency selector in input column
    selected_currency = st.selectbox(
        "Monedă",
        options=list(currency_options.keys()),
        index=0  # Default to EUR
    )
    currency_symbol = currency_options[selected_currency]
    
    # Home value input
    home_value = st.number_input(
        f"Valoarea imobilului ({currency_symbol})",
        min_value=0.0,
        value=125000.0,
        step=10000.0,
        format="%.2f"
    )
    
    # Downpayment input with toggle between percentage and amount
    downpayment_type = st.radio(
        "Tip avans",
        ["Procent", "Sumă"],
        horizontal=True
    )
    
    if downpayment_type == "Procent":
        downpayment_pct = st.slider(
            "Avans (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.5
        )
        downpayment_amount = home_value * (downpayment_pct / 100)
    else:
        downpayment_amount = st.number_input(
            f"Suma avansului ({currency_symbol})",
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
        f"Suma creditului ({currency_symbol})",
        min_value=0.0,
        value=calculated_loan,
        step=10000.0,
        format="%.2f",
        help="Calculată automat ca Valoarea imobilului - Avans, dar poate fi ajustată"
    )
    
    # Interest rate
    interest_rate = st.number_input(
        "Rata anuală a dobânzii (%)",
        min_value=0.0,
        max_value=20.0,
        value=4.5,
        step=0.1,
        format="%.2f"
    )
    
    # Loan term
    loan_term_years = st.number_input(
        "Perioada creditului (ani)",
        min_value=1,
        max_value=50,
        value=30,
        step=1
    )
    
    # Start date
    start_date = st.date_input(
        "Data începerii creditului",
        value=datetime.now().date(),
        min_value=datetime(2000, 1, 1).date(),
        max_value=datetime(2100, 12, 31).date()
    )
    
    # Grace period (no interest, no payments)
    grace_months = st.number_input(
        "Perioadă de grație (luni)",
        min_value=0,
        max_value=120,
        value=0,
        step=1,
        help="Numărul de luni fără plăți și fără acumulare de dobândă"
    )
    
    # Payment deferral period (interest accrues, no payments)
    deferral_months = st.number_input(
        "Perioadă amânare plăți (luni)",
        min_value=0,
        max_value=120,
        value=0,
        step=1,
        help="Numărul de luni pentru amânarea plăților în timp ce dobânda se acumulează compus lunar"
    )

# Calculate mortgage details (outside column context)
if loan_amount > 0 and interest_rate > 0:
    # Monthly interest rate
    monthly_rate = interest_rate / 100 / 12
    
    # Total number of payments
    total_payments = loan_term_years * 12
    
    # Calculate interest accrued during deferral period
    # Grace period: no interest accrues
    # Deferral period: compound interest accrues monthly
    if deferral_months > 0:
        # Compound interest accrual during deferral (more accurate for mortgages)
        adjusted_principal = loan_amount * ((1 + monthly_rate) ** deferral_months)
        deferred_interest = adjusted_principal - loan_amount
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
    # First payment is after grace period + deferral period
    first_payment_date = datetime.combine(start_date, datetime.min.time()) + relativedelta(months=grace_months + deferral_months)
    payoff_date = first_payment_date + relativedelta(months=total_payments)
    
    # Generate amortization schedule
    schedule_data = []  # For chart (sampled)
    detailed_schedule_data = []  # For detailed monthly table (all months)
    
    month_counter = 1
    current_date = datetime.combine(start_date, datetime.min.time())
    
    # Phase 1: Grace period (no interest accrues, no payments)
    balance = loan_amount
    for grace_month in range(grace_months):
        payment_date = current_date + relativedelta(months=grace_month)
        detailed_schedule_data.append({
            "Lună": month_counter,
            "Data": payment_date.strftime("%b %Y"),
            "Plată principal": 0,
            "Dobândă": 0,
            "Plată totală": 0,
            "Sold rămas": balance,
            "Status": "Grație"
        })
        month_counter += 1
    
    # Phase 2: Deferral period (interest accrues monthly, no payments)
    for deferral_month in range(deferral_months):
        payment_date = current_date + relativedelta(months=grace_months + deferral_month)
        interest_accrued = balance * monthly_rate
        balance += interest_accrued
        detailed_schedule_data.append({
            "Lună": month_counter,
            "Data": payment_date.strftime("%b %Y"),
            "Plată principal": 0,
            "Dobândă": interest_accrued,
            "Plată totală": 0,
            "Sold rămas": balance,
            "Status": "Amânare"
        })
        month_counter += 1
    
    # Phase 3: Regular payment period
    balance = adjusted_principal
    cumulative_interest = 0
    cumulative_principal = 0
    
    for payment_month in range(1, total_payments + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance -= principal_payment
        cumulative_interest += interest_payment
        cumulative_principal += principal_payment
        
        payment_date = first_payment_date + relativedelta(months=payment_month-1)
        
        # Store detailed data for every month (for table)
        detailed_schedule_data.append({
            "Lună": month_counter,
            "Data": payment_date.strftime("%b %Y"),
            "Plată principal": principal_payment,
            "Dobândă": interest_payment,
            "Plată totală": monthly_payment,
            "Sold rămas": max(0, balance),
            "Status": "Plată"
        })
        month_counter += 1
        
        # Store sampled data for chart visualization
        if total_payments <= 360 or payment_month % max(1, total_payments // 360) == 0 or payment_month == total_payments:
            schedule_data.append({
                "Month": payment_month,
                "Date": payment_date,
                "Balance": max(0, balance),  # Ensure no negative balance due to rounding
                "Principal": cumulative_principal,
                "Interest": cumulative_interest
            })
    
    amortization_df = pd.DataFrame(schedule_data)
    detailed_amortization_df = pd.DataFrame(detailed_schedule_data)

# Row 1 (continued): Display chart after title
if loan_amount > 0 and interest_rate > 0:
    st.subheader("Amortizarea creditului în timp")
    
    # Create chart data in long format for Altair
    chart_data = pd.DataFrame({
        "Date": amortization_df["Date"].tolist() * 3,
        "Amount": (
            amortization_df["Balance"].tolist() + 
            amortization_df["Principal"].tolist() + 
            amortization_df["Interest"].tolist()
        ),
        "Type": (
            ["Sold"] * len(amortization_df) + 
            ["Principal plătit"] * len(amortization_df) + 
            ["Dobândă plătită"] * len(amortization_df)
        )
    })
    
    # Create interactive bar chart with Altair
    chart = alt.Chart(chart_data).mark_bar(size=20).encode(
        x=alt.X("Date:T", title="Data", axis=alt.Axis(format="%b %Y")),
        y=alt.Y("Amount:Q", title="Sumă"),
        color=alt.Color("Type:N", title="Categorie"),
        tooltip=[
            alt.Tooltip("Date:T", title="Data", format="%B %Y"),
            alt.Tooltip("Type:N", title="Categorie"),
            alt.Tooltip("Amount:Q", title="Sumă", format=",.2f")
        ]
    ).properties(
        height=400
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)
    
    # Detailed monthly payment schedule table
    st.subheader("Scadentar lunar detaliat")
    
    # Format the detailed schedule for display
    display_df = detailed_amortization_df.copy()
    display_df["Plată principal"] = display_df["Plată principal"].apply(lambda x: f"{currency_symbol}{x:,.2f}")
    display_df["Dobândă"] = display_df["Dobândă"].apply(lambda x: f"{currency_symbol}{x:,.2f}")
    display_df["Plată totală"] = display_df["Plată totală"].apply(lambda x: f"{currency_symbol}{x:,.2f}")
    display_df["Sold rămas"] = display_df["Sold rămas"].apply(lambda x: f"{currency_symbol}{x:,.2f}")
    
    st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)

# Row 2: Right column - Output metrics (reuse the col_output from above)
with col_output:
    st.header("Rezultate calcul")
    
    if loan_amount > 0 and interest_rate > 0:
        st.metric(
            "Plată lunară",
            f"{currency_symbol}{monthly_payment:,.2f}"
        )
        
        st.metric(
            "Data primei plăți",
            first_payment_date.strftime("%d %B %Y")
        )
        
        st.metric(
            "Data finalizării creditului",
            payoff_date.strftime("%d %B %Y")
        )
        
        st.metric(
            "Total dobândă plătită",
            f"{currency_symbol}{total_interest:,.2f}"
        )
        
        st.metric(
            "Suma totală plătită",
            f"{currency_symbol}{total_amount_paid:,.2f}"
        )
        
        # Additional summary
        st.divider()
        st.subheader("Rezumat")
        
        summary_data = {
            "Parametru": [
                "Valoarea imobilului",
                "Avans",
                "Avans %",
                "Suma creditului",
                "Rata dobânzii",
                "Perioada creditului",
                "Perioadă de grație",
                "Perioadă amânare",
                "Dobândă acumulată în perioada de amânare",
                "Principal ajustat"
            ],
            "Value": [
                f"{currency_symbol}{home_value:,.2f}",
                f"{currency_symbol}{downpayment_amount:,.2f}",
                f"{downpayment_pct:.2f}%",
                f"{currency_symbol}{loan_amount:,.2f}",
                f"{interest_rate:.2f}%",
                f"{loan_term_years} ani",
                f"{grace_months} luni",
                f"{deferral_months} luni",
                f"{currency_symbol}{deferred_interest:,.2f}",
                f"{currency_symbol}{adjusted_principal:,.2f}"
            ]
        }
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
    else:
        st.warning("Te rog introdu o sumă validă a creditului și o rată a dobânzii pentru a calcula detaliile ipotecare.")
