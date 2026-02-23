def amend_template(request, template_id):
    existing = BMADTemplate.objects.get(id=template_id)
    if request.method == 'POST':
        # Logic to update JSONField 'sections' based on new user input
        new_sections = {k: v for k, v in request.POST.items() if k != 'csrfmiddlewaretoken'}
        existing.sections = new_sections
        existing.save()
        # Redirect to generation