import pandas as pd
from datetime import datetime

# --- 1. ПРАВИЛА ТА КОНСТАНТИ ---
BASE_POINTS = {'win': 10, 'draw': 4, 'loss': -3}

TOURNAMENTS = {
    'EURO_FIN':  {'win': 1.40, 'loss': 0.60},
    'NL_A':      {'win': 1.20, 'loss': 0.80},
    'QUAL_EURO': {'win': 1.00, 'loss': 1.00},
    'QUAL_WC':   {'win': 1.00, 'loss': 1.00},
    'NL_B':      {'win': 1.00, 'loss': 1.00},
    'NL_C':      {'win': 0.85, 'loss': 1.15},
    'NL_D':      {'win': 0.70, 'loss': 1.30}
}

def get_c_base(rank):
    if rank <= 8: return 1.0
    elif rank <= 11: return 0.95
    elif rank <= 18: return 0.90
    elif rank <= 21: return 0.85
    elif rank <= 28: return 0.80
    elif rank <= 31: return 0.75
    elif rank <= 38: return 0.70
    elif rank <= 41: return 0.65
    elif rank <= 48: return 0.60
    elif rank <= 51: return 0.55
    else: return 0.50

def get_r_coef(match_date, current_date):
    days_diff = (current_date - match_date).days
    months_diff = days_diff / 30.44
    if months_diff <= 12: return 1.0
    elif months_diff <= 24: return 0.9
    elif months_diff <= 36: return 0.8
    elif months_diff <= 48: return 0.7
    else: return 0.0

def calculate_match_points(result, tournament_id, opp_rank, location, is_playoff, is_god, goal_diff, r_coef):
    base = BASE_POINTS[result]
    t_mults = TOURNAMENTS.get(tournament_id, {'win': 1.0, 'loss': 1.0})
    t = t_mults['win'] if result in ['win', 'draw'] else t_mults['loss']
    c = get_c_base(opp_rank)
    mod = 0.0
    if location == 'Away': mod += 0.1
    elif location == 'Home': mod -= 0.1
    if abs(goal_diff) >= 3:
        if result == 'win': mod += 0.05
        elif result == 'loss': mod -= 0.05
    if is_playoff == 1: mod += 0.05
    if is_god == 1 and opp_rank <= 20: mod += 0.1
    return base * t * c * (1 + mod) * r_coef

def get_current_ranks(teams_dict):
    sorted_teams = sorted(teams_dict.items(), key=lambda x: x[1], reverse=True)
    return {team: i + 1 for i, (team, score) in enumerate(sorted_teams)}

# --- 2. ПРОЦЕСОР ---
def process_matches(df):
    if df.empty: return pd.DataFrame(), {}, {}
    
    teams = {}
    team_history = {}
    points_over_time = {}
    
    all_teams = pd.concat([df['Team_A'], df['Team_B']]).unique()
    for team in all_teams:
        teams[team] = 100.0
        team_history[team] = []
        points_over_time[team] = [{'Date': df['Date'].min(), 'Points': 100.0}]

    current_date = df['Date'].max()
    last_date = current_date
    previous_teams = {}
    previous_ranks = {}

    for index, row in df.iterrows():
        r_coef = get_r_coef(row['Date'], current_date)
        if r_coef == 0.0: continue

        if row['Date'] == last_date and not previous_teams:
            previous_teams = teams.copy()
            previous_ranks = get_current_ranks(previous_teams)

        team_a, team_b = row['Team_A'], row['Team_B']
        current_ranks_for_match = get_current_ranks(teams)
        rank_a, rank_b = current_ranks_for_match[team_a], current_ranks_for_match[team_b]
        
        if row['Score_A'] > row['Score_B']: res_a, res_b = 'win', 'loss'
        elif row['Score_A'] < row['Score_B']: res_a, res_b = 'loss', 'win'
        else: res_a, res_b = 'draw', 'draw'
            
        goal_diff = row['Score_A'] - row['Score_B']
        loc_a = row['Location_A']
        loc_b = 'Away' if loc_a == 'Home' else ('Home' if loc_a == 'Away' else 'Neutral')
        
        pts_a = calculate_match_points(res_a, row['Tournament'], rank_b, loc_a, row['Is_Playoff'], row['Is_GoD'], goal_diff, r_coef)
        pts_b = calculate_match_points(res_b, row['Tournament'], rank_a, loc_b, row['Is_Playoff'], row['Is_GoD'], -goal_diff, r_coef)
        
        teams[team_a] += pts_a
        teams[team_b] += pts_b

        points_over_time[team_a].append({'Date': row['Date'], 'Points': round(teams[team_a], 2)})
        points_over_time[team_b].append({'Date': row['Date'], 'Points': round(teams[team_b], 2)})

        date_str = row['Date'].strftime('%Y-%m-%d')
        team_history[team_a].append(f"{date_str} | {row['Tournament']} | vs {team_b} ({row['Score_A']}:{row['Score_B']}) | {pts_a:+.2f}")
        team_history[team_b].append(f"{date_str} | {row['Tournament']} | vs {team_a} ({row['Score_B']}:{row['Score_A']}) | {pts_b:+.2f}")

    final_ranks = get_current_ranks(teams)
    
    # СИСТЕМА "ЧАСОВОГО ЗАМКА":
    # Якщо найновіший матч зіграно до 1 травня 2026, примусово не показуємо зміни.
    # Коли база підтягне матчі за вересень 2026, цей блок вимкнеться.
    is_initial_run = current_date <= pd.to_datetime('2026-05-01')

    if not previous_teams or is_initial_run:
        previous_teams = teams.copy()
        previous_ranks = final_ranks.copy()

    result_list = []
    for team, score in teams.items():
        curr_rank = final_ranks[team]
        prev_rank = previous_ranks.get(team, curr_rank)
        rank_diff = prev_rank - curr_rank
        
        if rank_diff > 0: trend = f"{curr_rank}  🔼 {rank_diff}"
        elif rank_diff < 0: trend = f"{curr_rank}  🔽 {abs(rank_diff)}"
        else: trend = f"{curr_rank}  ➖"

        curr_pts = round(score, 2)
        pts_diff = round(curr_pts - round(previous_teams.get(team, 100.0), 2), 2)
        
        if pts_diff > 0: pts_trend = f"+{pts_diff:.2f}"
        elif pts_diff < 0: pts_trend = f"{pts_diff:.2f}"
        else: pts_trend = "0.00"

        result_list.append({'SortRank': curr_rank, 'Місце': trend, 'Збірна': team, 'Бали': curr_pts, 'Зміна очок': pts_trend})
        
    final_df = pd.DataFrame(result_list).sort_values(by='SortRank').drop(columns=['SortRank']).reset_index(drop=True)
    for t in team_history: team_history[t] = list(reversed(team_history[t]))[:5]

    return final_df, team_history, points_over_time