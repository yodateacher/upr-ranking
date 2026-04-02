import streamlit as st
import pandas as pd
import engine

st.set_page_config(page_title="UEFA Power Rating", page_icon="🏆", layout="wide")

st.title("🏆 UEFA Power Rating (UPR) — GLOBAL")
st.markdown("Повний рейтинг усіх збірних УЄФА за період 2022-2026.")
st.divider()

uploaded_file = st.file_uploader("📥 Завантажте повну базу УЄФА (CSV)", type="csv")

if uploaded_file:
    matches_db = engine.load_data(uploaded_file)
    final_ranking, team_history, points_over_time = engine.process_matches(matches_db)
    
    col_table, col_viz = st.columns([1, 1.2])

    with col_table:
        st.subheader("Таблиця рейтингу")
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
            # Малюємо графік балів
            history_df = pd.DataFrame(points_over_time[selected_team])
            st.line_chart(history_df.set_index('Date')['Points'])
            
            st.markdown(f"**Останні 5 результатів {selected_team}:**")
            for m in team_history[selected_team]:
                st.code(m, language="text")

    # Кнопка експорту внизу
    csv = final_ranking.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Скачати підсумковий рейтинг", data=csv, file_name='upr_full_2026.csv')