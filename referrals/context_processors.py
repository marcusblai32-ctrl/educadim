from .models import Rating, StaffMember, SystemFlag
from .services import SYSTEM_KEYS


def system_flags(request):
    stored_flags = dict(SystemFlag.objects.values_list("key", "is_active"))
    flags = {key: stored_flags.get(key, True) for key in SYSTEM_KEYS}
    context = {"flags": flags}
    if flags["rating_system"]:
        context["approved_ratings"] = Rating.objects.filter(
            is_approved=True
        ).select_related("user", "course")[:12]
    else:
        context["approved_ratings"] = ()
    if flags["staff_carousel"]:
        context["active_staff"] = StaffMember.objects.filter(is_active=True)
    else:
        context["active_staff"] = ()
    return context
