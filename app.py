import streamlit as st
import pdfplumber
import re
from datetime import datetime

st.set_page_config(page_title="📄 Розрахунок доходу з PDF")
st.title("📄 Розрахунок доходу з довідки ПФУ")
uploaded_file = st.file_uploader("Завантаж PDF-довідку", type="pdf")

current_year = datetime.now().year

if uploaded_file is not None:
    with open("uploaded_file.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    tmp_path = "uploaded_file.pdf"

    with pdfplumber.open(tmp_path) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]

    full_text = "\n".join(pages_text)

    full_text = re.sub(r"(?<=[а-яА-Яіїєґ0-9])(?=[А-ЯІЇЄҐ])", " ", full_text)

    blocks = re.split(r"Звітний\s*рік[: ]?\s*(\d{4})", full_text)

    yearly_data = {}

    for i in range(1, len(blocks), 2):
        year = blocks[i]
        block_text = blocks[i + 1]
        cleaned_block = block_text.replace(" ", "").replace("\n", "")

        match = re.search(r"Усьогозарік[:]?([\d\.]+)", cleaned_block)
        
        if not match and i + 3 <= len(blocks):
            next_block = blocks[i + 3].replace(" ", "").replace("\n", "")
            match = re.search(r"Усьогозарік[:]?([\d\.]+)", next_block)

        if match:
            try:
                amount = float(match.group(1).replace(",", "."))
                yearly_data[year] = amount
            except ValueError:
                pass
        else:
            st.warning(f"⚠️ Не знайдено суму за {year}")

    if yearly_data:
        rows = [("Рік", "Сума", "7%", "Після вирахування")]
        total_all = 0
        total_after_all = 0
        cumulative = 0

        for year in sorted(yearly_data.keys()):
            total = yearly_data[year]
            year_int = int(year)

            if year_int < current_year:
                cumulative = cumulative + total
                percent_7 = round(total * 0.07, 2)
                cumulative = cumulative * 0.93
                after = round(cumulative, 2)
            else:
                cumulative += total
                percent_7 = 0.00
                after = round(cumulative, 2)

            rows.append((year, total, percent_7, after))
            total_all += total
            total_after_all = after
            

        rows.append(("Усього", round(total_all, 2), "", round(total_after_all, 2)))

        st.success("✅ Дані оброблено:")
        st.table(rows)
    else:
        st.error("❌ Не знайдено жодної суми.")
