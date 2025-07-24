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
        pages_text = []
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            pages_text.append(page_text)
            st.text(f"----- Сторінка {i+1} -----\n" + page_text[:1500]) 
    full_text = "\n".join(pages_text)

    full_text = re.sub(r"(?<=[а-яА-Яіїєґ0-9])(?=[А-ЯІЇЄҐ])", " ", full_text)

    st.subheader("🔍 Debug: Увесь витягнутий текст")
    st.text(full_text[:3000]) 

    blocks = re.split(r"Звітний рік: (\d{4})", full_text)

    st.subheader("🔍 Debug: Розбиті блоки по роках")
    for i in range(1, len(blocks), 2):
        year = blocks[i]
        content = blocks[i + 1][:800]  
        st.markdown(f"**{year}**\n```\n{content}\n```")

    yearly_data = {}

    for i in range(1, len(blocks), 2):
        year = blocks[i]
        block_text = blocks[i + 1]
        match = re.search(r"Усього за рік:\s*([\d\.]+)", block_text)
        if match:
            amount = float(match.group(1).replace(",", "."))
            yearly_data[year] = amount
        else:
            st.warning(f"⚠️ Не знайдено суму за {year}")

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
        st.error("❌ Не знайдено жодної суми.")
