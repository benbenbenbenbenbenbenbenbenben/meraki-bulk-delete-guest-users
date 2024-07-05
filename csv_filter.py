import csv
from datetime import datetime
from typing import List, Dict

def is_older_than(created_at: str, days: int) -> bool:
    """
    Check if the given date string is older than the specified number of days.
    """
    creation_date = datetime.strptime(created_at, "%H:%M %b %d %Y")
    return (datetime.now() - creation_date).days > days

def filter_guest_accounts(file_path: str, days: int) -> List[Dict[str, str]]:
    """
    Filter accounts of type 'Guest' that are older than the specified number of days.
    """
    filtered_accounts = []
    with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Account type'] == 'Guest' and is_older_than(row['Created at'], days):
                filtered_accounts.append(row)
    return filtered_accounts
