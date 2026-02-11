from team2.models import Article, Tag, Version
import google.generativeai as genai
from django.conf import settings
import json

genai.configure(api_key=settings.GEMINI_API_KEY)

MODEL = genai.GenerativeModel("gemini-1.5-flash")

def tag_article(article_name):
    article = Article.objects.get(name=article_name)
    version_name = article.current_version
    if version_name is None:
        return None
 
    version = Version.objects.get(name=version_name) 
    content = version.content

    existing_tags = list(Tag.objects.values_list("name", flat=True))

    prompt = f"""
You are a content classification assistant.

Your job:
1. Select relevant tags from the EXISTING TAGS list below.
2. Only suggest NEW tags if absolutely necessary.
3. Return output strictly in JSON format like this:

{{
  "selected_existing_tags": ["tag1", "tag2"],
  "new_tags": ["new_tag1"]
}}

Guidelines:
- Use concise, lowercase tags
- Avoid duplicates
- Maximum 5 total tags
- Prefer existing tags whenever possible

EXISTING TAGS:
{existing_tags}

ARTICLE:
\"\"\"
{content}
\"\"\"
"""

    response = MODEL.generate_content(prompt)

    try:
        data = json.loads(response.text)

        selected_existing = data.get("selected_existing_tags", [])
        new_tags = data.get("new_tags", [])

    except Exception:
        return None

    for tag_name in selected_existing:
        try:
            tag = Tag.objects.get(name=tag_name)
            version.tags.add(tag)
        except Tag.DoesNotExist:
            continue

    for tag_name in new_tags:
        tag, _ = Tag.objects.get_or_create(name=tag_name.lower())
        version.tags.add(tag)

    return {
        "selected_existing_tags": selected_existing,
        "new_tags": new_tags,
    }



def summarize_article(article_name):
    article = Article.objects.get(name=article_name)
    version_name = article.current_version
    
    if version_name is None:
        return

    version = Version.objects.get(name=version_name) 
    content = version.content

    prompt = f"""
You are an assistant that writes concise, neutral summaries.

Summarize the following article in 3–6 sentences.
Do not add information that is not present.
Be factual and clear.

ARTICLE:
\"\"\"
{content}
\"\"\"
"""

    response = MODEL.generate_content(prompt)
    summary = response.text.strip()

    version.summary = summary
    version.save(update_fields=["summary"])

    return summary
