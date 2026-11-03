import pandas as pd

data = pd.read_csv("gameplay_data.csv")

print("===== GAMEPLAY DATA =====")
print(data)

print("\n===== COLUMNS =====")
print(data.columns.tolist())

print("\n===== SHAPE =====")
print(data.shape)

print("\n===== DATA TYPES =====")
print(data.dtypes)