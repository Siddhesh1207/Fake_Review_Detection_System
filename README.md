# Verisure 🛡️
### AI-Powered Fake Review Detection & Consensus Analysis System

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Backend-Flask-000000?logo=flask&logoColor=white)
![PyTorch](https://img.shields.io/badge/AI-PyTorch%20%26%20Transformers-EE4C2C?logo=pytorch&logoColor=white)
![Selenium](https://img.shields.io/badge/Scraping-Selenium%20%2B%20Chromium-43B02A?logo=selenium&logoColor=white)
![Docker](https://img.shields.io/badge/Deployment-Docker-2496ED?logo=docker&logoColor=white)

**Verisure** is a full-stack authenticity verification platform designed to detect fake reviews in the hospitality industry. It combines a **fine-tuned DistilRoBERTa transformer model** with real-time web scraping to analyze feedback.

Beyond simple classification, it features a novel **"Cross-Check" logic** that contextualizes individual reviews against the consensus of historical data to identify suspicious outliers.

---

## 🌟 Live Demo
- **Frontend (UI):** [https://sid12verisure.netlify.app/]
- **Backend (API):** [https://siddhesh1207-verisure.hf.space]

---

## 🔥 Key Features

### 🧠 Advanced AI Detection
- Uses a **DistilRoBERTa** transformer model fine-tuned on a dataset of 20k+ fake and real reviews.
- Provides confidence scores for every prediction.

### 🕷️ Real-Time URL Analysis
- **Live Scraping:** Paste a Booking.com URL, and the system autonomously scrapes the latest reviews using **Selenium & Chromium**.
- **Stealth Mode:** Implements `selenium-stealth` to bypass bot detection mechanisms.

### 📊 Contextual Cross-Check
- **Consensus Engine:** Analyzes the aggregate sentiment of a hotel's history (e.g., "WiFi is generally bad").
- **Outlier Detection:** Flags reviews that contradict the established facts (e.g., a review praising "Super fast WiFi" in a hotel known for bad connectivity is flagged as suspicious).

### 📂 Bulk Analysis
- Supports **CSV File Uploads** for batch processing of thousands of reviews at once.

---

## 🏗️ Architecture

The application uses a **Microservices-style** architecture to handle heavy ML loads and browser automation:

1.  **Frontend:** Hosted on **Netlify**. A responsive interface built with HTML5/CSS3/JS that communicates via REST API.
2.  **Backend:** Hosted on **Hugging Face Spaces**.
    - **Dockerized Environment:** Runs a custom container with Python 3.10 and **Headless Chromium** installed.
    - **Flask API:** Exposes endpoints for prediction, scraping, and file analysis.
    - **Git LFS:** Manages the large model weights (~400MB).

---

## 🛠️ Tech Stack

- **Language:** Python 3.10
- **Web Framework:** Flask
- **ML Framework:** PyTorch, Hugging Face Transformers
- **Model:** Fine-tuned DistilRoBERTa
- **Scraping:** Selenium, Selenium-Stealth, BeautifulSoup4
- **Deployment:** Docker, Hugging Face Spaces (16GB RAM instance), Netlify
