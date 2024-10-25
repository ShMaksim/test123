from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_post, name='create_post'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    path('<int:pk>/reply/', views.create_reply, name='create_reply'),
    path('<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('', views.post_list, name='post_list'),
    path('register/', views.register, name='register'),
    path('register/success/', views.register_success, name='register_success'),
    path('verify/<str:code>/', views.verify, name='verify'),
    path('yandex_login/', views.yandex_login, name='yandex_login'),
    path('yandex_callback/', views.yandex_callback, name='yandex_callback'),
    path('profile/', views.user_profile, name='user_profile'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('subscriptions/', views.manage_subscriptions, name='manage_subscriptions'),
    path('replies/', views.replies, name='replies'),
    path('replies/filter/', views.filter_replies, name='filter_replies'),
    path('replies/delete/<int:reply_id>/', views.delete_reply, name='delete_reply'),
    path('replies/accept/<int:reply_id>/', views.accept_reply, name='accept_reply'),
    path('logout/', views.logout_view, name='logout'),
    path('my_posts/', views.my_posts, name='my_posts'),
    path('subscriptions/', views.manage_subscriptions, name='manage_subscriptions'),
]