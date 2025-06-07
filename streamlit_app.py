import streamlit as st
import pandas as pd
import random
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import tempfile

# --------------------- CSS Edukatif ---------------------
st.markdown("""
    <style>
        html, body, .main {
            background-color: #f5f7fa;
            font-family: 'Segoe UI', sans-serif;
        }

        .block-container {
            padding: 2rem 2rem;
            background-color: #ffffff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }

        h1, h2, h3 {
            color: #2c3e50;
        }

        .stButton>button {
            background-color: #2e86de;
            color: white;
            border-radius: 8px;
            font-size: 16px;
            padding: 8px 16px;
        }

        .stButton>button:hover {
            background-color: #1e70bf;
        }

        .stRadio > div {
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------- Load dari Excel ---------------------
# @st.cache_data
def load_questions_from_excel(file_path):
    q_df = pd.read_excel(file_path, sheet_name='Questions')
    a_df = pd.read_excel(file_path, sheet_name='Answers')
    
    merged = q_df.merge(a_df, left_on='id', right_on='question_id')
    
    questions = {}
    for _, row in merged.iterrows():
        qid = row['id']
        if qid not in questions:
            questions[qid] = {
                'id': qid,
                'text': row['question_text'],
                'options': []
            }
        questions[qid]['options'].append({
            'personality_type': row['personality_type'],
            'answer_text': row['answer_text']
        })
    
    # Ubah dict ke list
    questions_list = list(questions.values())
    
    # Acak pilihan jawaban setiap pertanyaan
    for q in questions_list:
        random.shuffle(q['options'])
    
    # Acak urutan pertanyaan
    random.shuffle(questions_list)
    
    return questions_list

# --------------------- Fungsi PDF ---------------------
def generate_pdf(name, counts, chart_buf):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    ls_judul = f"Hasil Kuesioner Jenis Kepribadian  {name}"
    pdf.cell(200, 10, txt=ls_judul, ln=1, align="C")
    pdf.ln(5)
    pdf.ln(5)
    for k, label in zip(['M','S','K','P'], ['Melankolis', 'Sanguinis', 'Kloris', 'Plegmatis']):
        pdf.cell(200, 10, txt=f"{label}: {counts[k]}", ln=1)
    

    # Simpan chart ke file sementara
    if chart_buf is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            tmpfile.write(chart_buf.getbuffer())
            tmpfile_path = tmpfile.name
        pdf.image(tmpfile_path, x=30, w=150)

    # ✅ Simpan hasil PDF ke BytesIO
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    output = BytesIO(pdf_bytes)
    return output

# --------------------- App Utama ---------------------
st.title("📝 Kuesioner Jenis Kepribadian")

st.markdown("""
Selamat datang di kuisioner **Jenis Kepribadian** – alat bantu yang dirancang untuk membantu Anda mengenali **dominasi kepribadian** Anda.

Melalui serangkaian pertanyaan sederhana, Anda akan mendapatkan gambaran apakah Anda cenderung memiliki kepribadian sebagai:

- 🎯 **Melankolis** – analitis, perfeksionis, dan cermat dalam berpikir  
- 😄 **Sanguinis** – ekspresif, optimis, dan mudah bergaul  
- 🔥 **Koleris** – tegas, berorientasi tujuan, dan pemimpin alami  
- 🌿 **Plegmatis** – tenang, sabar, dan penengah yang baik

Silakan masukkan nama lengkap Anda dan pilih jawaban yang paling sesuai dengan diri Anda dalam setiap pertanyaan.  
Hasil akhir akan membantu Anda lebih memahami kekuatan dan kecenderungan kepribadian Anda.
""")

name = st.text_input("📛 Masukkan Nama Lengkap Anda:")

questions = load_questions_from_excel("kepribadian_kuesioner.xlsx")

responses = {}
with st.form("quiz_form"):
    st.subheader("📚 Pertanyaan Kuesioner")

    for idx, q in enumerate(questions, 1):
        st.markdown(f"**{idx}. {q['text']}**")
        labels = [opt['answer_text'] for opt in q['options']]
        values = [opt['personality_type'] for opt in q['options']]
        selected = st.radio("", options=labels, key=f"q{idx}")
        responses[idx] = values[labels.index(selected)]

    submitted = st.form_submit_button("📤 Kirim Jawaban")

# --------------------- Hasil ---------------------
if submitted and name:
    counts = {'M': 0, 'S': 0, 'K': 0, 'P': 0}
    for ans in responses.values():
        counts[ans] += 1

    st.success("✅ Jawaban berhasil dikirim!")
    st.subheader(f"Kecenderungan Kepribadian untuk **{name}**")

    for k, label in zip(['M','S','K','P'], ['Melankolis', 'Sanguinis', 'Kloris', 'Plegmatis']):
        st.write(f"**{label}**: {counts[k]} poin")

    # Donut chart
    fig, ax = plt.subplots()
    labels = ['Melankolis', 'Sanguinis', 'Kloris', 'Plegmatis']
    values = [counts['M'], counts['S'], counts['K'], counts['P']]
    colors = ['#76c7c0', '#ffa07a', '#d8bfd8', '#fdd835']
    ax.pie(values, labels=labels, colors=colors, autopct='%1.1f%%',
           startangle=90, wedgeprops=dict(width=0.4))
    ax.axis('equal')
    st.pyplot(fig)

    # Simpan grafik
    chart_buf = BytesIO()
    fig.savefig(chart_buf, format='png')
    chart_buf.seek(0)

    # Unduh PDF
    pdf_data = generate_pdf(name, counts, chart_buf)
    file_name = f"hasil_kepribadian_{name}.pdf"
    st.download_button("📄 Unduh PDF Hasil", data=pdf_data, file_name=file_name, mime="application/pdf")

elif submitted:
    st.warning("⚠️ Silakan isi nama terlebih dahulu sebelum mengirim.")

