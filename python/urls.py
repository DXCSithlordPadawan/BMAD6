from django.urls import path
from . import views

urlpatterns = [
    # List all available BMAD templates (e.g., SDR Agent, Research Doc)
    path('', views.TemplateListView.as_view(), name='template_list'),
    
    # The guided interview for a specific template
    path('guide/<int:template_id>/', views.guide_user_view, name='bmad_guide'),
    
    # The sharding engine trigger
    path('generate-shards/<int:template_id>/', views.generate_sharded_bmad, name='generate_shards'),
    
    # The Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # The Download Zip
    path('download/<str:agent_name>/', views.download_agent_zip, name='download_zip'),
    
    # Amend an existing template structure
    path('amend/<int:template_id>/', views.amend_template, name='amend_template'),
]