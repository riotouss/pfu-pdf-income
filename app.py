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
        match_cumulative = re.search(r"Усьогозарікзурахуваннямминулихроків[:]?(\d+[\s\.,\d]*)", cleaned_block)

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

        rows_main = [("Рік", "Сума за рік", "Після вирахування 7 %")]
        rows_7percent = [("Рік", "7% від суми")]
        rows_explain = [("Рік", "Як проводився розрахунок")]

        total_all = 0.0
        accumulated = 0.0

        for year in sorted(yearly_data.keys(), key=int):
            year_int = int(year)
            total_year = yearly_data[year]["total_year"]
            total_all += total_year

            if year_int == current_year:
                percent_7 = 0.0
                after = f"{round(accumulated, 2)} + (дохід за {year} р.: {round(total_year, 2)} грн, без вирах. 7%)"
                explain = f"Сума за {year} р.: {round(total_year, 2)} грн (без вирахування 7%, бо рік ще не завершено)"
            elif total_year == 0:
                combined = accumulated
                percent_7 = round(combined * 0.07, 2)
                accumulated = round(combined * 0.93, 2)
                after = accumulated
                explain = (
                    f"Сума за попередні роки + сума за {year} р. = {combined} + 0 = {combined}\n"
                    f"Вираховуємо 7%: {combined} * 0.93 = {accumulated}"
                )
            else:
                combined = accumulated + total_year
                percent_7 = round(combined * 0.07, 2)
                accumulated = round(combined * 0.93, 2)
                after = accumulated
                explain = (
                    f"Сума за попередні роки + сума за {year} р. = {round(combined - total_year, 2)} + {round(total_year, 2)} = {round(combined, 2)}\n"
                    f"Вираховуємо 7%: {round(combined, 2)} * 0.93 = {accumulated}"
                )

            rows_main.append((year, round(total_year, 2), after))
            rows_7percent.append((year, percent_7))
            rows_explain.append((year, explain))

        last_year_val = yearly_data[str(current_year)]["total_year"]
        rows_main.append((
            "Усього",
            round(total_all, 2),
            f"{round(accumulated, 2)} + (дохід за {current_year} р.: {round(last_year_val, 2)} грн, без вирах. 7%)"
        ))

        st.success("✅ Дані оброблено:")

        show_extra = st.checkbox("📊 Показати пояснення розрахунку 7%", value=False)

        st.subheader("📋 Основна таблиця")
        st.markdown("""
            <style>
            .element-container:has(table) table td {
                white-space: nowrap;
            }
            </style>
        """, unsafe_allow_html=True)
        st.table(rows_main)

        st.markdown(f"<div style='font-size: 1.8em; font-weight: bold;'>Загальна сума за всі роки: {round(total_all, 2)} грн</div>", unsafe_allow_html=True)

        st.write(
            f"Сума після вирахування 7% (за всі роки, крім поточного): **{round(accumulated, 2)} грн** + Дохід за поточний ({current_year}) рік — **{round(last_year_val, 2)} грн**"
        )

        doc_type = "ОК-?"

        for line in full_text.split("\n"):
            line_nospace = line.replace(" ", "").upper()
            form_match = re.search(r"ОК[-–— ]?\s*(\d+)", line_nospace)
            if form_match:
                doc_type = f"ОК-{form_match.group(1)}"

        years_present = sorted(map(int, yearly_data.keys()))
        max_valid_year = max(y for y in years_present if yearly_data[str(y)]["total_year"] > 0)
        min_valid_year = min(y for y in years_present if yearly_data[str(y)]["total_year"] > 0)

        if min_valid_year == max_valid_year:
            year_range = f"{min_valid_year}"
        else:
            year_range = f"{min_valid_year}-{max_valid_year}"

        total_copy_sum = round(sum(
            data["total_year"] for year, data in yearly_data.items() if min_valid_year <= int(year) <= max_valid_year
        ), 2)

        last_year_val = yearly_data[str(current_year)]["total_year"]

        total_after_7 = round(accumulated + last_year_val, 2)

        copy_text = (
            f"Надано {doc_type} за період {year_range}; "
            f"загальна сума {total_copy_sum} грн; "
            f"з урахуванням 7% {total_after_7} грн"
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
                    font-family: 'Segoe UI', sans-serif;
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
                        transition: background-color 0.2s ease;
                        font-family: 'Segoe UI', sans-serif;
                    "
                    onmouseover="this.style.backgroundColor='#45a049'"
                    onmouseout="this.style.backgroundColor='#4CAF50'">
                    📋 Скопіювати
                </button>
            </div>
        """, height=150)

        if show_extra:
            st.subheader("🔢 Пояснення розрахунку")
            html_table = """
            <style>
            .responsive-table {
                border-collapse: collapse;
                width: 100%;
                table-layout: auto;
            }
            .responsive-table th, .responsive-table td {
                border: 1px solid #ccc;
                padding: 8px;
                text-align: left;
                vertical-align: top;
                word-break: break-word;
                white-space: pre-wrap;
            }
            .responsive-table th {
                background-color: #f9f9f9;
            }
            </style>
            <table class="responsive-table">
                <thead><tr><th>Рік</th><th>Як проводився розрахунок</th></tr></thead>
                <tbody>
            """
            for year, explanation in rows_explain[1:]:
                explanation_html = explanation.replace("\n", "<br>")
                html_table += f"<tr><td>{year}</td><td>{explanation_html}</td></tr>"
            html_table += "</tbody></table>"

            st.markdown(html_table, unsafe_allow_html=True)

            st.subheader("📉 7% від суми")
            st.table(rows_7percent)
