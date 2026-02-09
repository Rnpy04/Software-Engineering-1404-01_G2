from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import WikiArticle, WikiTag
import threading

def generate_ai_content(article):
    """تولید خلاصه و تگ در پس‌زمینه"""
    try:
        from .services.llm_service import FreeAIService
        llm_service = FreeAIService()
        
        # تولید خلاصه
        summary = llm_service.generate_summary(article.body_fa)
        
        # استخراج تگ‌ها
        tags_list = llm_service.extract_tags(article.body_fa, article.title_fa)
        
        # ذخیره خلاصه
        article.summary = summary
        article.save()
        
        # اضافه کردن تگ‌ها
        for tag_name in tags_list:
            tag, created = WikiTag.objects.get_or_create(
                title_fa=tag_name,
                defaults={
                    'slug': tag_name.replace(' ', '-').replace('‌', '-')[:50],
                    'title_en': tag_name
                }
            )
            article.tags.add(tag)
            
    except Exception as e:
        print(f"⚠️ خطا در تولید AI: {e}")

@receiver(post_save, sender=WikiArticle)
def handle_new_article(sender, instance, created, **kwargs):
    """هنگام ایجاد مقاله جدید"""
    if created and instance.body_fa:
        # در پس‌زمینه اجرا شود
        thread = threading.Thread(target=generate_ai_content, args=(instance,))
        thread.daemon = True
        thread.start()