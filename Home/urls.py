from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('',index,name="index"),
    path('features/',features,name="features"),
    path('dictionary/',dictionary,name="dictionary"),
    path('spell/',check_spelling,name="spell"),
    path('lesson/',lessons,name="lessons"),
    path('chat/', chat_view, name='chat'),
    path('register/',register,name="register"),
    path('login/',loginpage,name="login"),
    path('logout/',logout_view, name='logout'),
    path('topic', topic_list, name='topic_list'),
    path('topic/<int:topic_id>/quizzes/', quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/<int:question_number>/',quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/result/',quiz_result, name='quiz_result'),
    path('lesson/<int:id>/', lesson_detail, name='lesson_detail'),
    path('profile/',profile_view,name="profile"),
    path('lesson/<int:lesson_id>/complete/', complete_lesson, name='complete_lesson'),
    path('quiz/<int:quiz_id>/download-pdf/', download_quiz_pdf, name='download_quiz_pdf'),

    
]
