import pandas as pd
import numpy as np
import os
from datetime import datetime

def generate_multivariate_data(output_path):
    np.random.seed(42)
    
    # 48 months: Jan 2020 to Dec 2023
    start_date = datetime(2020, 1, 1)
    dates = [start_date + pd.DateOffset(months=i) for i in range(48)]
    
    # Feature 1: Number of ITGate Engineers (growing over time 15 -> 60)
    engineers = np.linspace(15, 60, 48) + np.random.normal(0, 1.5, 48)
    engineers = np.maximum(engineers, 10).round().astype(int)
    
    # Feature 2: Number of active client projects (growing 4 -> 22)
    active_projects = (engineers * 0.35 + np.random.normal(0, 1, 48)).round().astype(int)
    active_projects = np.maximum(active_projects, 3)
    
    # Feature 3: Average contract value in TND (3000 -> 5500)
    avg_contract_value = 3000 + np.linspace(0, 2500, 48) + np.random.normal(0, 200, 48)
    avg_contract_value = np.round(avg_contract_value, 2)
    
    # Target: Revenue = (active_projects * avg_contract_value) + seasonality + noise
    seasonality = 8000 * np.sin(2 * np.pi * np.array(range(48)) / 12)
    revenue = (active_projects * avg_contract_value) + seasonality + np.random.normal(0, 2000, 48)
    revenue = np.round(np.maximum(revenue, 15000), 2)
    
    df = pd.DataFrame({
        "date": dates,
        "num_engineers": engineers,
        "active_projects": active_projects,
        "avg_contract_value": avg_contract_value,
        "revenue": revenue
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Dataset multi-varie genere avec succes dans : {output_path}")

if __name__ == "__main__":
    output_path = "data/raw/itgate_revenue_multivariate.csv"
    generate_multivariate_data(output_path)
