import streamlit as st
import pandas as pd
import engine
import os

st.set_page_config(page_title="UEFA Power Rating", page_icon="🏆", layout="wide")

st.title("🏆 UEFA Power Rating (UPR) — GLOBAL")
st.markdown("Справедливий рейтинг усіх 55 збірних УЄФА за період 2022-2026.")
st.divider()

# Вказуємо програмі, де лежить наша база даних
db_path = 'database_full.csv'

# Перевіряємо, чи існує файл
if os.path.exists(db_path):
    # Завантажуємо базу автоматично!
    matches_db = engine.load_data(db_path)
    final_ranking, team_history, points_over_time = engine.process_matches(matches_db)
    
    col_table, col_viz = st.columns([1, 1.2])

    with col_table:
        st.subheader(f"Таблиця рейтингу (Матчів: {len(matches_db)})")
        st.dataframe(
            final_ranking, hide_index=True, height=600,
            column_config={
                "Місце": st.column_config.TextColumn(width=80),
                "Збірна": st.column_config.TextColumn(width=200),
                "Бали": st.column_config.NumberColumn(format="%.2f", width=100),
                "Зміна очок": st.column_config.TextColumn(width=100)
            }
        )

    with col_viz:
        st.subheader("Аналітика та прогрес")
        selected_team = st.selectbox("Оберіть збірну для аналізу:", final_ranking['Збірна'].unique())
        
        if selected_team:
            # Малюємо графік
            history_df = pd.DataFrame(points_over_time[selected_team])
            st.line_chart(history_df.set_index('Date')['Points'])
            
            st.markdown(f"**Останні 5 результатів {selected_team}:**")
            for m in team_history[selected_team]:
                st.code(m, language="text")

    st.download_button("💾 Скачати підсумковий рейтинг", data=final_ranking.to_csv(index=False).encode('utf-8'), file_name='upr_full_2026.csv')
else:
    st.error(f"❌ Файл {db_path} не знайдено! Переконайтеся, що він завантажений на GitHub.")