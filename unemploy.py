import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

FILE_1 = "C:\\Users\\PARTH\\Desktop\\SEM 5\\CodeAlpha\\Unemployment Analysis\\Unemployment in India.csv"            
FILE_2 = "C:\\Users\\PARTH\\Desktop\\SEM 5\\CodeAlpha\\Unemployment Analysis\\Unemployment_Rate_upto_11_2020.csv"   
LOCKDOWN_START = pd.Timestamp("2020-03-25")     
LOCKDOWN_END = pd.Timestamp("2020-05-31")       
PRE_END = pd.Timestamp("2020-03-31")            

os.makedirs("charts", exist_ok=True)
sns.set_theme(style="whitegrid")
UR, EMP, LPR = "unemployment_rate", "employed", "labour_participation"


def clean(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "Estimated Unemployment Rate (%)": UR,
        "Estimated Employed": EMP,
        "Estimated Labour Participation Rate (%)": LPR})
    df = df.dropna(how="all")                      
    for col in df.columns:                         
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].str.strip()
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
    return df

df1 = clean(FILE_1)
df2 = clean(FILE_2).rename(columns={"Region.1": "Zone"})

print("File 1:", df1.shape, "|", df1["Date"].min().date(), "to", df1["Date"].max().date())
print("File 2:", df2.shape, "|", df2["Date"].min().date(), "to", df2["Date"].max().date())
print("\nMissing values (file 1):", df1.isnull().sum().sum(),
      "| (file 2):", df2.isnull().sum().sum())
print("Duplicates (file 1):", df1.duplicated().sum(), "| (file 2):", df2.duplicated().sum())
print("\nSummary statistics (file 1):\n", df1[[UR, EMP, LPR]].describe().round(2))


nat1 = df1.groupby("Date")[[UR, LPR]].mean()
nat2 = df2.groupby("Date")[[UR, LPR]].mean()

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(nat1.index, nat1[UR], marker="o", label="File 1 (state-area records)")
ax.plot(nat2.index, nat2[UR], marker="s", label="File 2 (state records)")
ax.axvspan(LOCKDOWN_START, LOCKDOWN_END, color="red", alpha=0.15, label="Strict lockdown")
ax.set(title="Average Unemployment Rate Across Indian States", ylabel="Unemployment rate (%)")
ax.legend()
fig.autofmt_xdate()
fig.savefig("charts/01_national_trend.png", dpi=130, bbox_inches="tight")
plt.close()


def period(d):
    if d <= PRE_END: return "1. Pre-lockdown"
    if d <= LOCKDOWN_END:  return "2. Lockdown"
    return "3. Post-lockdown"

df1["period"] = df1["Date"].apply(period)
df2["period"] = df2["Date"].apply(period)


print("\n--- Average unemployment rate by period (file 1: May 2019 - Jun 2020) ---")
print(df1.groupby("period")[UR].mean().round(2))
print("\n--- Same, using file 2 (Jan - Oct 2020) ---")
print(df2.groupby("period")[UR].mean().round(2))

peak = nat2[UR].idxmax()
print(f"\nPeak national average (file 2): {nat2[UR].max():.1f}% in {peak:%B %Y}")
print(f"Latest month (file 2): {nat2[UR].iloc[-1]:.1f}% in {nat2.index[-1]:%B %Y}")


emp = df1.groupby("Date")[EMP].sum() / 1e6
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
axes[0].plot(emp.index, emp.values, marker="o", color="tab:green")
axes[0].set(title="Total Estimated Employed (millions)", ylabel="Millions")
axes[1].plot(nat1.index, nat1[LPR], marker="o", color="tab:purple")
axes[1].set(title="Avg Labour Participation Rate (%)", ylabel="%")
for a in axes:
    a.axvspan(LOCKDOWN_START, LOCKDOWN_END, color="red", alpha=0.15)
    a.tick_params(axis="x", rotation=45)
fig.savefig("charts/02_employment_and_participation.png", dpi=130, bbox_inches="tight")
plt.close()
drop = (1 - emp.min() / emp.loc[emp.index < LOCKDOWN_START].mean()) * 100
print(f"\nEmployment fell to a low of {emp.min():.0f}M in {emp.idxmin():%B %Y}, "
      f"about {drop:.0f}% below the pre-lockdown average.")


area = df1.groupby(["Date", "Area"])[UR].mean().unstack()
fig, ax = plt.subplots(figsize=(11, 5))
area.plot(ax=ax, marker="o")
ax.axvspan(LOCKDOWN_START, LOCKDOWN_END, color="red", alpha=0.15)
ax.set(title="Unemployment Rate: Urban vs Rural", ylabel="Unemployment rate (%)")
fig.savefig("charts/03_urban_vs_rural.png", dpi=130, bbox_inches="tight")
plt.close()
print("\n--- Urban vs rural by period ---")
print(df1.groupby(["period", "Area"])[UR].mean().unstack().round(2))


state = df1.pivot_table(index="Region", columns="period", values=UR, aggfunc="mean")
state["increase"] = state["2. Lockdown"] - state["1. Pre-lockdown"]
worst = state["increase"].sort_values(ascending=False).head(10)
fig, ax = plt.subplots(figsize=(9, 5))
sns.barplot(x=worst.values, y=worst.index, color="tab:red", ax=ax)
ax.set(title="Top 10 States: Rise in Unemployment (Lockdown vs Pre-lockdown)",
       xlabel="Percentage-point increase", ylabel="")
fig.savefig("charts/04_most_affected_states.png", dpi=130, bbox_inches="tight")
plt.close()
print("\n--- 10 states with the biggest increase (percentage points) ---")
print(worst.round(1))


zone = df2.groupby(["Date", "Zone"])[UR].mean().unstack()
fig, ax = plt.subplots(figsize=(11, 5))
zone.plot(ax=ax, marker="o")
ax.axvspan(LOCKDOWN_START, LOCKDOWN_END, color="red", alpha=0.15)
ax.set(title="Unemployment Rate by Zone, 2020", ylabel="Unemployment rate (%)")
fig.savefig("charts/05_zone_trends.png", dpi=130, bbox_inches="tight")
plt.close()

heat = df2.pivot_table(index="Region", columns=df2["Date"].dt.strftime("%b"),
                       values=UR, aggfunc="mean")
heat = heat[["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct"]]
fig, ax = plt.subplots(figsize=(10, 9))
sns.heatmap(heat, cmap="YlOrRd", annot=True, fmt=".0f", cbar_kws={"label": "%"}, ax=ax)
ax.set(title="Unemployment Rate by State and Month, 2020", xlabel="", ylabel="")
fig.savefig("charts/06_state_month_heatmap.png", dpi=130, bbox_inches="tight")
plt.close()


months = df1["Date"].dt.to_period("M").nunique()
print(f"\n--- Seasonality ---\nFile 1 covers only {months} months and file 2 only 10, "
      "so every calendar month (except May/June in file 1) appears just once.\n"
      "A true seasonal pattern cannot be separated from the Covid shock with this data.")


print("\n--- Key takeaways ---")
pre = df2[df2["period"] == "1. Pre-lockdown"][UR].mean()
print(f"* Avg state unemployment: {pre:.1f}% (Jan-Mar 2020) -> {nat2[UR].max():.1f}% "
      f"at the {peak:%B} peak -> {nat2[UR].iloc[-1]:.1f}% by {nat2.index[-1]:%B}.")
print("* Charts saved in the 'charts' folder.")