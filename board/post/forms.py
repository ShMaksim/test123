from django import forms
from .models import Post, Reply, Newsletter, Subscription
from ckeditor.widgets import CKEditorWidget
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile
from django.contrib.auth.models import User

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = False
        if commit:
            user.save()
        profile = UserProfile.objects.create(user=user)
        return user
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image1', 'image2', 'video1', 'video2', 'category']
        widgets = {
            'content': CKEditorWidget(),
        }

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']

class NewsletterForm(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = ['subject', 'content']

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['newsletter']