from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_community.utilities import SQLDatabase
from langchain.schema.runnable import RunnablePassthrough
import datetime
import mysql.connector
from dotenv import load_dotenv
import os
import json
import re
import logging

# Load environment variables from .env
load_dotenv("c:/Users/mikik/OneDrive/Documents/Desktop/Smartsacco1/.env")
print("Environment variables loaded:")
for var in ['TIDB_HOST', 'TIDB_PORT', 'TIDB_USER', 'TIDB_PASSWORD', 'TIDB_DB']:
    value = os.getenv(var)
    print(f"{var}: {value}")
if not all([os.getenv('TIDB_HOST'), os.getenv('TIDB_USER'), os.getenv('TIDB_PASSWORD'), os.getenv('TIDB_DB')]):
    raise ValueError("Missing required environment variables in .env file")

# Database connection using TiDB Cloud details with SSL
db_uri = (
    f"mysql+mysqlconnector://{os.getenv('TIDB_USER')}:{os.getenv('TIDB_PASSWORD')}"
    f"@{os.getenv('TIDB_HOST')}:{os.getenv('TIDB_PORT', 4000)}/{os.getenv('TIDB_DB', 'test')}"
    "?ssl_ca=isrgrootx1 (5).pem"
)
print(f"Connecting to TiDB with URI: {db_uri}")  # Debug output
db = SQLDatabase.from_uri(db_uri)

# Direct MySQL connection for logging
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('TIDB_HOST'),
        port=int(os.getenv('TIDB_PORT', 4000)),
        user=os.getenv('TIDB_USER'),
        password=os.getenv('TIDB_PASSWORD'),
        database=os.getenv('TIDB_DB', 'test'),
        ssl_ca="C:\\Users\\mikik\\Documents\\tidb-ca.pem"  # Path to the CA certificate
    )

# Authentication function for admin_logins
def authenticate_user(email, password):
    query = "SELECT password FROM admin_logins WHERE email = %s"
    result = db.run(query, parameters=[(email,)])  # Tuple for positional parameter
    if result and result[0][0] == password:  # Simple match for now
        return True
    return False

# Retrieval Tool
def retrieve_member_data(member_id):
    query = """
    SELECT 
        md.member_id, 
        md.member_name, 
        COALESCE(SUM(i.amount_invested), 0) AS total_invested,
        md.credit_score, 
        md.member_phoneno,
        lh.loan_id, 
        lh.amount_borrowed, 
        lh.amount_due, 
        lh.amount_paid, 
        lh.due_date
    FROM 
        member_data md
    LEFT JOIN 
        loan_history2 lh ON md.member_id = lh.member_id
    LEFT JOIN 
        investments i ON md.member_id = i.member_id
    WHERE 
        md.member_id = :member_id
    GROUP BY 
        md.member_id, md.member_name, md.credit_score, md.member_phoneno, 
        lh.loan_id, lh.amount_borrowed, lh.amount_due, lh.amount_paid, lh.due_date
    """
    return db.run(query, parameters={"member_id": member_id})

# Analysis Chain
llm = OllamaLLM(model="mistral:7b")
prompt = PromptTemplate(
    input_variables=["data", "amount"],
    template="""
    Analyze the following member data: {data} for a loan of ${amount}. 
    Predict if the member will default. Output ONLY a valid JSON object with these fields:
    {{
        "eligible": "yes" or "no",
        "reasons": "brief explanation",
        "current_balance": amount_invested,
        "due_date": "date or 'none'",
        "total_invested": amount_invested,
        "credit_score": credit_score
    }}. 
    Eligible if no defaults (amount_due = 0) and loan amount <= 3x total_invested and credit_score > 450. 
    Suggest 'remind' in reasons if due_date is within 7 days from 2025-09-10 (i.e., <= '2025-09-17'). 
    Do NOT include any text outside the JSON object.
    """
)
analysis_chain = prompt | llm

# Notification Function
def process_notification(member_id, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notifications (member_id, message, sent_date) VALUES (%s, %s, %s)",
        (member_id, message, datetime.datetime.now())
    )
    conn.commit()
    conn.close()
    return {"notification": message, "member_id": member_id}

# Orchestrate
def process_loan_request(member_id, amount):
    print(f"Processing request for name: {member_id}, type: {type(member_id)}, amount: {amount}")  # Debug
    data = retrieve_member_data(member_id)
    if not data or not any(data):
        return {"error": "Member not found"}
    
    data_str = str(data)
    analysis = analysis_chain.invoke({"data": data_str, "amount": amount})
    try:
        # Extract JSON block from response
        json_str = re.search(r'\{.*\}', analysis, re.DOTALL)
        result = json.loads(json_str.group()) if json_str else {"error": "No valid JSON found"}
        member_id = data[0][0] if data and len(data[0]) > 0 else None
        
        if result.get("eligible") == "yes" and "remind" in result.get("reasons", "").lower() and member_id:
            notification = process_notification(member_id, f"Pay reminder: Due by {result.get('due_date', 'soon')}")
            result["notification"] = notification["notification"]
        
        return result
    except (json.JSONDecodeError, AttributeError) as e:
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Failed to parse LLM output: {e}, raw response: {analysis}")
        return {"error": "Failed to parse LLM output or invalid data"}

# Export function for app.py
def get_loan_prediction(member_id, amount):
    return process_loan_request(member_id, amount)