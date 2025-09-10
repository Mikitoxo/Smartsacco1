import streamlit as st
import agents  # Import the agents module

# Title
st.title("SmartSacco Loan Eligibility")

# Sidebar for login
st.sidebar.header("Login")
username = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")
if st.sidebar.button("Login"):
    if username == "admin" and password == "password":  # Dummy credentials
        st.session_state.logged_in = True
    else:
        st.sidebar.error("Invalid credentials")

# Main content
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    st.header("Loan Request Form")
    member_id = st.number_input("Member id")
    amount = st.number_input("Requested Loan Amount", min_value=0.0)

    if st.button("Predict Eligibility"):
        if member_id and amount:
            with st.spinner("Analyzing..."):
                result = agents.get_loan_prediction(member_id, amount)
            if "error" in result:
                st.error(result["error"])
            else:
                st.success(f"Eligible: {result.get('eligible', 'Unknown')}")
                st.write(f"Reasons: {result.get('reasons', 'N/A')}")
                st.write(f"Current Balance: ${result.get('current_balance', 0)}")
                st.write(f"Due Date: {result.get('due_date', 'N/A')}")
                st.write(f"Total Investments: {result.get('amount_invested', 0)}")
                st.write(f"Credit score: {result.get('credit_score', 'N/A')}")
                if "notification" in result:
                    st.info(f"Notification Sent: {result['notification']}")
        else:
            st.warning("Please fill in all fields")
else:
    st.warning("Please log in to continue")