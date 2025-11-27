# 🏦 Streamlit Banking Management System

A simple yet fully functional **Banking Application** built with **Python** and **Streamlit**, featuring real-time account management, transaction history tracking, and search & filtering capabilities.  
This project simulates a basic core banking UI and stores data locally in `data.json`.

---

## 🚀 Features

- ✳️ Create new bank accounts
- 💰 Deposit money
- 💸 Withdraw money
- 📄 View account details
- 🔐 Update account information
- 🗑️ Delete accounts
- 📋 List all accounts with **search & filter**
- 📊 Detailed **transaction history** with timestamp and balance updates
- 🗃️ Local JSON database (no SQL setup required)

---

## 🖼️ UI Preview (Streamlit)

The full UI is built in Streamlit with sidebar navigation, forms, tables and interactive components.

---

## 🧠 Tech Stack

| Technology | Usage |
|------------|--------|
| **Python** | Core backend logic |
| **Streamlit** | Interactive UI |
| **JSON** | Persistent database |
| **GitHub** | Version control & repository |
| **(Optional)** Streamlit Cloud / Render | Deployment platform |

---

## 📁 Project Structure

bank-app/
  ├─ app.py
  ├─ data.json        # optional, can be created at runtime
  ├─ requirements.txt
  └─ README.md

---

## ⚙️ Installation & Running Locally

### **Clone the repository**
```bash
git clone https://github.com/<your-username>/streamlit-bank-app.git
cd streamlit-bank-app
pip install -r requirements.txt
streamlit run app.py
```
