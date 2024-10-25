from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from .models import Post, Reply, Newsletter, Subscription, UserProfile
from .forms import PostForm, ReplyForm, NewsletterForm, SubscriptionForm, RegistrationForm


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            registration_code = get_random_string(length=32)
            user.profile.registration_code = registration_code
            user.profile.save()
            subject = 'Верификация аккаунта'
            html_message = render_to_string(
                'email/registration_confirmation.html',
                {'user': user, 'registration_code': registration_code}
            )
            send_mail(
                subject,
                '',
                'maximssshepelev@yandex.ru',
                [user.email],
                html_message=html_message,
                fail_silently=False
            )
            messages.success(request, 'Письмо с кодом верификации отправлено на ваш email.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'post/register.html', {'form': form})

def register_success(request):
    messages.success(request, 'Регистрация успешно завершена!')
    return redirect('post_list')

def verify(request, code):
    try:
        profile = UserProfile.objects.get(registration_code=code)
    except UserProfile.DoesNotExist:
        messages.error(request, 'Неверный код верификации.')
        return redirect('login')
    user = profile.user
    user.is_active = True
    user.save()
    profile.registration_code = None
    profile.is_verified = True
    profile.save()
    login(request, user)
    messages.success(request, 'Аккаунт успешно верифицирован.')
    return redirect('post_list')

def yandex_login(request):
    return redirect('social:begin', 'yandex')

def yandex_callback(request):
    user = request.user
    if not user.is_authenticated:
        user = UserSocialAuth.objects.get(provider='yandex', uid=request.session['social_auth_yandex_uid']).user
        login(request, user)
    return redirect('post_list')

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'post/post_create.html', {'form': form})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    replies = post.replies.all()
    reply_form = ReplyForm()
    return render(request, 'post/post_detail.html', {'post': post, 'replies': replies, 'reply_form': reply_form})

@login_required
def create_reply(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.author = request.user
            reply.post = post
            reply.save()
            send_reply_notification(post, reply, reply.author)
            return redirect('post_detail', pk=pk)
    return redirect('post_detail', pk=pk)

@login_required
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user != post.author:
        return redirect('post_detail', pk=pk)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('post_detail', pk=pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'post/post_edit.html', {'form': form, 'post': post})

def post_list(request):
    category = request.GET.get('category')
    if category:
        posts = Post.objects.filter(category=category)
    else:
        posts = Post.objects.all()
    categories = Post.CATEGORY_CHOICES
    return render(request, 'post/post_list.html', {'posts': posts, 'categories': categories})

@login_required
def user_profile(request):
    user = request.user
    posts = user.posts.all()
    replies = user.replies.all()
    subscriptions = user.subscriptions.all()
    return render(request, 'post/user_profile.html', {'user': user, 'posts': posts, 'replies': replies, 'subscriptions': subscriptions})

@login_required
def subscribe(request):
    if request.method == 'POST':
        form = SubscriptionForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вы успешно подписались на рассылку.')
            return redirect('user_profile')
    else:
        form = SubscriptionForm(instance=request.user)
    return render(request, 'post/subscribe.html', {'form': form})

@login_required
def manage_subscriptions(request):
    subscriptions = request.user.subscriptions.all()
    return render(request, 'post/manage_subscriptions.html', {'subscriptions': subscriptions})

@login_required
def replies(request):
    replies = request.user.replies.all()
    return render(request, 'post/replies.html', {'replies': replies})

@login_required
def filter_replies(request):
    replies = request.user.replies.all()

    is_accepted = request.GET.get('is_accepted')
    if is_accepted == 'true':
        replies = replies.filter(is_accepted=True)
    elif is_accepted == 'false':
        replies = replies.filter(is_accepted=False)

    post_id = request.GET.get('post_id')
    if post_id:
        try:
            post = Post.objects.get(pk=post_id)
            replies = replies.filter(post=post)
        except Post.DoesNotExist:
            messages.error(request, 'Объявление не найдено.')

    return render(request, 'post/filter_replies.html', {'replies': replies})

@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(Reply, pk=reply_id)
    if request.user == reply.author:
        reply.delete()
        messages.success(request, 'Отклик успешно удален.')
    return redirect('replies')

@login_required
def accept_reply(request, reply_id):
    reply = get_object_or_404(Reply, pk=reply_id)
    if request.user == reply.post.author:
        reply.is_accepted = True
        reply.save()
        send_accept_reply_notification(reply.post, reply, reply.author)
        messages.success(request, 'Отклик принят.')
    return redirect('replies')

def send_reply_notification(post, reply, reply_author):
    author = post.author
    if author.email:
        subject = f'Новый отклик на ваше объявление "{post.title}"'
        html_message = render_to_string(
            'email/reply_notification.html',
            {'post': post, 'reply': reply, 'reply_author': reply_author}
        )
        send_mail(
            subject,
            '',
            'maximssshepelev@yandex.ru',
            [author.email],
            html_message=html_message,
            fail_silently=False
        )

def send_accept_reply_notification(post, reply, reply_author):
    if reply_author.email:
        subject = f'Ваш отклик на объявление "{post.title}" принят!'
        html_message = render_to_string(
            'email/accept_reply_notification.html',
            {'post': post, 'reply': reply, 'reply_author': reply_author}
        )
        send_mail(
            subject,
            '',
            'maximssshepelev@yandex.ru',
            [reply_author.email],
            html_message=html_message,
            fail_silently=False
        )

def logout_view(request):
    logout(request)
    return redirect('post_list')

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Вы успешно вошли в систему как {username}")
                return redirect('user_profile')
            else:
                messages.error(request, "Неверный логин или пароль")
    else:
        form = AuthenticationForm()
    return render(request, 'post/login.html', {'form': form})

@login_required
def my_posts(request):
    user = request.user
    posts = user.posts.all()
    return render(request, 'post/my_posts.html', {'posts': posts})

@login_required
def send_newsletter(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            newsletter = form.save()
            send_newsletter_notification(newsletter)
            messages.success(request, 'Рассылка успешно отправлена.')
            return redirect('user_profile')
    else:
        form = NewsletterForm()
    return render(request, 'post/send_newsletter.html', {'form': form})

def send_newsletter_notification(newsletter):
    subscriptions = newsletter.subscriptions.all()
    for subscription in subscriptions:
        user = subscription.user
        if user.email:
            subject = newsletter.subject
            html_message = render_to_string(
                'email/newsletter.html',
                {'newsletter': newsletter}
            )
            send_mail(
                subject,
                '',
                'maximssshepelev@yandex.ru',
                [user.email],
                html_message=html_message,
                fail_silently=False
            )