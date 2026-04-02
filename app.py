import streamlit as st
import pandas as pd
import engine

st.set_page_config(page_title="UEFA Power Rating", page_icon="🏆", layout="wide")

st.title("🏆 UEFA Power Rating (UPR)")
st.markdown("Справедливий рейтинг збірних УЄФА")
st.divider()

# Кешуємо дані на 24 години. Це гарантує миттєве завантаження для користувачів.
@st.cache_data(ttl=86400)
def fetch_and_parse_data():
    url = "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
    df = pd.read_csv(url)
    df['date'] = pd.to_datetime(df['date'])

    # Скрипт автоматично бере матчі від 1 серпня 2022 до "сьогоднішнього дня"
    df = df[df['date'] >= '2022-08-01']

    uefa_teams = [
        "Albania", "Andorra", "Armenia", "Austria", "Azerbaijan", "Belarus", "Belgium", "Bosnia and Herzegovina",
        "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Denmark", "England", "Estonia", "Faroe Islands",
        "Finland", "France", "Georgia", "Germany", "Gibraltar", "Greece", "Hungary", "Iceland", "Israel",
        "Italy", "Kazakhstan", "Kosovo", "Latvia", "Liechtenstein", "Lithuania", "Luxembourg", "Malta",
        "Moldova", "Montenegro", "Netherlands", "North Macedonia", "Northern Ireland", "Norway", "Poland",
        "Portugal", "Republic of Ireland", "Romania", "Russia", "San Marino", "Scotland", "Serbia",
        "Slovakia", "Slovenia", "Spain", "Sweden", "Switzerland", "Turkey", "Ukraine", "Wales"
    ]
    
    df = df[df['home_team'].isin(uefa_teams) & df['away_team'].isin(uefa_teams)]

    tournament_map = {
        "UEFA Euro": "EURO_FIN",
        "UEFA Euro qualification": "QUAL_EURO",
        "FIFA World Cup qualification": "QUAL_WC",
        "UEFA Nations League": "NL_B"
    }
    df = df[df['tournament'].isin(tournament_map.keys())].copy()
    df['Tournament_Mapped'] = df['tournament'].map(tournament_map)

    df_final = pd.DataFrame()
    df_final['Date'] = df['date']
    df_final['Team_A'] = df['home_team']
    df_final['Team_B'] = df['away_team']
    df_final['Score_A'] = df['home_score'].astype(int)
    df_final['Score_B'] = df['away_score'].astype(int)
    df_final['Tournament'] = df['Tournament_Mapped']
    df_final['Location_A'] = df['neutral'].apply(lambda x: 'Neutral' if x else 'Home')
    df_final['Is_Playoff'] = 0
    df_final['Is_GoD'] = 0
    
    df_final = df_final.sort_values(by='Date').reset_index(drop=True)
    return df_final

with st.spinner('Синхронізація з глобальною базою матчів...'):
    try:
        matches_db = fetch_and_parse_data()
        final_ranking, team_history, points_over_time = engine.process_matches(matches_db)
        
        col_table, col_viz = st.columns([1, 1.2])

        with col_table:
            # Динамічно формуємо заголовок на основі дат знайдених матчів
            first_date = matches_db['Date'].min().strftime('%d.%m.%Y')
            last_date = matches_db['Date'].max().strftime('%d.%m.%Y')
            st.subheader(f"Таблиця рейтингу (за {first_date} - {last_date})")
            
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
                history_df = pd.DataFrame(points_over_time[selected_team])
                st.line_chart(history_df.set_index('Date')['Points'])
                
                st.markdown(f"**Останні 5 результатів {selected_team}:**")
                for m in team_history[selected_team]:
                    st.code(m, language="text")

        st.download_button(
            "💾 Скачати підсумковий рейтинг", 
            data=final_ranking.to_csv(index=False).encode('utf-8'), 
            file_name='upr_full_auto.csv'
        )

    except Exception as e:
        st.error(f"❌ Сталася помилка: {e}")