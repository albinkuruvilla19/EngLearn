from django.shortcuts import render
from .forms import CustomUserForm
from django.contrib.auth import authenticate,logout
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render,HttpResponse
from .models import *
from django.db.models import Sum, Avg, F
# Create your views here.
def index(request):
    return render(request,'index.html')

def features(request):
    return render(request,'features.html')

def dictionary(request):
    return render(request,'dictionary.html')

def spell(request):
    return render(request,'spell.html')

def lessons(request):
    lessons = Lesson.objects.all()
    completed_lessons = LessonCompletion.objects.filter(user=request.user).values_list('lesson_id', flat=True)
    return render(request,'lesson.html',{"lessons":lessons,"completed_lessons":completed_lessons})

# views.py
from django.shortcuts import render, get_object_or_404
from .models import Lesson

def lesson_detail(request, id):
    lesson = get_object_or_404(Lesson, id=id)
    sections = LessonSection.objects.filter(lesson=lesson).order_by('order')
    completed_lessons = LessonCompletion.objects.filter(user=request.user).values_list('lesson_id', flat=True)
    return render(request, 'lesson_detail.html', {'lesson': lesson, 'sections': sections, "completed_lessons":completed_lessons})



from django.shortcuts import render
from django.http import JsonResponse
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()


# Configure API key directly
API_KEY = os.getenv('API_KEY')
genai.configure(api_key=API_KEY)

# Initialize model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="Alice, as an English tutor, should focus on improving users' English proficiency through interactive and scenario-based conversations. Engage users in realistic dialogues, such as daily conversations or professional interactions, and provide feedback on grammar, vocabulary, and sentence structure. Avoid theoretical explanations; instead, offer practical examples and corrections within the conversation. Encourage users to use varied sentence structures and vocabulary, provide positive reinforcement, and track their progress to address common errors effectively.",
)

chat_session = model.start_chat(
    history=[
        {"role": "user", "parts": ["hi"]},
        
    ]
)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def chat_view(request):
    if request.method == 'POST':
        user_message = request.POST.get('message')
        response = chat_session.send_message(user_message)
        return JsonResponse({'response': response.text})

    return render(request, 'chat.html')



def register(request):
    form = CustomUserForm
    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"Registration success. Login now!!!")
            return redirect('/login')
    return render(request,"register.html",{"form":form})

def loginpage(request):
    if request.method == 'POST':
        name = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=name, password=pwd)

        if user is not None:
            auth_login(request, user)
            
            if user.is_superuser:
                messages.success(request, "Superuser logged in successfully")
                return redirect('index')
            else:
                messages.success(request, "Logged in successfully")
                return redirect("index")
        else:
            messages.error(request, "Invalid Username or password")
            return redirect('login')

    return render(request, "login.html")

def logout_view(request):
    # Use the built-in logout function to log the user out
    logout(request)
    return redirect('login')


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Topic, Quiz, Question, Option, UserQuizScore

# View for listing topics
def topic_list(request):
    topics = Topic.objects.all()
    return render(request, 'topic_list.html', {'topics': topics})

# View for listing quizzes based on a selected topic
@login_required
def quiz_list(request, topic_id):
    topic = get_object_or_404(Topic, pk=topic_id)
    quizzes = Quiz.objects.filter(topic=topic)
    user_quiz_scores = UserQuizScore.objects.filter(user=request.user, quiz__in=quizzes)

    # Create a dictionary to check which quizzes the user has completed
    completed_quizzes = {score.quiz_id: score for score in user_quiz_scores}

    return render(request, 'quiz_list.html', {
        'topic': topic,
        'quizzes': quizzes,
        'completed_quizzes': completed_quizzes,
    })
# View for attending a quiz

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz, Question, Option, UserQuizScore

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Quiz, Option, UserQuizScore

