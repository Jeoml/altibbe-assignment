# 🧠 Altibbe Assignment — Product Assessment Platform (Full Stack)

This project is a full-stack implementation of a **product transparency and AI-powered assessment system**. It enables companies to register their products, answer detailed questions about them, and receive scores based on AI-driven evaluations. Built with a modular, scalable architecture across three services:

- **Frontend** (Next.js + Tailwind)
- **Backend API** (FastAPI + PostgreSQL)
- **AI Assessment Service** (LLM-based scoring and analysis)

---

## 🚀 Live Deployments

| Section         | Live URL                                                                 |
|----------------|--------------------------------------------------------------------------|
| 🌐 Frontend     | [frontend-altibbe.vercel.app](https://frontend-altibbe.vercel.app/)       |
| 🔗 Backend API  | [altibbe-backend-production.up.railway.app/docs](https://altibbe-backend-production.up.railway.app/docs) |
| 🤖 AI Service   | [fbc41cc5185c.ngrok-free.app/docs](https://fbc41cc5185c.ngrok-free.app/docs) *(temporary endpoint)* |

> Note: AI service is tunneled via **Ngrok** due to quota exhaustion on deployment services.

## 💡 Features

- 🔐 **Secure User and Product Registration**
- 🧾 **Dynamic Question & Answer Flow per Product**
- ⚖️ **AI-Powered Evaluation with Real-time Scoring**
- 🌍 **Frontend Hosted via Vercel, Backend on Railway**
- 🧠 **Pluggable AI Service via Ngrok Tunnel**

---

## 🧪 Tech Stack

| Layer       | Technology                       |
|------------|----------------------------------|
| Frontend   | Next.js, Tailwind CSS, SWR       |
| Backend    | FastAPI, SQLAlchemy, PostgreSQL  |
| AI Service | FastAPI, LangChain, OpenAI       |
| Auth       | JWT, OAuth2 Password Flow        |
| DevOps     | Railway, Vercel, Ngrok           |

---

## 🛠️ Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jeoml/altibbe-assignment.git
   cd altibbe-assignment
