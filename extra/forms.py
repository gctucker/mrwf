# MRWF - extra/forms.py
#
# Copyright (C) 2009, 2010, 2011. 2012, 2013
# Guillaume Tucker <guillaume@mangoz.org>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

from django import forms
from django.contrib.auth.models import User
from cams.models import Record, Person, Organisation, Contact
from mrwf.extra.models import StallEvent

def check_ibounds(data, name, imin, imax):
    val = data[name]
    if val is None:
        return None
    try:
        ival = int(val)
        if (ival < imin) or (ival > imax):
            raise forms.ValidationError(
                'Value out of bounds (min={0}, max={1})'.format(imin, imax))
        else:
            return val
    except ValueError:
        raise forms.ValidationError('Invalid value for {0}'.format(name))


class IsEmptyMixin(object):
    def is_empty(self):
        for f in self:
            if f.value():
                return False
        return True


class UserNameForm(forms.ModelForm):
    class Meta(object):
        model = User
        fields = ['username', 'email']


class PersonForm(forms.ModelForm, IsEmptyMixin):
    last_name = forms.CharField(max_length=127, required=True)

    class Meta(object):
        model = Person
        exclude = ['alter', 'status', 'basic_name']


class OrganisationForm(forms.ModelForm):
    class Meta(object):
        model = Organisation
        exclude = ['status', 'members', 'basic_name']


class ContactForm(forms.ModelForm, IsEmptyMixin):
    email = forms.EmailField(max_length=127, help_text=Contact.email_help_text,
                             label="E-mail address", required=False)

    class Meta(object):
        model = Contact
        exclude = ['status', 'person', 'addr_order', 'addr_suborder',
                   'country', 'fax']


class ApplicationContactForm(ContactForm):
    line_1 = forms.CharField(max_length=63, required=True)
    town = forms.CharField(max_length=63, required=True)
    postcode = forms.CharField(max_length=15, required=True)
    email = forms.EmailField(max_length=127, required=True,
                             help_text=Contact.email_help_text,
                             label="E-mail address")


class ConfirmForm(forms.Form):
    confirm = forms.CharField(initial='confirm', widget=forms.HiddenInput)

    def is_valid(self):
        return super(ConfirmForm, self).is_valid()

    def clean_confirm(self):
        if self.cleaned_data['confirm'] != 'confirm':
            raise forms.ValidationError('Failded to confirm')
        return self.cleaned_data


class StatusForm(forms.Form):
    status = forms.TypedChoiceField(coerce=int, empty_value=None,
                                    initial=Record.ACTIVE,
                                    choices=Record.xstatus)



class StallForm(forms.ModelForm):
    # ToDo: do not hard-code this (take from database)
    MARKET_STALL_PK = 1
    FOOD_FAIR_PK = 2

    _attrs = {'cols': '60', 'rows': '3'}
    org_name = forms.CharField(max_length=128, required=False)
    description = forms.CharField(widget=forms.Textarea(attrs=_attrs))
    comments = \
        forms.CharField(widget=forms.Textarea(attrs=_attrs), required=False)
    extra_web_contact = \
        forms.CharField(widget=forms.Textarea(attrs=_attrs), required=False)
    infrastructure = \
        forms.CharField(widget=forms.Textarea(attrs=_attrs), required=False)
    _stall_type_attrs = { 'onchange': 'on_stall_type_change(this);' }
    stall_type = \
        forms.ChoiceField(choices=((0, '-- PLEASE SELECT A STALL TYPE --'),
                                   (MARKET_STALL_PK, "Market & Craft"),
                                   (FOOD_FAIR_PK, "Food Fair")),
                          widget=forms.Select(attrs=_stall_type_attrs))
    food_safety_read = \
        forms.BooleanField(widget=forms.CheckboxInput(), required=False)

    class Meta(object):
        model = StallEvent
        fields = ('name', 'org_name', 'description', 'mc_stall_option',
                  'main_contact', 'extra_web_contact', 'comments',
                  'plot_type', 'media_usage', 'infrastructure', 'stall_type',
                  'food_safety_read')

    def clean_n_spaces(self):
        return check_ibounds(self.cleaned_data, 'n_spaces', 1, 2)

    def clean_n_tables(self): # ToDo: deprecate... or make dynamic
        #return check_ibounds(self.cleaned_data, 'n_tables', 0, 3)
        return None

    def _check_required(self, f):
        if f in self.cleaned_data and (self.cleaned_data[f] is None
                                       or self.cleaned_data[f] == ''):
            self._errors[f] = self.error_class([u"This field is required."])
            del self.cleaned_data[f]

    def _check_true(self, f):
        return f in self.cleaned_data and self.cleaned_data[f]

    def clean(self):
        self.cleaned_data = super(StallForm, self).clean()
        stall_type_pk = int(self.cleaned_data['stall_type'])
        if stall_type_pk == StallForm.MARKET_STALL_PK:
            self._check_required('mc_stall_option')
            del self.cleaned_data['plot_type']
            self.cleaned_data['infrastructure'] = ''
        elif stall_type_pk == StallForm.FOOD_FAIR_PK:
            self._check_required('plot_type')
            self._check_required('infrastructure')
            if not self._check_true('food_safety_read'):
                self._errors['food_safety_read'] = self.error_class(
                    [u"Please read the document and tick this box."])
            del self.cleaned_data['mc_stall_option']
        else:
            self._errors['stall_type'] = self.error_class(
                ["Please select a valid stall type"])
            del self.cleaned_data['stall_type']
        return self.cleaned_data
