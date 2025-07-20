from datetime import datetime, time
import pytz

# --- Helper Functions ---
def get_session():
    tz = pytz.timezone("Africa/Lagos")
    now = datetime.now(tz)

    # Define the session days and their cut‑off times (2 PM)
    sessions = [
        # (session_date, column_name)
        (datetime(2025, 7, 19).date(), "Check-in day2"),
        (datetime(2025, 7, 20).date(), "Check-in day 3"),
    ]

    for session_date, col_name in sessions:
        # deadline is that date at 14:00
        deadline = tz.localize(datetime.combine(session_date, time(14, 0)))
        if now.date() < session_date:
            # it's before the session day → upcoming
            return col_name
        elif now.date() == session_date and now <= deadline:
            # it's the session day and before 2 PM
            return col_name

    # if past both deadlines
    return None

# --- in your main app, use exactly the same get_session() call as before ---
session_col = get_session()
if not session_col:
    st.warning("Registration/check‑in is now closed for all sessions.")
    st.stop()

# Show current local time
now = datetime.now(pytz.timezone("Africa/Lagos"))
st.info(f"Current Time: **{now.strftime('%A %d %B %Y, %I:%M %p')}**")
