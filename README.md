# 🍏 Healthy Snack Ideas Generator

Welcome to the **Healthy Snack Ideas Generator**!  
This Flask-based web app helps users generate healthy snack ideas based on the ingredients they have at home. It uses the **Groq API** to power the AI-driven snack suggestions. Users can save their favorite snacks to a personalized diet plan.

---

## 🚀 Features

- **🧠 AI-Powered Snack Ideas**: Generate healthy snack ideas based on ingredients and optional goals (e.g., lose weight, high protein).
- **📋 Save to Diet Plan**: Save your favorite snacks to a personalized list.
- **🗑️ Remove Snacks**: Easily remove snacks from your plan.
- **💻 Simple and Intuitive UI**: Built with **Tailwind CSS** for a clean, modern experience.

---

## 🧾 Prerequisites

Make sure you have the following installed:

- ✅ Python 3.8+
- ✅ pip (Python package manager)
- ✅ Groq API Key ([Get it here](https://groq.com/))

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/healthy-snack-ideas-generator.git
cd healthy-snack-ideas-generator
```

---

### 2. Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Set Up Environment Variables

1. Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

2. Open the `.env` file and add your Groq API Key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

> 💡 Replace `your_groq_api_key_here` with your actual key from [Groq](https://groq.com/)

---

## ▶️ Run the App Locally

```bash
flask run
```

---

## 🧪 Example `.env.example`

```env
# Rename this file to .env and add your API key below
GROQ_API_KEY=your_groq_api_key_here
```


