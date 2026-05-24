import streamlit as st
import pandas as pd
from pathlib import Path

DATA_FILE = "rake_data.csv"
TARGET_CYCLE_HOURS = 7

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------

st.set_page_config(
    page_title="Rake Tracking & Scheduler",
    page_icon="🚆",
    layout="wide"
)

# -------------------------------------------------
# CUSTOM UI DESIGN
# -------------------------------------------------

st.markdown("""
<style>

/* Main App */
.stApp {
    background: linear-gradient(135deg, #f4f7fb 0%, #e8eef7 100%);
    color: #1f2937;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}

[data-testid="stSidebar"] * {
    color: white;
}

/* Titles */
h1 {
    color: #0f172a;
    font-weight: 800;
}

h2, h3 {
    color: #1e3a8a;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: white;
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0px 4px 14px rgba(0,0,0,0.08);
    border-left: 6px solid #2563eb;
}

/* Data Tables */
[data-testid="stDataFrame"] {
    background: white;
    border-radius: 16px;
    padding: 10px;
    box-shadow: 0px 4px 14px rgba(0,0,0,0.08);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 12px;
    padding: 10px 24px;
    border: none;
    font-weight: 600;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #1d4ed8, #1e40af);
    color: white;
}

/* Upload Section */
[data-testid="stFileUploader"] {
    background: white;
    padding: 12px;
    border-radius: 14px;
}

/* Alerts */
.stAlert {
    border-radius: 14px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# DATA STRUCTURE
# -------------------------------------------------

BASE_COLUMNS = [
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
    "Remarks",
    "Scheduled Start",
    "Scheduled End",
    "Manual Sequence",
    "Scheduled Tippler",
    "Scheduler Remarks"
]

DATE_COLUMNS = [
    "Arrival Time",
    "Placement Time",
    "Unloading Start",
    "Unloading End",
    "Scheduled Start",
    "Scheduled End"
]

# -------------------------------------------------
# FUNCTIONS
# -------------------------------------------------

def empty_dataframe():
    return pd.DataFrame(columns=BASE_COLUMNS)

def prepare_dataframe(df):

    for col in BASE_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    for col in DATE_COLUMNS:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    return df[BASE_COLUMNS]

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------

uploaded_file = st.sidebar.file_uploader(
    "📂 Upload New Rake Excel / CSV File",
    type=["xlsx", "csv"]
)

def load_data():

    if uploaded_file is not None:

        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        df = prepare_dataframe(df)

        save_data(df)

        st.sidebar.success("✅ New data uploaded successfully!")

    elif Path(DATA_FILE).exists():

        df = pd.read_csv(DATA_FILE)
        df = prepare_dataframe(df)

    else:
        df = empty_dataframe()

    return df

df = load_data()

# -------------------------------------------------
# CALCULATIONS
# -------------------------------------------------

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

# -------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------

st.sidebar.title("🚆 CHP Operations")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Manual Scheduler",
        "Auto Scheduler",
        "Edit Data",
        "Raw Data"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("🎯 Target unloading cycle time: 7 Hours")

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------

if page == "Dashboard":

    st.title("🚆 Coal Handling Plant Dashboard")

    st.caption("Real-Time Rake Tracking & Scheduling System")

    if df.empty:

        st.warning("Upload an Excel or CSV file from the sidebar.")

    else:

        total_rakes = len(df)

        completed = len(df[df["Status"] == "Completed"])

        in_progress = total_rakes - completed

        delayed = len(df[df["Delay Status"] == "Delayed"])

        avg_cycle = round(df["Cycle Hours"].dropna().mean(), 2)

        avg_waiting = round(df["Waiting Hours"].dropna().mean(), 2)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Rakes", total_rakes)

        col2.metric("Completed", completed)

        col3.metric("In Progress", in_progress)

        col4.metric("Delayed", delayed)

        st.markdown("##")

        col5, col6 = st.columns(2)

        col5.metric("Average Cycle Hours", avg_cycle)

        col6.metric("Average Waiting Hours", avg_waiting)

        st.markdown("---")

        st.subheader("📊 Live Rake Status")

        st.dataframe(
            df[[
                "Rake ID",
                "Rake Type",
                "Arrival Time",
                "Scheduled Start",
                "Scheduled End",
                "Scheduled Tippler",
                "Manual Sequence",
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

        st.subheader("📈 Delay Reason Analysis")

        st.bar_chart(
            df["Delay Reason"].fillna("Not Available").value_counts()
        )

# -------------------------------------------------
# MANUAL SCHEDULER
# -------------------------------------------------

elif page == "Manual Scheduler":

    st.title("🗓 Manual Scheduler")

    if df.empty:

        st.warning("Upload data first.")

    else:

        schedule_cols = [
            "Rake ID",
            "Rake Type",
            "Arrival Time",
            "Priority",
            "Status",
            "Scheduled Start",
            "Scheduled End",
            "Manual Sequence",
            "Scheduled Tippler",
            "Scheduler Remarks"
        ]

        editable_schedule = df[schedule_cols].copy()

        edited_schedule = st.data_editor(
            editable_schedule,
            use_container_width=True,
            num_rows="fixed"
        )

        if st.button("💾 Save Schedule"):

            for col in [
                "Priority",
                "Status",
                "Scheduled Start",
                "Scheduled End",
                "Manual Sequence",
                "Scheduled Tippler",
                "Scheduler Remarks"
            ]:
                df[col] = edited_schedule[col]

            save_data(df[BASE_COLUMNS])

            st.success("✅ Schedule updated successfully!")

# -------------------------------------------------
# AUTO SCHEDULER
# -------------------------------------------------

elif page == "Auto Scheduler":

    st.title("⚙ Auto Scheduler")

    if df.empty:

        st.warning("Upload data first.")

    else:

        pending_df = df[df["Status"] != "Completed"].copy()

        priority_map = {
            "High": 1,
            "Medium": 2,
            "Low": 3
        }

        pending_df["Priority Rank"] = pending_df["Priority"].map(priority_map)

        pending_df = pending_df.sort_values(
            by=["Priority Rank", "Arrival Time"]
        )

        pending_df["Suggested Sequence"] = range(
            1,
            len(pending_df) + 1
        )

        st.dataframe(
            pending_df[[
                "Suggested Sequence",
                "Rake ID",
                "Rake Type",
                "Arrival Time",
                "Priority",
                "Status"
            ]],
            use_container_width=True
        )

# -------------------------------------------------
# EDIT DATA
# -------------------------------------------------

elif page == "Edit Data":

    st.title("✏ Edit Operational Data")

    if df.empty:

        st.warning("Upload data first.")

    else:

        edited_df = st.data_editor(
            df[BASE_COLUMNS],
            use_container_width=True,
            num_rows="dynamic"
        )

        if st.button("💾 Save Edited Data"):

            edited_df = prepare_dataframe(edited_df)

            save_data(edited_df)

            st.success("✅ Data saved successfully!")

# -------------------------------------------------
# RAW DATA
# -------------------------------------------------

elif page == "Raw Data":

    st.title("📁 Raw Data")

    st.dataframe(df, use_container_width=True)

    csv = df[BASE_COLUMNS].to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download CSV",
        data=csv,
        file_name="rake_data_export.csv",
        mime="text/csv"
    )
