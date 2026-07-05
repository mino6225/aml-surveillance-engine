import pandas as pd
import random   
import datetime
from datetime import timedelta
from dataclasses import dataclass, field
import os 
import uuid
import networkx as nx
from pyvis.network import Network

# ============================================================
# MODULE 1 — SYNTHETIC DATA GENERATION
# ============================================================

# Define a dataclass for transactions
@dataclass
class Transaction:
    transaction_id: str
    account_id: str
    counterparty_id: str
    jurisdiction: str
    transaction_type: str
    amount: float
    date: datetime.datetime
    flagged: bool = field(default=False)

def generate_random_transactions(num_transactions=1000):
    
    # Define the possible values for jurisdiction and transaction type
    jurisdictions = ['USA', 'UK', 'Germany', 'France', 'China', 'Russia', 
                    'India', 'Iran', 'North Korea', 'Syria', 'Myanmar', 'Cuba']
    transaction_types = ['Wire Transfer', 'Cash Deposit', 'ACH', 'Online Payment']
    
    # Create an empty list to hold all transactions
    transactions = []   
    
    # LEGITIMATE TRANSACTIONS
    # Loop 1000 times, generating one fresh transaction per iteration
    for _ in range(num_transactions):
        transaction_id = str(uuid.uuid4())
        account_id = f"Account_{random.randint(10, 100)}"
        counterparty_id = f"Account_{random.randint(10, 100)}"
        jurisdiction = random.choice(jurisdictions)
        transaction_type = random.choice(transaction_types)
        amount = round(random.uniform(100, 50000), 2)
        date = datetime.datetime.now() - timedelta(days=random.randint(0, 365))
        transactions.append(Transaction(
            transaction_id=transaction_id,
            account_id=account_id,
            counterparty_id=counterparty_id,
            jurisdiction=jurisdiction,
            transaction_type=transaction_type,
            amount=amount,
            date=date,
            flagged=False  
        ))
    
    # STRUCTURING PATTERNS 
    # Accounts 1-5 will be structuring suspects
    # Each account makes 10 transactions just below the $10,000 threshold
    # This simulates someone deliberately breaking up a large amount
    for account_num in range(1, 6):
        for _ in range(10):
            transactions.append(Transaction(
                transaction_id=str(uuid.uuid4()),
                # Use the specific suspect account number
                account_id=f"Account_{account_num}",
                counterparty_id=f"Account_{random.randint(10, 100)}",
                jurisdiction=random.choice(jurisdictions),
                transaction_type='Cash Deposit',
                # Amount deliberately between $9,000-$9,999 — just below threshold
                amount=round(random.uniform(9000, 9999), 2),
                # Spread across last 30 days — realistic structuring window
                date=datetime.datetime.now() - timedelta(days=random.randint(0, 30)),
                flagged=True
            ))
    
    # RAPID MOVEMENT PATTERNS
    # Accounts 6-8 will be rapid movement suspects
    # Each account receives money then sends it out within hours — classic layering
    for account_num in range(6, 9):
        for _ in range(5):
            receive_date = datetime.datetime.now() - timedelta(hours=random.randint(24, 72))
            send_date = receive_date + timedelta(hours=random.randint(1, 3))
            amount = round(random.uniform(5000, 30000), 2)
            
            # Incoming transaction — money arriving
            transactions.append(Transaction(
                transaction_id=str(uuid.uuid4()),
                account_id=f"Account_{account_num}",
                counterparty_id=f"Account_{random.randint(10, 100)}",
                jurisdiction=random.choice(jurisdictions),
                transaction_type='Wire Transfer',
                amount=amount,
                date=receive_date,
                flagged=False  
            ))
            
            # Outgoing transaction — money leaving shortly after
            transactions.append(Transaction(
                transaction_id=str(uuid.uuid4()),
                account_id=f"Account_{account_num}",
                counterparty_id=f"Account_{random.randint(10, 100)}",
                jurisdiction=random.choice(jurisdictions),
                transaction_type='Wire Transfer',
                amount=amount, 
                date=send_date,  
                flagged=True
            ))
    
    # ROUND-TRIP PATTERNS 
    # 5 pairs of accounts sending money back and forth
    # Money goes A→B then B→A — classic integration pattern
    for i in range(5):
        account_a = f"Account_{i+1}"   
        account_b = f"Account_{i+6}"  
        amount = round(random.uniform(10000, 40000), 2)
        # A sends to B
        send_date = datetime.datetime.now() - timedelta(hours=random.randint(24, 48))
        # B sends back a few hours later
        return_date = send_date + timedelta(hours=random.randint(2, 6))
        
        # A → B
        transactions.append(Transaction(
            transaction_id=str(uuid.uuid4()),
            account_id=account_a,
            counterparty_id=account_b,  
            jurisdiction=random.choice(jurisdictions),
            transaction_type='Wire Transfer',
            amount=amount,
            date=send_date,
            flagged=True
        ))
        
        # B → A (the return trip — account_id and counterparty_id are swapped)
        transactions.append(Transaction(
            transaction_id=str(uuid.uuid4()),
            account_id=account_b,       
            counterparty_id=account_a,  
            jurisdiction=random.choice(jurisdictions),
            transaction_type='Wire Transfer',
            amount=amount,  
            date=return_date,
            flagged=True
        ))
    
    return transactions

