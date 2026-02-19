import streamlit as st
import pandas as pd

FILE = "Travel_Expense_Tracker.xlsx"

st.title("✈️ Travel Expense Tracker")

# ===============================
# LOAD DATA
# ===============================
members_df = pd.read_excel(FILE, sheet_name="Members")
expenses_df = pd.read_excel(FILE, sheet_name="Expenses")

members = members_df["name"].tolist()

# ===============================
# ADD EXPENSE
# ===============================
st.header("➕ Add Expense")

date = st.date_input("Date", value=pd.Timestamp.today(), key="add_date")
desc = st.text_input("Description", key="add_desc")
amount = st.number_input("Amount", min_value=0.0, key="add_amount")
payer = st.selectbox("Paid by", members, key="add_payer")
participants = st.multiselect("Participants", members, default=[payer], key="add_participants")

if st.button("Add Expense"):

    new_id = expenses_df["expense_id"].max() + 1 if len(expenses_df) else 1

    new_row = {
        "expense_id": new_id,
        "date": date,
        "description": desc,
        "amount": amount,
        "paid_by": payer,
        "participants": ",".join(participants)
    }

    expenses_df = pd.concat([expenses_df, pd.DataFrame([new_row])], ignore_index=True)

    with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        expenses_df.to_excel(writer, sheet_name="Expenses", index=False)

    st.success("Expense added")
    st.rerun()

# ===============================
# SHOW EXPENSES
# ===============================
st.header("📋 Expenses")
st.dataframe(expenses_df.astype(str))

# ===============================
# TOTAL EXPENSE
# ===============================
total_expense = expenses_df["amount"].sum()

st.metric("💵 Total Trip Expense", f"₹ {round(total_expense,2)}")

avg_per_person = total_expense / len(members) if len(members) else 0
st.metric("👤 Avg per person", f"₹ {round(avg_per_person,2)}")

# ===============================
# BALANCE DASHBOARD
# ===============================
st.header("💰 Balance Dashboard")

balance = {m: 0 for m in members}

for _, row in expenses_df.iterrows():

    payer = row["paid_by"]
    amount = row["amount"]

    participants = str(row["participants"]).split(",")

    if len(participants) == 0:
        continue

    share = amount / len(participants)

    for p in participants:
        if p in balance:
            balance[p] -= share

    if payer in balance:
        balance[payer] += amount

bal_df = pd.DataFrame(list(balance.items()), columns=["Member", "Net Balance"])
bal_df["Net Balance"] = bal_df["Net Balance"].round(2)

st.dataframe(bal_df.astype(str))

# ===============================
# SETTLEMENT
# ===============================
st.header("🤝 Settlement Suggestions")

creditors = []
debtors = []

for person, amt in balance.items():
    if amt > 0:
        creditors.append([person, amt])
    elif amt < 0:
        debtors.append([person, -amt])

settlements = []

i = 0
j = 0

while i < len(debtors) and j < len(creditors):

    debtor, d_amt = debtors[i]
    creditor, c_amt = creditors[j]

    pay = min(d_amt, c_amt)

    settlements.append((debtor, creditor, round(pay, 2)))

    debtors[i][1] -= pay
    creditors[j][1] -= pay

    if debtors[i][1] < 0.01:
        i += 1
    if creditors[j][1] < 0.01:
        j += 1

if settlements:
    for s in settlements:
        st.write(f"👉 **{s[0]} pays {s[1]} ₹{s[2]}**")
else:
    st.write("All settled 👍")

# ===============================
# WHATSAPP SUMMARY
# ===============================
st.header("📱 WhatsApp Settlement Summary")

trip_name = st.text_input("Trip name (optional)", value="Trip")

if st.button("Generate WhatsApp Message"):

    if settlements:

        msg = f"*{trip_name} Settlement*\n\n"

        for s in settlements:
            msg += f"{s[0]} pays {s[1]} ₹{s[2]}\n"

        msg += "\nThanks 🙂"

        st.text_area("Copy message", msg, height=200)

    else:
        st.info("Nothing to settle")


# ===============================
# EDIT / DELETE
# ===============================
st.header("✏️ Edit / Delete Expense")

if len(expenses_df) > 0:

    expense_ids = expenses_df["expense_id"].tolist()

    selected_id = st.selectbox("Select expense", expense_ids, key="select_expense")

    selected_row = expenses_df[expenses_df["expense_id"] == selected_id].iloc[0]

    st.write("Selected expense:")
    st.write(selected_row.astype(str))

    # Safe date conversion
    try:
        default_date = pd.to_datetime(selected_row["date"])
    except:
        default_date = pd.Timestamp.today()

    st.subheader("Edit Expense")

    edit_date = st.date_input("Date", default_date, key="edit_date")
    edit_desc = st.text_input("Description", selected_row["description"], key="edit_desc")
    edit_amount = st.number_input("Amount", value=float(selected_row["amount"]), key="edit_amount")
    edit_payer = st.selectbox(
        "Paid by",
        members,
        index=members.index(selected_row["paid_by"]),
        key="edit_payer"
    )

    edit_participants = st.multiselect(
        "Participants",
        members,
        default=str(selected_row["participants"]).split(","),
        key="edit_participants"
    )

    # SAVE
    if st.button("💾 Save Changes"):

        expenses_df.loc[expenses_df["expense_id"] == selected_id, "date"] = edit_date
        expenses_df.loc[expenses_df["expense_id"] == selected_id, "description"] = edit_desc
        expenses_df.loc[expenses_df["expense_id"] == selected_id, "amount"] = edit_amount
        expenses_df.loc[expenses_df["expense_id"] == selected_id, "paid_by"] = edit_payer
        expenses_df.loc[expenses_df["expense_id"] == selected_id, "participants"] = ",".join(edit_participants)

        with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            expenses_df.to_excel(writer, sheet_name="Expenses", index=False)

        st.success("Expense updated")
        st.rerun()

    # DELETE
    if st.button("🗑️ Delete Expense"):

        expenses_df = expenses_df[expenses_df["expense_id"] != selected_id]

        with pd.ExcelWriter(FILE, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            expenses_df.to_excel(writer, sheet_name="Expenses", index=False)

        st.success("Expense deleted")
        st.rerun()
# ===============================
# BACKUP DOWNLOAD
# ===============================
st.header("💾 Backup & Export")

with open(FILE, "rb") as f:
    st.download_button(
        label="⬇️ Download Excel Backup",
        data=f,
        file_name="Travel_Expense_Backup.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

