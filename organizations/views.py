from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from .models import Organization, OrganizationMembership, Invitation
from .forms import OrganizationSetupForm, InviteForm
from django.core.mail import send_mail
from django.conf import settings


def get_org(request):
    m = request.user.memberships.select_related('organization').first()
    return m.organization if m else None


@login_required
def org_settings(request):
    org = get_org(request)
    if not org:
        # First time — create org
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
                messages.success(request, f'Organization "{org.name}" created!')
                return redirect('dashboard:dashboard')
        else:
            form = OrganizationSetupForm()
        return render(request, 'organizations/onboarding.html', {'form': form})

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
    form = InviteForm(request.POST)
    if form.is_valid():
        invitation = form.save(commit=False)
        invitation.organization = org
        invitation.invited_by = request.user
        invitation.save()
        accept_url = request.build_absolute_uri(f'/organizations/invite/accept/{invitation.token}/')
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
    if not request.user.is_authenticated:
        return redirect(f'/accounts/login/?next=/organizations/invite/accept/{token}/')
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
    membership = get_object_or_404(OrganizationMembership, pk=pk, organization=org)
    if membership.role == 'owner':
        messages.error(request, 'Cannot remove the owner.')
    else:
        membership.delete()
        messages.success(request, 'Member removed.')
    return redirect('organizations:settings')
