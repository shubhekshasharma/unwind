import sqlite3
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from datetime import datetime

DATABASE_FILE = "user_device_data.db"
OUTPUT_FILE = "unwind_insights.png"

C_BLUE   = "#5B8DB8"
C_SALMON = "#E07B6A"
C_ORANGE = "#E8A838"


def load_sessions(db_path: str) -> list[dict]:
    """Return all stop_unwind sessions ordered chronologically."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute(
        "SELECT * FROM sessions WHERE event_type = 'stop_unwind' ORDER BY id ASC"
    )
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def parse_session(session: dict) -> dict:
    """Enrich a raw DB row with derived fields."""
    raw_start = session.get("session_started_at", "")
    try:
        start_dt = datetime.strptime(raw_start, "%y%m%d%H%M%S")
    except ValueError:
        start_dt = None

    return {
        **session,
        "start_dt": start_dt,
        "duration_min": round((session.get("duration_seconds") or 0) / 60, 1),
        "pickup_count": session.get("pickup_count") or 0,
    }


def add_value_labels(ax, bars, fmt="{:.0f}"):
    """Print a value above each bar."""
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + ax.get_ylim()[1] * 0.01,
            fmt.format(height),
            ha="center", va="bottom", fontsize=8, color="#444444",
        )


def fmt_dt(dt: datetime) -> str:
    """Cross-platform short date+time label (no leading-zero flags)."""
    return f"{dt.month}/{dt.day}\n{dt.hour % 12 or 12}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def plot_dashboard(sessions: list[dict]):
    n = len(sessions)
    x = list(range(n))
    labels = []
    for i, s in enumerate(sessions):
        dt_str = fmt_dt(s["start_dt"]) if s["start_dt"] else f"#{i+1}"
        labels.append(f"S{i+1}\n{dt_str}")

    durations = [s["duration_min"] for s in sessions]
    pickups   = [s["pickup_count"] for s in sessions]

    avg_duration = sum(durations) / n
    avg_pickups  = sum(pickups) / n

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor("#F7F7F7")
    fig.suptitle("Unwind — Sleep Wind-Down Insights", fontsize=17,
                 fontweight="bold", color="#222222", y=1.02)

    for ax in (ax1, ax2):
        ax.set_facecolor("#FFFFFF")
        for spine in ax.spines.values():
            spine.set_color("#DDDDDD")
        ax.tick_params(colors="#555555")
        ax.title.set_color("#222222")
        ax.yaxis.label.set_color("#555555")
        ax.xaxis.label.set_color("#555555")

    # Panel 1 – Session Duration
    bars1 = ax1.bar(x, durations, color=C_BLUE, alpha=0.85, zorder=3)
    ax1.axhline(avg_duration, color=C_ORANGE, linewidth=1.5, linestyle="--",
                label=f"Avg  {avg_duration:.1f} min", zorder=4)
    ax1.set_title("Session Duration", fontweight="bold")
    ax1.set_ylabel("Minutes")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=7)
    ax1.legend(fontsize=8)
    ax1.grid(axis="y", alpha=0.3, zorder=0)
    ax1.set_ylim(0, max(durations) * 1.18 if durations else 1)
    add_value_labels(ax1, bars1, "{:.1f}m")
    
    # Panel 2 – Phone Pickups per Session
    bars2 = ax2.bar(x, pickups, color=C_SALMON, alpha=0.85, zorder=3)
    ax2.axhline(avg_pickups, color=C_ORANGE, linewidth=1.5, linestyle="--",
                label=f"Avg  {avg_pickups:.1f}", zorder=4)
    ax2.set_title("Phone Pickups per Session", fontweight="bold")
    ax2.set_ylabel("Number of Pickups")
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=7)
    ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3, zorder=0)
    ax2.set_ylim(0, max(pickups) * 1.25 + 0.5 if any(p > 0 for p in pickups) else 3)
    add_value_labels(ax2, bars2, "{:.0f}")

    plt.tight_layout()
    plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Dashboard saved → {OUTPUT_FILE}")
    plt.show()


if __name__ == "__main__":
    sessions_raw = load_sessions(DATABASE_FILE)
    if not sessions_raw:
        print("No completed sessions found in the database. Run a session first.")
    else:
        sessions = [parse_session(s) for s in sessions_raw]
        print(f"Loaded {len(sessions)} completed session(s).")
        plot_dashboard(sessions)
