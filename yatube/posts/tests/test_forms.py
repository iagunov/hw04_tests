from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текст',
            pub_date='14.07.2022',
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.form = PostForm()

    def test_create_post(self):
        """Валидная форма создает запись в Posts."""
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        form_data = {
            'text': 'Тестовый текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': 'author'}
            )
        )
        self.assertEqual(Post.objects.count(), 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )

    def test_edit_post(self):
        """Измененный Post записывается в базу."""
        update_url = reverse('posts:post_edit', args=('1',))
        response = self.authorized_client.get(update_url)

        form = response.context['form']
        data = form.initial
        data['text'] = 'Новый тестовый текст'

        self.authorized_client.post(update_url, data)
        self.authorized_client.get(update_url)
        self.assertTrue(
            Post.objects.filter(
                text='Новый тестовый текст',
            ).exists()
        )
