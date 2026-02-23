import os
import yaml
from django.shortcuts import render
from django.template import Template, Context
from .forms import SectionInputForm
from .models import BMADTemplate

def guide_user_view(request, template_id):
    # 1. Load Global Config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)['app_settings']

    template_obj = BMADTemplate.objects.get(id=template_id)
    
    if request.method == 'POST':
        form = SectionInputForm(request.POST, sections=template_obj.sections)
        if form.is_valid():
            # 2. Build the Markdown Document
            context_data = form.cleaned_data
            context_data['app_title'] = config['application_title']
            
            # Construct the Markdown String
            md_content = f"# {template_obj.name}\n\n"
            for section, content in form.cleaned_data.items():
                md_content += f"## {section.replace('_', ' ').title()}\n{content}\n\n"
            
            # 3. Export File
            file_name = f"{template_obj.name.lower().replace(' ', '_')}.md"
            save_path = os.path.join(config['base_location'], file_name)
            
            os.makedirs(config['base_location'], exist_ok=True)
            with open(save_path, 'w') as f:
                f.write(md_content)
                
            return render(request, 'success.html', {'path': save_path})
    else:
        form = SectionInputForm(sections=template_obj.sections)

    return render(request, 'guide.html', {'form': form, 'config': config})

def generate_bmad_document(user_data):
    # 1. Load your separate YAML config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 2. Your BMAD v6 Markdown Template
    # This can be loaded from a .md file in your /templates/ folder
    raw_template = """
    # Agent: {{ name }}
    **Role:** {{ role_description }}
    
    ## Workflow
    {% for step in steps %}
    - [ ] {{ step }}
    {% endfor %}
    
    ---
    *Generated via {{ app_title }}*
    """

    # 3. Render using Django Context
    t = Template(raw_template)
    c = Context({
        "name": user_data['name'],
        "role_description": user_data['role'],
        "steps": user_data['steps'],
        "app_title": config['app_settings']['title']
    })
    
    rendered_md = t.render(c)
    
    # 4. Save to the base_location from YAML
    file_path = f"{config['app_settings']['base_dir']}{user_data['name']}.md"
    with open(file_path, "w") as f:
        f.write(rendered_md)

def dashboard_view(request):
    config = get_bmad_config()
    base_path = config.get('base_location', './bmad_output/')
    
    # List all folders in the output directory
    if os.path.exists(base_path):
        agents = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    else:
        agents = []
        
    return render(request, 'dashboard.html', {'agents': agents, 'config': config})

def download_agent_zip(request, agent_name):
    config = get_bmad_config()
    agent_dir = os.path.join(config.get('base_location'), agent_name)
    
    # Create a temporary ZIP file of the agent's sharded directory
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # shutil.make_archive adds the .zip extension automatically
        zip_path = shutil.make_archive(tmp.name, 'zip', agent_dir)
        
    # Serve the file back to the user
    response = FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=f"{agent_name}.zip")
    return response

def generate_sharded_bmad(request, template_id):
    # Load YAML Config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)['app_settings']

    if request.method == 'POST':
        # Collect data from form
        data = request.POST.dict()
        agent_name = data.get('agent_name', 'Unnamed_Agent').replace(" ", "_")
        
        # Create a dedicated directory for this agent's shards
        agent_dir = os.path.join(config['base_location'], agent_name)
        os.makedirs(agent_dir, exist_ok=True)

        # 1. Generate individual Step Files (Shards)
        steps_manifest = []
        for i, (section_title, content) in enumerate(data.items()):
            if section_title in ['csrfmiddlewaretoken', 'agent_name']: continue
            
            step_filename = f"step-{i:02d}_{section_title}.md"
            step_path = os.path.join(agent_dir, step_filename)
            
            with open(step_path, 'w') as f:
                f.write(f"# {section_title.replace('_', ' ').title()}\n{content}")
            
            steps_manifest.append(step_filename)

        # 2. Generate the Master Agent File (The Controller)
        master_content = f"""# Agent: {agent_name} {config['icon']}
## Overview
This agent is managed by {config['application_title']}.

## Sharded Workflow
{% for step in steps %}
- [ ] {{ step }}
{% endfor %}
"""
        # Render Master with Django Template engine for variables
        from django.template import Template, Context
        master_template = Template(master_content)
        final_agent_md = master_template.render(Context({'steps': steps_manifest}))

        with open(os.path.join(agent_dir, "agent.md"), 'w') as f:
            f.write(final_agent_md)

        return render(request, 'success.html', {'dir': agent_dir})