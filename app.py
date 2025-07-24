import streamlit as st
import pdfplumber
import re

st.set_page_config(page_title="📄 Розрахунок доходу з PDF")

st.title("📄 Розрахунок доходу з довідки ПФУ")
uploaded_file = st.file_uploader("Завантаж PDF-довідку", type="pdf")

if uploaded_file is not None:
    with open("uploaded_file.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    tmp_path = "uploaded_file.pdf"

    with pdfplumber.open(tmp_path) as pdf:
        text = "".join([page.extract_text() for page in pdf.pages])

    text_fixed = re.sub(r"(?<=[а-яіїєґ0-9])(?=[А-ЯІЇЄҐ])", " ", text)

    years = re.findall(r"Звітний\s?рік[: ]?(\d{4})", text_fixed)
    amounts = re.findall(r"Усього\s?зарік[: ]?([\d\.]+)грн", text_fixed)
    matches = list(zip(years, amounts))

    if matches:
        rows = [("Рік", "Сума", "7%", "Після вирахування")]
        for year, amount in matches:
            total = float(amount)
            percent_7 = round(total * 0.07, 2)
            after = round(total - percent_7, 2)
            rows.append((year, total, percent_7, after))

        rows.append(("Усього", round(total_all, 2), "", round(total_after_all, 2)))

        st.success("✅ Дані оброблено:")
        st.table(rows)
    else:
        st.warning("❗ Не знайдено сум за рік у файлі.")

