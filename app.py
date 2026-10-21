from flask import Flask, render_template, jsonify
import pandas as pd
import os
import numpy as np

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_data():
    # Letakkan file latihan1.csv atau latihan1 (1).csv di folder yang sama dengan app.py
    candidates = ["latihan1.csv", "latihan1 (1).csv"]
    for name in candidates:
        path = os.path.join(BASE_DIR, name)
        if os.path.exists(path):
            df = pd.read_csv(path)
            return df, name
    return None, None

def clean_number(value):
    if pd.isna(value):
        return None
    return round(float(value), 2)

def build_dashboard():
    df, filename = load_data()
    if df is None:
        return {
            "loaded": False,
            "message": "File CSV belum ditemukan. Letakkan latihan1.csv di folder yang sama dengan app.py.",
            "filename": None
        }

    df = df.dropna(how="all")
    numeric = df.select_dtypes(include="number")
    categorical = df.select_dtypes(exclude="number")

    summary = []
    for col in df.columns:
        series = df[col].dropna()
        if col in numeric.columns:
            s = numeric[col].dropna()
            modes = s.mode()
            summary.append({
                "name": col, "type": "Numerik", "count": int(s.count()),
                "mean": clean_number(s.mean()), "median": clean_number(s.median()),
                "mode": ", ".join(map(str, modes.head(3).tolist())) if not modes.empty else "-",
                "std": clean_number(s.std()), "min": clean_number(s.min()),
                "max": clean_number(s.max())
            })
        else:
            modes = series.mode()
            summary.append({
                "name": col, "type": "Kategori/Teks", "count": int(series.count()),
                "mean": None, "median": None,
                "mode": ", ".join(map(str, modes.head(3).tolist())) if not modes.empty else "-",
                "std": None, "min": None, "max": None
            })

    charts = {}
    for col in numeric.columns:
        vals = numeric[col].dropna()
        if vals.empty:
            continue
        # Batasi label supaya chart tetap mudah dibaca
        counts = vals.value_counts().sort_index()
        if len(counts) > 18:
            bins = pd.cut(vals, bins=10)
            counts = bins.value_counts().sort_index()
            labels = [str(x) for x in counts.index]
        else:
            labels = [str(x) for x in counts.index]
        charts[col] = {"labels": labels, "values": [int(x) for x in counts.values]}

    category_charts = {}
    for col in categorical.columns:
        counts = df[col].dropna().astype(str).value_counts().head(10)
        if not counts.empty:
            category_charts[col] = {"labels": counts.index.tolist(), "values": counts.astype(int).tolist()}

    decisions = []
    lower_map = {str(c).strip().lower(): c for c in df.columns}

    def find_col(*names):
        for name in names:
            if name.lower() in lower_map:
                return lower_map[name.lower()]
        return None

    score_col = find_col("Exam_Score", "Exam Score", "Nilai", "Score")
    study_col = find_col("Study_Hours", "Study Hours", "Jam_Belajar")
    sleep_col = find_col("Sleep_Hours", "Sleep Hours", "Jam_Tidur")
    attendance_col = find_col("Attendance", "Kehadiran")
    screen_col = find_col("Screen_Hours", "Screen Hours", "Jam_Layar")
    satisfaction_col = find_col("Satisfaction", "Kepuasan")

    def mean_of(col):
        return float(pd.to_numeric(df[col], errors="coerce").mean()) if col else None

    if score_col:
        score = pd.to_numeric(df[score_col], errors="coerce").dropna()
        if not score.empty:
            avg = score.mean()
            med = score.median()
            decisions.append({
                "title": "Gambaran nilai",
                "detail": f"Rata-rata {score_col} adalah {avg:.2f}, sedangkan median {med:.2f}. " +
                          ("Rata-rata di bawah 60; evaluasi materi dan dukungan belajar perlu diprioritaskan." if avg < 60 else
                           "Rata-rata 60–74; penguatan materi dan latihan terarah dapat membantu." if avg < 75 else
                           "Rata-rata minimal 75; pertahankan strategi belajar dan identifikasi siswa yang masih membutuhkan bantuan.")
            })
            if score.std() is not None:
                decisions.append({
                    "title": "Pemerataan hasil",
                    "detail": f"Simpangan baku nilai adalah {score.std():.2f}. " +
                              ("Nilai cukup beragam; sebaiknya dukungan belajar disesuaikan per kelompok." if score.std() >= 15 else
                               "Sebaran nilai relatif lebih rapat; tetap periksa siswa dengan nilai terendah.")
                })

    if study_col and score_col:
        temp = df[[study_col, score_col]].apply(pd.to_numeric, errors="coerce").dropna()
        if len(temp) >= 3 and temp[study_col].nunique() > 1 and temp[score_col].nunique() > 1:
            corr = temp[study_col].corr(temp[score_col])
            strength = "positif" if corr > 0.2 else "negatif" if corr < -0.2 else "lemah/tidak jelas"
            decisions.append({
                "title": "Jam belajar dan nilai",
                "detail": f"Korelasi antara {study_col} dan {score_col} sebesar {corr:.2f} ({strength}). " +
                          "Gunakan ini sebagai petunjuk awal, bukan bukti sebab-akibat."
            })

    if attendance_col:
        avg = mean_of(attendance_col)
        if avg is not None:
            decisions.append({
                "title": "Kehadiran",
                "detail": f"Rata-rata {attendance_col} adalah {avg:.2f}. Periksa satuan dan rentang kolom ini sebelum menetapkan target kehadiran."
            })

    if sleep_col:
        avg = mean_of(sleep_col)
        if avg is not None:
            decisions.append({
                "title": "Pola tidur",
                "detail": f"Rata-rata {sleep_col} adalah {avg:.2f} jam. Bandingkan dengan kebutuhan tidur yang sesuai usia; jangan menyimpulkan dampak pada nilai tanpa analisis lebih lanjut."
            })

    if screen_col:
        avg = mean_of(screen_col)
        if avg is not None:
            decisions.append({
                "title": "Waktu layar",
                "detail": f"Rata-rata {screen_col} adalah {avg:.2f} jam. Pertimbangkan keseimbangan waktu layar, belajar, istirahat, dan aktivitas fisik."
            })

    if satisfaction_col:
        counts = df[satisfaction_col].dropna().astype(str).value_counts()
        if not counts.empty:
            decisions.append({
                "title": "Kepuasan",
                "detail": f"Kategori kepuasan terbanyak adalah “{counts.index[0]}” ({int(counts.iloc[0])} data). Telusuri alasan di balik penilaian tersebut sebelum menentukan perbaikan."
            })

    if not decisions:
        decisions.append({
            "title": "Keputusan umum",
            "detail": "Periksa tabel statistik dan distribusi data. Keputusan substantif belum bisa dibuat sebelum kolom dan makna nilainya dipahami."
        })

    return {
        "loaded": True, "filename": filename, "rows": int(len(df)),
        "columns": int(len(df.columns)), "missing": int(df.isna().sum().sum()),
        "numeric_count": int(len(numeric.columns)), "category_count": int(len(categorical.columns)),
        "columns_list": list(map(str, df.columns)), "summary": summary,
        "charts": charts, "category_charts": category_charts, "decisions": decisions
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/dashboard")
def api_dashboard():
    return jsonify(build_dashboard())

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
