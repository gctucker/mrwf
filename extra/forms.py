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
        exclude = ['alter', 'status']


class OrganisationForm(forms.ModelForm):
    class Meta(object):
        model = Organisation
        exclude = ['status', 'members']


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
    tombola_gift = \
        forms.BooleanField(widget=forms.CheckboxInput(
            attrs={'onChange': 'update_tombola_desc(this);'}), required=False)
    tombola_description = \
        forms.CharField(widget=forms.Textarea(attrs=_attrs), required=False)
    _stall_type_attrs = { 'onChange': 'update_stall_type(this);' }
    stall_type = \
        forms.ChoiceField(choices=((MARKET_STALL_PK, "Market & Craft"),
                                   (FOOD_FAIR_PK, "Food Fair")),
                          widget=forms.Select(attrs=_stall_type_attrs))

    class Meta(object):
        model = StallEvent
        fields = ('name', 'org_name', 'description', 'n_spaces',
                  'main_contact', 'extra_web_contact', 'comments',
                  'plot_type', 'media_usage', 'infrastructure', 'tombola_gift',
                  'tombola_description', 'stall_type')

    def clean_n_spaces(self):
        return check_ibounds(self.cleaned_data, 'n_spaces', 1, 3)

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
            self._check_required('n_spaces')
            del self.cleaned_data['plot_type']
            elf.cleaned_data['infrastructure'] = ''
            del self.cleaned_data['tombola_gift']
            elf.cleaned_data['tombola_description'] = ''
        elif stall_type_pk == StallForm.FOOD_FAIR_PK:
            self._check_required('plot_type')
            self._check_required('infrastructure')
            if self._check_true('tombola_gift'):
                self._check_required('tombola_description')
            else:
                self.cleaned_data['tombola_description'] = ''
            del self.cleaned_data['n_spaces']
        else:
            self._errors['stall_type'] = self.error_class(
                ["Invalid stall type"])
            del self.cleaned_data['stall_type']
        return self.cleaned_data
