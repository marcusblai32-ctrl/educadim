from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.db.models import Q
from .models import ChatRoom, Message
from courses.models import Course
from enrollments.models import Enrollment
from accounts.models import CustomUser
import json

@login_required
def liste_salons(request):
    salons = request.user.chat_rooms.all().order_by('-created_at')
    return render(request, 'chat/room_list.html', {'salons': salons})

@login_required
def detail_salon(request, pk):
    salon = get_object_or_404(ChatRoom, pk=pk)
    if request.user not in salon.participants.all():
        raise PermissionDenied(_("Vous n'avez pas acces a ce salon."))
    messages_list = salon.messages.filter(is_deleted=False).select_related('user')

    from django.utils import timezone
    now = timezone.now()
    yesterday = now - timezone.timedelta(days=1)

    return render(request, 'chat/room_detail.html', {
        'salon': salon,
        'messages': messages_list,
        'now': now,
        'yesterday': yesterday,
    })

@login_required
def supprimer_message(request, pk):
    msg = get_object_or_404(Message, pk=pk)
    if request.user == msg.user or request.user.is_staff:
        msg.is_deleted = True
        msg.save()
        messages.success(request, _("Message supprime."))
    else:
        messages.error(request, _("Vous n'etes pas autorise a supprimer ce message."))
    return redirect('chat:detail_salon', pk=msg.room.pk)

@login_required
def get_new_messages(request, room_pk, last_message_id):
    """Retounen nouvo mesaj depi dènye ID a (JSON)"""
    salon = get_object_or_404(ChatRoom, pk=room_pk)
    
    if request.user not in salon.participants.all():
        return JsonResponse({'messages': []}, status=403)

    new_messages = salon.messages.filter(
        is_deleted=False,
        id__gt=last_message_id
    ).select_related('user')

    if not new_messages:
        return JsonResponse({'messages': []})

    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'contenu': msg.contenu,
            'sender': 'user' if msg.user == request.user else 'other',
            'sender_name': msg.user.get_full_name() or msg.user.username,
            'time': msg.created_at.strftime('%H:%M'),
            'date': msg.created_at.strftime('%d/%m/%Y'),
            'user_id': msg.user.id,
        })

    return JsonResponse({'messages': messages_data})

@login_required
def send_message(request, room_pk):
    """Voye yon mesaj epi retounen an JSON"""
    print(f"🔵 send_message called: room_pk={room_pk}, user={request.user}")
    
    salon = get_object_or_404(ChatRoom, pk=room_pk)
    
    if request.user not in salon.participants.all():
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    # Jwenn kontni an
    contenu = None
    
    # Eseye jwenn nan JSON
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            contenu = data.get('contenu', '').strip()
        except:
            pass
    
    # Eseye jwenn nan POST form
    if contenu is None:
        contenu = request.POST.get('contenu', '').strip()
    
    print(f"🔵 contenu: '{contenu}'")
    
    if not contenu:
        return JsonResponse({'error': 'Empty message'}, status=400)
    
    # Kreye mesaj la nan baz done
    try:
        msg = Message.objects.create(
            room=salon,
            user=request.user,
            contenu=contenu
        )
        print(f"✅ Message created: ID={msg.id}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
    # Retounen mesaj la an JSON
    return JsonResponse({
        'status': 'ok',
        'id': msg.id,
        'contenu': msg.contenu,
        'sender': 'user',
        'sender_name': request.user.get_full_name() or request.user.username,
        'time': msg.created_at.strftime('%H:%M'),
        'date': msg.created_at.strftime('%d/%m/%Y'),
        'user_id': request.user.id,
    })

@login_required
def liste_etudiants_chat(request):
    cours_ids = Enrollment.objects.filter(
        utilisateur=request.user,
        statut='active'
    ).values_list('cours_id', flat=True)

    etudiants = CustomUser.objects.filter(
        inscriptions__cours_id__in=cours_ids,
        inscriptions__statut='active'
    ).exclude(id=request.user.id).distinct()

    search_query = request.GET.get('search', '')
    if search_query:
        etudiants = etudiants.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    for etudiant in etudiants:
        existing = ChatRoom.objects.filter(
            type='private',
            participants=request.user
        ).filter(participants=etudiant).first()
        etudiant.chat_existe = existing is not None
        etudiant.chat_id = existing.pk if existing else None

    return render(request, 'chat/etudiants_list.html', {
        'etudiants': etudiants,
        'search_query': search_query,
    })

@login_required
def creer_salon_prive(request, user_id):
    other = get_object_or_404(CustomUser, pk=user_id)

    cours_communs = Course.objects.filter(
        inscriptions__utilisateur=request.user,
        inscriptions__statut='active'
    ).filter(
        inscriptions__utilisateur=other,
        inscriptions__statut='active'
    )

    if not cours_communs.exists():
        messages.error(request, _("Vous devez partager un cours pour creer un chat prive."))
        return redirect('chat:liste_etudiants')

    existing = ChatRoom.objects.filter(
        type='private',
        participants=request.user
    ).filter(participants=other).first()

    if existing:
        return redirect('chat:detail_salon', pk=existing.pk)

    salon = ChatRoom.objects.create(
        type='private',
        nom=f"Prive: {request.user.get_full_name()} & {other.get_full_name()}",
        created_by=request.user
    )
    salon.participants.add(request.user, other)
    salon.save()

    messages.success(request, _("Salon prive cree avec {}.").format(other.get_full_name()))
    return redirect('chat:detail_salon', pk=salon.pk)

@login_required
def creer_salon_groupe(request, course_pk):
    course = get_object_or_404(Course, pk=course_pk)
    if not (request.user.is_staff or Enrollment.objects.filter(utilisateur=request.user, cours=course, statut='active').exists()):
        messages.error(request, _("Vous n'etes pas inscrit a ce cours."))
        return redirect('courses:course_detail', pk=course_pk)
    
    existing = ChatRoom.objects.filter(type='group', course=course).first()
    if existing:
        return redirect('chat:detail_salon', pk=existing.pk)
    
    salon = ChatRoom.objects.create(
        type='group',
        nom=f"Groupe - {course.titre}",
        course=course,
        created_by=request.user
    )
    participants = CustomUser.objects.filter(inscriptions__cours=course, inscriptions__statut='active')
    salon.participants.add(*participants)
    if request.user.is_staff:
        admins = CustomUser.objects.filter(is_staff=True)
        salon.participants.add(*admins)
    salon.save()
    messages.success(request, _("Salon de groupe cree."))
    return redirect('chat:detail_salon', pk=salon.pk)

@login_required
def creer_salon_feedback(request, user_id):
    if not request.user.is_staff:
        messages.error(request, _("Seuls les administrateurs peuvent creer un salon de feedback."))
        return redirect('chat:liste_salons')
    
    student = get_object_or_404(CustomUser, pk=user_id)
    existing = ChatRoom.objects.filter(type='feedback', participants=request.user).filter(participants=student).first()
    
    if existing:
        return redirect('chat:detail_salon', pk=existing.pk)
    
    salon = ChatRoom.objects.create(
        type='feedback',
        nom=f"Feedback {student.get_full_name()}",
        created_by=request.user
    )
    salon.participants.add(request.user, student)
    salon.save()
    messages.success(request, _("Salon de feedback cree."))
    return redirect('chat:detail_salon', pk=salon.pk)