# Generate transactions and convert to dataframe
transactions = generate_random_transactions ()
df = pd.DataFrame([t.__dict__ for t in transactions])
print(f"Total transactions generated: {len(df)}")
print(f"Flagged transactions: {df['flagged'].sum()}")
print(df.head())

# Save the raw data to CSV
filepath = os.path.expanduser("~/Downloads/aml-surveillance-engine/raw_transactions.csv")
df.to_csv(filepath, index=False) 

# ============================================================
# MODULE 2 — DATA INGESTION AND CLEANING
# ============================================================

# Reload from CSV
df_loaded = pd.read_csv(filepath)

# Check for null values
total_missing = df_loaded.isnull().sum().sum()

# Filter rows where values are null
if total_missing < 1:
    print("No missing values found")

# Check for duplicate transaction IDs
total_duplicates = df_loaded.duplicated(subset=['transaction_id']).sum()

# Filter rows where transaction IDs are duplicates
if total_duplicates < 1:
    print("No duplicate transaction IDs found")

# Overwrite date column to reclassify dtype of dates
df_loaded['date'] = pd.to_datetime(df_loaded['date'])

# Data is clean but going through cleaning steps regardless for practice
# Drop duplicate transaction IDs
df_loaded_clean =  df_loaded.drop_duplicates(subset=['transaction_id'])

# Parse date column to datetime
df_loaded_clean["date"] = pd.to_datetime(df_loaded_clean['date'])

# Drop nulls from dataset
df_loaded_clean =  df_loaded_clean.dropna()

# Print data quality report
print(f"Total transactions generated: {len(df_loaded)}")
print(f"Total missing values: {total_missing}")
print(f"Total duplicate transaction IDs: {total_duplicates}")
print(df_loaded_clean.shape)

# ============================================================
# MODULE 3 — AML RULE ENGINE
# ============================================================

# Create high-risk jurisdiction list
HIGH_RISK_JURISDICTIONS = ["Iran", "North Korea", "Syria", "Myanmar", "Cuba"]

# Rule results to serve as results dictionary
rule_results = []

# HRJ-001: High Risk Jurisdictions
# Flag transactions where the jurisdiction is in the high-risk list
# This rule matters in AML because transactions involving high-risk jurisdictions are more likely to be associated with money laundering

def rule_high_risk_jurisdiction(df_loaded_clean):
    flagged = df_loaded_clean[df_loaded_clean["jurisdiction"].isin(HIGH_RISK_JURISDICTIONS)]
    result = {
        "rule_name": "High Risk Jurisdictions",
        "rule_code": "HRJ-001",
        "flagged_transactions": flagged,
        "flagged_account_ids": flagged["account_id"].unique(),
        "transaction_count": len(flagged),
        "account_count": len(flagged["account_id"].unique()),   
        "summary": f"{len(flagged)} transactions flagged across {len(flagged['account_id'].unique())} accounts for high-risk jurisdiction exposure."
        }
    return result

# STR-001: Structuring
# Flag transactions where the transaction type is "Cash Deposit" and the amount is between $9,000 and $9,999
# This rule matters in AML because structuring is a common technique used to avoid reporting requirements and can indicate attempts to launder money.

def rule_structuring(df_loaded_clean): 
    suspects = df_loaded_clean[
        (df_loaded_clean["transaction_type"] == "Cash Deposit") &
        (df_loaded_clean["amount"] >= 9000) &
        (df_loaded_clean["amount"] <= 9999)
    ]
    suspects = suspects.sort_values(["account_id", "date"])
    suspects["rolling_count"] = suspects.groupby("account_id")["date"].transform(lambda x: x.apply(lambda d: ((x >= d) & (x <= d + pd.Timedelta(days=30))).sum())
    )
    flagged = suspects[suspects["rolling_count"] >1 ]
    result = {
        "rule_name": "Structuring",
        "rule_code": "STR-001",
        "flagged_transactions": flagged,
        "flagged_account_ids": flagged["account_id"].unique(),
        "transaction_count": len(flagged),
        "account_count": len(flagged["account_id"].unique()),
        "summary": f"{len(flagged)} transactions flagged across {len(flagged['account_id'].unique())} accounts for potential structuring behavior"
    }
    return result

