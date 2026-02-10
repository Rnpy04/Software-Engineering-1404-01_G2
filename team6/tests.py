from django.test import TestCase, Client
from django.urls import reverse
from .models import WikiArticle, WikiCategory
from unittest.mock import patch
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model

# به دست آوردن مدل کاربر فعال پروژه
User = get_user_model()
@login_required
class TeamPingTests(TestCase):
    def test_ping_requires_auth(self):
        res = self.client.get("/team6/ping/")
        self.assertEqual(res.status_code, 401)

#هنوز مشکل داره بعدا حل میکنم
class WikiArticleTests(TestCase):
    databases = {'team6'}
    def setUp(self):
        # ساخت یک دسته‌بندی برای تست‌ها
        self.category = WikiCategory.objects.create(
            title_fa="طبیعت", 
            slug="nature"
        )
        # ساخت یک کاربر فرضی (Mock User)
        self.client = Client()
        
    @patch('team6.views.GoogleTranslator.translate')
    @patch('team6.services.llm_service.FreeAIService.generate_summary')
    def test_article_creation_flow(self, mock_ai_summary, mock_translate):
        """تست چرخه کامل ساخت مقاله با شبیه‌سازی هوش مصنوعی و ترجمه"""
        
        # تنظیم مقادیر بازگشتی شبیه‌سازی شده (Mock)
        mock_translate.return_value = "Test English Title"
        mock_ai_summary.return_value = "این یک خلاصه هوشمند است."

        # فرض می‌کنیم کاربر لاگین کرده است (شبیه‌سازی لاگین)
        # استفاده از مدل کاربر صحیح و دادن ایمیل اجباری
        User = get_user_model()
        user = User.objects.create_user(
            email='test@example.com'  
        ) 
        self.client.force_login(user)
        
        data = {
            'title_fa': 'تست جنگل ابر',
            'place_name': 'جنگل ابر',
            'body_fa': 'این یک متن طولانی درباره جنگل ابر است...',
            'category': self.category.id_category,
        }

        response = self.client.post(reverse('team6:article_add'), data)
        
        # بررسی ریدایرکت بعد از ساخت موفق
        self.assertEqual(response.status_code, 302)
        
        # بررسی ذخیره شدن در دیتابیس
        article = WikiArticle.objects.get(title_fa='تست جنگل ابر')
        self.assertEqual(article.summary, "این یک خلاصه هوشمند است.")
        self.assertEqual(article.title_en, "Test English Title")

    # def test_semantic_search_with_no_results(self):
    #     """تست هندلینگ خطای جستجوی معنایی وقتی نتیجه‌ای یافت نشود"""
    #     response = self.client.get(reverse('team6:index'), {'q': 'فضانوردی', 'search_type': 'semantic'})
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "نتیجه‌ای یافت نشد") # یا هر پیامی که در تمپلیت دارید

    def test_article_detail_404(self):
        """تست نمایش درست خطای ۴۰۴ برای اسلاگ‌های ناموجود"""
        response = self.client.get(reverse('team6:article_detail', kwargs={'slug': 'not-exists'}))
        self.assertEqual(response.status_code, 404)
        # چک کردن اینکه آیا تمپلیت خطای اختصاصی ما لود شده یا نه
        self.assertTemplateUsed(response, 'team6/errors/404.html')