from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from .models import Organization, OrganizationMembership, Invitation
from .forms import OrganizationSetupForm, InviteForm
from django.core.mail import send_mail
from django.conf import settings


def get_org(request):
    active_id = request.session.get('active_org_id')
    if active_id:
        membership = request.user.memberships.filter(organization_id=active_id).select_related('organization').first()
        if membership:
            return membership.organization

    membership = request.user.memberships.select_related('organization').first()
    if membership:
        request.session['active_org_id'] = str(membership.organization.id)
        return membership.organization
    return None


@login_required
def switch_org(request, org_id):
    membership = get_object_or_404(OrganizationMembership, user=request.user, organization_id=org_id)
    request.session['active_org_id'] = str(membership.organization.id)
    messages.success(request, f'Switched to {membership.organization.name}')
    return redirect('dashboard:dashboard')


@login_required
def org_create(request):
    if request.method == 'POST':
        form = OrganizationSetupForm(request.POST, request.FILES)
        if form.is_valid():
            org = form.save(commit=False)
            org.owner = request.user
            if not org.slug:
                org.slug = slugify(org.name)
            org.save()
            OrganizationMembership.objects.create(
                user=request.user, organization=org, role='owner'
            )
            request.session['active_org_id'] = str(org.id)
            messages.success(request, f'Organization "{org.name}" created!')
            return redirect('organizations:settings')
    else:
        form = OrganizationSetupForm()
    return render(request, 'organizations/onboarding.html', {'form': form})


@login_required
def org_settings(request):
    org = get_org(request)
    if not org:
        return redirect('organizations:create')

    # Edit existing org
    membership = request.user.memberships.filter(organization=org).first()
    if request.method == 'POST':
        form = OrganizationSetupForm(request.POST, request.FILES, instance=org)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved.')
            return redirect('organizations:settings')
    else:
        form = OrganizationSetupForm(instance=org)

    members = OrganizationMembership.objects.filter(organization=org).select_related('user')
    pending = Invitation.objects.filter(organization=org, is_accepted=False)
    invite_form = InviteForm()

    return render(request, 'organizations/settings.html', {
        'org': org,
        'form': form,
        'membership': membership,
        'members': members,
        'pending_invitations': pending,
        'invite_form': invite_form,
    })


@login_required
def invite_member(request):
    org = get_org(request)
    if not org or request.method != 'POST':
        return redirect('organizations:settings')
    # Only owner/admin can invite
    requester = request.user.memberships.filter(organization=org).first()
    if not requester or requester.role not in ('owner', 'admin'):
        messages.error(request, 'You do not have permission to invite members.')
        return redirect('organizations:settings')
    form = InviteForm(request.POST)
    if form.is_valid():
        invitation = form.save(commit=False)
        invitation.organization = org
        invitation.invited_by = request.user
        # Expire in 7 days
        from django.utils import timezone
        from datetime import timedelta
        invitation.expires_at = timezone.now() + timedelta(days=7)
        invitation.save()
        base_url = getattr(settings, 'SITE_URL', '').rstrip('/')
        accept_url = f'{base_url}/organizations/invite/accept/{invitation.token}/'
        send_mail(
            subject=f'You\'re invited to join {org.name} on InvoiceFlow',
            message=f'Click here to accept: {accept_url}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=True,
        )
        messages.success(request, f'Invitation sent to {invitation.email}')
    return redirect('organizations:settings')


def accept_invitation(request, token):
    invitation = get_object_or_404(Invitation, token=token, is_accepted=False)

    # Check if invitation has expired
    from django.utils import timezone
    if invitation.expires_at and timezone.now() > invitation.expires_at:
        messages.error(request, 'This invitation has expired.')
        return redirect('dashboard:dashboard')

    if not request.user.is_authenticated:
        return redirect(f'/accounts/login/?next=/organizations/invite/accept/{token}/')

    # Verify the invitation email matches the logged-in user
    if invitation.email.lower() != request.user.email.lower():
        messages.error(request, f'This invitation was sent to {invitation.email}. Please log in with that email.')
        return redirect('dashboard:dashboard')

    if not OrganizationMembership.objects.filter(
        user=request.user, organization=invitation.organization
    ).exists():
        OrganizationMembership.objects.create(
            user=request.user,
            organization=invitation.organization,
            role=invitation.role,
        )
    invitation.is_accepted = True
    invitation.save()
    messages.success(request, f'You joined {invitation.organization.name}!')
    return redirect('dashboard:dashboard')


@login_required
def remove_member(request, pk):
    org = get_org(request)
    requester = request.user.memberships.filter(organization=org).first()
    membership = get_object_or_404(OrganizationMembership, pk=pk, organization=org)

    # Only owner/admin can remove members
    if not requester or requester.role not in ('owner', 'admin'):
        messages.error(request, 'You do not have permission to remove members.')
        return redirect('organizations:settings')
    # Cannot remove the owner
    if membership.role == 'owner':
        messages.error(request, 'Cannot remove the owner.')
    # Admins cannot remove other admins
    elif requester.role == 'admin' and membership.role == 'admin':
        messages.error(request, 'Admins cannot remove other admins.')
    else:
        membership.delete()
        messages.success(request, 'Member removed.')
    return redirect('organizations:settings')
