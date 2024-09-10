from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.login_view, name='login'),  # Custom login page as the default home page
    path('home/', views.home, name='home'),  # Home page
    path('calculate/', views.calculate_fees_view, name='calculate_fees'),  # Calculate page
    path('fees-dollars/', views.view_fees_dollars, name='view_fees_dollars'),  # Fees Dollars page
    path('download-fees/', views.download_fees, name='download_fees'),  # Download Fees page
    path('upload-fees/', views.upload_fees, name='upload_fees'),  # Upload Fees page
    path('bulk_download/', views.bulk_download, name='bulk_download'),  # Bulk download
    path('gpt-categorize/', views.gpt_categorize_view, name='gpt_categorize'),  # GPT page
    path('gpt-craft/', views.gpt_craft_view, name='gpt_craft'),  # GPT page
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),  # Custom logout view
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
