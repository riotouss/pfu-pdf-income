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

        match_year = re.search(r"Усього за рік[:]?([\d\s\.,]+)", cleaned_block)
    
        match_cumulative = re.search(r"Усього за рік з урахуванням минулих років[:]?([\d\s\.,]+)", cleaned_block)

        if match_year:
            try:
                total_year = float(match_year.group(1).replace(" ", "").replace(",", "."))
            except ValueError:
                total_year = 0.0
        else:
            total_year = 0.0
            st.warning(f"⚠️ Не знайдено суму за рік {year}")

        if match_cumulative:
            try:
                total_cumulative = float(match_cumulative.group(1).replace(" ", "").replace(",", "."))
            except ValueError:
                total_cumulative = total_year
        else:
            total_cumulative = total_year

        yearly_data[year] = {
            "total_year": total_year,
            "total_cumulative": total_cumulative
        }

    if yearly_data:
        all_years = list(range(min(map(int, yearly_data.keys())), current_year + 1))
        for y in all_years:
            if str(y) not in yearly_data:
                yearly_data[str(y)] = {"total_year": 0.0, "total_cumulative": 0.0}

        rows = [("Рік", "Сума за рік", "Кумулятивна сума", "7% від кумулятивної", "Після вирахування")]
        total_all = 0
        total_after_all = 0

        for year in sorted(yearly_data.keys(), key=int):
            data = yearly_data[year]
            total_year = data["total_year"]
            total_cumulative = data["total_cumulative"]
            year_int = int(year)

            if year_int < current_year:
                percent_7 = round(total_cumulative * 0.07, 2)
                after = round(total_cumulative * 0.93, 2)
            else:
                percent_7 = 0.0
                after = total_cumulative

            rows.append((year, total_year, total_cumulative, percent_7, after))
            total_all += total_year
            total_after_all = after  

        rows.append(("Усього", round(total_all, 2), "", "", round(total_after_all, 2)))

        st.success("✅ Дані оброблено:")
        st.table(rows)
        st.write(f"Загальна сума за всі роки: {round(total_all, 2)} грн")
        st.write(f"Загальна сума після вирахування 7% (за всі роки, крім поточного): {round(total_after_all, 2)} грн")
    else:
        st.error("❌ Не знайдено жодної суми.")
