from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Topic)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(UserQuizScore)
admin.site.register(Lesson)
admin.site.register(LessonSection)
admin.site.register(UserAnswer)
admin.site.register(LessonCompletion)
admin.site.register(UserProfile)