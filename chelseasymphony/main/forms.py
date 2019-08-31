"""Django Forms"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import NewMemberRequest


class NewMemberRequestForm(forms.ModelForm):
    """ModelForm for new member requests"""
    class Meta:
        model = NewMemberRequest
        fields = [
            'first_name', 'last_name', 'email', 'instrument',
            'resume', 'source', 'link', 'read_policies'
        ]
        labels = {
            'source': _('How did you hear about hear about TCS?:'),
            'link': _(
                'If you would like to include a sample of your playing '
                'on YouTube, Spotify, etc.), please provide a URL here.'
            ),
            'read_policies': _('I have read the TCS policies and understand '
                               'that the orchestra\'s regular series concerts '
                               'are not compensated.')
        }

    def clean_read_policies(self):
        """Validate that user has checked box indicating that they've read
        the orchestra's policies"""
        read_policies = self.cleaned_data.get('read_policies')
        if not read_policies:
            raise forms.ValidationError('Please confirm that you have '
                                        'read TCS\'s policies.')

        return read_policies
