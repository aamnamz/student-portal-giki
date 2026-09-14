"""
Audience calculation for the notification engine.

Every function here returns a QuerySet of `applications.Application`
rows, filtered by admissions-workflow state. Functions are composable —
combined filters (e.g. "MS applicants who passed the test") are just
another function that intersects two conditions in one query, not a
chain of Python-side filtering, so there's no N+1 risk.

The AUDIENCE_REGISTRY maps a stable string key (stored on
ScheduledNotification.audience_filter) to one of these functions, so
the admin UI can list/preview audiences without hardcoding logic
in two places.
"""

from applications.models import Application


def _base():
    return Application.objects.select_related("applicant")


def all_submitted_applicants():
    return _base().filter(status="submitted")


def all_under_review():
    return _base().filter(status="under_review")


def all_action_required():
    return _base().filter(status="action_required")


def all_eligible_for_entry_test():
    """Submitted (or later) and haven't taken the test yet."""
    return _base().filter(
        status__in=["submitted", "under_review", "action_required"],
        entry_test_result="not_taken",
    )


def all_passed_entry_test():
    return _base().filter(entry_test_result="passed")


def all_failed_entry_test():
    return _base().filter(entry_test_result="failed")


def all_interviews_scheduled():
    return _base().filter(interview_status="scheduled")


def all_attended_interview():
    return _base().filter(interview_status="attended")


def all_missed_interview():
    return _base().filter(interview_status="missed")


def all_accepted():
    return _base().filter(final_decision="accepted")


def all_rejected():
    return _base().filter(final_decision="rejected")


def all_waitlisted():
    return _base().filter(final_decision="waitlisted")


def all_ms_applicants():
    return _base().filter(program_preference__degree_level="ms")


def all_phd_applicants():
    return _base().filter(program_preference__degree_level="phd")


def ms_passed_test():
    return all_passed_entry_test().filter(program_preference__degree_level="ms")


def phd_passed_test():
    return all_passed_entry_test().filter(program_preference__degree_level="phd")


def accepted_ms():
    return all_accepted().filter(program_preference__degree_level="ms")


def accepted_phd():
    return all_accepted().filter(program_preference__degree_level="phd")


def action_required_in_cycle(admission_cycle=None):
    """
    Not registered directly (takes an argument) — called by the
    program_filter/admission_cycle-aware wrapper in scheduler.py, since
    ScheduledNotification rows may scope any audience to one cycle.
    """
    return all_action_required()


# Registry: key -> callable returning a QuerySet[Application].
# Keys are what's stored in ScheduledNotification.audience_filter and
# shown (as human labels) in the admin preview UI.
AUDIENCE_REGISTRY = {
    "submitted_applicants": all_submitted_applicants,
    "under_review": all_under_review,
    "action_required": all_action_required,
    "eligible_for_entry_test": all_eligible_for_entry_test,
    "passed_entry_test": all_passed_entry_test,
    "failed_entry_test": all_failed_entry_test,
    "interviews_scheduled": all_interviews_scheduled,
    "attended_interview": all_attended_interview,
    "missed_interview": all_missed_interview,
    "accepted": all_accepted,
    "rejected": all_rejected,
    "waitlisted": all_waitlisted,
    "ms_applicants": all_ms_applicants,
    "phd_applicants": all_phd_applicants,
    "ms_passed_test": ms_passed_test,
    "phd_passed_test": phd_passed_test,
    "accepted_ms": accepted_ms,
    "accepted_phd": accepted_phd,
}

AUDIENCE_LABELS = {
    "submitted_applicants": "All Submitted Applicants",
    "under_review": "All Applicants Under Review",
    "action_required": "All Applicants — Action Required",
    "eligible_for_entry_test": "All Applicants Eligible for Entry Test",
    "passed_entry_test": "All Applicants Who Passed the Entry Test",
    "failed_entry_test": "All Applicants Who Failed the Entry Test",
    "interviews_scheduled": "All Applicants With Interview Scheduled",
    "attended_interview": "All Applicants Who Attended Interview",
    "missed_interview": "All Applicants Who Missed Interview",
    "accepted": "All Accepted Applicants",
    "rejected": "All Rejected Applicants",
    "waitlisted": "All Waitlisted Applicants",
    "ms_applicants": "All MS Applicants",
    "phd_applicants": "All PhD Applicants",
    "ms_passed_test": "MS Applicants Who Passed the Test",
    "phd_passed_test": "PhD Applicants Who Passed the Test",
    "accepted_ms": "Accepted MS Applicants",
    "accepted_phd": "Accepted PhD Applicants",
}


def get_audience_queryset(audience_key, program_filter="", admission_cycle=None):
    """
    Resolve a registry key (+ optional extra program/cycle scoping used
    by custom scheduled announcements) into a concrete QuerySet.
    """
    func = AUDIENCE_REGISTRY.get(audience_key)
    if func is None:
        return Application.objects.none()

    qs = func()

    if program_filter:
        qs = qs.filter(program_preference__degree_level=program_filter)

    # admission_cycle is accepted for forward-compatibility with a
    # per-application cycle relationship; the current AdmissionCycle is
    # a site-wide singleton (see AdmissionCycle.get_active()), so there
    # is nothing to filter by yet unless a cycle FK is added to
    # Application/ProgramPreference later.

    return qs.distinct()