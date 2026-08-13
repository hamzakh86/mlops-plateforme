import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_revenue_data(output_path):
    np.random.seed(42)
    
    # 4 years of monthly data: Jan 2020 to Dec 2023
    start_date = datetime(2020, 1, 1)
    dates = [start_date + pd.DateOffset(months=i) for i in range(48)]
    
    # Base revenue starting at 50,000
    base_revenue = 50000
    
    # Upward trend (approx 1000 per month)
    trend = np.linspace(0, 1000 * 48, 48)
    
    # Seasonality (e.g., higher at end of year Q4, lower in summer)
    # Sinusoidal wave with period 12
    seasonality = 10000 * np.sin(2 * np.pi * np.array(range(48)) / 12)
    
    # Random noise
    noise = np.random.normal(0, 3000, 48)
    
    revenue = base_revenue + trend + seasonality + noise
    
    # Ensure no negative revenue (just in case)
    revenue = np.maximum(revenue, 10000)
    
    df = pd.DataFrame({
        "date": dates,
        "revenue": np.round(revenue, 2)
    })
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"✅ Données générées avec succès : {output_path}")

if __name__ == "__main__":
    output_path = "data/raw/itgate_revenue.csv"
    generate_revenue_data(output_path)
