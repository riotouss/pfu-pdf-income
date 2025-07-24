import streamlit as st
import pdfplumber
import re
from collections import defaultdict

st.set_page_config(page_title="📄 Розрахунок доходу з PDF")
st.title("📄 Розрахунок доходу з довідки ПФУ")
uploaded_file = st.file_uploader("Завантаж PDF-довідку", type="pdf")

if uploaded_file is not None:
    with open("uploaded_file.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    tmp_path = "uploaded_file.pdf"

    with pdfplumber.open(tmp_path) as pdf:
        text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    text_fixed = re.sub(r"(?<=[а-яА-ЯіїєґІЇЄҐ0-9])(?=[А-ЯІЇЄҐ])", " ", text)

    year_amount_matches = re.findall(r"Звітний рік: (\d{4}).*?Усього за рік:\s*([\d\.]+) грн", text_fixed, re.DOTALL)

    yearly_data = {}
    for year, amount in year_amount_matches:
        yearly_data[year] = float(amount.replace(",", "."))

    if yearly_data:
        rows = [("Рік", "Сума", "7%", "Після вирахування")]
        total_all = 0
        total_after_all = 0

        for year in sorted(yearly_data.keys()):
            total = yearly_data[year]
            percent_7 = round(total * 0.07, 2)
            after = round(total - percent_7, 2)
            rows.append((year, total, percent_7, after))
            total_all += total
            total_after_all += after

        rows.append(("Усього", round(total_all, 2), "", round(total_after_all, 2)))

        st.success("✅ Дані оброблено:")
        st.table(rows)
    else:
        st.warning("❗ Не знайдено сум за рік у файлі.")
