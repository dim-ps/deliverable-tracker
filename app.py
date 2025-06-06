import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
import plotly.express as px
from fpdf import FPDF

st.set_page_config(page_title="Project Deliverables Tracker", layout="wide")
st.title("📋 Project Deliverables Tracker")

# Αρχικό template δεδομένων
def create_empty_df():
    return pd.DataFrame(columns=[
        "Project Name", "Task/Deliverable", "Description", "Role", "Status",
        "Soft Deadline", "Hard Deadline", "Actual Completion",
        "Priority", "Comments"
    ])

# Αρχικοποίηση session state αν δεν υπάρχει
if "df" not in st.session_state:
    st.session_state.df = create_empty_df()

# Εισαγωγή νέου παραδοτέου
st.subheader("➕ Add New Deliverable")
with st.form("add_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        project = st.text_input("Project Name")
        role = st.selectbox("Role", ["Lead", "Contributor"])
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    with col2:
        task = st.text_input("Task/Deliverable")
        description = st.text_area("Description")
        status = st.selectbox("Status", ["Not Started", "In Progress", "Completed", "Delayed"])
    with col3:
        soft_deadline = st.date_input("Soft Deadline")
        hard_deadline = st.date_input("Hard Deadline")
        actual_completion = st.date_input("Actual Completion", value=None, disabled=False)
        comments = st.text_input("Comments")

    submitted = st.form_submit_button("Add Deliverable")
    if submitted:
        new_row = {
            "Project Name": project,
            "Task/Deliverable": task,
            "Description": description,
            "Role": role,
            "Status": status,
            "Soft Deadline": soft_deadline,
            "Hard Deadline": hard_deadline,
            "Actual Completion": actual_completion if actual_completion else "",
            "Priority": priority,
            "Comments": comments
        }
        st.session_state.df = st.session_state.df.append(new_row, ignore_index=True)
        st.success("Deliverable added!")

# Εισαγωγή από αρχείο Excel
st.subheader("📤 Import from Excel")
uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
if uploaded_file:
    imported_df = pd.read_excel(uploaded_file)
    st.session_state.df = pd.concat([st.session_state.df, imported_df], ignore_index=True)
    st.success("Excel data imported successfully!")

# Φίλτρο ανά ρόλο
st.subheader("🔍 Filter by Role")
selected_role = st.selectbox("Select Role to Filter", ["All"] + sorted(st.session_state.df["Role"].dropna().unique().tolist()))

filtered_df = st.session_state.df.copy()
if selected_role != "All":
    filtered_df = filtered_df[filtered_df["Role"] == selected_role]

# Ειδοποιήσεις για επερχόμενα deadlines
st.subheader("⏰ Upcoming Deadlines")
today = datetime.today().date()
upcoming_df = filtered_df[(pd.to_datetime(filtered_df["Hard Deadline"]) - pd.to_datetime(today)).dt.days <= 7]
if not upcoming_df.empty:
    st.warning("You have deliverables with hard deadlines within the next 7 days!")
    st.dataframe(upcoming_df, use_container_width=True)
else:
    st.info("No upcoming deadlines in the next 7 days.")

# Προβολή δεδομένων
st.subheader("📊 Current Deliverables")
if not filtered_df.empty:
    def highlight_status(s):
        color_map = {
            "Not Started": "#FFCC00",
            "In Progress": "#00B0F0",
            "Completed": "#92D050",
            "Delayed": "#FF0000",
        }
        return [f"background-color: {color_map.get(val, '')}" for val in s]

    styled_df = filtered_df.style.apply(highlight_status, subset=["Status"])
    st.dataframe(styled_df, use_container_width=True)
else:
    st.info("No deliverables added yet.")

# Ημερολόγιο παραδοτέων
st.subheader("🗓️ Calendar View")
calendar_df = filtered_df[["Project Name", "Task/Deliverable", "Hard Deadline"]].copy()
calendar_df = calendar_df.rename(columns={"Hard Deadline": "date", "Task/Deliverable": "name"})
calendar_df["date"] = pd.to_datetime(calendar_df["date"])
calendar_df["name"] = calendar_df["Project Name"] + " - " + calendar_df["name"]
st.dataframe(calendar_df[["date", "name"]].sort_values("date"), use_container_width=True)

# Gantt Chart
st.subheader("📈 Gantt Chart")
if not filtered_df.empty:
    gantt_df = filtered_df.copy()
    gantt_df["Start"] = pd.to_datetime(gantt_df["Soft Deadline"])
    gantt_df["End"] = pd.to_datetime(gantt_df["Hard Deadline"])
    fig = px.timeline(gantt_df, x_start="Start", x_end="End", y="Task/Deliverable", color="Status", title="Gantt Chart")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

# Εξαγωγή σε Excel
st.subheader("📥 Export")
if st.button("Export to Excel"):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.df.to_excel(writer, index=False, sheet_name="Deliverables")
    st.download_button(
        label="Download Excel File",
        data=output.getvalue(),
        file_name="deliverables_tracker.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Εξαγωγή σε PDF
if st.button("Export to PDF"):
    class PDF(FPDF):
        def header(self):
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, "Project Deliverables Report", ln=True, align="C")

        def chapter_title(self, title):
            self.set_font("Arial", "B", 10)
            self.cell(0, 10, title, ln=True, align="L")

        def chapter_body(self, text):
            self.set_font("Arial", "", 9)
            self.multi_cell(0, 8, text)

    pdf = PDF()
    pdf.add_page()
    for index, row in filtered_df.iterrows():
        pdf.chapter_title(f"{row['Project Name']} - {row['Task/Deliverable']}")
        pdf.chapter_body(
            f"Role: {row['Role']}\nStatus: {row['Status']}\nPriority: {row['Priority']}\nSoft Deadline: {row['Soft Deadline']}\nHard Deadline: {row['Hard Deadline']}\nActual Completion: {row['Actual Completion']}\nDescription: {row['Description']}\nComments: {row['Comments']}"
        )
        pdf.ln(5)
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    st.download_button(
        label="Download PDF Report",
        data=pdf_output.getvalue(),
        file_name="deliverables_report.pdf",
        mime="application/pdf"
    )
