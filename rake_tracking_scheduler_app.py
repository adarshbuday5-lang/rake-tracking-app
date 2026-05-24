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

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #eef4fb 0%, #dbeafe 100%);
    color: #111827;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
}
[data-testid="stSidebar"] * {
    color: white !important;
}
.hero-card {
    background: linear-gradient(90deg, #0f172a, #1d4ed8);
    padding: 32px;
    border-radius: 26px;
    margin-bottom: 28px;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.18);
}
.hero-title {
    color: white !important;
    font-size: 42px;
    font-weight: 900;
}
.hero-subtitle {
    color: #dbeafe !important;
    font-size: 18px;
}
.metric-card {
    background: white;
    padding: 22px;
    border-radius: 22px;
    box-shadow: 0px 8px 22px rgba(0,0,0,0.10);
    border-left: 8px solid #2563eb;
}
.metric-label {
    color: #475569 !important;
    font-size: 15px;
    font-weight: 700;
}
.metric-value {
    color: #0f172a !important;
    font-size: 34px;
    font-weight: 900;
}
.section-card {
    background: white;
    padding: 24px;
    border-radius: 22px;
    box-shadow: 0px 8px 22px rgba(0,0,0,0.08);
    margin-top: 24px;
}
.stButton > button {
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white !important;
    border-radius: 12px;
    padding: 10px 24px;
    border: none;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

BASE_COLUMNS = [
    "Rake ID", "Coal Type", "Rake Type", "Source",
    "Arrival Time", "Placement Time", "Unloading Start", "Unloading End",
    "Tippler", "Priority", "Status", "Delay Reason", "Remarks",
    "Scheduled Start", "Scheduled End", "Manual Sequence",
    "Scheduled Tippler", "Scheduler Remarks"
]

DATE_COLUMNS = [
    "Arrival Time", "Placement Time", "Unloading Start",
    "Unloading End", "Scheduled Start", "Scheduled End"
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
    "📂 Upload Rake Excel / CSV File",
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
        st.sidebar.success("✅ Data uploaded successfully!")

    elif Path(DATA_FILE).exists():
        df = pd.read_csv(DATA_FILE)
        df = prepare_dataframe(df)

    else:
        df = empty_dataframe()

    return df

df = load_data()

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

st.sidebar.markdown("## 🚆 CHP Operations")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Control Charts",
        "Alerts",
        "Manual Scheduler",
        "Auto Scheduler",
        "Edit Data",
        "Raw Data"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("🎯 Target unloading cycle time: 7 hours")

st.markdown("""
<div class="hero-card">
    <div class="hero-title">🚆 Coal Rake Tracking & Scheduler</div>
    <div class="hero-subtitle">
        Digital CHP solution for rake monitoring, delay control, scheduling and process improvement
    </div>
</div>
""", unsafe_allow_html=True)

if not df.empty:
    st.sidebar.markdown("## 🔎 Filters")

    rake_filter = st.sidebar.multiselect(
        "Rake Type",
        options=sorted(df["Rake Type"].dropna().unique()),
        default=sorted(df["Rake Type"].dropna().unique())
    )

    status_filter = st.sidebar.multiselect(
        "Status",
        options=sorted(df["Status"].dropna().unique()),
        default=sorted(df["Status"].dropna().unique())
    )

    tippler_filter = st.sidebar.multiselect(
        "Tippler",
        options=sorted(df["Tippler"].dropna().unique()),
        default=sorted(df["Tippler"].dropna().unique())
    )

    filtered_df = df[
        df["Rake Type"].isin(rake_filter) &
        df["Status"].isin(status_filter) &
        df["Tippler"].isin(tippler_filter)
    ].copy()
else:
    filtered_df = df.copy()

if page == "Dashboard":

    if filtered_df.empty:
        st.warning("No data available. Upload file or adjust filters.")
    else:
        total_rakes = len(filtered_df)
        completed = len(filtered_df[filtered_df["Status"] == "Completed"])
        in_progress = total_rakes - completed
        delayed = len(filtered_df[filtered_df["Delay Status"] == "Delayed"])

        avg_cycle = round(filtered_df["Cycle Hours"].dropna().mean(), 2)
        avg_waiting = round(filtered_df["Waiting Hours"].dropna().mean(), 2)
        delayed_pct = round((delayed / total_rakes) * 100, 2)

        delay_counts = filtered_df["Delay Reason"].replace("", "Not Available").value_counts()
        top_delay = delay_counts.idxmax() if not delay_counts.empty else "N/A"

        c1, c2, c3, c4 = st.columns(4)

        c1.markdown(f'<div class="metric-card"><div class="metric-label">Total Rakes</div><div class="metric-value">{total_rakes}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-label">Completed</div><div class="metric-value">{completed}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-label">Delayed %</div><div class="metric-value">{delayed_pct}%</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-label">Top Delay Reason</div><div class="metric-value" style="font-size:24px;">{top_delay}</div></div>', unsafe_allow_html=True)

        c5, c6 = st.columns(2)

        c5.markdown(f'<div class="metric-card"><div class="metric-label">Average Cycle Hours</div><div class="metric-value">{avg_cycle}</div></div>', unsafe_allow_html=True)
        c6.markdown(f'<div class="metric-card"><div class="metric-label">Average Waiting Hours</div><div class="metric-value">{avg_waiting}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📊 Live Rake & Schedule Status")

        st.dataframe(
            filtered_df[[
                "Rake ID", "Rake Type", "Arrival Time",
                "Scheduled Start", "Scheduled End", "Scheduled Tippler",
                "Manual Sequence", "Priority", "Status",
                "Cycle Hours", "Waiting Hours", "Delay Status", "Delay Reason"
            ]],
            use_container_width=True,
            hide_index=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📈 Delay Reason Chart")
        st.bar_chart(filtered_df["Delay Reason"].fillna("Not Available").value_counts())
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("⚙ Tippler-wise Average Cycle Hours")
        tippler_chart = filtered_df.groupby("Tippler")["Cycle Hours"].mean().dropna()
        st.bar_chart(tippler_chart)
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Control Charts":

    st.title("📉 Control Charts")

    if filtered_df.empty:
        st.warning("No data available.")
    else:
        chart_type = st.radio(
            "Select Control Chart",
            ["Cycle Hours", "Waiting Hours"],
            horizontal=True
        )

        chart_data = filtered_df[[chart_type]].dropna().reset_index(drop=True)

        if chart_data.empty:
            st.warning("Not enough data for control chart.")
        else:
            values = chart_data[chart_type]

            mean = values.mean()
            std = values.std()
            ucl = mean + 3 * std
            lcl = max(mean - 3 * std, 0)

            control_df = pd.DataFrame({
                "Rake Sequence": range(1, len(values) + 1),
                chart_type: values,
                "Mean": mean,
                "UCL": ucl,
                "LCL": lcl
            })

            if chart_type == "Cycle Hours":
                control_df["Target 7 Hours"] = TARGET_CYCLE_HOURS

            st.line_chart(
                control_df.set_index("Rake Sequence"),
                use_container_width=True
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Mean", round(mean, 2))
            c2.metric("UCL", round(ucl, 2))
            c3.metric("LCL", round(lcl, 2))

            outliers = values[(values > ucl) | (values < lcl)]

            if len(outliers) > 0:
                st.error(f"{len(outliers)} points are outside control limits.")
            else:
                st.success("Process is within control limits based on available data.")

elif page == "Alerts":

    st.title("🚨 Operational Alerts")

    if filtered_df.empty:
        st.warning("No data available.")
    else:
        delayed_rakes = filtered_df[filtered_df["Cycle Hours"] > TARGET_CYCLE_HOURS]

        high_priority = filtered_df[
            (filtered_df["Priority"] == "High") &
            (filtered_df["Status"] != "Completed")
        ]

        pending_df = filtered_df[filtered_df["Status"] != "Completed"].copy()
        pending_df["Manual Sequence"] = pd.to_numeric(
            pending_df["Manual Sequence"],
            errors="coerce"
        )

        pending_df = pending_df.sort_values(
            by=["Manual Sequence", "Scheduled Start", "Arrival Time"],
            na_position="last"
        )

        if not pending_df.empty:
            next_rake = pending_df.iloc[0]

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.subheader("🚆 Next Rake to Handle")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Rake ID", next_rake.get("Rake ID", "N/A"))
            c2.metric("Tippler", next_rake.get("Scheduled Tippler", "N/A"))
            c3.metric("Priority", next_rake.get("Priority", "N/A"))
            c4.metric("Status", next_rake.get("Status", "N/A"))

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🔴 Rakes Above 7 Hours")

        if delayed_rakes.empty:
            st.success("No rake has crossed target cycle time.")
        else:
            st.dataframe(
                delayed_rakes[[
                    "Rake ID", "Rake Type", "Cycle Hours",
                    "Delay Reason", "Tippler", "Status"
                ]],
                use_container_width=True,
                hide_index=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("⚠ High Priority Pending Rakes")

        if high_priority.empty:
            st.success("No high priority rake pending.")
        else:
            st.dataframe(
                high_priority[[
                    "Rake ID", "Arrival Time", "Scheduled Start",
                    "Scheduled Tippler", "Status", "Scheduler Remarks"
                ]],
                use_container_width=True,
                hide_index=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Manual Scheduler":

    st.title("🗓 Manual Scheduler")

    if df.empty:
        st.warning("Upload data first.")
    else:
        schedule_cols = [
            "Rake ID", "Rake Type", "Arrival Time", "Priority", "Status",
            "Scheduled Start", "Scheduled End", "Manual Sequence",
            "Scheduled Tippler", "Scheduler Remarks"
        ]

        edited_schedule = st.data_editor(
            df[schedule_cols].copy(),
            use_container_width=True,
            num_rows="fixed"
        )

        if st.button("💾 Save Schedule"):
            for col in [
                "Priority", "Status", "Scheduled Start", "Scheduled End",
                "Manual Sequence", "Scheduled Tippler", "Scheduler Remarks"
            ]:
                df[col] = edited_schedule[col]

            save_data(df[BASE_COLUMNS])
            st.success("✅ Schedule updated successfully!")

elif page == "Auto Scheduler":

    st.title("⚙ Auto Scheduler")

    if filtered_df.empty:
        st.warning("No data available.")
    else:
        pending_df = filtered_df[filtered_df["Status"] != "Completed"].copy()

        priority_map = {
            "High": 1,
            "Medium": 2,
            "Low": 3
        }

        pending_df["Priority Rank"] = pending_df["Priority"].map(priority_map).fillna(4)
        pending_df = pending_df.sort_values(by=["Priority Rank", "Arrival Time"])
        pending_df["Suggested Sequence"] = range(1, len(pending_df) + 1)

        st.dataframe(
            pending_df[[
                "Suggested Sequence", "Rake ID", "Rake Type",
                "Arrival Time", "Priority", "Status", "Delay Reason"
            ]],
            use_container_width=True,
            hide_index=True
        )

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

elif page == "Raw Data":

    st.title("📁 Raw Data")

    if df.empty:
        st.warning("No data available.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df[BASE_COLUMNS].to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇ Download CSV",
            data=csv,
            file_name="rake_data_export.csv",
            mime="text/csv"
        )
