import streamlit as st
import agents   # Import the agents module

# Custom styling and branding with uniform font
st.set_page_config(page_title="SmartSacco Loan Portal", layout="wide", page_icon="💵")

st.markdown(
    """
    <style>
    .stApp {
        background-image: url('C:/Users/mikik/OneDrive/Documents/Desktop/Smartsacco1/images/sacco-bg.jpg');
        background-size: cover;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    .stHeader {
        background-color: rgba(44, 62, 80, 0.8);
        color: white;
        padding: 10px;
        text-align: center;
        font-family: Arial, sans-serif;
        font-size: 24px;
    }
    .stContent {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 10px;
        font-family: Arial, sans-serif;
        font-size: 16px;
        line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Title with Sacco branding
st.markdown("<h1 class='stHeader'>💵SmartSacco Loan Eligibility Portal💵</h1>", unsafe_allow_html=True)
st.write("Welcome to SmartSacco, your trusted cooperative for secure loans!")

# Sidebar for login
st.sidebar.header("Login")
username = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")
if st.sidebar.button("Login"):
    if username == "admin@smartsacco.com" and password == "password456":  # Dummy credentials
        st.session_state.logged_in = True
    else:
        st.sidebar.error("Invalid credentials")

# Main content
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in:
    st.markdown("<div class='stContent'>", unsafe_allow_html=True)
    st.header("Loan Request Form")
    member_id = st.number_input("Member ID", min_value=1, step=1)
    amount = st.number_input("Requested Loan Amount", min_value=0.0)

    if st.button("Predict Eligibility"):
        if member_id and amount:
            with st.spinner("Analyzing..."):
                result = agents.get_loan_prediction(member_id, amount)
            if "error" in result:
                st.error(result["error"])
            else:
                st.markdown("### Eligibility Analysis")
                st.markdown(f"<div style='font-family: Arial, sans-serif; font-size: 16px;'>{result.get('narrative', 'No analysis available.')}</div>", unsafe_allow_html=True)
                if "notification" in result:
                    st.info(f"Notification Sent: {result['notification']}")
        else:
            st.warning("Please fill in all fields")
    st.markdown("</div>", unsafe_allow_html=True)

    # Additional Sacco-specific section
    st.subheader("Sacco Updates")
    st.write("Stay tuned for new investment opportunities and repayment plans!")
else:
    st.warning("Please log in to continue")