# models.py
from django.db import models

class BMADTemplate(models.Model):
    name = models.CharField(max_length=100)
    # Stores section titles and their default content
    sections = models.JSONField(default=dict) 
    is_agent = models.BooleanField(default=False) # Toggle between agent.md and doc.md

# forms.py
from django import forms

class SectionInputForm(forms.Form):
    # This form is generated dynamically in the view based on the template
    def __init__(self, *args, **kwargs):
        sections = kwargs.pop('sections')
        super().__init__(*args, **kwargs)
        for key, value in sections.items():
            self.fields[key] = forms.CharField(
                widget=forms.Textarea, 
                initial=value,
                required=False
            )