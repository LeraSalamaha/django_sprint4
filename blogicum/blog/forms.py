from django import forms
from .models import Post, Comments
from django.contrib.auth.models import User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'location', 'category', 'pub_date', 'image']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'email')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ['text']
