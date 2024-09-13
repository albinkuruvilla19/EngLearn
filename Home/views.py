from django.shortcuts import render
from .forms import CustomUserForm
from django.contrib.auth import authenticate,logout
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render,HttpResponse
from .models import *
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
    return render(request,'lesson.html')

def tenses(request):
    return render(request,'tenses.html')

def nouns(request):
    return render(request,'nouns.html')


from django.shortcuts import render
from django.http import JsonResponse
import google.generativeai as genai

import google.generativeai as genai

# Configure API key directly
api_key = "AIzaSyCThnASZ53viHUOfF7sqIBcc2-hBNLfZyw"
genai.configure(api_key=api_key)

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
                return redirect('view')
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

    return render(request, 'quiz_result.html', {
        'quiz': quiz,
        'user_score': user_score,
        'total_possible_score': total_possible_score,
        'questions': questions,
        'answers': answers,
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
