import json
import random
import string
from pathlib import Path
from datetime import datetime

import streamlit as st


# ------------------ Core Banking Logic (No input(), UI-agnostic) ------------------ #

class Bank:
    def __init__(self, database: str = "data.json"):
        self.database = Path(database)
        self.data = self._load()

    def _load(self):
        if self.database.exists():
            try:
                return json.loads(self.database.read_text())
            except Exception as err:
                # If file is corrupted, start fresh
                print(f"Error reading database: {err}")
                return []
        else:
            return []

    def _save(self):
        self.database.write_text(json.dumps(self.data, indent=2))

    def _generate_account_no(self):
        """Generate a random 10-character account number (5 letters + 5 digits)."""
        while True:
            alpha = random.choices(string.ascii_uppercase, k=5)
            num = random.choices(string.digits, k=5)
            acc_id_list = alpha + num
            random.shuffle(acc_id_list)
            acc_no = "".join(acc_id_list)

            # make sure it's unique
            if not any(a["accountNo"] == acc_no for a in self.data):
                return acc_no

    def _find_account(self, account_no: str, pin: str | None = None):
        for acc in self.data:
            if acc["accountNo"] == account_no and (pin is None or acc["pin"] == pin):
                return acc
        return None

    def _add_transaction(self, acc: dict, tx_type: str, amount: int, description: str = ""):
        """Append a transaction record to the account."""
        if "transactions" not in acc or not isinstance(acc["transactions"], list):
            acc["transactions"] = []

        acc["transactions"].append({
            "time": datetime.now().isoformat(timespec="seconds"),
            "type": tx_type,
            "amount": amount,
            "balance_after": acc["balance"],
            "description": description
        })

    # ------------ Public methods used by UI ------------ #

    def create_account(self, name: str, age: int, email: str, pin: str):
        if age < 18:
            raise ValueError("Age must be 18 or above to create an account.")

        if len(pin) != 4 or not pin.isdigit():
            raise ValueError("PIN must be a 4-digit number.")

        account_no = self._generate_account_no()
        info = {
            "name": name.strip(),
            "age": age,
            "email": email.strip(),
            "pin": pin,          # store as string so leading zeros are preserved
            "accountNo": account_no,
            "balance": 0,
            "transactions": []   # new: transaction history
        }

        # initial transaction (account created)
        self._add_transaction(info, "ACCOUNT_CREATED", 0, "Account opened")

        self.data.append(info)
        self._save()
        return info

    def deposit(self, account_no: str, pin: str, amount: int):
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than 0.")

        acc = self._find_account(account_no, pin)
        if not acc:
            raise ValueError("Invalid account number or PIN.")

        acc["balance"] += amount
        self._add_transaction(acc, "DEPOSIT", amount, "Amount deposited")
        self._save()
        return acc["balance"]

    def withdraw(self, account_no: str, pin: str, amount: int):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than 0.")

        acc = self._find_account(account_no, pin)
        if not acc:
            raise ValueError("Invalid account number or PIN.")

        if acc["balance"] < amount:
            raise ValueError("Insufficient balance.")

        acc["balance"] -= amount
        self._add_transaction(acc, "WITHDRAW", amount, "Amount withdrawn")
        self._save()
        return acc["balance"]

    def get_details(self, account_no: str, pin: str):
        acc = self._find_account(account_no, pin)
        if not acc:
            raise ValueError("Invalid account number or PIN.")
        # don't return PIN in UI
        acc_copy = acc.copy()
        acc_copy.pop("pin", None)
        return acc_copy

    def get_transactions(self, account_no: str, pin: str):
        """Return list of transactions for an account."""
        acc = self._find_account(account_no, pin)
        if not acc:
            raise ValueError("Invalid account number or PIN.")

        # if no transactions key (old accounts), return empty list
        txs = acc.get("transactions", [])
        # Could sort by time if you want; currently order of insertion
        return txs

    def update_details(self, account_no: str, pin: str, name=None, email=None, new_pin=None):
        acc = self._find_account(account_no, pin)
        if not acc:
            raise ValueError("Invalid account number or PIN.")

        changed_fields = []
        if name is not None and name.strip():
            acc["name"] = name.strip()
            changed_fields.append("name")
        if email is not None and email.strip():
            acc["email"] = email.strip()
            changed_fields.append("email")
        if new_pin is not None and new_pin.strip():
            if len(new_pin) != 4 or not new_pin.isdigit():
                raise ValueError("New PIN must be a 4-digit number.")
            acc["pin"] = new_pin
            changed_fields.append("pin")

        if changed_fields:
            desc = "Updated: " + ", ".join(changed_fields)
            self._add_transaction(acc, "ACCOUNT_UPDATE", 0, desc)

        self._save()
        return True

    def delete_account(self, account_no: str, pin: str):
        acc = self._find_account(account_no, pin)
        if not acc:
            raise ValueError("Invalid account number or PIN.")

        self.data.remove(acc)
        self._save()
        return True

    def list_accounts(self):
        # Don't expose pins or transactions in the listing
        cleaned = []
        for acc in self.data:
            c = acc.copy()
            c.pop("pin", None)
            # optional: don't show full transactions in list view
            c.pop("transactions", None)
            cleaned.append(c)
        return cleaned


# ------------------ Streamlit UI ------------------ #

# Initialize a shared Bank instance in session_state
if "bank" not in st.session_state:
    st.session_state.bank = Bank()

bank: Bank = st.session_state.bank

st.set_page_config(page_title="Central Bank", page_icon="🏦")
st.title("🏦 Central Bank")
st.write("Welcome! Manage your accounts with a simple web interface built using Streamlit.")

