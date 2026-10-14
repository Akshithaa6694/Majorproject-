# Financial Fraud Detection - Real-Time Streamlit Demo

## Run
```powershell
cd "C:\Users\Dell\Desktop\Devin project\Financial-Fraud-Detection"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## What works
- Demo login with any non-empty username/password
- Demo bank details
- Real-time transaction input and prediction
- Random Forest model trained on included synthetic transaction data
- Dynamic fraud risk score
- Dynamic suspicious-location comparison against the user's recent transactions
- Explainable risk reasons
- Report as Fraud / Mark as Safe actions
- SQLite transaction history
- Incoming transaction simulator for live classroom demonstration
- Dashboard-style Streamlit UI

## Important
The included data are **synthetic demo data**, not real bank records. The app is not connected to a bank, payment network, GPS provider, or live financial account. Exact physical location is not inferred automatically; the transaction location/distance must be supplied by the demo transaction source.
