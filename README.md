# 🧠 Altibbe Assignment — Product Assessment Platform (AI Service Now on AWS EC2)

This is a full-stack implementation of a **product transparency and AI-powered assessment system**. It allows companies to register their products, respond to dynamically generated questions, and receive scores based on AI evaluations. 

> ⚠️ **Note**: As of **August 3rd, 1:05 AM IST**, the AI service was migrated from my laptop to an **AWS EC2 instance** for improved stability and performance.

---

## 🚀 Live Deployments

| Section         | Live URL                                                                 |
|----------------|--------------------------------------------------------------------------|
| 🌐 Frontend     | [frontend-altibbe.vercel.app](https://frontend-altibbe.vercel.app/)       |
| 🔗 Backend API  | [altibbe-backend-production.up.railway.app/docs](https://altibbe-backend-production.up.railway.app/docs) |
| 🤖 AI Service   | [New AI Service on EC2 (FastAPI Docs)](https://<your-ec2-public-ip>.ngrok-free.app/docs) *(Live as of Aug 3, 1:05 AM)* |

---

## 💡 Features

- 🔐 **Secure Company & Product Registration**
- ❓ **Dynamic Product Q&A Flow**
- 🧠 **AI-Powered Scoring System**
- 📊 **Assessment Progress Tracking**
- 🌐 **Frontend on Vercel**, **Backend on Railway**, **AI Service on EC2**

---

## 🧪 Tech Stack

| Layer       | Technology                       |
|------------|----------------------------------|
| Frontend   | Next.js, Tailwind CSS, SWR       |
| Backend    | FastAPI, SQLAlchemy, PostgreSQL  |
| AI Service | FastAPI, LangChain, OpenAI       |
| Auth       | JWT, OAuth2 Password Flow        |
| DevOps     | Railway, Vercel, AWS EC2, Ngrok  |

---

## 🛠️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jeoml/altibbe-assignment.git
   cd altibbe-assignment
