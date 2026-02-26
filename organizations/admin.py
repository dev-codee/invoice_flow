from django.contrib import admin
from .models import Organization, OrganizationMembership, Invitation


class MembershipInline(admin.TabularInline):
    model = OrganizationMembership
    extra = 0


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'owner', 'plan', 'currency', 'created_at']
    list_filter = ['plan', 'currency']
    search_fields = ['name', 'slug', 'owner__email']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [MembershipInline]


@admin.register(OrganizationMembership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'joined_at']
    list_filter = ['role']


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'organization', 'role', 'is_accepted', 'created_at']
    list_filter = ['is_accepted', 'role']
    readonly_fields = ['token']
