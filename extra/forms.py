from django import forms
from cams.models import Person, Contact, PersonContact
from mrwf.extra.models import StallEvent

def check_ibounds (data, name, imin, imax):
    try:
        val = int (data[name])

        if (val < imin) or (val > imax):
            raise forms.ValidationError (
                "Value out of bounds (min=%d, max=%d)" % (imin, imax))
        else:
            return val

    except ValueError:
        raise forms.ValidationError ("Invalid value for %s" % name)


class PersonForm (forms.ModelForm):
    last_name = forms.CharField (max_length = 127, required = True)

    class Meta:
        model = Person
        exclude = ['nickname', 'alter', 'status']


class PersonContactForm (forms.ModelForm):
    line_1 = forms.CharField (max_length = 63, required = True)
    town = forms.CharField (max_length = 63, required = True)
    postcode = forms.CharField (max_length = 15, required = True)
    email = forms.EmailField (max_length = 127, required = True,
                              help_text = Contact.email_help_text)

    class Meta:
        model = PersonContact
        exclude = ['status', 'person', 'addr_order', 'addr_suborder',
                   'country', 'fax']

class StallForm (forms.ModelForm):
    attrs = {'cols': '60', 'rows': '3'}
    description = forms.CharField (widget = forms.Textarea (attrs = attrs))

    class Meta:
        model = StallEvent
        fields = ('name', 'n_spaces', 'n_tables', 'main_contact',
                  'description')

    def clean_n_spaces (self):
        return check_ibounds (self.cleaned_data, 'n_spaces', 1, 3)

    def clean_n_tables (self):
        return check_ibounds (self.cleaned_data, 'n_tables', 0, 3)