menu = st.sidebar.radio(
    "Select an action",
    [
        "Create Account",
        "Deposit Money",
        "Withdraw Money",
        "Show Account Details",
        "Transaction History",       # NEW
        "Update Account Details",
        "Delete Account",
        "List All Accounts",
    ]
)

st.sidebar.info("All data is stored locally in `data.json`.")


# --------- Create Account --------- #
if menu == "Create Account":
    st.header("Create a New Account")

    with st.form("create_account_form"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        email = st.text_input("Email")
        pin = st.text_input("4-digit PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Create Account")

    if submitted:
        try:
            acc = bank.create_account(name, int(age), email, pin)
            st.success("Account created successfully! Please note down your account number.")
            st.code(f"Account Number: {acc['accountNo']}")
            st.subheader("Account Details")
            st.json({k: v for k, v in acc.items() if k not in ["pin", "transactions"]})
        except ValueError as e:
            st.error(str(e))


# --------- Deposit Money --------- #
elif menu == "Deposit Money":
    st.header("Deposit Money")

    with st.form("deposit_form"):
        acc_no = st.text_input("Account Number")
        pin = st.text_input("PIN", type="password", max_chars=4)
        amount = st.number_input("Amount to Deposit", min_value=1, step=1)
        submitted = st.form_submit_button("Deposit")

    if submitted:
        try:
            new_balance = bank.deposit(acc_no, pin, int(amount))
            st.success(f"Deposit successful. New balance: {new_balance}")
        except ValueError as e:
            st.error(str(e))


# --------- Withdraw Money --------- #
elif menu == "Withdraw Money":
    st.header("Withdraw Money")

    with st.form("withdraw_form"):
        acc_no = st.text_input("Account Number")
        pin = st.text_input("PIN", type="password", max_chars=4)
        amount = st.number_input("Amount to Withdraw", min_value=1, step=1)
        submitted = st.form_submit_button("Withdraw")

    if submitted:
        try:
            new_balance = bank.withdraw(acc_no, pin, int(amount))
            st.success(f"Withdrawal successful. New balance: {new_balance}")
        except ValueError as e:
            st.error(str(e))


# --------- Show Account Details --------- #
elif menu == "Show Account Details":
    st.header("Show Account Details")

    with st.form("show_details_form"):
        acc_no = st.text_input("Account Number")
        pin = st.text_input("PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Show Details")

    if submitted:
        try:
            details = bank.get_details(acc_no, pin)
            st.subheader("Account Information")
            st.json(details)
        except ValueError as e:
            st.error(str(e))


# --------- Transaction History (NEW) --------- #
elif menu == "Transaction History":
    st.header("Transaction History")

    with st.form("tx_history_form"):
        acc_no = st.text_input("Account Number")
        pin = st.text_input("PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Show History")

    if submitted:
        try:
            txs = bank.get_transactions(acc_no, pin)
            if not txs:
                st.info("No transactions found for this account.")
            else:
                st.subheader("Transactions")
                # Newest first (optional)
                txs_sorted = sorted(txs, key=lambda x: x["time"], reverse=True)
                st.dataframe(txs_sorted, use_container_width=True)
        except ValueError as e:
            st.error(str(e))


# --------- Update Account Details --------- #
elif menu == "Update Account Details":
    st.header("Update Account Details")

    with st.form("update_details_form"):
        acc_no = st.text_input("Account Number")
        pin = st.text_input("Current PIN", type="password", max_chars=4)

        st.markdown("#### Fields to Update (optional)")
        new_name = st.text_input("New Name", placeholder="Leave blank to keep unchanged")
        new_email = st.text_input("New Email", placeholder="Leave blank to keep unchanged")
        new_pin = st.text_input("New 4-digit PIN", type="password", max_chars=4, placeholder="Leave blank to keep unchanged")

        submitted = st.form_submit_button("Update")

    if submitted:
        try:
            kwargs = {}
            if new_name.strip():
                kwargs["name"] = new_name
            if new_email.strip():
                kwargs["email"] = new_email
            if new_pin.strip():
                kwargs["new_pin"] = new_pin

            if not kwargs:
                st.warning("You didn't enter anything to update.")
            else:
                bank.update_details(acc_no, pin, **kwargs)
                st.success("Details updated successfully.")
        except ValueError as e:
            st.error(str(e))


# --------- Delete Account --------- #
elif menu == "Delete Account":
    st.header("Delete Account")

    with st.form("delete_account_form"):
        acc_no = st.text_input("Account Number")
        pin = st.text_input("PIN", type="password", max_chars=4)
        confirm = st.checkbox("I understand this will permanently delete my account.")
        submitted = st.form_submit_button("Delete Account")

    if submitted:
        if not confirm:
            st.warning("Please confirm that you want to delete the account.")
        else:
            try:
                bank.delete_account(acc_no, pin)
                st.success("Account deleted successfully.")
            except ValueError as e:
                st.error(str(e))


# --------- List All Accounts + SEARCH BY NAME/EMAIL ONLY --------- #
elif menu == "List All Accounts":
    st.header("All Accounts")

    accounts = bank.list_accounts()

    if not accounts:
        st.info("No accounts found.")
    else:
        st.subheader("Search")

        query = st.text_input("Search by name or email (optional)")

        # Apply search filter
        filtered = accounts
        if query.strip():
            q = query.strip().lower()
            filtered = [
                acc for acc in accounts
                if q in acc.get("name", "").lower()
                or q in acc.get("email", "").lower()
            ]

        st.subheader("Results")

        if not filtered:
            st.info("No accounts match the current search.")
        else:
            st.write(f"Showing **{len(filtered)}** account(s).")
            st.table(filtered)
