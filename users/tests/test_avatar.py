from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class AvatarTests(APITestCase):
    def setUp(self):
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='Securepassword123',
            first_name='testuser',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)  # Авторизуем пользователя
    
    def create_image_with_target_size(self, target_size_kb, initial_resolution=(1000, 1000)):
        """
        Create an image with a target file size in KB.
        
        :param target_size_kb: Target file size in kilobytes (KB).
        :param output_path: Path to save the output image.
        :param initial_resolution: Initial resolution of the image (width, height).
        """
        target_size_bytes = target_size_kb * 1024  # Convert KB to bytes
        img = Image.new('RGB', initial_resolution, color='white')  # Create a blank image

        diff = 0

        # Adjust quality to reach the target size
        while True:
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            size = buffer.tell()  # Get the size of the image in bytes
            if size < target_size_bytes:
                # Increase resolution or quality to make the image larger
                diff = (abs(target_size_bytes - size)) / 500
                if diff < 100:
                    diff = 100
                diff = int(diff)
                new_resolution = (img.size[0] + diff, img.size[1] + diff)
                img = img.resize(new_resolution)
            else:
                diff = int(abs(target_size_bytes - size) / 2000)
                if diff < 1:
                    diff = 1
                new_resolution = (img.size[0] - diff, img.size[1] - diff)
                img = img.resize(new_resolution)

            if abs(size - target_size_bytes) <= target_size_kb/100 * 1024:  # Allow 1 KB tolerance
                break


        buffer = BytesIO()
        img.save(buffer, format="JPEG")
        return SimpleUploadedFile("test_image.jpg", buffer.getvalue(), content_type="image/jpeg")


    def test_upload_avatar_success(self):
        """
        Тест успешной загрузки аватарки.
        """
        url = reverse("avatar")
        avatar = self.create_image_with_target_size(100)  # Создаем изображение размером 100 КБ

        response = self.client.post(url, {"avatar": avatar}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertIn("avatar", response.data)
        

    def test_delete_avatar_success(self):
        """
        Тест успешного удаления аватарки.
        """
        # Сначала загружаем аватарку
        avatar = self.create_image_with_target_size(100)
        self.user.avatar.save("test_avatar.jpg", avatar)
        self.user.save()
        self.user.refresh_from_db()

        url = reverse("avatar")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что аватарка удалена и заменена на аватарку по умолчанию
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.avatar)

    def test_delete_avatar_no_avatar(self):
        """
        Тест удаления аватарки, если её нет.
        """
        url = reverse("avatar")
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

        # Проверяем, что аватарка по умолчанию создана
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.avatar)


    def test_heavy_image(self):
        """
        Тест отправки изображения больше 200 КБ.
        """
        avatar = self.create_image_with_target_size(201)  # Создаем изображение размером 5 мб
        url = reverse("avatar")

        response = self.client.post(url, {"avatar": avatar}, format="multipart")
        print(response.data)
        self.assertEqual(response.status_code, 400)
