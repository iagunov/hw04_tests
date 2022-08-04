from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='новая тестовая группа',
            slug='new_test_slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group_1,
            text='Тестовый текст',
            pub_date='14.07.2022',
            image=uploaded,
        )

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.guest = Client()
        cls.form = PostForm()

    def test_edit_post(self):
        """Измененный Post записывается в базу."""
        update_url = reverse('posts:post_edit', args=('1',))

        # не авторизированный юзер при попытке
        # получить пост получает 302 redirect
        response_guest = self.guest.get(update_url)
        self.assertEqual(response_guest.status_code, HTTPStatus.FOUND)
        # количество постов осталось прежним 1
        self.assertEqual(Post.objects.count(), 1)

        # авторизированный пользователь получает страницу
        # и через форму пушит новый текст
        response_auth = self.authorized_client.get(update_url)
        form = response_auth.context['form']
        data = form.initial
        data['text'] = 'Новый тестовый текст'

        self.authorized_client.post(update_url, data)
        self.authorized_client.get(update_url)

        self.assertTrue(
            Post.objects.filter(
                text='Новый тестовый текст',
            ).exists()
        )
        # авторизированный пользователь меняет группу
        # так же через форму
        response_auth = self.authorized_client.get(update_url)
        form = response_auth.context['form']
        data = form.initial
        data['group'] = 2
        self.authorized_client.post(update_url, data)
        self.authorized_client.get(update_url)
        self.assertTrue(
            Post.objects.filter(
                group=self.group_2,
            ).exists()
        )
        # в старом списке поста не осталось
        get_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': 'test_slug'})
        response = self.authorized_client.get(
            get_group_list)
        group = (response.context
                 ['page_obj'])
        self.assertEqual(len(group), 0)

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
