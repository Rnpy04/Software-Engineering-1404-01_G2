from django.http import JsonResponse
from django.shortcuts import render
from core.auth import api_login_required
from .models import *
from .serializers import *
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q
from .models import WikiArticle, WikiCategory, WikiTag, WikiArticleRevision, WikiArticleReports
from django.utils import timezone

from django.http import JsonResponse
from .models import WikiArticle

TEAM_NAME = "team6"

# --- ویوهای پایه ---
@api_login_required
def ping(request):
    return JsonResponse({"team": TEAM_NAME, "ok": True})

def base(request):
    articles = WikiArticle.objects.using(TEAM_NAME).filter(status='published')
    return render(request, f"{TEAM_NAME}/index.html", {"articles": articles})

# 2 & 7. لیست مقالات + سرچ کلمه‌ای + فیلتر کتگوری (مورد 12)
class ArticleListView(ListView):
    model = WikiArticle
    template_name = 'team6/article_list.html'
    context_object_name = 'articles'

    def get_queryset(self):
        queryset = WikiArticle.objects.using('team6').all()
        q = self.request.GET.get('q')
        cat = self.request.GET.get('category')
        tag = self.request.GET.get('tag')

        if q: # سرچ مستقیم کلمه یا جمله
            queryset = queryset.filter(Q(title_fa__icontains=q) | Q(body_fa__icontains=q))
        if cat: # فیلتر دسته‌بندی
            queryset = queryset.filter(category__slug=cat)
        if tag: # سرچ با تگ (مورد 6)
            queryset = queryset.filter(tags__slug=tag)
            
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = WikiCategory.objects.using('team6').all()
        context['tags'] = WikiTag.objects.using('team6').all()
        return context

# 3. اضافه کردن مقاله
class ArticleCreateView(CreateView):
    model = WikiArticle
    fields = ['title_fa', 'place_name', 'slug', 'body_fa', 'category', 'summary']
    template_name = 'team6/article_form.html'
    success_url = '/team6/'

    def form_valid(self, form):
        form.instance.status = 'published'
        # اینجا می‌توانید author_user_id را از request.user بگیرید
        return super().form_valid(form)

# 4. ویرایش مقاله (همراه با ثبت نسخه جدید - مورد 8)
def edit_article(request, slug):
    article = get_object_or_404(WikiArticle.objects.using('team6'), slug=slug)
    if request.method == "POST":
        # قبل از آپدیت، نسخه فعلی را در تاریخچه (Revision) ذخیره می‌کنیم
        WikiArticleRevision.objects.using('team6').create(
            article=article,
            revision_no=article.current_revision_no,
            body_fa=article.body_fa,
            change_note=request.POST.get('change_note', 'No note')
        )
        # آپدیت مقاله
        article.body_fa = request.POST.get('body_fa')
        article.current_revision_no += 1
        article.save()
        return redirect('article_detail', slug=article.slug)
    
    return render(request, 'team6/article_edit.html', {'article': article})

# 5. گزارش دادن مقاله
def report_article(request, pk):
    if request.method == "POST":
        article = get_object_or_404(WikiArticle.objects.using('team6'), pk=pk)
        WikiArticleReports.objects.using('team6').create(
            article=article,
            reporter_user_id=request.user.id if request.user.is_authenticated else uuid.uuid4(),
            report_type=request.POST.get('type'),
            description=request.POST.get('desc')
        )
        return JsonResponse({"status": "success"})

# 8. نمایش نسخه‌های مختلف
def article_revisions(request, slug):
    article = get_object_or_404(WikiArticle.objects.using('team6'), slug=slug)
    revisions = WikiArticleRevision.objects.using('team6').filter(article=article).order_now('-created_at')
    return render(request, 'team6/revisions.html', {'article': article, 'revisions': revisions})

# 10 & 11. نمایش جزئیات + خلاصه‌سازی (LLM)
def article_detail(request, slug):
    article = get_object_or_404(WikiArticle.objects.using('team6'), slug=slug)
    article.view_count += 1
    article.save()
    return render(request, 'team6/article_detail.html', {'article': article})


def get_wiki_content(request):
    place_query = request.GET.get('place', None)
    
    if not place_query:
        return JsonResponse({"error": "پارامتر place الزامی است"}, status=400)
    
    # جستجو بر اساس نام مکان یا عنوان (مطابق با نیازمندی جستجوی مستقیم)
    article = WikiArticle.objects.using('team6').filter(
        Q(place_name__icontains=place_query) | Q(title_fa__icontains=place_query)
    ).first()

    if not article:
        return JsonResponse({"message": "محتوایی برای این مکان یافت نشد"}, status=404)

    # ساخت خروجی طبق فرمت توافق شده با تیم‌ها
    data = {
        "id": str(article.id_article),
        "title": article.title_fa,
        "place_name": article.place_name,
        "category": article.category.title_fa,
        "tags": list(article.tags.values_list('title_fa', flat=True)),
        "summary": article.summary,
        "description": article.body_fa,
        "images": [article.featured_image_url] if article.featured_image_url else [],
        "url": article.url,
        "updated_at": article.updated_at.isoformat()
    }
    return JsonResponse(data)