@login_required
def quiz_detail(request, quiz_id, question_number=1):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    questions = quiz.question_set.all()
    total_questions = questions.count()

    # Redirect if the question_number is out of range
    if question_number < 1 or question_number > total_questions:
        return redirect('quiz_detail', quiz_id=quiz_id, question_number=1)

    current_question = questions[question_number - 1]

    # Check if the user has already completed the quiz
    user_quiz_score = UserQuizScore.objects.filter(user=request.user, quiz=quiz).first()
    if user_quiz_score:
        return redirect('quiz_result', quiz_id=quiz_id)

    if request.method == 'POST':
        selected_option_id = request.POST.get(f'question-{current_question.id}')
        if selected_option_id:
            selected_option = get_object_or_404(Option, id=selected_option_id)
            if selected_option.is_correct:
                request.session[f'quiz_{quiz_id}_score'] = request.session.get(f'quiz_{quiz_id}_score', 0) + 1

        # Move to the next question or finish the quiz
        if question_number < total_questions:
            return redirect('quiz_detail', quiz_id=quiz_id, question_number=question_number + 1)
        else:
            final_score = request.session.pop(f'quiz_{quiz_id}_score', 0)
            UserQuizScore.objects.update_or_create(
                user=request.user, quiz=quiz,
                defaults={'score': final_score}
            )
            return redirect('quiz_result', quiz_id=quiz_id)

    return render(request, 'quiz_detail.html', {
        'quiz': quiz,
        'current_question': current_question,
        'question_number': question_number,
        'total_questions': total_questions
    })



# View for displaying the quiz result


