import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Posts."""
        Post.objects.all().delete()
        # Подсчитаем количество записей в Task
        self.assertEqual(Post.objects.count(), 0)
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
        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': 'author'}
            )
        )
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), 1)
        # Проверяем, что создалась запись с заданным в БД
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image='posts/small.gif',
            ).exists()
        )

        # Проверяем, context на главной
        response = (self.authorized_client.get(
            reverse('posts:index')))
        post_index = response.context['page_obj'][0].image.name
        self.assertEqual(post_index, 'posts/small.gif')

        # Проверяем, context на странице профайла
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'author'})))
        post_index = response.context['page_obj'][0].image.name
        self.assertEqual(post_index, 'posts/small.gif')

        # Проверяем, context на странице группы
        # response = (self.authorized_client.get(
        #     reverse('posts:group_list',
        #             kwargs={'slug': 'test_slug'})))
        # post_index = response.context['page_obj'][0].image.name
        # self.assertEqual(post_index, 'posts/small.gif')

        # Проверяем, context на странице поста
        # response = (self.authorized_client.get(
        #     reverse('posts:post_detail',
        #             kwargs={'post_id': '1'})))
        # post_index = response.context['post'].image.name
        # self.assertEqual(post_index, 'posts/small.gif')

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
                image='posts/small.gif',
            ).exists()
        )
