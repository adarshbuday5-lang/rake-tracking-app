import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

TARGET_CYCLE_HOURS = 7

st.set_page_config(
    page_title="Rake Tracking System",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #EEF2FF 0%, #F8FAFC 45%, #ECFEFF 100%);
    color: #0F172A;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%);
}

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: white !important;
}

.main-title {
    background: linear-gradient(90deg, #1E3A8A, #2563EB, #0891B2);
    padding: 28px;
    border-radius: 22px;
    color: white;
    text-align: center;
    margin-bottom: 25px;
    box-shadow: 0px 8px 25px rgba(15, 23, 42, 0.18);
}

.main-title h1 {
    color: white !important;
    margin-bottom: 5px;
}

.main-title p {
    color: #E0F2FE !important;
    font-size: 18px;
}

.kpi-card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0px 6px 20px rgba(15, 23, 42, 0.08);
    border-left: 6px solid #2563EB;
}

.kpi-card h4 {
    color: #475569 !important;
    font-size: 15px;
    margin-bottom: 5px;
}

.kpi-card h2 {
    color: #0F172A !important;
    font-size: 32px;
    margin: 0;
}

.section-card {
    background: white;
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0px 6px 20px rgba(15, 23, 42, 0.08);
    margin-top: 18px;
    margin-bottom: 18px;
}

.kanban-header {
    padding: 14px;
    border-radius: 15px;
    text-align: center;
    font-weight: 800;
    margin-bottom: 12px;
    color: #0F172A !important;
}

.kanban-card {
    background: white;
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 12px;
    box-shadow: 0px 4px 12px rgba(15,23,42,0.12);
    border-left: 5px solid #2563EB;
    font-size: 14px;
}

.kanban-card b {
    color: #1E3A8A !important;
    font-size: 16px;
}