@login_required
def quiz_result(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    user_score = get_object_or_404(UserQuizScore, user=request.user, quiz=quiz)
    total_possible_score = quiz.question_set.count()

    # Retrieve all questions and their correct answers
    questions = quiz.question_set.all().prefetch_related('options')
    answers = {
        question.id: question.options.filter(is_correct=True).first() for question in questions
    }

    # Retrieve user's answers
    user_answers = {
        question.id: question.options.filter(useranswer__user=request.user).first() for question in questions
    }

    return render(request, 'quiz_result.html', {
        'quiz': quiz,
        'user_score': user_score,
        'total_possible_score': total_possible_score,
        'questions': questions,
        'answers': answers,
        'user_answers': user_answers,
    })




from django.shortcuts import render
from .forms import SpellCheckForm
import language_tool_python

def check_spelling(request):
    original_text = None
    highlighted_text = None
    suggestions = []

    if request.method == 'POST':
        form = SpellCheckForm(request.POST)
        if form.is_valid():
            original_text = form.cleaned_data['text']

            # Initialize the language tool
            tool = language_tool_python.LanguageTool('en-US')

            # Check the text for spelling and grammar mistakes
            matches = tool.check(original_text)

            # Initialize a variable to build the highlighted text
            highlighted_text = original_text
            offset = 0

            for match in matches:
                # Use start and end offsets from the match object
                start = match.offset
                end = match.offset + match.errorLength
                error = original_text[start:end]
                highlighted_text = (
                    highlighted_text[:start + offset] +
                    f"<span style='color:red;'>{error}</span>" +
                    highlighted_text[end + offset:]
                )
                offset += len(f"<span style='color:red;'>{error}</span>") - len(error)
                
                # Store suggestions for each error
                suggestions.append({
                    'error': error,
                    'suggestions': match.replacements
                })

    else:
        form = SpellCheckForm()

    return render(request, 'spell.html', {
        'form': form,
        'original_text': original_text,
        'highlighted_text': highlighted_text,
        'suggestions': suggestions,
    })






from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F

@login_required
def profile_view(request):
    user = request.user
    quiz_scores = UserQuizScore.objects.filter(user=user)  # Fetch user's quiz scores
    user_profile = UserProfile.objects.get(user=request.user)

    # Calculate total skillup points for the current user
    user_total_skillup_points = UserQuizScore.objects.filter(user=user).aggregate(
        total_skillup_points=Sum(F('score') * 10)
    )['total_skillup_points'] or 0

    # Calculate total skillup points for each user and rank them
    user_skillup_points = (
        UserQuizScore.objects.values('user__username')
        .annotate(total_skillup_points=Sum(F('score') * 10))
        .order_by('-total_skillup_points')
    )

    # Add ranks to the users
    ranked_users = list(enumerate(user_skillup_points, start=1))

    # Get the average total skillup points for all users
    average_total_skillup_points = UserQuizScore.objects.aggregate(
        average_skillup_points=Sum(F('score') * 10) / UserProfile.objects.count()
    )['average_skillup_points'] or 0

    # Get the count of completed lessons by the current user
    completed_lessons_count = LessonCompletion.objects.filter(user=user).count()

    context = {
        'user': user,
        'quiz_scores': quiz_scores,
        'total_skillup_points': user_total_skillup_points,
        'login_streak': user_profile.login_streak,  # Pass login streak to the template
        'ranked_scores': ranked_users,
        'user_total_skillup_points': user_total_skillup_points,
        'average_total_skillup_points': average_total_skillup_points,
        'completed_lessons_count': completed_lessons_count,
    }

    return render(request, 'user_dash.html', context)



from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Lesson, LessonCompletion

@login_required
def complete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Check if the lesson has already been completed by the user
    if not LessonCompletion.objects.filter(user=request.user, lesson=lesson).exists():
        # Mark the lesson as completed
        LessonCompletion.objects.create(user=request.user, lesson=lesson)

    # Redirect to a success page or back to the lessons list
    return redirect('lessons')  # Update this to your actual lessons list URL


from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile

@receiver(user_logged_in)
def update_login_streak(sender, request, user, **kwargs):
    user_profile, created = UserProfile.objects.get_or_create(user=user)
    today = timezone.now().date()

    if user_profile.last_login_date:
        # Check if the user logged in yesterday
        if user_profile.last_login_date == today - timezone.timedelta(days=1):
            # Increment the streak
            user_profile.login_streak += 1
        # If the user logs in today after missing a day, reset the streak
        elif user_profile.last_login_date < today - timezone.timedelta(days=1):
            user_profile.login_streak = 1
    else:
        # First login or the first login after creating the profile
        user_profile.login_streak = 1

    # Update last login date
    user_profile.last_login_date = today
    user_profile.save()


from django.shortcuts import render
from .models import UserProfile

def streak(request):
    user_profile = UserProfile.objects.get(user=request.user)
    return render(request, 'streak.html', {'login_streak': user_profile.login_streak})




from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
from .models import Quiz, UserQuizScore, UserAnswer

@login_required
def download_quiz_pdf(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    user_score = get_object_or_404(UserQuizScore, user=request.user, quiz=quiz)

    # Create a byte stream buffer
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Define the width and height of the page
    width, height = letter

    # Set the title for the PDF
    p.setTitle(f"{quiz.name} - Results")

    # Set the starting Y position
    y_position = height - 50

    # Write the quiz name and user's score at the top of the PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y_position, f"Quiz: {quiz.name}")
    y_position -= 30
    p.setFont("Helvetica", 12)
    p.drawString(50, y_position, f"User: {request.user.username}")
    y_position -= 20
    p.drawString(50, y_position, f"Score: {user_score.score}/{quiz.question_set.count()}")
    y_position -= 30

    # Retrieve all questions and their correct answers
    questions = quiz.question_set.all().prefetch_related('options')
    for idx, question in enumerate(questions, start=1):
        # Write the question text
        p.drawString(50, y_position, f"Q{idx}: {question.question_text}")
        y_position -= 20

        # Retrieve the correct answer
        correct_option = question.options.filter(is_correct=True).first()
        if correct_option:
            p.drawString(60, y_position, f"Answer: {correct_option.option_text}")
            y_position -= 20

        # Check if user's answer was correct or not
        user_answer = UserAnswer.objects.filter(user=request.user, question=question).first()
        if user_answer:
            if user_answer.selected_option == correct_option:
                p.setFillColorRGB(0, 0.6, 0)  # Green color for correct answer
            else:
                p.setFillColorRGB(1, 0, 0)  # Red color for wrong answer
            p.drawString(60, y_position, f"Your Answer: {user_answer.selected_option.option_text}")
            p.setFillColorRGB(0, 0, 0)  # Reset to default black color
            y_position -= 20

        # Add space between questions
        y_position -= 10

        # Create a new page if the y_position is too low
        if y_position < 100:
            p.showPage()
            y_position = height - 50

    # Finalize and save the PDF file
    p.showPage()
    p.save()

    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()

    # Create the response and set the content type to PDF
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{quiz.name}_result.pdf"'

    return response

import calendar
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth.decorators import login_required







