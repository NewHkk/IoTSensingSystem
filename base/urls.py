from django.urls import path
from . import views

urlpatterns = [
    path('', views.loginPage, name="login"),
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('home/', views.home, name="home"),
    path('makepost/', views.test_makepost, name="makepost"),
    path('node_charts/<str:pk>', views.nodechartsPage, name="node_charts"),
    path('time_charts/<str:node_id>/<str:datatype>', views.nodeLinechartsPage, name="node_time_charts"),

    path('line/<str:node_id>/<str:dataname>', views.LineView.as_view(), name="node_chart_line"),

    path('gauge/<str:pk>/<str:dataname>', views.GaugeView.as_view(), name='node_charts_gauge'),
    path('getpost/', views.get_save_msg, name="getpost"),

    path('exportCSV/<str:node_id>', views.exportCSV, name='exportCSV'),
    path('offline/<str:node_id>', views.offline, name='offline'),
    path('abnormal/<str:node_id>', views.abnormal, name='abnormal'),

    path('sendemail/', views.send_email, name='sendemail')

]