from django.urls import path, re_path
from . import views
from .views import error_404, error_500, error_403, error_400 # ایمپورت ویوهای خطا
app_name = "team6"

urlpatterns = [
    # صفحه اصلی تیم 6 (لیست مقالات)
    path("", views.ArticleListView.as_view(), name="index"),
    
    # ویو پایه / API پایه
    path("ping/", views.ping, name="ping"),
    
    # اضافه کردن مقاله
    path("create/", views.ArticleCreateView.as_view(), name="article_add"),
    
    # جزئیات مقاله با slug
    re_path(r'^article/(?P<slug>[^/]+)/$', views.article_detail, name='article_detail'),
    
    # ویرایش مقاله
    re_path(r'^article/(?P<slug>[^/]+)/edit/$', views.edit_article, name="article_edit"),
    
    #حذف مقاله
    re_path(r'^article/(?P<slug>[^/]+)/delete/$', views.delete_article, name="article_delete"),
    
    # نمایش نسخه‌ها
    re_path(r'^article/(?P<slug>[^/]+)/revisions/$', views.article_revisions, name="article_revisions"),
    
    # گزارش مقاله با slug (ساده‌ترین راه)
    re_path(r'^article/(?P<slug>[^/]+)/report/$', views.report_article, name="article_report"),
    
    # API خارجی برای محتوا
    path("api/wiki/content", views.get_wiki_content, name="external_api"),

    
    re_path(
    r'^article/(?P<slug>[^/]+)/revisions/(?P<revision_no>\d+)/$',
    views.article_revision_detail,
    name="article_revision_detail"
),
    # re_path(r'^article/(?P<slug>[^/]+)/generate-ai/$', views.generate_ai_content_api, name='generate_ai'),
    path("api/preview-ai/", views.preview_ai_content, name='preview_ai'),
]


handler404 = 'team6.views.error_404'
handler500 = 'team6.views.error_500'
handler403 = 'team6.views.error_403'
handler400 = 'team6.views.error_400'