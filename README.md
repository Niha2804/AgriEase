# 🌱 AgriEase — Soil & Irrigation Assistant

A **stylish, elegant, and beginner‑friendly** Streamlit application made for **Agricultural Engineering students**. AgriEase helps users analyze soil parameters, get fertilizer recommendations, calculate irrigation needs, generate crop calendars, and produce downloadable field reports.

---

## ✅ Features

### 🔬 **Soil Analyzer**

* Input N‑P‑K values and soil pH
* Instant fertilizer recommendations (rule‑based)
* Optimal ranges displayed per crop
* pH‑based suggestions

### 💧 **Irrigation Helper**

* Calculates crop water requirement (mm/day)
* Considers:

  * Temperature
  * Soil texture
  * Crop growth stage
  * Rainfall (recent + forecast)
  * Canopy cover
* Outputs **net irrigation requirement** with a clean UI

### 🗓️ **Crop Calendar Generator**

* Auto‑generates stage‑wise crop schedule
* Includes start/end dates and key task recommendations

### ⚙️ **Tools Section**

#### 1. Drip Runtime Scheduler

* Calculates runtime in **minutes** based on:

  * Plant spacing
  * Emitters per plant
  * Emitter flow rate
  * Area
  * Target irrigation depth

#### 2. Water Budget & Area Tool

* Computes:

  * Field area
  * Total water required (in liters)
  * Efficiency‑adjusted volume

### 🧾 **Records & Report Export**

* Save all inputs as a record
* Review them in a table
* Export:

  * CSV record file
  * Clean HTML Field Report

---

## 🚀 Getting Started

### ✅ **1. Clone the repository**

```bash
https://github.com/your-username/AgriEase.git
```

### ✅ **2. Install dependencies**

```bash
pip install -r requirements.txt
```

### ✅ **3. Run the app**

```bash
streamlit run app.py
```

---

## 📦 Deployment (Streamlit Community Cloud)

1. Push this project to a **public GitHub repository**.
2. Go to: [https://streamlit.io/cloud](https://streamlit.io/cloud)
3. Click **New App** → Select the repo
4. Set `app.py` as the entry point.
5. Deploy 🎉

---

## 🗂️ Project Structure

```
AgriEase/
│── app.py                # Main Streamlit application
│── requirements.txt      # Python dependencies
│── data/records.csv      # Auto‑generated storage
│── README.md             # Project documentation
```

---

## 🎨 UI & Styling

* Clean green‑white gradient theme
* Soft elevated cards
* Modern typography
* Fully readable **black text**
* Fully mobile‑friendly Streamlit layout

---

## 📘 Educational Purpose

AgriEase is designed primarily for **students, beginners, and academic demonstrations**.
The values and recommendations provided are **simplified and rule‑based**. Users should consult local agronomy experts for real‑world decisions.

---

## 🤝 Contributing

Pull requests are welcome! Feel free to:

* Add more crops
* Improve UI styling
* Add more smart tools
* Enhance irrigation logic

---

## 📄 License

This project is licensed under the **MIT License**.

---

## 🌟 Acknowledgements

* Streamlit for the amazing framework
* Agricultural Engineering community
* Open‑source contributors

---

