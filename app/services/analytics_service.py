"""Analytics business logic: activity map, streaks and weekly series.

Kept separate from the routes so computing results is independently testable
and reusable by future dashboards/exports.
"""

from datetime import date, timedelta

from ..models import task as task_model


def activity_map(user_id):
    """``{"YYYY-MM-DD": count}`` for every day a task was completed."""
    counts = {}
    for day in task_model.completed_dates(user_id):
        counts[day] = counts.get(day, 0) + 1
    return counts


def compute_streaks(dates_set):
    """Current and longest streak of consecutive days with activity."""
    today = date.today()
    today_iso = today.isoformat()

    # A streak is not broken when today is simply not finished yet.
    yesterday = today - timedelta(days=1)
    anchor = None
    if today_iso in dates_set:
        anchor = today
    elif yesterday.isoformat() in dates_set:
        anchor = yesterday

    current = 0
    if anchor:
        day = anchor
        while day.isoformat() in dates_set:
            current += 1
            day -= timedelta(days=1)

    previous = None
    longest = 0
    run = 0
    for d in sorted(dates_set):
        day = date.fromisoformat(d)
        run = run + 1 if previous and day == previous + timedelta(days=1) else 1
        longest = max(longest, run)
        previous = day

    return current, longest


def analytics(user_id):
    """Everything the dashboard needs in one response."""
    counts = task_model.stats(user_id)
    activity = activity_map(user_id)
    current_streak, longest_streak = compute_streaks(set(activity.keys()))
    return {
        **counts,
        "activity": activity,
        "weekly": task_model.weekly_counts(user_id),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }