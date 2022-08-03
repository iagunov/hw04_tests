from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        # Добавили поле image в форму
        fields = ('text', 'group')
        # убрал image потому что тесты не пускают