# RMV-001: Rapid Movement
# Flag transactions where the transaction type is "Wire Transfer" and the time gap between consecutive transactions for the same account is less than or equal to 6 hours
# This rule matters in AML because rapid movement of funds can indicate layering, a common money laundering technique used to obscure the origin of illicit funds.

def rule_rapid_movement(df_loaded_clean):
    wires = df_loaded_clean[
        (df_loaded_clean["transaction_type"] == "Wire Transfer")
    ]
    wires = wires.sort_values(["account_id", "date"])
    wires["prev_time"] = wires.groupby("account_id")["date"].shift(1)
    wires["time_gap"] = wires["date"] - wires["prev_time"]
    wire_suspects = wires[
        (wires["time_gap"] <= pd.Timedelta(hours=6))
    ]
    result = {
        "rule_name": "Rapid Movement",
        "rule_code": "RMV-001",
        "flagged_transactions": wire_suspects,
        "flagged_account_ids": wire_suspects["account_id"].unique(),
        "transaction_count": len(wire_suspects),
        "account_count": len(wire_suspects["account_id"].unique()),
        "summary": f"{len(wire_suspects)} wire transfers flagged across {len(wire_suspects['account_id'].unique())} accounts for rapid movement"
    }
    
    return result

# RRT-001: Round Trip Transactions
# Flag transactions where an account sends money to a counterparty and then receives money back from the same counterparty within 6 hours, and the amounts are within 6% of each other
# This rule matters in AML because round-trip transactions can indicate layering or integration, where illicit funds are moved back and forth to obscure their origin.

def rule_round_trip(df_loaded_clean):
   merged = pd.merge(df_loaded_clean, df_loaded_clean, left_on=["account_id", "counterparty_id"], right_on=["counterparty_id", "account_id"], suffixes=("_a", "_b"))
   merged["time_gap"] = abs(merged["date_a"] - merged["date_b"])
   merged["time_match"] = merged["time_gap"] <= pd.Timedelta(hours=6)
   merged["amount_match"] = abs(merged["amount_a"] - merged["amount_b"]) <= 0.06 * merged["amount_a"]
   merged["flagged_round_trip"] = merged["time_match"] & merged["amount_match"]
   merged["keep_row"] = merged["account_id_a"] < merged["account_id_b"]
   flagged = merged[merged["flagged_round_trip"] & merged ["keep_row"]]
   result = {
     "rule_name": "Round Trip Transactions",
     "rule_code": "RRT-001",
     "flagged_transactions": flagged,
     "flagged_account_ids": pd.concat([flagged["account_id_a"], flagged["account_id_b"]]).unique(),
     "transaction_count": len(flagged),
     "account_count": len(pd.concat([flagged["account_id_a"], flagged["account_id_b"]]).unique()),
     "summary": f"{len(flagged)} transactions across {len(pd.concat([flagged['account_id_a'], flagged['account_id_b']]).unique())} accounts for round trip movement"
    }

   return result

# VEL-001: Velocity Anomaly
# Flag transactions where the amount is greater than the mean amount for that account plus 2 standard deviations
# This rule matters in AML because velocity anomalies can indicate unusual or suspicious activity, such as sudden spikes in transaction amounts that deviate significantly from an account's normal behavior.

def rule_velocity_anomaly(df_loaded_clean): 
   df_loaded_clean["amount_mean"] = df_loaded_clean.groupby("account_id")["amount"].transform("mean")
   df_loaded_clean["amount_std"] = df_loaded_clean.groupby("account_id")["amount"].transform("std")
   flagged = df_loaded_clean[df_loaded_clean["amount"] > (df_loaded_clean["amount_mean"] + 2 * df_loaded_clean["amount_std"])]
   result = {
     "rule_name": "Velocity Anomaly",
     "rule_code": "VEL-001",
     "flagged_transactions": flagged,
     "flagged_account_ids": flagged["account_id"].unique(),
     "transaction_count": len(flagged),
     "account_count": len(flagged["account_id"].unique()),
     "summary": f"{len(flagged)} transactions flagged across {len(flagged['account_id'].unique())} accounts for velocity anomaly"
    }
   
   return result

