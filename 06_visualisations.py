"""
IPL Analytics — All 5 Visualisations
Run this file from your project folder (where matches.csv and deliveries.csv are).
Charts will be saved to a 'charts/' folder automatically.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

# ── Create charts folder ──
os.makedirs('charts', exist_ok=True)

# ── SETUP — Load & Clean ──
matches = pd.read_csv("matches.csv")
deliveries = pd.read_csv("deliveries.csv")

matches['city'] = matches['city'].fillna('Unknown')
matches['player_of_match'] = matches['player_of_match'].fillna('Unknown')
matches['winner'] = matches['winner'].fillna('No Result')
matches['season'] = matches['season'].replace({
    '2007/08': '2008', '2009/10': '2010', '2020/21': '2020'
}).astype(int)

name_map = {
    'Delhi Daredevils': 'Delhi Capitals',
    'Kings XI Punjab': 'Punjab Kings',
    'Royal Challengers Bangalore': 'Royal Challengers Bengaluru',
    'Deccan Chargers': 'Sunrisers Hyderabad',
    'Rising Pune Supergiant': 'Rising Pune Supergiants'
}
for col in ['team1', 'team2', 'winner', 'toss_winner']:
    matches[col] = matches[col].replace(name_map)

deliveries = deliveries[deliveries['inning'] <= 2]

# ── Shared style ──
DARK_BG   = '#0f0f1a'
GRID_COL  = '#2a2a3a'
TEXT_COL  = '#e8e6f2'
MUTED_COL = '#8884a8'
ACCENT    = '#7B6FFA'
GREEN     = '#4FFFA0'
YELLOW    = '#FFD166'
RED       = '#FF6B9D'
BLUE      = '#4FC3F7'

def set_style(ax, title, xlabel='', ylabel=''):
    ax.set_facecolor(DARK_BG)
    ax.figure.set_facecolor(DARK_BG)
    ax.set_title(title, color=TEXT_COL, fontsize=14, fontweight='bold', pad=16)
    ax.set_xlabel(xlabel, color=MUTED_COL, fontsize=11)
    ax.set_ylabel(ylabel, color=MUTED_COL, fontsize=11)
    ax.tick_params(colors=MUTED_COL)
    ax.spines[:].set_color(GRID_COL)
    ax.grid(axis='x', color=GRID_COL, linewidth=0.6, linestyle='--')
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)


# ══════════════════════════════════════════
# CHART 1 — Top 15 Batsmen by Runs/Innings
# ══════════════════════════════════════════
batsman_stats = deliveries.groupby('batter').agg(
    total_runs=('batsman_runs', 'sum'),
    balls_faced=('batsman_runs', 'count'),
    innings_played=('match_id', 'nunique')
).reset_index()
batsman_stats['strike_rate'] = (batsman_stats['total_runs'] / batsman_stats['balls_faced']) * 100
batsman_stats['avg_per_innings'] = batsman_stats['total_runs'] / batsman_stats['innings_played']
qualified = batsman_stats[batsman_stats['innings_played'] >= 30].sort_values('avg_per_innings', ascending=False).head(15)

# Colour bars by strike rate bucket
def sr_colour(sr):
    if sr >= 145: return GREEN
    if sr >= 135: return ACCENT
    return BLUE

colours = [sr_colour(sr) for sr in qualified['strike_rate']]

fig, ax = plt.subplots(figsize=(13, 7), facecolor=DARK_BG)
bars = ax.barh(qualified['batter'], qualified['avg_per_innings'], color=colours, edgecolor='none', height=0.65)

# Value labels
for bar, val in zip(bars, qualified['avg_per_innings']):
    ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
            f'{val:.1f}', va='center', color=TEXT_COL, fontsize=10, fontweight='bold')

ax.invert_yaxis()
ax.set_xlim(0, 45)
set_style(ax,
    title='Top 15 IPL Batsmen — Runs per Innings  (min. 30 innings, 2008–2024)',
    xlabel='Average Runs per Innings', ylabel='')
ax.tick_params(axis='y', labelcolor=TEXT_COL, labelsize=10)

# Legend
legend_items = [
    mpatches.Patch(color=GREEN,  label='SR ≥ 145 (Explosive)'),
    mpatches.Patch(color=ACCENT, label='SR 135–144 (Aggressive)'),
    mpatches.Patch(color=BLUE,   label='SR < 135 (Steady)')
]
ax.legend(handles=legend_items, loc='lower right', facecolor='#1a1a2e',
          labelcolor=TEXT_COL, edgecolor=GRID_COL, fontsize=9)

ax.text(0.99, -0.08, 'Colour = Strike Rate category',
        transform=ax.transAxes, color=MUTED_COL, fontsize=8, ha='right')
plt.tight_layout()
plt.savefig('charts/01_batsman_value.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.show()
print("✓ Chart 1 saved")


# ══════════════════════════════════════════
# CHART 2 — All-Time Team Win Rates
# ══════════════════════════════════════════
wins = matches[matches['winner'] != 'No Result']
win_counts = wins['winner'].value_counts().reset_index()
win_counts.columns = ['team', 'wins']
total_matches_df = pd.concat([matches['team1'], matches['team2']]).value_counts().reset_index()
total_matches_df.columns = ['team', 'total']
team_winrate = win_counts.merge(total_matches_df, on='team')
team_winrate['win_rate'] = team_winrate['wins'] / team_winrate['total']
# Keep only current/major franchises (10+ matches)
team_winrate = team_winrate[team_winrate['total'] >= 30].sort_values('win_rate', ascending=True)

# Colour active vs defunct
active = ['Gujarat Titans','Chennai Super Kings','Mumbai Indians','Lucknow Super Giants',
          'Kolkata Knight Riders','Rajasthan Royals','Royal Challengers Bengaluru',
          'Delhi Capitals','Punjab Kings','Sunrisers Hyderabad']
bar_colours = [ACCENT if t in active else MUTED_COL for t in team_winrate['team']]

fig, ax = plt.subplots(figsize=(13, 7), facecolor=DARK_BG)
bars = ax.barh(team_winrate['team'], team_winrate['win_rate']*100, color=bar_colours, height=0.65, edgecolor='none')

for bar, (_, row) in zip(bars, team_winrate.iterrows()):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
            f"{row['win_rate']*100:.1f}%  ({int(row['wins'])}/{int(row['total'])})",
            va='center', color=TEXT_COL, fontsize=9)

ax.set_xlim(0, 78)
ax.axvline(50, color=YELLOW, linewidth=1.2, linestyle='--', alpha=0.7, label='50% baseline')
set_style(ax, title='IPL All-Time Team Win Rates (2008–2024)', xlabel='Win Rate (%)', ylabel='')
ax.tick_params(axis='y', labelcolor=TEXT_COL, labelsize=9.5)
legend_items = [
    mpatches.Patch(color=ACCENT, label='Active franchise'),
    mpatches.Patch(color=MUTED_COL, label='Defunct franchise'),
    mpatches.Patch(color=YELLOW, label='50% benchmark')
]
ax.legend(handles=legend_items, loc='lower right', facecolor='#1a1a2e',
          labelcolor=TEXT_COL, edgecolor=GRID_COL, fontsize=9)
plt.tight_layout()
plt.savefig('charts/02_team_winrates.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.show()
print("✓ Chart 2 saved")


# ══════════════════════════════════════════
# CHART 3 — Strategy Evolution (Dual Line)
# ══════════════════════════════════════════
del_with_season = deliveries.merge(matches[['id', 'season']], left_on='match_id', right_on='id')
pp_data    = del_with_season[del_with_season['over'] <= 6].groupby('season')['total_runs'].mean().reset_index()
death_data = del_with_season[del_with_season['over'] >= 17].groupby('season')['total_runs'].mean().reset_index()
pp_data['runs_per_over']    = pp_data['total_runs'] * 6
death_data['runs_per_over'] = death_data['total_runs'] * 6

fig, ax = plt.subplots(figsize=(13, 6), facecolor=DARK_BG)
ax.plot(pp_data['season'], pp_data['runs_per_over'], color=ACCENT, linewidth=2.5,
        marker='o', markersize=6, label='Powerplay (Overs 1–6)')
ax.plot(death_data['season'], death_data['runs_per_over'], color=RED, linewidth=2.5,
        marker='s', markersize=6, label='Death Overs (Overs 17–20)')

# Annotate 2008 and 2024 endpoints
for data, colour in [(pp_data, ACCENT), (death_data, RED)]:
    for year in [2008, 2024]:
        row = data[data['season'] == year]
        val = row['runs_per_over'].values[0]
        ax.annotate(f'{val:.2f}', (year, val), textcoords='offset points',
                    xytext=(0, 10), color=colour, fontsize=9, fontweight='bold', ha='center')

ax.fill_between(pp_data['season'], pp_data['runs_per_over'], alpha=0.08, color=ACCENT)
ax.fill_between(death_data['season'], death_data['runs_per_over'], alpha=0.08, color=RED)
set_style(ax,
    title='How IPL Batting Strategy Has Evolved — Powerplay vs Death Overs (2008–2024)',
    xlabel='Season', ylabel='Avg Runs per Over')
ax.tick_params(axis='x', labelcolor=TEXT_COL, labelsize=10)
ax.tick_params(axis='y', labelcolor=TEXT_COL, labelsize=10)
ax.set_xticks(pp_data['season'])
ax.set_xticklabels(pp_data['season'], rotation=45)
ax.legend(facecolor='#1a1a2e', labelcolor=TEXT_COL, edgecolor=GRID_COL, fontsize=10)
plt.tight_layout()
plt.savefig('charts/03_strategy_evolution.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.show()
print("✓ Chart 3 saved")


# ══════════════════════════════════════════
# CHART 4 — Toss Advantage by Venue
# ══════════════════════════════════════════
toss = matches[matches['winner'] != 'No Result'].copy()
toss['toss_won_match'] = toss['toss_winner'] == toss['winner']
venue_toss = toss.groupby('venue')['toss_won_match'].agg(['mean', 'count']).reset_index()
venue_toss.columns = ['venue', 'toss_win_rate', 'matches']
venue_toss = venue_toss[venue_toss['matches'] >= 20].sort_values('toss_win_rate', ascending=True)
# Shorten long venue names
venue_toss['venue_short'] = venue_toss['venue'].str.replace('Stadium', 'Stad.').str.replace(', Mumbai', '').str.replace('Cricket Association', 'CA')

overall_rate = toss['toss_won_match'].mean()

fig, ax = plt.subplots(figsize=(13, 8), facecolor=DARK_BG)
bar_cols = [GREEN if r > 0.55 else ACCENT if r > 0.50 else MUTED_COL
            for r in venue_toss['toss_win_rate']]
bars = ax.barh(venue_toss['venue_short'], venue_toss['toss_win_rate']*100,
               color=bar_cols, height=0.65, edgecolor='none')

for bar, (_, row) in zip(bars, venue_toss.iterrows()):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
            f"{row['toss_win_rate']*100:.1f}%  (n={int(row['matches'])})",
            va='center', color=TEXT_COL, fontsize=9)

ax.axvline(overall_rate*100, color=YELLOW, linewidth=1.5, linestyle='--',
           label=f'Overall average: {overall_rate*100:.1f}%')
ax.set_xlim(0, 78)
set_style(ax, title='Toss Advantage by Venue — Does Winning the Toss Actually Help? (2008–2024)',
          xlabel='% Matches Won After Winning Toss', ylabel='')
ax.tick_params(axis='y', labelcolor=TEXT_COL, labelsize=9)
legend_items = [
    mpatches.Patch(color=GREEN, label='Strong toss advantage (>55%)'),
    mpatches.Patch(color=ACCENT, label='Slight advantage (50–55%)'),
    mpatches.Patch(color=MUTED_COL, label='Below average (<50%)'),
]
ax.legend(handles=legend_items + [mpatches.Patch(color=YELLOW, label=f'Overall avg ({overall_rate*100:.1f}%)')],
          loc='lower right', facecolor='#1a1a2e', labelcolor=TEXT_COL, edgecolor=GRID_COL, fontsize=9)
plt.tight_layout()
plt.savefig('charts/04_toss_advantage.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.show()
print("✓ Chart 4 saved")


# ══════════════════════════════════════════
# CHART 5 — Knockout Underperformers
# ══════════════════════════════════════════
knockout_types = ['Final', 'Semi Final', 'Qualifier 1', 'Qualifier 2', 'Eliminator']
knockout_ids = matches[matches['match_type'].isin(knockout_types)]['id']
regular_ids  = matches[~matches['match_type'].isin(knockout_types)]['id']

del_ko  = deliveries[deliveries['match_id'].isin(knockout_ids)]
del_reg = deliveries[deliveries['match_id'].isin(regular_ids)]

def batting_avg(df):
    return df.groupby('batter').agg(
        runs=('batsman_runs', 'sum'),
        innings=('match_id', 'nunique')
    ).assign(avg=lambda x: x['runs'] / x['innings'])

ko_avg  = batting_avg(del_ko).rename(columns={'avg': 'knockout_avg'})
reg_avg = batting_avg(del_reg).rename(columns={'avg': 'regular_avg'})
comparison = reg_avg[['regular_avg']].join(ko_avg[['knockout_avg']]).dropna()
# Filter: 20+ regular innings AND 3+ knockout innings (removes single-game noise)
reg_innings_map = del_reg.groupby('batter')['match_id'].nunique()
ko_innings_map  = del_ko.groupby('batter')['match_id'].nunique()
comparison = comparison[
    comparison.index.map(lambda x: reg_innings_map.get(x, 0) >= 20) &
    comparison.index.map(lambda x: ko_innings_map.get(x, 0) >= 3)
]
comparison['diff'] = comparison['regular_avg'] - comparison['knockout_avg']
top10 = comparison.sort_values('diff', ascending=False).head(10).reset_index()

fig, ax = plt.subplots(figsize=(13, 7), facecolor=DARK_BG)
x = range(len(top10))
width = 0.35
b1 = ax.bar([i - width/2 for i in x], top10['regular_avg'], width=width,
            color=ACCENT, label='Regular Season Avg', edgecolor='none')
b2 = ax.bar([i + width/2 for i in x], top10['knockout_avg'], width=width,
            color=RED, label='Knockout Avg', edgecolor='none')

# Difference arrow annotation
for i, (_, row) in enumerate(top10.iterrows()):
    ax.annotate('', xy=(i + width/2, row['knockout_avg']),
                xytext=(i - width/2, row['regular_avg']),
                arrowprops=dict(arrowstyle='->', color=YELLOW, lw=1.5))
    ax.text(i, max(row['regular_avg'], row['knockout_avg']) + 0.8,
            f"−{row['diff']:.1f}", ha='center', color=YELLOW, fontsize=8, fontweight='bold')

ax.set_xticks(list(x))
ax.set_xticklabels(top10['batter'], rotation=30, ha='right', color=TEXT_COL, fontsize=9.5)
set_style(ax,
    title='The Big Match Problem — Biggest Batting Drop-offs in IPL Knockouts (2008–2024)',
    xlabel='', ylabel='Runs per Innings')
ax.tick_params(axis='y', labelcolor=TEXT_COL)
ax.legend(facecolor='#1a1a2e', labelcolor=TEXT_COL, edgecolor=GRID_COL, fontsize=10)
ax.text(0.99, 0.98, 'Numbers above bars = avg drop in knockouts',
        transform=ax.transAxes, color=MUTED_COL, fontsize=8, ha='right', va='top')
plt.tight_layout()
plt.savefig('charts/05_knockout_underperformers.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
plt.show()
print("✓ Chart 5 saved")

print("\n✅ All 5 charts saved to charts/ folder")

qualified.to_csv('charts/batting_data.csv', index=False)
team_winrate.to_csv('charts/team_winrates.csv', index=False)
pp_data.to_csv('charts/powerplay_data.csv', index=False)
death_data.to_csv('charts/death_data.csv', index=False)
venue_toss.to_csv('charts/toss_data.csv', index=False)
top10.to_csv('charts/knockout_data.csv', index=False)

pp_data["phase"] = "Powerplay"
death_data["phase"] = "Death Overs"

combined = pd.concat([pp_data, death_data], ignore_index=True)

combined.to_csv("charts/strategy_combined.csv", index=False)

print("✓ strategy_combined.csv saved")
