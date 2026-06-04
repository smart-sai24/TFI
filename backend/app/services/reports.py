def certificate_eligibility_summary(records):
    eligible = sum(1 for record in records if record.get('attendance_status') == 'Full')
    total = len(records)
    return {
        'certificate_eligible': eligible,
        'total_students': total,
        'eligibility_rate': round((eligible / total) * 100, 1) if total else 0,
    }
