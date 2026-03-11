import sqlite3
import numpy as np
import pandas as pd
import os

# ─────────────────────────────────────────────────────────────────────────────
# Path to your SQLite database inside the data/ folder
# ─────────────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "ncaa.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# Team queries
# ─────────────────────────────────────────────────────────────────────────────
def get_team_logo(team_name: str) -> str | None:
    """
    Look up a team logo URL by location (e.g. 'Drake', 'Northern Iowa').
    Returns the URL string, or None if not found.
    """
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT logo_url FROM teams WHERE location = ?", (team_name,)
            ).fetchone()
        return row["logo_url"] if row else None
    except Exception as e:
        print(f"[db] get_team_logo error for '{team_name}': {e}")
        return None

# ------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH)


def get_team_names():
    with get_conn() as conn:
        df = pd.read_sql_query("SELECT DISTINCT display_name FROM teams ORDER BY display_name", conn)
    return df["display_name"].tolist()


def get_conference_names():
    with get_conn() as conn:
        df = pd.read_sql_query(
            "SELECT DISTINCT conference_short_name FROM conferences ORDER BY conference_short_name", conn
        )
    return df["conference_short_name"].tolist()


def get_conferences_by_tier(tier):
    col_map = {
        "High Major": "is_high_major",
        "Mid Major": "is_mid_major",
        "One Bid": "is_one_bid",
        "Low Major": "is_low_major",
    }
    col = col_map.get(tier)
    if not col:
        return []
    with get_conn() as conn:
        df = pd.read_sql_query(
            f"SELECT conference_short_name FROM conferences WHERE {col}=1 OR {col}='TRUE' OR {col}='true'",
            conn,
        )
    return df["conference_short_name"].tolist()


def build_game_filter(split, conferences, teams):
    conditions, params = [], []
    if split == "Conference":
        conditions.append("g.conference_competition = 1")
    elif split == "Non-Conference":
        conditions.append("g.conference_competition = 0")
    elif split == "Home":
        conditions.append("bs.home_away = 'home'")
    elif split == "Away":
        conditions.append("bs.home_away = 'away'")
    elif split == "Neutral":
        conditions.append("g.neutral_site = 1")
    if conferences:
        conditions.append(f"c.conference_short_name IN ({','.join('?'*len(conferences))})")
        params.extend(conferences)
    if teams:
        conditions.append(f"t.display_name IN ({','.join('?'*len(teams))})")
        params.extend(teams)
    return (" AND ".join(conditions) if conditions else "1=1"), params


def get_ranking_data(split, conferences, teams, metric_type):
    where_clause, params = build_game_filter(split, conferences, teams)
    if metric_type in ("Kills", "Kills / Win%"):
        stat_col, per_game_col, total_col = "kills", "Kill per Game", "Total Kills"
        conceded_pg_col, conceded_total_col = "Kill Conceded per Game", "Total Kills Conceded"
    else:
        stat_col, per_game_col, total_col = "killshots", "Killshot per Game", "Total Killshots"
        conceded_pg_col, conceded_total_col = "Killshot Conceded per Game", "Total Killshots Conceded"

    query = f"""
    WITH team_stats AS (
        SELECT bs.team_id, bs.game_id, bs.{stat_col} AS team_stat,
               g.conference_competition, g.neutral_site, bs.home_away,
               CASE WHEN bs.home_away='home' THEN g.home_team_winner
                    WHEN bs.home_away='away' THEN g.away_team_winner
                    ELSE NULL END AS is_winner
        FROM boxscores_team bs JOIN games g ON bs.game_id=g.id
        WHERE g.status_completed=1
    ),
    opponent_stats AS (
        SELECT ts.team_id, ts.game_id, bs_opp.{stat_col} AS opp_stat,
               ts.conference_competition, ts.neutral_site, ts.home_away, ts.is_winner
        FROM team_stats ts
        JOIN boxscores_team bs_opp ON ts.game_id=bs_opp.game_id AND ts.team_id!=bs_opp.team_id
    )
    SELECT t.display_name AS Team, t.logo_url AS Logo,
           AVG(CAST(ts.team_stat AS FLOAT)) AS "{per_game_col}",
           SUM(ts.team_stat) AS "{total_col}",
           AVG(CAST(os.opp_stat AS FLOAT)) AS "{conceded_pg_col}",
           SUM(os.opp_stat) AS "{conceded_total_col}",
           COUNT(*) AS "Games Played",
           ROUND(AVG(CAST(os.is_winner AS FLOAT))*100,1) AS "Win%"
    FROM team_stats ts
    JOIN opponent_stats os ON ts.team_id=os.team_id AND ts.game_id=os.game_id
    JOIN teams t ON ts.team_id=t.id
    JOIN conferences c ON t.conference_id=c.id
    JOIN games g ON ts.game_id=g.id
    JOIN boxscores_team bs ON ts.game_id=bs.game_id AND ts.team_id=bs.team_id
    WHERE {where_clause}
    GROUP BY t.display_name HAVING COUNT(*)>0
    ORDER BY AVG(CAST(ts.team_stat AS FLOAT)) DESC
    """
    try:
        with get_conn() as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"DB error: {e}")
        return pd.DataFrame()


def get_win_pct_by_kill_count(split, conferences, teams):
    where_clause, params = build_game_filter(split, conferences, teams)
    query = f"""
    WITH team_stats AS (
        SELECT bs.team_id, bs.game_id, bs.kills AS team_kills, bs.home_away,
               CASE WHEN bs.home_away='home' THEN g.home_team_winner
                    WHEN bs.home_away='away' THEN g.away_team_winner
                    ELSE NULL END AS is_winner
        FROM boxscores_team bs JOIN games g ON bs.game_id=g.id
        WHERE g.status_completed=1
    )
    SELECT ts.team_kills AS Kills, COUNT(*) AS Games, SUM(ts.is_winner) AS Wins,
           ROUND(AVG(CAST(ts.is_winner AS FLOAT))*100,1) AS "Win%"
    FROM team_stats ts
    JOIN teams t ON ts.team_id=t.id
    JOIN conferences c ON t.conference_id=c.id
    JOIN games g ON ts.game_id=g.id
    JOIN boxscores_team bs ON ts.game_id=bs.game_id AND ts.team_id=bs.team_id
    WHERE {where_clause}
    GROUP BY ts.team_kills HAVING COUNT(*)>0 AND ts.team_kills IS NOT NULL
    ORDER BY ts.team_kills ASC
    """
    try:
        with get_conn() as conn:
            return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"DB error win%: {e}")
        return pd.DataFrame()