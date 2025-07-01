import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.set_page_config(page_title="Expense Tracker AI", layout="wide")
st.title("💰 Expense Tracker with Budget AI Insights")

# === Phase 1: File Upload ===
uploaded_file = st.file_uploader("📁 Upload your bank statement (CSV)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.dropna(inplace=True)

    # === Phase 2: Data Cleaning ===
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df.dropna(subset=['Date'], inplace=True)
    df['Amount'] = df['Amount'].astype(float)
    df['Type'] = df['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')

    # === Phase 3: Categorization ===
    def categorize(description):
        description = description.lower()
        if "zomato" in description or "swiggy" in description or "restaurant" in description:
            return "Food"
        elif "uber" in description or "ola" in description or "fuel" in description or "petrol" in description:
            return "Transport"
        elif "electricity" in description or "bill" in description or "internet" in description:
            return "Utilities"
        elif "amazon" in description or "flipkart" in description or "shopping" in description or "big bazaar" in description:
            return "Shopping"
        elif "salary" in description or "income" in description:
            return "Salary"
        elif "netflix" in description:
            return "Entertainment"
        else:
            return "Other"

    df['Category'] = df['Description'].apply(categorize)
    df['YearMonth'] = df['Date'].dt.to_period('M').astype(str)

    st.markdown("### 📊 Cleaned & Categorized Data")
    st.dataframe(df)

    # === Phase 4: Visual Dashboard ===
    total_income = df[df['Type'] == 'Income']['Amount'].sum()
    total_expense = -df[df['Type'] == 'Expense']['Amount'].sum()
    balance = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"₹ {total_income:,.0f}")
    col2.metric("Total Expense", f"₹ {total_expense:,.0f}")
    col3.metric("Net Balance", f"₹ {balance:,.0f}")

    st.markdown("### 🗕 Monthly Expense Trend")
    monthly_expense = df[df['Type'] == 'Expense'].groupby('YearMonth')['Amount'].sum()
    monthly_expense = -monthly_expense

    fig, ax = plt.subplots()
    ax.plot(monthly_expense.index, monthly_expense.values, marker='o', color='skyblue')
    ax.set_title("Monthly Expense Trend")
    ax.set_xlabel("Month")
    ax.set_ylabel("₹ Expense")
    ax.tick_params(axis='x', rotation=0)
    st.pyplot(fig)

    st.markdown("### 👁 Expense by Category (Pie Chart)")
    expense_df = df[df['Type'] == 'Expense']
    category_sum = expense_df.groupby('Category')['Amount'].sum()
    category_sum = -category_sum.sort_values()

    fig2, ax2 = plt.subplots()
    ax2.pie(category_sum, labels=category_sum.index, autopct='%1.1f%%', startangle=90)
    ax2.axis('equal')
    st.pyplot(fig2)

    # === Phase 5: Overspending Prediction ===
    st.markdown("### 🧮 Overspending Prediction")
    avg_expense = monthly_expense.mean()
    threshold = avg_expense * 1.2

    prediction_df = monthly_expense.reset_index()
    prediction_df.columns = ['Month', 'Expense']
    prediction_df['Status'] = prediction_df['Expense'].apply(
        lambda x: '🔴 Overspending Risk' if x > threshold else '🟢 Within Budget'
    )

    st.dataframe(prediction_df)

    if any(prediction_df['Status'] == '🔴 Overspending Risk'):
        st.warning("⚠️ Warning: You are at risk of overspending in some months.")

    # === Phase 6: Smart Budget Advice ===
    st.markdown("### 🤖 Smart Budget Advice")

    category_expense = expense_df.groupby('Category')['Amount'].sum()
    category_expense = -category_expense.sort_values(ascending=True)
    top_categories = category_expense.head(3)

    st.write("🧾 Top Spending Categories:")
    st.dataframe(top_categories)

    advice = []
    for category in top_categories.index:
        if category == 'Food':
            advice.append("🍔 You’re spending a lot on food. Try cooking at home more often or setting a monthly dining budget.")
        elif category == 'Shopping':
            advice.append("🛍️ High shopping bills detected. Consider limiting impulse buys or setting a wishlist before shopping.")
        elif category == 'Transport':
            advice.append("🚗 Transport costs are high. Try carpooling, using public transport, or optimizing your routes.")
        elif category == 'Utilities':
            advice.append("💡 Utilities seem high. Consider energy-saving habits or reviewing your internet/electricity plans.")
        elif category == 'Entertainment':
            advice.append("📺 Subscriptions and entertainment are adding up. Cancel unused subscriptions or switch to cheaper plans.")
        else:
            advice.append(f"💡 Spending on **{category}** is significant. Try to review if all those purchases were essential.")

    for tip in advice:
        st.success(tip)

    # === Phase 7: Budget Chat Assistant via LM Studio ===
    st.markdown("### 💬 Chat with your Budget Assistant (Offline, via LM Studio)")
    question = st.text_input("Ask any question about your spending data...")

    if question:
        summary = f"""
        - Total Income: ₹{total_income:,.0f}
        - Total Expense: ₹{total_expense:,.0f}
        - Balance: ₹{balance:,.0f}
        - Top Categories: {', '.join(top_categories.index.tolist())}
        - Overspending Months: {', '.join(prediction_df[prediction_df['Status'] == '🔴 Overspending Risk']['Month'].tolist())}
        """

        prompt = f"""
        You are a helpful budgeting assistant. Based on this summary:
        {summary}

        User's Question: {question}

        Answer in a simple, friendly tone.
        """

        with st.spinner("💭 Thinking..."):
            try:
                response = requests.post(
                    "http://localhost:1234/v1/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": "mistral-7b-instruct-v0.1",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7
                    }
                )
                reply = response.json()['choices'][0]['message']['content']
                st.success(reply)
            except Exception as e:
                st.error(f"⚠️ Failed to get response from LM Studio. Make sure the server is running. Error: {e}")

else:
    st.info("👆 Please upload a CSV file to get started.")



