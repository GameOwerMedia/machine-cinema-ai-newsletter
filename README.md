# Machine Cinema Poland - AI Daily Newsletter

Automatyczny system generujący codzienne newslettery AI w języku polskim, skupiający się na polskim rynku i twórcach.

## 🚀 Funkcjonalności

- **Automatyczne zbieranie newsów** AI z różnych źródeł
- **Inteligentna kategoryzacja** na 3 grupy: twórcy, marketing, biznes
- **Formatowanie treści** z odpowiednim stylem dla każdej kategorii
- **Zapobieganie duplikatom** - system śledzi już wykorzystane artykuły
- **Wieloformatowy output** - Markdown i HTML
- **Polskie tłumaczenia** i lokalizacja treści

## 📁 Struktura projektu

```
machine-cinema-ai-newsletter/
├── fetch_ai_news.py     # Moduł zbierania newsów
├── make_posts.py        # Moduł formatowania postów
├── generate_all.py      # Główny generator newslettera
├── setup.py            # Skrypt instalacyjny
├── requirements.txt    # Zależności Pythona
├── seen_urls.txt       # Śledzenie wykorzystanych URLi
├── out/               # Wygenerowane newslettery (MD)
└── site/              # Strona HTML z newsletterami
    ├── index.html     # Najnowszy newsletter
    ├── YYYY-MM-DD.html # Archiwalne newslettery
    └── assets/        # Style CSS i assets
```

## ⚙️ Instalacja

1. **Zainstaluj zależności:**
   ```bash
   python setup.py
   ```

2. **Sprawdź konfigurację:**
   ```bash
   python -c "from fetch_ai_news import gather; from make_posts import format_post; print('System gotowy!')"
   ```

## 🎯 Użycie

### Generowanie newslettera
```bash
cd machine-cinema-ai-newsletter
python generate_all.py
```

### Outputy systemu
- `out/YYYY-MM-DD_ALL.md` - Newsletter w formacie Markdown
- `site/YYYY-MM-DD.html` - Newsletter w formacie HTML  
- `site/index.html` - zawsze najnowszy newsletter
- `seen_urls.txt` - lista już wykorzystanych artykułów

## 🎨 Kategorie treści

### 1. GenerativeAI creators 🧠
Artykuły dla twórców treści generatywnych:
- Prompt engineering
- Narzędzia AI (Stable Diffusion, Midjourney, Runway)
- Workflowy kreatywne
- Techniki generowania mediów

### 2. Marketing / fun 🚀
Treści marketingowe i viralowe:
- Kampanie reklamowe z AI
- Trendy social media
- Case studies
- Zabawne zastosowania AI

### 3. Biznes & dev 💼
Biznes i rozwój technologiczny:
- Regulacje prawne AI
- Inwestycje i funding
- Rozwój enterprise
- Narzędzia dla developerów

## 🔧 Konfiguracja

### Edycja źródeł newsów
Zmodyfikuj funkcję `fetch_news_from_api()` w `fetch_ai_news.py`:
```python
def fetch_news_from_api():
    # Dodaj swoje źródła RSS, API lub scraping
    return your_news_sources
```

### Dostosowanie kategoryzacji  
Edytuj listy keywords w `generate_all.py`:
- `CREATORS_KW` - słowa kluczowe dla twórców
- `MARKETING_KW` - słowa dla marketingu  
- `BIZDEV_KW` - słowa dla biznesu

### Personalizacja formatowania
Modyfikuj `make_posts.py` aby zmienić:
- Symbole kategorii
- Style hooków
- Format outputu

## 🎯 Przykładowy output

```markdown
# Newsletter AI — Machine Cinema Poland — 2025-10-25

## GenerativeAI creators

1. [AI] Nowe narzędzia AI dla twórców - rewolucja w generatywnych mediach — workflow i praktyka
Firma OpenAI wprowadza nowe funkcje dla twórców treści, ułatwiające generowanie wysokiej jakości materiałów.
LINK: https://example.com/ai-tools (Źródło: example.com)
```

## 🤖 Automatyzacja

### Codzienne uruchamianie
Dodaj do crona/planisty zadań:
```bash
0 9 * * * cd /path/to/machine-cinema-ai-newsletter && python generate_all.py
```

### Integracja z systemem
System można łatwo zintegrować z:
- Systemami email (do wysyłki newslettera)
- Social media (auto-posting)
- CMS (automatyczne publikowanie)

## 🐛 Rozwiązywanie problemów

### Problem: Brak nowych artykułów
- Sprawdź źródła w `fetch_ai_news.py`
- Usuń `seen_urls.txt` aby zresetować stan

### Problem: Kodowanie znaków
- Upewnij się że pliki używają UTF-8
- W konsoli: `chcp 65001` dla UTF-8

### Problem: Import modułów
- Uruchom `python setup.py` ponownie
- Sprawdź `requirements.txt`

## 📞 Wsparcie

Projekt Machine Cinema Poland - automatyzacja treści AI dla polskiego rynku.

---
*Automatycznie wygenerowany system newsletterowy* 🚀

## 🌐 GitHub Deployment & Automation

### GitHub Pages Setup
1. **Enable GitHub Pages:**
   - Go to Repository Settings → Pages
   - Source: **GitHub Actions**
   - Custom domain (optional): `newsletter.machinecinema.pl`

2. **Repository Secrets** (Settings → Secrets → Actions):
   - Add any API keys for news sources
   - Add domain configuration if using custom domain

### Automated Workflows
- **Daily Generation:** Runs at 09:00 UTC (10:00 Warsaw) daily
- **Manual Testing:** Trigger manually via GitHub Actions UI
- **Auto-deployment:** Deploys to GitHub Pages after generation

### GitHub Actions Features
✅ **Scheduled daily runs**  
✅ **Manual testing workflow**  
✅ **Automatic deployment**  
✅ **Artifact storage** (7 days retention)  
✅ **Email notifications** on failure

## 🚀 Quick GitHub Setup

1. **Create new repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Machine Cinema AI Newsletter"
   git branch -M main
   git remote add origin https://github.com/yourusername/machine-cinema-newsletter.git
   git push -u origin main
   ```

2. **Enable GitHub Pages:**
   - Settings → Pages → Build and deployment → GitHub Actions

3. **Add secrets** (if using APIs):
   - Settings → Secrets and variables → Actions
   - Add `NEWS_API_KEY`, `RSS_FEEDS`, etc.

4. **Trigger first build:**
   - Actions → Manual Newsletter Test → Run workflow

## 📊 Monitoring & Analytics

- **GitHub Actions:** View run history and logs
- **GitHub Pages:** Monitor website traffic
- **Artifacts:** Download generated newsletters
- **Email notifications:** Get alerts on failures

## 🔧 Troubleshooting GitHub Deployment

### Common Issues:
1. **Dependencies failing:** Check `requirements.txt` compatibility
2. **Encoding issues:** Ensure UTF-8 handling in workflows
3. **Deployment failures:** Verify GitHub Pages settings
4. **Scheduled runs not working:** Check cron syntax and timezone

### Debugging:
- Use Manual Test workflow for debugging
- Check Actions logs for detailed error messages
- Test locally before pushing changes
