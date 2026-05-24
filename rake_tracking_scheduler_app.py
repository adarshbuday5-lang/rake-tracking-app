import streamlit as st
import pandas as pd
from pathlib import Path

DATA_FILE = "rake_data.csv"
TARGET_CYCLE_HOURS = 7

st.set_page_config(
    page_title="Rake Tracking & Scheduler",
    page_icon="🚆",
    layout="wide"
)

BASE_COLUMNS = [
    "Rake ID", "Coal Type", "Rake Type", "Source",
    "Arrival Time", "Placement Time", "Unloading Start", "Unloading End",
    "Tippler", "Priority", "Status", "Delay Reason", "Remarks",
    "Scheduled Start", "Scheduled End", "Manual Sequence",
    "Scheduled Tippler", "Scheduler Remarks"
]

DATE_COLUMNS = [
    "Arrival Time", "Placement Time", "Unloading Start", "Unloading End",
    "Scheduled Start", "Scheduled End"
]


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


uploaded_file = st.sidebar.file_uploader(
    "Upload New Rake Excel / CSV File",
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
        st.sidebar.success("New data uploaded and saved!")

    elif Path(DATA_FILE).exists():
        df = pd.read_csv(DATA_FILE)
        df = prepare_dataframe(df)

    else:
        df = empty_dataframe()

    return df


df = load_data()


def calculate_cycle_hours(row):
    if pd.notna(row["Arrival Time"]) and pd.notna(row["Unloading End"]):
        return round((row["Unloading End"] - row["Arrival Time"]).total_seconds() / 3600, 2)
    return None


def calculate_waiting_hours(row):
    if pd.notna(row["Arrival Time"]) and pd.notna(row["Unloading Start"]):
        return round((row["Unloading Start"] - row["Arrival Time"]).total_seconds() / 3600, 2)
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


st.sidebar.title("🚆 Rake Tracking")
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
st.sidebar.info("Target cycle time: 7 hours")


if page == "Dashboard":
    st.title("Coal Handling Plant Rake Tracking Dashboard")

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

        col5, col6 = st.columns(2)
        col5.metric("Average Cycle Hours", avg_cycle)
        col6.metric("Average Waiting Hours", avg_waiting)

        st.markdown("---")
        st.subheader("Live Rake & Schedule Status")

        st.dataframe(
            df[[
                "Rake ID", "Rake Type", "Arrival Time",
                "Scheduled Start", "Scheduled End", "Scheduled Tippler",
                "Manual Sequence", "Priority", "Status",
                "Cycle Hours", "Waiting Hours", "Delay Status", "Delay Reason"
            ]],
            use_container_width=True
        )

        st.markdown("---")
        st.subheader("Delay Reason Analysis")
        st.bar_chart(df["Delay Reason"].fillna("Not Available").value_counts())


elif page == "Manual Scheduler":
    st.title("Manual Scheduler")
    st.caption("Edit schedule manually. Saved changes will reflect automatically in the dashboard.")

    if df.empty:
        st.warning("Upload data first.")
    else:
        schedule_cols = [
            "Rake ID", "Rake Type", "Arrival Time", "Priority", "Status",
            "Scheduled Start", "Scheduled End", "Manual Sequence",
            "Scheduled Tippler", "Scheduler Remarks"
        ]

        editable_schedule = df[schedule_cols].copy()

        edited_schedule = st.data_editor(
            editable_schedule,
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Scheduled Tippler": st.column_config.SelectboxColumn(
                    "Scheduled Tippler",
                    options=["WT-1", "WT-2", "WT-3", "Not Assigned"]
                ),
                "Priority": st.column_config.SelectboxColumn(
                    "Priority",
                    options=["High", "Medium", "Low"]
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Waiting", "Placed", "Unloading", "Completed"]
                )
            }
        )

        if st.button("Save Schedule"):
            for col in [
                "Priority", "Status", "Scheduled Start", "Scheduled End",
                "Manual Sequence", "Scheduled Tippler", "Scheduler Remarks"
            ]:
                df[col] = edited_schedule[col]

            save_data(df[BASE_COLUMNS])
            st.success("Schedule saved. Dashboard updated.")


elif page == "Auto Scheduler":
    st.title("Auto Scheduler")
    st.caption("Suggested unloading order based on priority and arrival time.")

    if df.empty:
        st.warning("Upload data first.")
    else:
        pending_df = df[df["Status"] != "Completed"].copy()

        if pending_df.empty:
            st.success("All rakes are completed.")
        else:
            priority_map = {"High": 1, "Medium": 2, "Low": 3}
            pending_df["Priority Rank"] = pending_df["Priority"].map(priority_map).fillna(4)

            pending_df = pending_df.sort_values(
                by=["Priority Rank", "Arrival Time"]
            )

            pending_df["Suggested Sequence"] = range(1, len(pending_df) + 1)

            st.dataframe(
                pending_df[[
                    "Suggested Sequence", "Rake ID", "Rake Type",
                    "Arrival Time", "Priority", "Tippler",
                    "Status", "Delay Reason"
                ]],
                use_container_width=True
            )

            st.info(
                "Auto Scheduler currently uses priority first and arrival time second. "
                "Later we can add tippler availability, expected unloading time, rake type, "
                "maintenance blocks, and AI-based scheduling."
            )


elif page == "Edit Data":
    st.title("Edit Rake Data")
    st.caption("Change operational data directly. Saved changes will update the dashboard.")

    if df.empty:
        st.warning("Upload data first.")
    else:
        editable_df = df[BASE_COLUMNS].copy()

        edited_df = st.data_editor(
            editable_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Rake Type": st.column_config.SelectboxColumn(
                    "Rake Type",
                    options=["BOXN", "BOBR", "Other"]
                ),
                "Coal Type": st.column_config.SelectboxColumn(
                    "Coal Type",
                    options=["Domestic", "Imported", "Mixed"]
                ),
                "Tippler": st.column_config.SelectboxColumn(
                    "Tippler",
                    options=["WT-1", "WT-2", "WT-3", "Not Assigned"]
                ),
                "Priority": st.column_config.SelectboxColumn(
                    "Priority",
                    options=["High", "Medium", "Low"]
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Waiting", "Placed", "Unloading", "Completed"]
                ),
                "Delay Reason": st.column_config.SelectboxColumn(
                    "Delay Reason",
                    options=[
                        "None", "Rake Bunching", "CHP Interruption",
                        "Sticky Coal", "Tippler Breakdown", "Loco Delay", "Other"
                    ]
                ),
                "Scheduled Tippler": st.column_config.SelectboxColumn(
                    "Scheduled Tippler",
                    options=["WT-1", "WT-2", "WT-3", "Not Assigned"]
                )
            }
        )

        if st.button("Save Edited Data"):
            edited_df = prepare_dataframe(edited_df)
            save_data(edited_df)
            st.success("Data saved. Dashboard updated.")


elif page == "Raw Data":
    st.title("Raw Rake Data")

    if df.empty:
        st.warning("No data available.")
    else:
        st.dataframe(df, use_container_width=True)

        csv = df[BASE_COLUMNS].to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Updated CSV",
            data=csv,
            file_name="rake_data_export.csv",
            mime="text/csv"
        )
