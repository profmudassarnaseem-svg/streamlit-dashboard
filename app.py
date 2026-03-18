import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------------
# Page Configuration
# -----------------------------------
st.set_page_config(layout="wide")
st.title("🩸 Blood Sample Compliance Dashboard")

# -----------------------------------
# File Path
# -----------------------------------
file1 = "Final_Blood_ReportB.xlsx"

# -----------------------------------
# Read Excel
# -----------------------------------
df = pd.read_excel(file1)

# -----------------------------------
# Data Cleaning
# -----------------------------------
df["COLLECT_DT_TM"] = df["COLLECT_DT_TM"].astype(str)
df["COLLECT_DT_TM"] = df["COLLECT_DT_TM"].str.replace(r"\.\d+", "", regex=True)

df["COLLECT_DT_TM"] = pd.to_datetime(
    df["COLLECT_DT_TM"],
    format="%Y-%m-%d %H:%M:%S",
    errors="coerce"
)

df = df.dropna(subset=["COLLECT_DT_TM"])

df["Month"] = df["COLLECT_DT_TM"].dt.to_period("M").astype(str)
df["Month_Date"] = df["COLLECT_DT_TM"].dt.to_period("M").dt.to_timestamp()

df["Volume_ml"] = (
    df["Sample Volume"]
    .astype(str)
    .str.replace(" mL", "", regex=False)
    .astype(float)
)

# -----------------------------------
# Sidebar Filters
# -----------------------------------
st.sidebar.header("Filters")

locations = st.sidebar.multiselect(
    "Select Location(s)",
    sorted(df["LOC_NURSE_UNIT"].unique()),
    default=sorted(df["LOC_NURSE_UNIT"].unique())
)

selected_month = st.sidebar.selectbox(
    "Select Month",
    sorted(df["Month"].unique())
)

# -----------------------------------
# Apply Filters
# -----------------------------------
filtered_df = df[
    (df["LOC_NURSE_UNIT"].isin(locations)) &
    (df["Month"] == selected_month)
]

# -----------------------------------
# KPI Calculations
# -----------------------------------
total_samples = len(filtered_df)

compliant_samples = len(
    filtered_df[filtered_df["Volume_ml"] >= 5]
)

compliance_rate = (
    (compliant_samples / total_samples) * 100
    if total_samples > 0 else 0
)

# -----------------------------------
# KPI Display
# -----------------------------------
st.subheader("📌 Monthly Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Total Bottles", total_samples)
col2.metric("Bottles ≥ 5 mL", compliant_samples)
col3.metric("Compliance Rate (%)", f"{compliance_rate:.2f}%")

# -----------------------------------
# Location-wise Performance
# -----------------------------------
st.subheader("📊 Location-wise Performance")

location_summary = (
    filtered_df
    .groupby("LOC_NURSE_UNIT")
    .agg(
        Total=("Volume_ml", "count"),
        Compliant=("Volume_ml", lambda x: (x >= 5).sum())
    )
    .reset_index()
)

if not location_summary.empty:

    # Compliance calculation
    location_summary["Compliance %"] = (
        location_summary["Compliant"] /
        location_summary["Total"]
    ) * 100

    # Chart copy
    location_chart = location_summary.copy()

    # -----------------------------------
    # Display Table with Buttons
    # -----------------------------------
    for _, row in location_summary.iterrows():

        col1, col2, col3, col4 = st.columns([3,1,1,1])

        col1.write(row["LOC_NURSE_UNIT"])
        col2.write(int(row["Total"]))
        col3.write(int(row["Compliant"]))

        if row["Compliance %"] >= 90:
            col4.success(f"{row['Compliance %']:.2f}%")
        else:
            col4.error(f"{row['Compliance %']:.2f}%")

    # -----------------------------------
    # Bar Chart
    # -----------------------------------
    colors = [
        "green" if val >= 90 else "red"
        for val in location_chart["Compliance %"]
    ]

    fig1, ax1 = plt.subplots(figsize=(10,6))

    ax1.bar(
        location_chart["LOC_NURSE_UNIT"],
        location_chart["Compliance %"],
        color=colors
    )

    ax1.axhline(
        y=90,
        color="blue",
        linestyle="--",
        linewidth=2,
        label="Target 90%"
    )

    ax1.set_ylabel("Compliance %")
    ax1.set_title("Compliance Rate per Location")

    plt.xticks(rotation=45)
    ax1.legend()

    st.pyplot(fig1)

else:
    st.warning("No data available for selected filters.")

# -----------------------------------
# Monthly Compliance Trend by Location
# -----------------------------------
st.subheader("📈 Monthly Compliance Trend by Location")

trend_df = df[df["LOC_NURSE_UNIT"].isin(locations)]

monthly_location_summary = (
    trend_df
    .groupby(["Month_Date", "LOC_NURSE_UNIT"])
    .agg(
        Total=("Volume_ml", "count"),
        Compliant=("Volume_ml", lambda x: (x >= 5).sum())
    )
    .reset_index()
)

monthly_location_summary["Compliance %"] = (
    monthly_location_summary["Compliant"] /
    monthly_location_summary["Total"]
) * 100

monthly_location_summary = monthly_location_summary.sort_values("Month_Date")

# -----------------------------------
# Trend Chart
# -----------------------------------
fig2, ax2 = plt.subplots(figsize=(10,6))

for location in monthly_location_summary["LOC_NURSE_UNIT"].unique():

    location_data = monthly_location_summary[
        monthly_location_summary["LOC_NURSE_UNIT"] == location
    ]

    ax2.plot(
        location_data["Month_Date"],
        location_data["Compliance %"],
        marker="o",
        linewidth=2,
        label=location
    )

ax2.axhline(
    y=90,
    color="blue",
    linestyle="--",
    linewidth=2,
    label="Target 90%"
)

ax2.set_ylabel("Compliance %")
ax2.set_xlabel("Month")
ax2.set_title("Monthly Compliance Trend by Location")

plt.xticks(rotation=45)

ax2.legend(
    title="Location",
    bbox_to_anchor=(1.02, 1),
    loc="upper left"
)

plt.tight_layout()

st.pyplot(fig2)
