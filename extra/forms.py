from django import forms
from django.contrib.auth.models import User
from cams.models import Record, Person, Organisation, Contact
from mrwf.extra.models import StallEvent

def check_ibounds(data, name, imin, imax):
    try:
        val = int(data[name])
        if (val < imin) or (val > imax):
            raise forms.ValidationError(
                'Value out of bounds (min={0}, max={1})'.format(imin, imax))
        else:
            return val
    except ValueError:
        raise forms.ValidationError('Invalid value for {0}'.format(name))


class UserNameForm(forms.ModelForm):
    class Meta(object):
        model = User
        fields = ['username', 'email']


class PersonForm(forms.ModelForm):
    last_name = forms.CharField(max_length=127, required=True)

    class Meta(object):
        model = Person
        exclude = ['alter', 'status']


class OrganisationForm(forms.ModelForm):
    class Meta(object):
        model = Organisation
        exclude = ['status', 'members']


class ContactForm(forms.ModelForm):
    email = forms.EmailField(max_length=127, help_text=Contact.email_help_text,
                             label="E-mail address", required=False)

    @property
    def is_empty(self):
        for f in self:
            if f.value():
                return False
        return True

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
    attrs = {'cols': '60', 'rows': '3'}
    description = forms.CharField(widget=forms.Textarea(attrs=attrs))

    class Meta(object):
        model = StallEvent
        fields = ('name', 'n_spaces', 'n_tables', 'main_contact','description')

    def clean_n_spaces(self):
        return check_ibounds(self.cleaned_data, 'n_spaces', 1, 3)

    def clean_n_tables(self):
        return check_ibounds(self.cleaned_data, 'n_tables', 0, 3)
