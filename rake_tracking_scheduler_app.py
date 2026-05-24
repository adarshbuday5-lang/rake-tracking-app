import streamlit as st
import pandas as pd
from pathlib import Path

# -----------------------------------
# CONFIGURATION
# -----------------------------------

DATA_FILE = "rake_data.csv"
TARGET_CYCLE_HOURS = 7

st.set_page_config(
    page_title="Rake Tracking System",
    page_icon="🚆",
    layout="wide"
)

# -----------------------------------
# DATA UPLOAD + LOAD DATA
# -----------------------------------

uploaded_file = st.sidebar.file_uploader(
    "Upload New Rake Excel / CSV File",
    type=["xlsx", "csv"]
)

def empty_dataframe():
    return pd.DataFrame(columns=[
        "Rake ID",
        "Coal Type",
        "Rake Type",
        "Source",
        "Arrival Time",
        "Placement Time",
        "Unloading Start",
        "Unloading End",
        "Tippler",
        "Priority",
        "Status",
        "Delay Reason",
        "Remarks"
    ])

def load_data():
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        df.to_csv(DATA_FILE, index=False)
        st.sidebar.success("New data uploaded and dashboard updated!")

    elif Path(DATA_FILE).exists():
        df = pd.read_csv(DATA_FILE)

    else:
        df = empty_dataframe()

    date_columns = [
        "Arrival Time",
        "Placement Time",
        "Unloading Start",
        "Unloading End"
    ]

    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df

df = load_data()

# -----------------------------------
# CALCULATIONS
# -----------------------------------

def calculate_cycle_hours(row):
    if pd.notna(row["Arrival Time"]) and pd.notna(row["Unloading End"]):
        return round(
            (row["Unloading End"] - row["Arrival Time"]).total_seconds() / 3600,
            2
        )
    return None

def calculate_waiting_hours(row):
    if pd.notna(row["Arrival Time"]) and pd.notna(row["Unloading Start"]):
        return round(
            (row["Unloading Start"] - row["Arrival Time"]).total_seconds() / 3600,
            2
        )
    return None

def get_delay_status(hours):
    if pd.isna(hours):
        return "In Progress"
    elif hours <= TARGET_CYCLE_HOURS:
        return "On Time"
    else:
        return "Delayed"

if not df.empty:
    df["Cycle Hours"] = df.apply(calculate_cycle_hours, axis=1)
    df["Waiting Hours"] = df.apply(calculate_waiting_hours, axis=1)
    df["Delay Status"] = df["Cycle Hours"].apply(get_delay_status)
else:
    df["Cycle Hours"] = []
    df["Waiting Hours"] = []
    df["Delay Status"] = []

# -----------------------------------
# SIDEBAR
# -----------------------------------

st.sidebar.title("🚆 Rake Tracking")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Scheduler", "Raw Data"]
)

st.sidebar.markdown("---")
st.sidebar.info("Target cycle time: 7 hours")

# -----------------------------------
# DASHBOARD
# -----------------------------------

if page == "Dashboard":

    st.title("Coal Handling Plant Rake Tracking Dashboard")
    st.caption("Live rake monitoring, delay tracking, and operational status view")

    if df.empty:
        st.warning("No data available. Upload an Excel or CSV file from the sidebar.")
    else:
        total_rakes = len(df)
        delayed = len(df[df["Delay Status"] == "Delayed"])
        completed = len(df[df["Status"] == "Completed"])
        in_progress = total_rakes - completed

        avg_cycle = round(df["Cycle Hours"].dropna().mean(), 2)
        avg_waiting = round(df["Waiting Hours"].dropna().mean(), 2)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Rakes", total_rakes)
        col2.metric("Completed", completed)
        col3.metric("In Progress", in_progress)
        col4.metric("Delayed", delayed)

        col5, col6 = st.columns(2)
        col5.metric("Average Cycle Hours", avg_cycle)
        col6.metric("Average Waiting Hours", avg_waiting)

        st.markdown("---")

        st.subheader("Live Rake Status")

        st.dataframe(
            df[[
                "Rake ID",
                "Rake Type",
                "Arrival Time",
                "Placement Time",
                "Unloading Start",
                "Unloading End",
                "Tippler",
                "Priority",
                "Status",
                "Cycle Hours",
                "Waiting Hours",
                "Delay Status",
                "Delay Reason"
            ]],
            use_container_width=True
        )

        st.markdown("---")

        st.subheader("Delay Reason Analysis")

        delay_summary = (
            df["Delay Reason"]
            .fillna("Not Available")
            .value_counts()
        )

        st.bar_chart(delay_summary)

# -----------------------------------
# SCHEDULER
# -----------------------------------

elif page == "Scheduler":

    st.title("Rake Scheduler")
    st.caption("Recommended unloading sequence based on priority and arrival time")

    if df.empty:
        st.warning("No data available. Upload an Excel or CSV file first.")
    else:
        pending_df = df[df["Status"] != "Completed"].copy()

        if pending_df.empty:
            st.success("All rakes are completed. No pending rakes for scheduling.")
        else:
            priority_map = {
                "High": 1,
                "Medium": 2,
                "Low": 3
            }

            pending_df["Priority Rank"] = pending_df["Priority"].map(priority_map)
            pending_df["Priority Rank"] = pending_df["Priority Rank"].fillna(4)

            pending_df = pending_df.sort_values(
                by=["Priority Rank", "Arrival Time"]
            )

            pending_df["Suggested Sequence"] = range(
                1,
                len(pending_df) + 1
            )

            st.subheader("Recommended Unloading Sequence")

            st.dataframe(
                pending_df[[
                    "Suggested Sequence",
                    "Rake ID",
                    "Rake Type",
                    "Arrival Time",
                    "Priority",
                    "Tippler",
                    "Status",
                    "Delay Reason"
                ]],
                use_container_width=True
            )

            st.markdown("---")

            st.info(
                "Current scheduling logic uses priority first and arrival time second. "
                "Later, this can be improved by adding tippler availability, expected unloading duration, "
                "maintenance blocks, coal urgency, and live CHP constraints."
            )

# -----------------------------------
# RAW DATA
# -----------------------------------

elif page == "Raw Data":

    st.title("Raw Rake Data")

    if df.empty:
        st.warning("No data available.")
    else:
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Updated CSV",
            data=csv,
            file_name="rake_data_export.csv",
            mime="text/csv"
        )