rule_results.append(rule_high_risk_jurisdiction(df_loaded_clean))
rule_results.append(rule_structuring(df_loaded_clean))
rule_results.append(rule_rapid_movement(df_loaded_clean))
rule_results.append(rule_round_trip(df_loaded_clean))
rule_results.append(rule_velocity_anomaly(df_loaded_clean))

for result in rule_results:
    print(result["summary"])

# ============================================================
# MODULE 4 — RISK SCORING AND REPORTING
# ============================================================

# Create a risk score for each account based on the number of rules triggered
RULE_WEIGHTS = {
    "RRT-001": 5,
    "VEL-001": 4,
    "STR-001": 3,
    "RMV-001": 2,
    "HRJ-001": 1
}

# Create a dictionary to hold the risk scores

def calculate_risk_scores(rule_results):
    account_scores = {}
    for result in rule_results:
        rule_code = result["rule_code"]
        weight = RULE_WEIGHTS[rule_code]
        for account_id in result["flagged_account_ids"]:
                account_scores[account_id] = account_scores.get(account_id, 0) + weight
    return account_scores

account_scores = calculate_risk_scores(rule_results)
assign_risk_tier = lambda score: "High" if score >= 5 else "Medium" if score >= 3 else "Low"
risk_df = pd.DataFrame(list(account_scores.items()), columns=["account_id", "risk_score"])
risk_df["risk_tier"] = risk_df["risk_score"].apply(assign_risk_tier)
risk_df = risk_df.sort_values(by="risk_score", ascending=False)
print(risk_df)

# ============================================================
# MODULE 5 — NETWORK ANALYSIS AND VISUALIZATION
# ============================================================

# Initialize empty graph
G = nx.Graph()

# Create nodes and edges for the network graph based on suspicious transactions
for _, row in df_loaded_clean.iterrows():
    G.add_edge(row["account_id"], row["counterparty_id"])

# Convert into dataframe to sort by degree and identify most connected nodes
degree_dict = dict(G.degree())
degree_df = pd.DataFrame(list(degree_dict.items()), columns=["account_id", "degree"])
degree_df = degree_df.sort_values(by="degree", ascending=False)

# Merge with risk_df to get risk scores for the most connected nodes
degree_df = degree_df.merge(risk_df, on="account_id", how="left")

# Print the top 10 most connected nodes with their risk scores
print(degree_df.head(10))

# Create a PyVis network for the graph
sub_net = Network(height='750px', width='100%', notebook=False)
sub_net.barnes_hut(gravity=-50000, central_gravity=0.3, spring_length=200)

# Build risk tier lookup dictionary
risk_tier_lookup = dict(zip(risk_df["account_id"], risk_df["risk_tier"]))

# Define color map
tier_colors = {
    "High": "red",
    "Medium": "orange",
    "Low": "green",
    "Unknown": "gray"
}

# Add nodes with colors
for node in G.nodes():
    tier = risk_tier_lookup.get(node, "Unknown")
    color = tier_colors.get(tier, "gray")
    sub_net.add_node(node, color=color)

# Add edges
for edge in G.edges():
    sub_net.add_edge(edge[0], edge[1])

# Save to HTML
sub_net.show("aml_network.html", notebook=False)

# ============================================================
# MODULE 6 — SAR REPORT GENERATOR
# ============================================================
def generate_sar_report(rule_results, risk_df, df_loaded_clean):
    # Create a list to hold SAR report data
    sar_reports = []

    high_risk_accounts = risk_df[risk_df["risk_tier"] == "High"]

    for _, row in high_risk_accounts.iterrows():
        account_id = row["account_id"]
        risk_score = row["risk_score"]
        risk_tier = row["risk_tier"]
    
        # Find which rules fired on this account
        triggered_rules = []
        for result in rule_results:
            if account_id in result["flagged_account_ids"]:
                triggered_rules.append(result["rule_name"])

        # Find associated counterparties
        associated_accounts = df_loaded_clean[df_loaded_clean["account_id"] == account_id]["counterparty_id"].unique()
    
        # Build report
        report = {
            "account_id": account_id,
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "rules_triggered": triggered_rules,
            "rule_count": len(triggered_rules),
            "associated_accounts": associated_accounts.tolist(),
            "narrative": f"Account {account_id} flagged with risk score {risk_score}. Rules triggered: {triggered_rules}. Associated with {associated_accounts.tolist()} counterparty accounts."
        }
        sar_reports.append(report)
    
    return sar_reports

# Call function to generate SAR reports, store result, loop through and print each report's narrative
sar_reports = generate_sar_report(rule_results, risk_df, df_loaded_clean)
for report in sar_reports:
    print(report["narrative"])
