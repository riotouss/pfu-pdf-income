import streamlit as st
import pdfplumber
import re
import io
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title="Розрахунок доходу з PDF")
st.title("📄 Розрахунок доходу з довідки ПФУ")
uploaded_file = st.file_uploader("Завантаж PDF-довідку", type="pdf")

current_year = datetime.now().year

if uploaded_file is not None:
    with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
        pages_text = [page.extract_text() or "" for page in pdf.pages]

    full_text = "\n".join(pages_text)

    full_text = re.sub(r"(?<=[а-яА-Яїєґ\d])(?=[А-ЯІЇЄҐ])", " ", full_text)

    blocks = re.split(r"Звітний\s*рік[: ]?\s*(\d{4})", full_text)

    yearly_data = {}

    for i in range(1, len(blocks), 2):
        year = blocks[i]
        block_text = blocks[i + 1]
        cleaned_block = block_text.replace(" ", "").replace("\n", "")

        match_year = re.search(r"Усьогозарік[:]?(\d+[\s\.,\d]*)", cleaned_block)

        if match_year:
            try:
                total_year = float(match_year.group(1).replace(" ", "").replace(",", "."))
            except ValueError:
                total_year = 0.0
        else:
            total_year = 0.0
            st.warning(f"⚠️ Не знайдено суму за рік {year}")

        yearly_data[year] = {"total_year": total_year}

    if yearly_data:
        all_years = list(range(min(map(int, yearly_data.keys())), current_year + 1))
        for y in all_years:
            if str(y) not in yearly_data:
                yearly_data[str(y)] = {"total_year": 0.0}

        rows_main = [("Рік", "Сума за рік", "Після -7%")]
        rows_7percent = [("Рік", "7% від суми")]
        rows_explain = [("Рік", "Як проводився розрахунок")]

        total_after_all_years = 0.0
        total_all_years = 0.0

        for year in sorted(yearly_data.keys(), key=int):
            total_year = yearly_data[year]["total_year"]
            total_all_years += total_year

            percent_7 = round(total_year * 0.07, 2)
            after_7 = round(total_year * 0.93, 2)

            total_after_all_years += after_7

            rows_main.append((year, round(total_year, 2), after_7))
            rows_7percent.append((year, percent_7))
            rows_explain.append((year, f"{round(total_year, 2)} грн - 7% = {after_7} грн"))

        rows_main.append(("Усього", round(total_all_years, 2), round(total_after_all_years, 2)))

        st.success("✅ Дані оброблено:")

        st.subheader("📋 Основна таблиця")
        st.table(rows_main)

        st.markdown(
            f"<div style='font-size: 1.8em; font-weight: bold;'>Загальна сума за всі роки: {round(total_all_years, 2)} грн</div>",
            unsafe_allow_html=True,
        )

        st.write(f"Сума після вирахування 7% за всі роки: **{round(total_after_all_years, 2)} грн**")

        doc_type = "ОК-?"

        for line in full_text.split("\n"):
            line_nospace = line.replace(" ", "").upper()
            form_match = re.search(r"ОК[-–— ]?\s*(\d+)", line_nospace)
            if form_match:
                doc_type = f"ОК-{form_match.group(1)}"

        years_present = sorted(map(int, yearly_data.keys()))
        max_valid_year = max(y for y in years_present if yearly_data[str(y)]["total_year"] > 0)
        min_valid_year = min(y for y in years_present if yearly_data[str(y)]["total_year"] > 0)

        year_range = f"{min_valid_year}" if min_valid_year == max_valid_year else f"{min_valid_year}-{max_valid_year}"

        total_copy_sum = round(sum(
            yearly_data[str(year)]["total_year"] for year in range(min_valid_year, max_valid_year + 1)
        ), 2)

        total_after_copy = round(total_after_all_years, 2)

        copy_text = (
            f"Надано {doc_type} за період {year_range}; "
            f"загальна сума {total_copy_sum} грн; "
            f"з урахуванням 7% {total_after_copy} грн"
        )

        st.markdown("📎 **Коментар для фіксації документу:**")
        components.html(f"""
            <div style="margin-bottom: 16px;">
                <div style="
                    background-color: #1e1e1e;
                    border: 1px solid #333;
                    border-radius: 8px;
                    padding: 12px 16px;
                    font-size: 16px;
                    color: white;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.25);
                " id="copyTextField">{copy_text}</div>

                <button onclick="navigator.clipboard.writeText(document.getElementById('copyTextField').innerText)"
                    style="
                        background-color: #4CAF50;
                        color: white;
                        padding: 10px 18px;
                        border: none;
                        border-radius: 6px;
                        cursor: pointer;
                        font-size: 16px;
                    ">
                    📋 Скопіювати
                </button>
            </div>
        """, height=150)

        show_extra = st.checkbox("📊 Показати пояснення розрахунку 7%")

        if show_extra:
            st.subheader("🔢 Пояснення розрахунку")
            st.table(rows_explain)

            st.subheader("📉 7% від кожного року")
            st.table(rows_7percent)
