import pandas as pd
import streamlit as st
import re
import requests 


Script_Url = st.secrets["SCRIPT_URL"]

TOKEN = st.secrets["TOKEN"]

# вывод таблицы
cols = ['номер', 'дата', 'телефон', 'фио', 'адрес', 'заказ', 'вывод', 'подрост', 'предоплата', 'примечание']

# Заголовок
st.set_page_config(page_title="База заказов", layout='wide')
st.title("Поиск по базе клиентов")

# запись в кеш
@st.cache_data(ttl=600)
def load_data():
    try:
        response = requests.get(f"{Script_Url}?token={TOKEN}")
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)

            missing_cols = [c for c in cols if c not in df.columns]
            if missing_cols:
                st.error(f"Критическая ошибка в Google таблице отсутствуют колонки: {', '.join(missing_cols)}")
                return pd.DataFrame()
            
            # колонки, которые нужно "протянуть" вниз
            fill_cols = ['фио','телефон','дата']
            for col in fill_cols:
                if col in df.columns:
                    # Замена пустых строк на None и протяжка значения сверху вниз
                    df[col] = df[col].replace('', None).ffill()

            for col in df.columns:
                df[col] = df[col].astype(str)
            return df
        else:
            st.error(f"Ошибка доступа к облаку (Код{response.status_code})")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Не удалось подключиться к Google: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

col1, col2 = st.columns(2)
# поле для ввода фио и телефон
with col1:
    search_name = st.text_input('Имя или Номер телефона:').strip()
# поле для ввода заказа
with col2:
    search_order = st.text_input('Cтрого заказ: ').strip()

# дублирование результата
result = df.copy()

# поиск по фио и телефон
if search_name:
    mask_name = (
        result['фио'].str.contains(search_name, case=False, na=False) |
        result['телефон'].str.contains(search_name, case=False, na=False)
    )
    result = result[mask_name]

# поис по Заказу
if search_order:

    keywords = [k.strip() for k in search_order.split(',') if k.strip()]

    filter_result = result.copy()

    for word in keywords:

        pattern = re.sub(r'(\d+)([а-яА-Яa-zA-Z]+)', r'\1\\s*\2', word)
        pattern = re.sub(r'([а-яА-Яa-zA-Z]+)(\d+)', r'\1\\s*\2', pattern)

        mask_order = filter_result['заказ'].str.contains(pattern, case=False, na=False, regex=True)
        filter_result = filter_result[mask_order]

    result = filter_result

# поиск
if search_name or search_order:
    if not result.empty:
        st.success(f"Найдено совпадений: {len(result)}")
        # фильтр по дате (можно выключить)
        result = result.sort_values(by='дата', ascending=False)
        # вывод таблицы (cols - что входит в таблицу)
        display_df = result[cols].copy()

        mask = display_df['фио'].duplicated()
        display_df.loc[mask,['фио', 'телефон', 'дата']] = ""

        st.dataframe(display_df, use_container_width=True)
    else:
        st.warning(f"Ничего не найдено по запросу: {search_name} {search_order}")
else:
    st.info("Введите данные")