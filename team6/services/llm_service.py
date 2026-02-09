import os
import requests
from typing import List
import re
from collections import Counter

class FreeAIService:
    def __init__(self):
        self.api_key = os.environ.get("HF_API_KEY")
        # مدل Summarization واقعی که فارسی هم پشتیبانی می‌کند
        self.base_url = "https://router.huggingface.co/hf-inference/models/csebuetnlp/mT5_multilingual_XLSum"

    def _call_api(self, text: str) -> str:
        """ارسال متن به HF API و دریافت خلاصه"""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        prompt = (
            "Please summarize the given text in five sentences in Persian, "
            "keeping the main points and important details, and removing any unnecessary information:\n\n"
            f"{text}"
        )
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 100,  # طول تقریبی خروجی
                "min_length": 30,   # حداقل طول منطقی
                "do_sample": False,  # deterministic output
                "num_beams": 4,      # برای کیفیت بهتر خلاصه
                "early_stopping": True  # زودتر متوقف شود وقتی جملات کافی شد
            }
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            if response.status_code != 200:
                print("HF Error:", response.text)
                return None

            data = response.json()
            if isinstance(data, list) and 'summary_text' in data[0]:
                return data[0]['summary_text']
            elif isinstance(data, dict) and 'summary_text' in data:
                return data['summary_text']
            else:
                return None

        except Exception as e:
            print("HF Exception:", e)
            return None

    def generate_summary(self, text: str) -> str:
        """تولید خلاصه فارسی با fallback هوشمند"""
        if len(text) < 50:
            # متن کوتاه → fallback: تمام متن یا جمله اول
            sentences = [s.strip() for s in text.split(".") if s.strip()]
            return ". ".join(sentences[:2]) + "..." if len(sentences) > 1 else text

        # متن بلند → API HF
        result = self._call_api(text[:2000])
        if result:
            return result.strip()

        # Fallback اگر HF خراب شد
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        return ". ".join(sentences[:3]) + "..." if len(sentences) > 2 else text[:200] + "..."

    def extract_tags(self, text: str, title: str = "") -> List[str]:
        """استخراج تگ فارسی دقیق‌تر، حداکثر ۱۵ تا"""
        # ترکیب عنوان و متن
        combined = title + " " + text

        # فقط کلمات فارسی با حداقل 3 حرف
        words = re.findall(r'[\u0600-\u06FF]{3,}', combined)

        # حذف کلمات خیلی رایج (stopwords ساده)
        stopwords = ["است", "بود", "شده", "یکی", "این", "بر", "برای", "با", "را"]
        words = [w for w in words if w not in stopwords]

        # شمارش فراوانی
        counter = Counter(words)
        most_common = [w for w, _ in counter.most_common(15)]

        return most_common
