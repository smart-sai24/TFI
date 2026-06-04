import pandas as pd


def compute_attendance_summary(records):
    df = pd.DataFrame(records)
    if df.empty:
        return {
            'full': 0,
            'partial': 0,
            'absent': 0,
            'total_records': 0,
        }

    categories = df['attendance_status'].str.title().value_counts().to_dict()
    return {
        'full': int(categories.get('Full', 0)),
        'partial': int(categories.get('Partial', 0)),
        'absent': int(categories.get('Absent', 0)),
        'total_records': int(len(df)),
    }


def compute_attendance_quality(records):
    df = pd.DataFrame(records)
    if df.empty:
        return {
            'average_attendance_percentage': 0,
            'average_engagement_score': 0,
            'late_joining_count': 0,
            'early_leaving_count': 0,
            'identity_match_rate': 0,
        }

    email_count = int(df['email'].astype(str).str.contains('@').sum()) if 'email' in df else 0
    return {
        'average_attendance_percentage': round(float(df['attendance_percentage'].mean()), 1),
        'average_engagement_score': round(float(df['engagement_score'].mean()), 1),
        'late_joining_count': int(df['late_joining'].sum()),
        'early_leaving_count': int(df['early_leaving'].sum()),
        'identity_match_rate': round((email_count / len(df)) * 100, 1),
    }
