# SmartSacco AI Agent

## What
- An AI agent/LLM that predicts whether a member of a given SACCO is likely to default on a loan based on previous loan history.
- Automates notifications to borrowers to remind them to repay their loans.

## Why
- Reduce loan defaulters in SACCOs.
- Reduce management workload by automating notifications.
- Streamline and expedite the loan approval process.

## Who
- Designed for SACCOs (and potentially financial institutions like banks in the future) to assess the loan eligibility of existing members.
- Eliminates the need for manual file reviews, saving time and effort—a simple prompt to SmartSacco quickly determines member eligibility.
- Frees up financial managers to focus on the growth of the SACCO.

## How It Works (Front End)
1. A financial officer/admin or SACCO member logs into SmartSacco.
2. The officer/member fills out a form with the member's ID number and requested loan amount.
3. The model returns a **Yes** or **No** decision based on SACCO data, including:
   - Current loan balance (if any).
   - Credit score.
   - Due date for the current loan repayment (if applicable).
   - If eligible, the member can receive a loan of up to **3× their investment balance**.
