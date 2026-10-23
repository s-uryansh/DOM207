import pandas as pd
import statsmodels.api as sm

df = pd.read_excel("SNUPerf.xlsx", sheet_name="Perf")
desc = pd.read_excel("SNUPerf.xlsx", sheet_name="Desc")

# GPA is the main variable
y = df["gpa"]

# Possible determinants of GPA
variables = ["hsgpa", "admscr", "lecmiss", "club", "dadcol", "momcol"]

# Hypotheses
hypotheses = {
    "hsgpa": "Higher high school GPA should be associated with higher university GPA",
    "admscr": "Higher admission score should be associated with higher GPA",
    "lecmiss": "More missed lectures should be associated with lower GPA",
    "club": "Club membership should be associated with GPA",
    "dadcol": "Students with college educated fathers should have higher GPA",
    "momcol": "Students with college educated mothers should have higher GPA"
}

print("GPA Determinant Analysis")
print("=" * 60)

print("\nHypotheses")
for var in variables:
    print(var, ":", hypotheses[var])

# Regression model
X = df[variables]
X = sm.add_constant(X)

model = sm.OLS(y, X).fit()

print("\nRegression Results")
print("=" * 60)
print("R-squared:", round(model.rsquared, 3))
print("Adjusted R-squared:", round(model.rsquared_adj, 3))

print("\nHypothesis Testing")
print("-" * 60)

for var in variables:
    beta = model.params[var]
    p = model.pvalues[var]

    if p < 0.05:
        null_result = "Reject H0"
        hypothesis_result = "Accepted"
    else:
        null_result = "Accept H0"
        hypothesis_result = "Not Accepted"

    print(
        var,
        "Beta =", round(beta, 3),
        "p-value =", round(p, 4),
        "|", null_result,
        "| H1:", hypothesis_result
    )

print("\nFull Regression Table")
print("=" * 60)
print(model.summary().tables[1])