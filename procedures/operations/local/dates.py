import datetime


def get_dates(days_back=30):
    # Get today's date
    today = datetime.date.today()

    # Calculate the start date
    start_date = today - datetime.timedelta(days=days_back)

    # Return both dates in the international standard of YYYY-MM-DD
    return start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")