.stButton > button {
    background: linear-gradient(90deg, #2563EB, #0891B2) !important;
    color: white !important;
    border-radius: 12px;
    border: none;
    padding: 10px 18px;
    font-weight: 600;
}

[data-testid="stFileUploader"] {
    background-color: #FFFFFF !important;
    border: 2px dashed #38BDF8 !important;
    border-radius: 16px;
    padding: 15px;
}

[data-testid="stFileUploader"] * {
    color: #0F172A !important;
}

.stAlert {
    border-radius: 14px;
}

[data-testid="stDataFrame"] {
    background-color: white !important;
    border-radius: 15px;
}

h1, h2, h3, h4, h5, h6, p, label, span, div {
    color: #0F172A;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-title">
    <h1>🚆 Rake Tracking & Scheduler System</h1>
    <p>Digital Coal Handling Plant Monitoring Dashboard</p>
</div>
""", unsafe_allow_html=True)

BASE_COLUMNS = [
    "Date", "Rake ID", "Rake Type", "Source",
    "Arrival Time", "Placement Time", "Unloading Start", "Unloading End",
    "Tippler", "Status", "Delay Reason", "Remarks",
    "Scheduled Start", "Scheduled End", "Manual Sequence",
    "Scheduled Tippler", "Scheduler Remarks"
]

TIME_COLUMNS = [
    "Arrival Time", "Placement Time", "Unloading Start", "Unloading End",
    "Scheduled Start", "Scheduled End"
]


def parse_time(value):
    if pd.isna(value) or value == "":
        return None

    try:
        if isinstance(value, datetime):
            return value.time()

        if hasattr(value, "hour") and hasattr(value, "minute"):
            return value

        value = str(value).strip()

        if " " in value:
            value = value.split(" ")[-1]

        parsed = pd.to_datetime(value, format="%H:%M", errors="coerce")

        if pd.isna(parsed):
            parsed = pd.to_datetime(value, errors="coerce")

        if pd.isna(parsed):
            return None

        return parsed.time()

    except:
        return None


def prepare_dataframe(df):
    for col in BASE_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    for col in TIME_COLUMNS:
        df[col] = df[col].apply(parse_time)

    return df[BASE_COLUMNS]


def combine_date_time(date_value, time_value):
    if pd.isna(date_value) or time_value is None:
        return None
    return datetime.combine(date_value.date(), time_value)


def calculate_cycle_hours(row):
    start = combine_date_time(row["Date"], row["Arrival Time"])
    end = combine_date_time(row["Date"], row["Unloading End"])

    if start is None or end is None:
        return None

    if end < start:
        end = end + timedelta(days=1)

    return round((end - start).total_seconds() / 3600, 2)


def calculate_waiting_hours(row):
    start = combine_date_time(row["Date"], row["Arrival Time"])
    unloading_start = combine_date_time(row["Date"], row["Unloading Start"])

    if start is None or unloading_start is None:
        return None

    if unloading_start < start:
        unloading_start = unloading_start + timedelta(days=1)

    return round((unloading_start - start).total_seconds() / 3600, 2)


def get_delay_status(hours):
    if pd.isna(hours):
        return "In Progress"
    elif hours <= TARGET_CYCLE_HOURS:
        return "On Time"
    else:
        return "Delayed"


def run_analysis(df):
    df["Cycle Hours"] = df.apply(calculate_cycle_hours, axis=1)
    df["Waiting Hours"] = df.apply(calculate_waiting_hours, axis=1)
    df["Delay Status"] = df["Cycle Hours"].apply(get_delay_status)
    return df


def create_performance_chart_data(df):
    chart_df = df.dropna(subset=["Cycle Hours"]).copy()
    chart_df = chart_df.sort_values(["Date", "Arrival Time"])
    chart_df["Rake Number"] = range(1, len(chart_df) + 1)
    chart_df["Target Limit"] = TARGET_CYCLE_HOURS
    return chart_df


def show_kpi(title, value, border_color="#2563EB"):
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left-color:{border_color};">
            <h4>{title}</h4>
            <h2>{value}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )


def show_kanban_card(row):
    cycle = row["Cycle Hours"] if pd.notna(row["Cycle Hours"]) else "NA"
    waiting = row["Waiting Hours"] if pd.notna(row["Waiting Hours"]) else "NA"

    st.markdown(
        f"""
        <div class="kanban-card">
            <b>{row["Rake ID"]}</b><br>
            Type: {row["Rake Type"]}<br>
            Source: {row["Source"]}<br>
            Tippler: {row["Tippler"]}<br>
            Arrival: {row["Arrival Time"]}<br>
            Cycle: {cycle} hrs<br>
            Waiting: {waiting} hrs<br>
            Delay Reason: {row["Delay Reason"]}
        </div>
        """,
        unsafe_allow_html=True
    )


if "df" not in st.session_state:
    st.session_state.df = None


st.sidebar.title("🚆 Rake System")
st.sidebar.caption("Digital CHP Monitoring Tool")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "📘 User Guide",
        "🧩 Kanban Board",
        "🗓️ Manual Scheduler",
        "📈 Cycle Time Performance",
        "✏️ Edit Data",
        "📄 Raw Data"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info("Target Cycle Time: 7 Hours")

df = st.session_state.df


# ---------------- USER GUIDE ----------------

if page == "📘 User Guide":
    st.subheader("📘 How to Use the App")

    st.markdown("""
<div class="section-card">
<h3>Required Excel Columns</h3>
<p>Your Excel file should contain the following columns:</p>
<ul>
<li>Date</li>
<li>Rake ID</li>
<li>Rake Type</li>
<li>Source</li>
<li>Arrival Time</li>
<li>Placement Time</li>
<li>Unloading Start</li>
<li>Unloading End</li>
<li>Tippler</li>
<li>Status</li>
<li>Delay Reason</li>
<li>Remarks</li>
<li>Scheduled Start</li>
<li>Scheduled End</li>
<li>Manual Sequence</li>
<li>Scheduled Tippler</li>
<li>Scheduler Remarks</li>
</ul>

<h3>Date Format</h3>
<p><b>Example:</b> 2026-06-01</p>

<h3>Time Format</h3>
<p><b>Example:</b> 06:00, 07:30, 14:45</p>
<p>Do not enter date inside time columns.</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="section-card">
<h3>💾 File Saving Instructions</h3>

<p><b>Recommended Format:</b></p>
<ul>
<li>Microsoft Excel Workbook (*.xlsx)</li>
</ul>

<p>
The application is optimized for Excel (.xlsx) files because it preserves
date and time formats correctly and reduces upload errors.
</p>

<p><b>Alternative Format:</b></p>
<ul>
<li>CSV UTF-8 (Comma delimited) (*.csv)</li>
</ul>

<p>If saving as CSV, always select:</p>

<p style="background-color:#E2E8F0;padding:10px;border-radius:8px;">
CSV UTF-8 (Comma delimited) (*.csv)
</p>

<p>This ensures proper encoding and prevents data import issues.</p>

<p><b>Do Not Use:</b></p>
<ul>
<li>CSV (Macintosh)</li>
<li>CSV (MS-DOS)</li>
<li>Unicode Text (*.txt)</li>
<li>Excel 97-2003 Workbook (*.xls)</li>
</ul>

<p><b>Recommended Naming Convention:</b></p>
<p style="background-color:#E2E8F0;padding:10px;border-radius:8px;">
rake_data.xlsx
</p>
<p>or</p>
<p style="background-color:#E2E8F0;padding:10px;border-radius:8px;">
rake_data.csv
</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="section-card">
<h3>Important Notes</h3>
<ul>
<li>Date column must contain only dates.</li>
<li>Time columns must contain only time values in HH:MM format.</li>
<li>Do not include date values inside time columns.</li>
<li>Use Status values only as: Waiting, Placed, Unloading, Completed.</li>
<li>Upload only .xlsx or CSV UTF-8 files.</li>
<li>After uploading the file, click <b>Use this file for analysis</b> to start dashboard calculations.</li>
</ul>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="section-card">
<h3>Kanban Board Interpretation</h3>
<p>
The Kanban Board visually separates rakes into Waiting, Placed, Unloading, Completed, and Delayed stages.
This helps supervisors quickly identify bottlenecks and delayed rakes.
</p>
</div>
""", unsafe_allow_html=True)


# ---------------- HOME / UPLOAD PAGE ----------------

elif df is None:
    st.markdown("""
<div class="section-card">
<h2>Welcome to the Digital Rake Monitoring System</h2>
<p>
This application is designed to support Coal Handling Plant rake unloading monitoring.
Upload the prescribed Excel or CSV UTF-8 file below to begin dashboard analysis.
</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div class="section-card">
<h3>📂 Upload Rake Data File</h3>
<p>Upload Microsoft Excel Workbook (.xlsx) or CSV UTF-8 (Comma delimited) file.</p>
</div>
""", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose Excel or CSV file",
        type=["xlsx", "csv"]
    )

    if uploaded_file is not None:
        st.success("File uploaded successfully.")

        if st.button("🚀 Use this file for analysis", use_container_width=True):
            if uploaded_file.name.endswith(".xlsx"):
                new_df = pd.read_excel(uploaded_file)
            else:
                new_df = pd.read_csv(uploaded_file)

            new_df = prepare_dataframe(new_df)
            new_df = run_analysis(new_df)

            st.session_state.df = new_df
            st.success("Analysis completed. Go to Dashboard from sidebar.")
            st.rerun()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="section-card">
        <h3>📊 Dashboard</h3>
        <p>Track total rakes, completed rakes, delayed rakes, cycle time and waiting time.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="section-card">
        <h3>🧩 Kanban</h3>
        <p>Visualize rake movement across Waiting, Placed, Unloading, Completed and Delayed stages.</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="section-card">
        <h3>📈 Performance</h3>
        <p>Compare actual unloading cycle time with the 7-hour operational target.</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="section-card">
        <h3>🗓️ Scheduling</h3>
        <p>Update rake sequence, scheduled start, scheduled end and assigned tippler.</p>
        </div>
        """, unsafe_allow_html=True)


# ---------------- MAIN APP AFTER UPLOAD ----------------

else:

    if page == "🏠 Dashboard":
        st.subheader("🏠 Operations Dashboard")

        total_rakes = len(df)
        completed = len(df[df["Status"] == "Completed"])
        in_progress = total_rakes - completed
        delayed = len(df[df["Delay Status"] == "Delayed"])

        avg_cycle_value = df["Cycle Hours"].dropna().mean()
        avg_waiting_value = df["Waiting Hours"].dropna().mean()

        avg_cycle = round(avg_cycle_value, 2) if pd.notna(avg_cycle_value) else 0
        avg_waiting = round(avg_waiting_value, 2) if pd.notna(avg_waiting_value) else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            show_kpi("Total Rakes", total_rakes, "#2563EB")
        with c2:
            show_kpi("Completed", completed, "#16A34A")
        with c3:
            show_kpi("In Progress", in_progress, "#F59E0B")
        with c4:
            show_kpi("Delayed", delayed, "#DC2626")

        c5, c6 = st.columns(2)
        with c5:
            show_kpi("Average Cycle Hours", avg_cycle, "#7C3AED")
        with c6:
            show_kpi("Average Waiting Hours", avg_waiting, "#0891B2")

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("🚦 Live Rake Status")

        display_df = df[[
            "Date", "Rake ID", "Rake Type", "Arrival Time",
            "Scheduled Start", "Scheduled End", "Scheduled Tippler",
            "Manual Sequence", "Status",
            "Cycle Hours", "Waiting Hours", "Delay Status", "Delay Reason"
        ]].copy()

        st.dataframe(display_df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("📌 Delay Reason Analysis")
        st.bar_chart(df["Delay Reason"].fillna("Not Available").value_counts())
        st.markdown('</div>', unsafe_allow_html=True)


    elif page == "🧩 Kanban Board":
        st.subheader("🧩 Rake Kanban Board")

        st.markdown("""
<div class="section-card">
<p>
The Kanban Board provides stage-wise visibility of rake movement. It helps identify queue build-up,
unloading bottlenecks, completed rakes, and delayed rakes in a simple visual format.
</p>
</div>
""", unsafe_allow_html=True)

        waiting_df = df[df["Status"] == "Waiting"]
        placed_df = df[df["Status"] == "Placed"]
        unloading_df = df[df["Status"] == "Unloading"]
        completed_df = df[df["Status"] == "Completed"]
        delayed_df = df[df["Delay Status"] == "Delayed"]

        col1, col2, col3, col4, col5 = st.columns(5)

        kanban_data = [
            ("⏳ Waiting", waiting_df, col1, "#FEF3C7"),
            ("📍 Placed", placed_df, col2, "#DBEAFE"),
            ("⚙️ Unloading", unloading_df, col3, "#E0F2FE"),
            ("✅ Completed", completed_df, col4, "#DCFCE7"),
            ("🚨 Delayed", delayed_df, col5, "#FEE2E2")
        ]

        for title, data, column, color in kanban_data:
            with column:
                st.markdown(
                    f"""
                    <div class="kanban-header" style="background-color:{color};">
                    {title}<br>{len(data)} Rakes
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if data.empty:
                    st.caption("No rakes")
                else:
                    for _, row in data.iterrows():
                        show_kanban_card(row)


    elif page == "🗓️ Manual Scheduler":
        st.subheader("🗓️ Manual Scheduler")

        schedule_cols = [
            "Date", "Rake ID", "Rake Type", "Arrival Time", "Status",
            "Scheduled Start", "Scheduled End", "Manual Sequence",
            "Scheduled Tippler", "Scheduler Remarks"
        ]

        edited_schedule = st.data_editor(
            df[schedule_cols].copy(),
            use_container_width=True,
            num_rows="fixed",
            column_config={
                "Scheduled Tippler": st.column_config.SelectboxColumn(
                    "Scheduled Tippler",
                    options=["WT-1", "WT-2", "WT-3", "Not Assigned"]
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Waiting", "Placed", "Unloading", "Completed"]
                )
            }
        )

        if st.button("💾 Save Schedule"):
            for col in [
                "Status", "Scheduled Start", "Scheduled End",
                "Manual Sequence", "Scheduled Tippler", "Scheduler Remarks"
            ]:
                df[col] = edited_schedule[col]

            df = prepare_dataframe(df[BASE_COLUMNS])
            df = run_analysis(df)

            st.session_state.df = df
            st.success("Schedule saved. Dashboard updated.")


    elif page == "📈 Cycle Time Performance":
        st.subheader("📈 Cycle Time Performance")

        chart_df = create_performance_chart_data(df)

        if chart_df.empty:
            st.warning("No completed cycle time data available.")
        else:
            performance_data = chart_df[
                ["Rake Number", "Cycle Hours", "Target Limit"]
            ].set_index("Rake Number")

            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.line_chart(performance_data)
            st.markdown('</div>', unsafe_allow_html=True)

            avg_cycle = round(chart_df["Cycle Hours"].mean(), 2)
            max_cycle = round(chart_df["Cycle Hours"].max(), 2)
            min_cycle = round(chart_df["Cycle Hours"].min(), 2)
            above_target = len(chart_df[chart_df["Cycle Hours"] > TARGET_CYCLE_HOURS])

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                show_kpi("Average Cycle Time", avg_cycle, "#7C3AED")
            with c2:
                show_kpi("Highest Cycle Time", max_cycle, "#DC2626")
            with c3:
                show_kpi("Lowest Cycle Time", min_cycle, "#16A34A")
            with c4:
                show_kpi("Rakes Above 7 Hrs", above_target, "#F97316")

            st.markdown("""
<div class="section-card">
<h3>Performance Interpretation</h3>
<p>
This chart compares actual rake unloading cycle time against the operational target of <b>7 hours</b>.
Points above the target line represent delayed unloading.
Repeated points above 7 hours indicate that the process is not consistently meeting the required standard.
</p>
</div>
""", unsafe_allow_html=True)

            st.dataframe(
                chart_df[[
                    "Date", "Rake ID", "Rake Type", "Cycle Hours",
                    "Delay Status", "Delay Reason"
                ]],
                use_container_width=True
            )


    elif page == "✏️ Edit Data":
        st.subheader("✏️ Edit Rake Data")

        edited_df = st.data_editor(
            df[BASE_COLUMNS].copy(),
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Rake Type": st.column_config.SelectboxColumn(
                    "Rake Type",
                    options=["BOXN", "BOBR", "Other"]
                ),
                "Tippler": st.column_config.SelectboxColumn(
                    "Tippler",
                    options=["WT-1", "WT-2", "WT-3", "Not Assigned"]
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

        if st.button("💾 Save Edited Data"):
            edited_df = prepare_dataframe(edited_df)
            edited_df = run_analysis(edited_df)

            st.session_state.df = edited_df
            st.success("Edited data saved. Dashboard updated.")


    elif page == "📄 Raw Data":
        st.subheader("📄 Raw Data")

        st.dataframe(df, use_container_width=True)

        csv = df[BASE_COLUMNS].to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Download Updated CSV",
            data=csv,
            file_name="rake_data_export.csv",
            mime="text/csv",
            use_container_width=True
        )
