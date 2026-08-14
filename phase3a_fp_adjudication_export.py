import pandas as pd

df = pd.read_csv("categorized_errors.csv")

print("Rows:", len(df))
print("Columns:", df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())

print("\n===== ERROR CATEGORY COUNTS =====")
print(df["category"].value_counts())

# Get only the 24 "not annotated by gold" cases
cases_24 = df[
    df["category"] == "Unsupported/fabricated (not annotated by gold)"
].copy()

print("Number of cases:", len(cases_24))

print(cases_24[
    ["error_type", "example_id", "context", "answer", "problem_span"]
])

cases_24["actually_hallucination"] = ""
cases_24["notes"] = ""

cases_24.to_csv(
    "24_unannotated_cases.csv",
    index=False
)

print("Saved successfully!")