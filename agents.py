from langchain.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_community.utilities import SQLDatabase
from langchain.schema.runnable import RunnablePassthrough
import datetime
import mysql.connector
from dotenv import load_dotenv
import os
import json

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
        ssl_ca="isrgrootx1 (5).pem"  # Path to the CA certificate
    )

# Retrieval Tool
def retrieve_member_data(name):
    query = """
    SELECT md.member_id, md.name, md.investment_balance, md.credit_score, md.phone,
           lh.loan_id, lh.amount, lh.status, lh.due_date, lh.balance
    FROM member_data md
    LEFT JOIN loan_history2 lh ON md.member_id = lh.member_id
    WHERE md.name = %s
    """
    return db.run(query, parameters=[name])

# Analysis Chain
llm = OllamaLLM(model="llama3")  # Ensure Ollama is running
prompt = PromptTemplate(
    input_variables=["data", "amount"],
    template="""
    Analyze the following member data: {data} for a loan of ${amount}. 
    Predict if the member will default. Output in JSON: 
    {'eligible': 'yes/no', 'reasons': 'brief explanation', 'current_balance': balance, 'due_date': 'date or none'}. 
    Eligible if no defaults and loan <= 3x investment_balance. Suggest 'remind' if due_date is within 7 days.
    """
)
analysis_chain = prompt | llm

# Notification Function (in-app version)
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
def process_loan_request(name, amount):
    data = retrieve_member_data(name)
    if not data or not any(data):
        return {"error": "Member not found"}
    
    data_str = str(data)
    analysis = analysis_chain.invoke({"data": data_str, "amount": amount})
    
    try:
        result = json.loads(analysis.strip())
        member_id = data[0][0] if data and len(data[0]) > 0 else None
        
        if result.get("eligible") == "yes" and "remind" in result.get("reasons", "").lower() and member_id:
            notification = process_notification(member_id, f"Pay reminder: Due by {result.get('due_date', 'soon')}")
            result["notification"] = notification["notification"]
        
        return result
    except (json.JSONDecodeError, IndexError):
        return {"error": "Failed to parse LLM output or invalid data"}

# Export function for app.py
def get_loan_prediction(name, amount):
    return process_loan_request(name, amount)