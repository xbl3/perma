# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.core import mail
from django.conf import settings

from perma.models import *

from .utils import PermaTestCase

from random import random
from bs4 import BeautifulSoup


class UserManagementViewsTestCase(PermaTestCase):

    fixtures = ['fixtures/users.json',
                'fixtures/folders.json',
                'fixtures/archive.json',
                ]

    def setUp(self):
        super(UserManagementViewsTestCase, self).setUp()

        self.admin_user = LinkUser.objects.get(pk=1)
        self.registrar_user = LinkUser.objects.get(pk=2)
        self.regular_user = LinkUser.objects.get(pk=4)
        self.registrar = self.registrar_user.registrar
        self.pending_registrar = Registrar.objects.get(pk=2)
        self.unrelated_registrar = Registrar.objects.exclude(pk=self.registrar.pk).first()
        self.unrelated_registrar_user = self.unrelated_registrar.users.first()
        self.organization = Organization.objects.get(pk=1)
        self.organization_user = self.organization.users.first()
        self.another_organization = Organization.objects.get(pk=2)
        self.unrelated_organization = self.unrelated_registrar.organizations.first()
        self.unrelated_organization_user = self.unrelated_organization.users.first()
        self.another_unrelated_organization_user = self.unrelated_organization.users.get(pk=11)
        self.deletable_organization = Organization.objects.get(pk=3)

    ### Helpers ###
    def pk_from_email(self, email):
        return LinkUser.objects.get(email=email).pk

    ### REGISTRAR A/E/D VIEWS ###

    def test_registrar_list_filters(self):
        # get just approved registrars
        self.get('user_management_manage_registrar',
                 user=self.admin_user,
                 request_kwargs={'data':{'status':'approved'}})

        # get just pending registrars
        self.get('user_management_manage_registrar',
                 user=self.admin_user,
                 request_kwargs={'data': {'status': 'pending'}})

    def test_admin_can_create_registrar(self):
        self.submit_form(
            'user_management_manage_registrar', {
                'a-name':'test_views_registrar',
                'a-email':'test@test.com',
                'a-website':'http://test.com'
            },
            user=self.admin_user,
            success_url=reverse('user_management_manage_registrar'),
            success_query=Registrar.objects.filter(name='test_views_registrar'))

    def test_admin_can_update_registrar(self):
        self.submit_form('user_management_manage_single_registrar',
                         user=self.admin_user,
                         reverse_kwargs={'args':[self.unrelated_registrar.pk]},
                         data={
                              'a-name': 'new_name',
                              'a-email': 'test@test.com2',
                              'a-website': 'http://test.com'},
                         success_url=reverse('user_management_manage_registrar'),
                         success_query=Registrar.objects.filter(name='new_name'))

    def test_registrar_can_update_registrar(self):
        self.submit_form('user_management_manage_single_registrar',
                         user=self.registrar_user,
                         reverse_kwargs={'args': [self.registrar.pk]},
                         data={
                             'a-name': 'new_name',
                             'a-email': 'test@test.com2',
                             'a-website': 'http://test.com'},
                         success_url=reverse('user_management_settings_affiliations'),
                         success_query=Registrar.objects.filter(name='new_name'))

    def test_registrar_cannot_update_unrelated_registrar(self):
        self.get('user_management_manage_single_registrar',
                 user=self.registrar_user,
                 reverse_kwargs={'args': [self.unrelated_registrar.pk]},
                 require_status_code=404)

    def test_admin_can_approve_pending_registrar(self):
        self.submit_form('user_management_approve_pending_registrar',
                         user=self.admin_user,
                         data={'status':'approved'},
                         reverse_kwargs={'args': [self.pending_registrar.pk]},
                         success_query=Registrar.objects.filter(pk=self.pending_registrar.pk,
                                                                status="approved").exists())

    def test_admin_can_deny_pending_registrar(self):
        self.submit_form('user_management_approve_pending_registrar',
                         user=self.admin_user,
                         data={'status': 'denied'},
                         reverse_kwargs={'args': [self.pending_registrar.pk]},
                         success_query=Registrar.objects.filter(pk=self.pending_registrar.pk,
                                                                status="denied").exists())

    ### ORGANIZATION A/E/D VIEWS ###

    def test_organization_list_filters(self):
        # get orgs for a single registrar
        self.get('user_management_manage_organization',
                 user=self.admin_user,
                 request_kwargs={'data': {'registrar': self.registrar.pk}})

    def test_admin_can_create_organization(self):
        self.submit_form('user_management_manage_organization',
                         user=self.admin_user,
                         data={
                             'a-name': 'new_name',
                             'a-registrar': self.registrar.pk},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_registrar_can_create_organization(self):
        self.submit_form('user_management_manage_organization',
                         user=self.registrar_user,
                         data={
                             'a-name': 'new_name'},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_admin_can_update_organization(self):
        self.submit_form('user_management_manage_single_organization',
                         user=self.admin_user,
                         reverse_kwargs={'args':[self.organization.pk]},
                         data={
                             'a-name': 'new_name',
                             'a-registrar': self.registrar.pk},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_registrar_can_update_organization(self):
        self.submit_form('user_management_manage_single_organization',
                         user=self.registrar_user,
                         reverse_kwargs={'args':[self.organization.pk]},
                         data={
                             'a-name': 'new_name'},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_org_user_can_update_organization(self):
        self.submit_form('user_management_manage_single_organization',
                         user=self.organization_user,
                         reverse_kwargs={'args': [self.organization.pk]},
                         data={
                             'a-name': 'new_name'},
                         success_url=reverse('user_management_manage_organization'),
                         success_query=Organization.objects.filter(name='new_name'))

    def test_registrar_cannot_update_unrelated_organization(self):
        self.get('user_management_manage_single_organization',
                 user=self.registrar_user,
                 reverse_kwargs={'args': [self.unrelated_organization.pk]},
                 require_status_code=404)

    def test_org_user_cannot_update_unrelated_organization(self):
        self.get('user_management_manage_single_organization',
                 user=self.organization_user,
                 reverse_kwargs={'args': [self.unrelated_organization.pk]},
                 require_status_code=404)

    def _delete_organization(self, user, should_succeed=True):
        if should_succeed:
            self.submit_form('user_management_manage_single_organization_delete',
                              user=user,
                              reverse_kwargs={'args': [self.deletable_organization.pk]},
                              success_url=reverse('user_management_manage_organization'),
                              success_query=Organization.objects.filter(user_deleted=True, pk=self.deletable_organization.pk))
        else:
            self.submit_form('user_management_manage_single_organization_delete',
                              user=user,
                              reverse_kwargs={'args': [self.deletable_organization.pk]},
                              require_status_code=404)

    def test_admin_user_can_delete_empty_organization(self):
        self._delete_organization(self.admin_user)
        self._delete_organization(self.admin_user, False)

    def test_registrar_user_can_delete_empty_organization(self):
        self._delete_organization(self.deletable_organization.registrar.users.first())
        self._delete_organization(self.deletable_organization.registrar.users.first(), False)

    def test_org_user_can_delete_empty_organization(self):
        self._delete_organization(self.deletable_organization.users.first())
        self._delete_organization(self.deletable_organization.users.first(), False)

    def test_cannot_delete_nonempty_organization(self):
        self.submit_form('user_management_manage_single_organization_delete',
                         user=self.admin_user,
                         reverse_kwargs={'args': [self.organization.pk]},
                         require_status_code=404)

    ### USER A/E/D VIEWS ###

    def test_create_and_delete_user(self):
        self.log_in_user(self.admin_user)

        base_user = {
            'a-first_name':'First',
            'a-last_name':'Last',
        }
        email = 'test_views_test@test.com'

        for view_name, form_extras in [
            ['registrar_user', {'a-registrar': 1}],
            ['user', {}],
            ['organization_user', {'a-organizations': 1}],
        ]:
            # create user
            email += '1'
            self.submit_form('user_management_' + view_name + '_add_user',
                           data=dict(base_user.items() + form_extras.items() + [['a-email', email]]),
                           success_url=reverse('user_management_manage_' + view_name),
                           success_query=LinkUser.objects.filter(email=email))
            new_user = LinkUser.objects.get(email=email)

            # delete user (deactivate)
            new_user.is_confirmed = True
            new_user.save()
            self.submit_form('user_management_manage_single_' + view_name + '_delete',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

            # reactivate user
            self.submit_form('user_management_manage_single_' + view_name + '_reactivate',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

            # delete user (really delete)
            new_user.is_confirmed = False
            new_user.save()
            self.submit_form('user_management_manage_single_' + view_name + '_delete',
                           reverse_kwargs={'args': [new_user.pk]},
                           success_url=reverse('user_management_manage_' + view_name))

    ### ADDING NEW USERS TO ORGANIZATIONS ###

    def test_admin_user_can_add_new_user_to_org(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=LinkUser.objects.filter(email='doesnotexist@example.com',
                                                               organizations=self.organization).exists())


    def test_registrar_user_can_add_new_user_to_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=LinkUser.objects.filter(email='doesnotexist@example.com',
                                                               organizations=self.organization).exists())


    def test_org_user_can_add_new_user_to_org(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=LinkUser.objects.filter(email='doesnotexist@example.com',
                                                               organizations=self.organization).exists())

    def test_registrar_user_cannot_add_new_user_to_inaccessible_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.unrelated_organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['organizations'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 organizations=self.unrelated_organization).exists())

    def test_org_user_cannot_add_new_user_to_inaccessible_org(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.unrelated_organization.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['organizations'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 organizations=self.unrelated_organization).exists())

    ### ADDING EXISTING USERS TO ORGANIZATIONS ###

    def test_admin_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_registrar_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_org_user_can_add_existing_user_to_org(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_organization_user'),
                         success_query=self.regular_user.organizations.filter(pk=self.organization.pk))

    def test_registrar_user_cannot_add_existing_user_to_inaccessible_org(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.unrelated_organization.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['organizations'])
        self.assertFalse(self.regular_user.organizations.filter(pk=self.unrelated_organization.pk).exists())

    def test_org_user_cannot_add_existing_user_to_inaccessible_org(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.another_organization.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['organizations'])
        self.assertFalse(self.regular_user.organizations.filter(pk=self.another_organization.pk).exists())

    def test_cannot_add_admin_user_to_org(self):
        self.log_in_user(self.organization_user)
        resp = self.submit_form('user_management_organization_user_add_user',
                         data={'a-organizations': self.organization.pk},
                         query_params={'email': self.admin_user.email})
        self.assertIn("is an admin user", resp.content)
        self.assertFalse(self.admin_user.organizations.exists())

    def test_cannot_add_registrar_user_to_org(self):
        self.log_in_user(self.organization_user)
        resp = self.submit_form('user_management_organization_user_add_user',
                                data={'a-organizations': self.organization.pk},
                                query_params={'email': self.registrar_user.email})
        self.assertIn("is already a registrar user", resp.content)
        self.assertFalse(self.registrar_user.organizations.exists())

    ### VOLUNTARILY LEAVING ORGANIZATIONS ###

    def test_org_user_can_leave_org(self):
        u = LinkUser.objects.get(email='test_another_library_org_user@example.com')
        orgs = u.organizations.all()

        # check assumptions
        self.assertEqual(len(orgs), 2)

        # 404 if tries to leave non-existent org
        self.submit_form('user_management_organization_user_leave_organization',
                          user=u,
                          data={},
                          reverse_kwargs={'args': [999]},
                          require_status_code=404)

        # returns to affiliations page if still a member of at least one org
        self.submit_form('user_management_organization_user_leave_organization',
                          user=u,
                          data={},
                          reverse_kwargs={'args': [orgs[0].pk]},
                          success_url=reverse('user_management_settings_affiliations'))

        # returns to create/manage page if no longer a member of any orgs
        self.submit_form('user_management_organization_user_leave_organization',
                          user=u,
                          data={},
                          reverse_kwargs={'args': [orgs[1].pk]},
                          success_url=reverse('create_link'))

        # 404 if tries to leave an org they are not a member of
        self.submit_form('user_management_organization_user_leave_organization',
                          user=u,
                          data={},
                          reverse_kwargs={'args': [orgs[1].pk]},
                          require_status_code=404)


    ### REMOVING USERS FROM ORGANIZATIONS ###

    # Just try to access the page with remove/deactivate links

    def test_registrar_can_edit_org_user(self):
        # User from one of registrar's own orgs succeeds
        self.log_in_user(self.registrar_user)
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.organization_user.pk]})
        # User from another registrar's org fails
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.another_unrelated_organization_user.pk]},
                  require_status_code=404)
        # Repeat with the other registrar, to confirm we're
        # getting 404s because of permission reasons, not because the
        # test fixtures are broken.
        self.log_in_user(self.unrelated_registrar_user)
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.organization_user.pk]},
                  require_status_code=404)
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.another_unrelated_organization_user.pk]})

    def test_org_can_edit_org_user(self):
        # User from own org succeeds
        org_one_users = ['test_org_user@example.com', 'test_org_rando_user@example.com']
        org_two_users = ['test_another_library_org_user@example.com', 'test_another_org_user@example.com']

        self.log_in_user(org_one_users[0])
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_one_users[1])]})
        # User from another org fails
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_two_users[0])]},
                  require_status_code=404)
        # Repeat in reverse, to confirm we're
        # getting 404s because of permission reasons, not because the
        # test fixtures are broken.
        self.log_in_user(org_two_users[1])
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_one_users[1])]},
                  require_status_code=404)
        # User from another org fails
        self.get('user_management_manage_single_organization_user',
                  reverse_kwargs={'args': [self.pk_from_email(org_two_users[0])]})

    # Actually try removing them

    def test_can_remove_user_from_organization(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_organization_user_remove',
                         data={'org': self.organization.pk},
                         reverse_kwargs={'args': [self.organization_user.pk]},
                         success_url=reverse('user_management_manage_organization_user'))
        self.assertFalse(self.organization_user.organizations.filter(pk=self.organization.pk).exists())

    def test_registrar_cannot_remove_unrelated_user_from_organization(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_organization_user_remove',
                         data={'org': self.unrelated_organization.pk},
                         reverse_kwargs={'args': [self.unrelated_organization_user.pk]},
                         require_status_code=404)

    def test_org_user_cannot_remove_unrelated_user_from_organization(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_manage_single_organization_user_remove',
                         data={'org': self.unrelated_organization.pk},
                         reverse_kwargs={'args': [self.unrelated_organization_user.pk]},
                         require_status_code=404)

    def test_can_remove_self_from_organization(self):
        self.log_in_user(self.organization_user)
        self.submit_form('user_management_manage_single_organization_user_remove',
                         data={'org': self.organization.pk},
                         reverse_kwargs={'args': [self.organization_user.pk]},
                         success_url=reverse('create_link'))
        self.assertFalse(self.organization_user.organizations.filter(pk=self.organization.pk).exists())

    ### ADDING NEW USERS TO REGISTRARS ###

    def test_admin_user_can_add_new_user_to_registrar(self):
        address = 'doesnotexist@example.com'
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_registrar_user_add_user',
                          data={'a-registrar': self.registrar.pk,
                                'a-first_name': 'First',
                                'a-last_name': 'Last',
                                'a-email': address},
                          query_params={'email': address},
                          success_url=reverse('user_management_manage_registrar_user'),
                          success_query=LinkUser.objects.filter(email=address,
                                                                registrar=self.registrar).exists())

    def test_registrar_user_can_add_new_user_to_registrar(self):
        address = 'doesnotexist@example.com'
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': address},
                         query_params={'email': address},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(email=address,
                                                               registrar=self.registrar).exists())
        # Try to add the same person again; should fail
        response = self.submit_form('user_management_registrar_user_add_user',
                                     data={'a-registrar': self.registrar.pk,
                                           'a-first_name': 'First',
                                           'a-last_name': 'Last',
                                           'a-email': address},
                                     query_params={'email': address}).content
        self.assertIn("{} is already a registrar user for your registrar.".format(address), response)

    def test_registrar_user_cannot_add_new_user_to_inaccessible_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.unrelated_registrar.pk,
                               'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         error_keys=['registrar'])
        self.assertFalse(LinkUser.objects.filter(email='doesnotexist@example.com',
                                                 registrar=self.unrelated_registrar).exists())

    ### ADDING EXISTING USERS TO REGISTRARS ###

    def test_admin_user_can_add_existing_user_to_registrar(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.registrar))

    def test_registrar_user_can_add_existing_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.registrar))

    def test_registrar_user_can_upgrade_org_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.organization_user.email},
                         success_url=reverse('user_management_manage_registrar_user'),
                         success_query=LinkUser.objects.filter(pk=self.organization_user.pk, registrar=self.registrar))
        self.assertFalse(LinkUser.objects.filter(pk=self.organization_user.pk, organizations=self.organization).exists())

    def test_registrar_user_cannot_upgrade_unrelated_org_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        resp = self.submit_form('user_management_registrar_user_add_user',
                                data={'a-registrar': self.registrar.pk},
                                query_params={'email': self.unrelated_organization_user.email})
        self.assertIn("belongs to organizations that are not controlled by your registrar", resp.content)
        self.assertFalse(LinkUser.objects.filter(pk=self.unrelated_organization_user.pk, registrar=self.registrar).exists())

    def test_registrar_user_cannot_add_existing_user_to_inaccessible_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.unrelated_registrar.pk},
                         query_params={'email': self.regular_user.email},
                         error_keys=['registrar'])
        self.assertFalse(LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.unrelated_registrar).exists())

    def test_cannot_add_admin_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        resp = self.submit_form('user_management_registrar_user_add_user',
                         data={'a-registrar': self.registrar.pk},
                         query_params={'email': self.admin_user.email})
        self.assertIn("is an admin user", resp.content)
        self.assertFalse(LinkUser.objects.filter(pk=self.admin_user.pk, registrar=self.registrar).exists())

    def test_cannot_add_registrar_user_to_registrar(self):
        self.log_in_user(self.registrar_user)
        resp = self.submit_form('user_management_registrar_user_add_user',
                                data={'a-registrar': self.registrar.pk},
                                query_params={'email': self.unrelated_registrar_user.email})
        self.assertIn("is already a member of another registrar", resp.content)
        self.assertFalse(LinkUser.objects.filter(pk=self.unrelated_registrar_user.pk, registrar=self.registrar).exists())

    ### REMOVING USERS FROM REGISTRARS ###

    def test_can_remove_user_from_registrar(self):
        self.log_in_user(self.registrar_user)
        self.regular_user.registrar = self.registrar
        self.regular_user.save()
        self.submit_form('user_management_manage_single_registrar_user_remove',
                         reverse_kwargs={'args': [self.regular_user.pk]},
                         success_url=reverse('user_management_manage_registrar_user'))
        self.assertFalse(LinkUser.objects.filter(pk=self.regular_user.pk, registrar=self.registrar).exists())

    def test_registrar_cannot_remove_unrelated_user_from_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_registrar_user_remove',
                         reverse_kwargs={'args': [self.unrelated_registrar_user.pk]},
                         require_status_code=404)

    def test_can_remove_self_from_registrar(self):
        self.log_in_user(self.registrar_user)
        self.submit_form('user_management_manage_single_registrar_user_remove',
                         reverse_kwargs={'args': [self.registrar_user.pk]},
                         success_url=reverse('create_link'))
        self.assertFalse(LinkUser.objects.filter(pk=self.registrar_user.pk, registrar=self.registrar).exists())

    ### ADDING NEW USERS AS ADMINS ###

    def test_admin_user_can_add_new_user_as_admin(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_admin_user_add_user',
                         data={'a-first_name': 'First',
                               'a-last_name': 'Last',
                               'a-email': 'doesnotexist@example.com'},
                         query_params={'email': 'doesnotexist@example.com'},
                         success_url=reverse('user_management_manage_admin_user'),
                         success_query=LinkUser.objects.filter(email='doesnotexist@example.com',
                                                               is_staff=True).exists())
    ### ADDING EXISTING USERS AS ADMINS ###

    def test_admin_user_can_add_existing_user_as_admin(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_admin_user_add_user',
                         query_params={'email': self.regular_user.email},
                         success_url=reverse('user_management_manage_admin_user'),
                         success_query=LinkUser.objects.filter(pk=self.regular_user.pk, is_staff=True))

    ### REMOVING USERS AS ADMINS ###

    def test_can_remove_user_from_admin(self):
        self.log_in_user(self.admin_user)
        self.regular_user.is_staff = True
        self.regular_user.save()
        self.submit_form('user_management_manage_single_admin_user_remove',
                         reverse_kwargs={'args': [self.regular_user.pk]},
                         success_url=reverse('user_management_manage_admin_user'))
        self.assertFalse(LinkUser.objects.filter(pk=self.regular_user.pk, is_staff=True).exists())

    def test_can_remove_self_from_admin(self):
        self.log_in_user(self.admin_user)
        self.submit_form('user_management_manage_single_admin_user_remove',
                         reverse_kwargs={'args': [self.admin_user.pk]},
                         success_url=reverse('create_link'))
        self.assertFalse(LinkUser.objects.filter(pk=self.admin_user.pk, is_staff=True).exists())

    ### SETTINGS ###

    def test_user_can_change_own_settings(self):
        self.submit_form('user_management_settings_profile',
                         user=self.admin_user,
                         data={
                             'a-first_name': 'Newfirst',
                             'a-last_name': 'Newlast',
                             'a-email': 'test_admin_user@example.com'
                         },
                         success_url=reverse('user_management_settings_profile'),
                         success_query=LinkUser.objects.filter(first_name='Newfirst'))

    def test_edit_org_privacy(self):
        '''
            Can an authorized user change the privacy setting of an org?
        '''

        # Toggle as an org user
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_org_user@example.com').content
        self.assertIn("Your Perma Links are currently <strong>Public</strong> by default.", response)
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                          user='test_org_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_affiliations'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_org_user@example.com').content
        self.assertIn("Your Perma Links are currently <strong>Private</strong> by default.", response)

        # Toggle as a registrar user
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                  user='test_registrar_user@example.com',
                  data={},
                  success_url=reverse('user_management_manage_organization'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_registrar_user@example.com').content
        self.assertIn("Your Perma Links are currently <strong>Public</strong> by default.", response)

        # Toggle as a staff user
        self.submit_form('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                  user='test_admin_user@example.com',
                  data={},
                  success_url=reverse('user_management_manage_organization'))
        response = self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[1]},
                             user='test_admin_user@example.com').content
        self.assertIn("Your Perma Links are currently <strong>Private</strong> by default.", response)

        # As staff, try to access non-existent org
        self.get('user_management_settings_organizations_change_privacy', reverse_kwargs={'args':[99999]},
                  user='test_admin_user@example.com',
                  require_status_code=404)

    # Tools

    def test_api_key(self):
        response = self.get('user_management_settings_tools',
                             user='test_user@example.com').content
        self.assertNotIn('id="id_api_key"', response)
        self.submit_form('api_key_create',
                          user='test_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_tools'))
        response = self.get('user_management_settings_tools',
                             user='test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        key = soup.find('input', {'id': 'id_api_key'})
        val = key.get('value', '')
        self.assertTrue(val)
        # do it again, and make sure the key changes
        self.submit_form('api_key_create',
                          user='test_user@example.com',
                          data={},
                          success_url=reverse('user_management_settings_tools'))
        response = self.get('user_management_settings_tools',
                             user='test_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        key = soup.find('input', {'id': 'id_api_key'})
        new_val = key.get('value', '')
        self.assertTrue(new_val)
        self.assertFalse(val == new_val)

    # Affiliations
    def test_affiliations(self):
        '''
            Does the expected information show up on the affliations page?
            (Tries not to be overly picky about the page design and markup.)
        '''
        # As an org user
        response = self.get('user_management_settings_affiliations',
                             user='multi_registrar_org_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        registrars = soup.select('h4 a')
        self.assertEqual(len(registrars), 2)
        for registrar in registrars:
            self.assertTrue(registrar.text.strip())
        orgs = soup.select('.settings-block p')
        self.assertEqual(len(orgs), 4)
        for org in orgs:
            self.assertTrue(org.text.strip())

        # As a registrar user
        response = self.get('user_management_settings_affiliations',
                             user='test_registrar_user@example.com').content
        soup = BeautifulSoup(response, 'html.parser')
        registrars = soup.select('h4')
        self.assertEqual(len(registrars), 1)
        for registrar in registrars:
            self.assertTrue(registrar.text.strip())
        settings = soup.select('dt')
        self.assertEqual(len(settings), 2)
        for setting in settings:
            self.assertTrue(org.text.strip())

        # As a pending registrar user
        response = self.get('user_management_settings_affiliations',
                             user='test_requested_registrar_account@example.com').content
        self.assertIn('Pending Registrar', response)
        self.assertIn('Thank you for requesting an account for your library. Perma.cc will review your request as soon as possible.', response)
        soup = BeautifulSoup(response, 'html.parser')
        registrars = soup.select('.sponsor-name')
        self.assertEqual(len(registrars), 1)
        for registrar in registrars:
            self.assertTrue(registrar.text.strip())
        settings = soup.select('dt')
        self.assertEqual(len(settings), 2)
        for setting in settings:
            self.assertTrue(org.text.strip())


    ###
    ### SIGNUP
    ###

    ### Libraries ###

    def new_lib(self):
        rand = random()
        return { 'email': u'library{}@university.org'.format(rand),
                 'name': u'University Library {}'.format(rand),
                 'website': u'http://website{}.org'.format(rand) }

    def new_lib_user(self):
        rand = random()
        return { 'email': u'user{}@university.org'.format(rand),
                 'first': u'Joe',
                 'last': u'Yacobówski' }

    def check_library_labels(self, soup):
        name_label = soup.find('label', {'for': 'id_b-name'})
        self.assertEqual(name_label.text, "Library name")
        email_label = soup.find('label', {'for': 'id_b-email'})
        self.assertEqual(email_label.text, "Library email")
        website_label = soup.find('label', {'for': 'id_b-website'})
        self.assertEqual(website_label.text, "Library website")

    def check_lib_user_labels(self, soup):
        email_label = soup.find('label', {'for': 'id_a-email'})
        self.assertEqual(email_label.text, "Your email")

    def check_lib_email(self, message, new_lib):
        our_address = settings.DEFAULT_FROM_EMAIL

        self.assertIn(new_lib['name'], message.body)
        self.assertIn(new_lib['email'], message.body)
        id = Registrar.objects.get(email=new_lib['email']).id
        approve_url = "http://testserver{}".format(reverse('user_management_approve_pending_registrar', args=[id]))
        self.assertIn(approve_url, message.body)
        self.assertEqual(message.subject, "Perma.cc new library registrar account request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': new_lib['email']})

    def check_lib_user_email(self, message, new_lib_user):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_lib_user['email']).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_lib_user['email']])

    def test_new_library_render(self):
        '''
           Does the library signup form display as expected?
        '''

        # NOT LOGGED IN

        # Registrar and user forms are displayed,
        # inputs are blank, and labels are customized as expected
        response = self.get('libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 7)
        for input in inputs:
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

        # If request_data is present in session, registrar form is prepopulated,
        # and labels are still customized as expected
        session = self.client.session
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        session['request_data'] = { u'b-email': new_lib['email'],
                                    u'b-website': new_lib['website'],
                                    u'b-name': new_lib['name'],
                                    u'a-email': new_lib_user['email'],
                                    u'a-first_name': new_lib_user['first'],
                                    u'a-last_name': new_lib_user['last'],
                                    u'csrfmiddlewaretoken': u'11YY3S2DgOw2DHoWVEbBArnBMdEA2svu' }
        session.save()
        response = self.get('libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 7)
        for input in inputs:
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            elif input['name'][:2] == "b-":
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

        # If there's an unsuccessful submission, field labels are still as expected.
        response = self.post('libraries').content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        self.check_lib_user_labels(soup)

        # LOGGED IN

        # Registrar form is displayed, but user form is not,
        # inputs are blank, and labels are still customized as expected
        response = self.get('libraries', user="test_user@example.com").content
        soup = BeautifulSoup(response, 'html.parser')
        self.check_library_labels(soup)
        inputs = soup.select('input')
        self.assertEqual(len(inputs), 5) # 5 because csrf is here and in the logout form
        for input in inputs:
            self.assertIn(input['name'],['csrfmiddlewaretoken', 'b-name', 'b-email', 'b-website'])
            if input['name'] == 'csrfmiddlewaretoken':
                self.assertTrue(input.get('value', ''))
            else:
                self.assertFalse(input.get('value', ''))

    def test_new_library_submit_success(self):
        '''
           Does the library signup form submit as expected? Success cases.
        '''
        expected_emails_sent = 0

        # Not logged in, submit all fields sans first and last name
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('libraries',
                          data = { u'b-email': new_lib['email'],
                                   u'b-website': new_lib['website'],
                                   u'b-name': new_lib['name'],
                                   u'a-email': new_lib_user['email'] },
                          success_url=reverse('register_library_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 2], new_lib)
        self.check_lib_user_email(mail.outbox[expected_emails_sent - 1], new_lib_user)

        # Not logged in, submit all fields including first and last name
        new_lib = self.new_lib()
        new_lib_user = self.new_lib_user()
        self.submit_form('libraries',
                          data = { u'b-email': new_lib['email'],
                                   u'b-website': new_lib['website'],
                                   u'b-name': new_lib['name'],
                                   u'a-email': new_lib_user['email'],
                                   u'a-first_name': new_lib_user['first'],
                                   u'a-last_name': new_lib_user['last']},
                          success_url=reverse('register_library_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 2], new_lib)
        self.check_lib_user_email(mail.outbox[expected_emails_sent - 1], new_lib_user)

        # Logged in
        new_lib = self.new_lib()
        existing_lib_user = { 'email': 'test_user@example.com'}
        self.submit_form('libraries',
                          data = { u'b-email': new_lib['email'],
                                   u'b-website': new_lib['website'],
                                   u'b-name': new_lib['name'] },
                          success_url=reverse('user_management_settings_affiliations'),
                          user=existing_lib_user['email'])
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_lib_email(mail.outbox[expected_emails_sent - 1], new_lib)

    def test_new_library_submit_failure(self):
        '''
           Does the library signup form submit as expected? Failures.
        '''
        new_lib = self.new_lib()
        existing_lib_user = { 'email': 'test_user@example.com'}

        # Not logged in, blank submission reports correct fields required
        # ('email' catches both registrar and user email errors, unavoidably,
        # so test with just that missing separately)
        self.submit_form('libraries',
                          data = {},
                          form_keys = ['registrar_form', 'user_form'],
                          error_keys = ['website', 'name', 'email'])
        self.assertEqual(len(mail.outbox), 0)

        # (checking user email missing separately)
        self.submit_form('libraries',
                          data = {u'b-email': new_lib['email'],
                                  u'b-website': new_lib['website'],
                                  u'b-name': new_lib['name']},
                          form_keys = ['registrar_form', 'user_form'],
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

        # Not logged in, user appears to have already registered
        data = {u'b-email': new_lib['email'],
                u'b-website': new_lib['website'],
                u'b-name': new_lib['name'],
                u'a-email': existing_lib_user['email']}
        self.submit_form('libraries',
                          data = data,
                          form_keys = ['registrar_form', 'user_form'],
                          success_url = '/login?next=/libraries/')
        self.assertDictEqual(self.client.session['request_data'], data)
        self.assertEqual(len(mail.outbox), 0)

        # Not logged in, registrar apepars to exist already
        # (actually, this doesn't currently fail)

        # Logged in, blank submission reports all fields required
        self.submit_form('libraries',
                          data = {},
                          user = existing_lib_user['email'],
                          error_keys = ['website', 'name', 'email'])
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, registrar appears to exist already
        # (actually, this doesn't currently fail)

    ### Courts ###

    def new_court(self):
        rand = random()
        return { 'requested_account_note': u'Court {}'.format(rand) }

    def new_court_user(self):
        rand = random()
        return { 'email': u'user{}@university.org'.format(rand),
                 'first': u'Joe',
                 'last': u'Yacobówski' }

    def check_court_email(self, message, court_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        # Doesn't check email contents yet; too many variations possible presently
        self.assertEqual(message.subject, "Perma.cc new library court account information request")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [our_address])
        self.assertDictEqual(message.extra_headers, {'Reply-To': court_email})

    def check_court_user_email(self, message, new_user):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_user['email']).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_user['email']])

    def test_new_court_success(self):
        '''
            Does the court signup form submit as expected? Success cases.
        '''
        new_court = self.new_court()
        new_user = self.new_court_user()
        existing_user = { 'email': 'test_user@example.com'}
        another_existing_user = { 'email': 'another_library_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # Existing user's email address, no court info
        # (currently succeeds, should probably fail; see issue 1746)
        self.submit_form('sign_up_courts',
                          data = { 'email': existing_user['email']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # Existing user's email address + court info
        self.submit_form('sign_up_courts',
                          data = { 'email': existing_user['email'],
                                   'requested_account_note': new_court['requested_account_note']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

        # New user email address, don't create account
        self.submit_form('sign_up_courts',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_court['requested_account_note']},
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # New user email address, create account
        self.submit_form('sign_up_courts',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_user_email(mail.outbox[expected_emails_sent - 2], new_user)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # LOGGED IN

        # New user email address
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_court_user()
        self.submit_form('sign_up_courts',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          user = existing_user['email'],
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 2
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_user_email(mail.outbox[expected_emails_sent - 2], new_user)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # Existing user's email address, not that of the user logged in.
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_courts',
                          data = { 'email': existing_user['email'],
                                   'requested_account_note': new_court['requested_account_note'],
                                   'create_account': True },
                          user = another_existing_user['email'],
                          success_url = reverse('court_request_response'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_court_email(mail.outbox[expected_emails_sent - 1], existing_user['email'])

    def test_new_court_failure(self):
        '''
            Does the court signup form submit as expected? Failure cases.
        '''
        # Not logged in, blank submission reports correct fields required
        self.submit_form('sign_up_courts',
                          data = {},
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # Logged in, blank submission reports same fields required
        # (This is odd; see issue 1749)
        self.submit_form('sign_up_courts',
                          data = {},
                          user = 'test_user@example.com',
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)


    ### Journals ###

    def new_journal(self):
        rand = random()
        return { 'requested_account_note': u'Journal {}'.format(rand)}

    def new_journal_user(self):
        rand = random()
        return { 'email': u'user{}@university.org'.format(rand),
                 'first': u'Joe',
                 'last': u'Yacobówski' }

    def check_journal_user_email(self, message, new_user_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_user_email).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_user_email])

    def test_new_journal_success(self):
        '''
            Does the journal signup form submit as expected? Success cases.
        '''
        new_journal = self.new_journal()
        new_user = self.new_journal_user()
        existing_user = {'email': 'test_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # New user email address + journal info
        self.submit_form('sign_up_journals',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_journal['requested_account_note']},
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_journal_user_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # LOGGED IN

        # New user email address + journal info
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_journal_user()
        self.submit_form('sign_up_journals',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_journal['requested_account_note']},
                          user = existing_user['email'],
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_journal_user_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

    def test_new_journal_failure(self):
        '''
            Does the journal signup form submit as expected? Failure cases.
        '''

        # NOT LOGGED IN

        # Blank submission reports correct fields required
        self.submit_form('sign_up_journals',
                          data = {},
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # If email address already belongs to an account, validation fails
        self.submit_form('sign_up_journals',
                          data = { 'email': 'test_user@example.com',
                                   'requested_account_note': 'Here'},
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

        # LOGGED IN
        # (This is odd; see issue 1749)

        # Blank submission reports correct fields required
        self.submit_form('sign_up_journals',
                          data = {},
                          user = 'test_user@example.com',
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # If email address already belongs to an account, validation fails
        self.submit_form('sign_up_journals',
                          data = { 'email': 'test_user@example.com',
                                   'requested_account_note': 'Here'},
                          user = 'test_user@example.com',
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)


    ### Faculty ###

    def new_faculty_user(self):
        rand = random()
        return { 'email': u'user{}@university.org'.format(rand),
                 'first': u'Joe',
                 'last': u'Yacobówski',
                 'requested_account_note': u'Journal {}'.format(rand) }

    def check_faculty_user_email(self, message, new_user_email):
        our_address = settings.DEFAULT_FROM_EMAIL

        confirmation_code = LinkUser.objects.get(email=new_user_email).confirmation_code
        confirm_url = "http://testserver{}".format(reverse('register_password', args=[confirmation_code]))
        self.assertIn(confirm_url, message.body)
        self.assertEqual(message.subject, "A Perma.cc account has been created for you")
        self.assertEqual(message.from_email, our_address)
        self.assertEqual(message.recipients(), [new_user_email])

    def test_new_faculty_success(self):
        '''
            Does the faculty signup form submit as expected? Success cases.
        '''
        new_user = self.new_faculty_user()
        existing_user = {'email': 'test_user@example.com'}
        expected_emails_sent = 0

        # NOT LOGGED IN

        # New user email address + journal info
        self.submit_form('sign_up_faculty',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_user['requested_account_note']},
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_faculty_user_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

        # LOGGED IN

        # New user email address + journal info
        # (This succeeds and creates a new account; see issue 1749)
        new_user = self.new_faculty_user()
        self.submit_form('sign_up_faculty',
                          data = { 'email': new_user['email'],
                                   'requested_account_note': new_user['requested_account_note']},
                          user = existing_user['email'],
                          success_url = reverse('register_email_instructions'))
        expected_emails_sent += 1
        self.assertEqual(len(mail.outbox), expected_emails_sent)
        self.check_faculty_user_email(mail.outbox[expected_emails_sent - 1], new_user['email'])

    def test_new_faculty_failure(self):
        '''
            Does the faculty signup form submit as expected? Failure cases.
        '''

        # NOT LOGGED IN

        # Blank submission reports correct fields required
        self.submit_form('sign_up_faculty',
                          data = {},
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # If email address already belongs to an account, validation fails
        self.submit_form('sign_up_faculty',
                          data = { 'email': 'test_user@example.com',
                                   'requested_account_note': 'Here'},
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

        # LOGGED IN
        # (This is odd; see issue 1749)

        # Blank submission reports correct fields required
        self.submit_form('sign_up_faculty',
                          data = {},
                          user = 'test_user@example.com',
                          error_keys = ['email', 'requested_account_note'])
        self.assertEqual(len(mail.outbox), 0)

        # If email address already belongs to an account, validation fails
        self.submit_form('sign_up_faculty',
                          data = { 'email': 'test_user@example.com',
                                   'requested_account_note': 'Here'},
                          user = 'test_user@example.com',
                          error_keys = ['email'])
        self.assertEqual(len(mail.outbox), 0)

    ### Individual Users ###

    def test_account_creation_views(self):
        # user registration
        new_user_email = "new_email@test.com"
        self.submit_form('sign_up', {'email': new_user_email, 'first_name': 'Test', 'last_name': 'Test'},
                         success_url=reverse('register_email_instructions'),
                         success_query=LinkUser.objects.filter(email=new_user_email))

        confirmation_code = LinkUser.objects.get(email=new_user_email).confirmation_code

        # reg confirm - non-matching passwords
        self.submit_form('register_password', reverse_kwargs={'args': [confirmation_code]},
                         data={'new_password1':'a', 'new_password2':'b'},
                         error_keys=['new_password2'])

        # reg confirm - correct
        self.submit_form('register_password', reverse_kwargs={'args': [confirmation_code]},
                         data={'new_password1': 'a', 'new_password2': 'a'},
                         success_url=reverse('user_management_limited_login'))

    def test_signup_with_existing_email_rejected(self):
        self.submit_form('sign_up',
                         {'email': self.registrar_user.email, 'first_name': 'Test', 'last_name': 'Test'},
                         error_keys=['email'])

    def test_registration_confirmation_with_bad_code_rejected(self):
        response = self.submit_form('register_password', reverse_kwargs={'args':['bad_confirmation_code']})
        self.assertTrue('no_code' in response.context)

    ### ADMIN STATS ###

    def test_admin_stats(self):
        self.log_in_user(self.admin_user)
        self.get('user_management_stats', reverse_kwargs={'args':['days']})
        self.get('user_management_stats', reverse_kwargs={'args':['celery']})
        self.get('user_management_stats', reverse_kwargs={'args':['random']})
        self.get('user_management_stats', reverse_kwargs={'args':['emails']})
        self.get('user_management_stats', reverse_kwargs={'args':['job_queue']})
