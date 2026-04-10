from datasets import load_dataset
import pandas as pd

# Load dataset
dataset = load_dataset("KisanVaani/agriculture-qa-english-only")
data = dataset['train']

# Convert to DataFrame
df = pd.DataFrame(data)

# Save as CSV
df.to_csv("agriculture_qa.csv", index=False)

print("CSV file created successfully!")
