# Machine Cinema - AI Daily Newsletter

Automatyczny system newsletterowy dla polskich wiadomości AI, inspirowany projektem [MachineCinemaPLNews](https://github.com/GameOwerMedia/MachineCinemaPLNews).

## 🎯 Funkcje

- **Automatyczne pobieranie wiadomości** z RSS feedów Google News
- **Kategoryzacja artykułów** na 3 kategorie:
  - GenerativeAI creators 🧠
  - Marketing / fun 🚀
  - Biznes & dev 💼
- **Filtrowanie duplikatów** z wykorzystaniem bazy danych
- **Generowanie newsletterów** w formacie HTML i Markdown
- **Archiwum newsletterów** z interfejsem webowym
- **Panel administracyjny** do zarządzania newsletterami
- **Integracja S3** do przechowywania plików
- **Uwierzytelnianie użytkowników** z rolami (admin/user)

## 🏗️ Architektura

### Backend
- **Node.js + Express** - serwer API
- **tRPC** - type-safe API
- **Drizzle ORM** - zarządzanie bazą danych
- **MySQL/TiDB** - baza danych
- **S3** - przechowywanie plików

### Frontend
- **React 19** - framework UI
- **Tailwind CSS 4** - stylowanie
- **shadcn/ui** - komponenty UI
- **Wouter** - routing

### Python Scripts
- **feedparser** - parsowanie RSS
- **PyYAML** - konfiguracja
- **python-dateutil** - obsługa dat

## 📁 Struktura projektu

```
machine-cinema-newsletter/
├── client/                    # Frontend React
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx      # Archiwum newsletterów
│   │   │   ├── Newsletter.tsx # Szczegóły newslettera
│   │   │   └── Admin.tsx     # Panel administracyjny
│   │   └── components/       # Komponenty UI
├── server/                    # Backend Node.js
│   ├── routers.ts            # Endpointy tRPC
│   ├── db.ts                 # Funkcje bazodanowe
│   └── storage.ts            # Integracja S3
├── drizzle/                   # Schemat bazy danych
│   └── schema.ts             # Tabele: newsletters, articles, seenUrls
├── scripts/                   # Skrypty Python
│   ├── fetch_ai_news.py      # Pobieranie RSS
│   ├── filters.py            # Filtrowanie treści
│   ├── make_posts.py         # Formatowanie postów
│   ├── generate_all.py       # Generator główny
│   └── utils.py              # Funkcje pomocnicze
├── config.yaml               # Konfiguracja feedów i kategorii
└── requirements.txt          # Zależności Python
```

## 🚀 Instalacja i uruchomienie

### 1. Zainstaluj zależności Node.js

```bash
pnpm install
```

### 2. Zainstaluj zależności Python

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Skonfiguruj bazę danych

```bash
pnpm db:push
```

### 4. Uruchom serwer deweloperski

```bash
pnpm dev
```

Aplikacja będzie dostępna pod adresem `http://localhost:3000`

## 📝 Konfiguracja

Edytuj `config.yaml` aby dostosować:

- **Źródła RSS** - dodaj lub usuń feedy Google News
- **Kategorie** - zdefiniuj własne kategorie i słowa kluczowe
- **Filtry** - ustaw kryteria filtrowania artykułów
- **Ustawienia newslettera** - tryb selekcji, liczba artykułów na kategorię

Przykład konfiguracji:

```yaml
sources:
  - name: "Google News - AI"
    url: "https://news.google.com/rss/search?q=artificial+intelligence&hl=pl&gl=PL&ceid=PL:pl"

categories:
  creators:
    keywords: ["OpenAI", "GPT", "model", "generative"]
  marketing:
    keywords: ["marketing", "reklama", "kampania"]
  bizdev:
    keywords: ["startup", "biznes", "finansowanie"]
```

## 🎨 Interfejs użytkownika

### Strona główna (Archiwum)
- Lista wszystkich newsletterów
- Sortowanie od najnowszych
- Liczba artykułów w każdym newsletterze
- Przycisk do panelu admina (dla administratorów)

### Strona newslettera
- Wyświetlanie artykułów pogrupowanych po kategoriach
- Linki do oryginalnych źródeł
- Podsumowania artykułów
- Możliwość pobrania HTML/Markdown

### Panel administracyjny
- Generowanie nowych newsletterów
- Wybór daty
- Lista istniejących newsletterów
- Status publikacji

## 🔐 Uwierzytelnianie

System wykorzystuje Manus OAuth do uwierzytelniania:

- **Użytkownicy** - mogą przeglądać newslettery
- **Administratorzy** - mogą generować i zarządzać newsletterami

Właściciel projektu automatycznie otrzymuje rolę administratora.

## 📊 Baza danych

### Tabele

**newsletters**
- `id` - ID newslettera
- `date` - Data (YYYY-MM-DD)
- `title` - Tytuł
- `htmlFileKey`, `htmlFileUrl` - Pliki HTML w S3
- `mdFileKey`, `mdFileUrl` - Pliki Markdown w S3
- `itemCount` - Liczba artykułów
- `published` - Status publikacji

**articles**
- `id` - ID artykułu
- `newsletterId` - Powiązanie z newsletterem
- `title` - Tytuł
- `summary` - Podsumowanie
- `url` - Link do źródła
- `source` - Nazwa źródła
- `category` - Kategoria (creators/marketing/bizdev)
- `publishedAt` - Data publikacji

**seenUrls**
- `id` - ID
- `url` - URL artykułu
- `firstSeen`, `lastSeen` - Daty

## 🔄 API Endpoints (tRPC)

### Newsletter
- `newsletter.list` - Lista wszystkich newsletterów
- `newsletter.getByDate` - Pobierz newsletter po dacie
- `newsletter.getWithArticles` - Pobierz newsletter z artykułami
- `newsletter.generate` - Generuj nowy newsletter (admin)
- `newsletter.uploadFiles` - Upload plików do S3 (admin)

### Article
- `article.getByNewsletterId` - Pobierz artykuły newslettera
- `article.create` - Utwórz artykuł (admin)

### Seen URLs
- `seenUrl.check` - Sprawdź czy URL był widziany
- `seenUrl.mark` - Oznacz URL jako widziany (admin)
- `seenUrl.list` - Lista wszystkich widzianych URL (admin)

## 🐍 Skrypty Python

### Generowanie newslettera

```bash
source venv/bin/activate
python scripts/generate_all.py
```

Ten skrypt:
1. Pobiera wiadomości z RSS feedów
2. Filtruje według relevancji
3. Usuwa duplikaty
4. Kategoryzuje artykuły
5. Generuje pliki HTML i Markdown
6. Zapisuje w bazie danych

### Ręczne pobieranie wiadomości

```bash
python scripts/fetch_ai_news.py
```

## 📦 Deployment

### Przygotowanie do publikacji

1. Utwórz checkpoint:
```bash
pnpm db:push  # Upewnij się, że schemat jest aktualny
```

2. Kliknij przycisk **Publish** w interfejsie zarządzania

3. Twoja aplikacja będzie dostępna pod adresem `*.manus.space`

### Zmienne środowiskowe

Wszystkie wymagane zmienne są automatycznie wstrzykiwane przez platformę Manus:
- `DATABASE_URL` - Połączenie z bazą danych
- `JWT_SECRET` - Klucz sesji
- `VITE_APP_TITLE` - Tytuł aplikacji
- Zmienne OAuth i S3

## 🛠️ Development

### Testowanie

Utwórz testowy newsletter:

```bash
pnpm exec tsx test_create_newsletter.ts
```

### Sprawdzanie bazy danych

Użyj panelu Database w interfejsie zarządzania lub:

```bash
pnpm db:push  # Synchronizuj schemat
```

## 📚 Dokumentacja techniczna

### Workflow generowania newslettera

1. **Fetch** - Pobieranie artykułów z RSS
2. **Filter** - Filtrowanie według słów kluczowych
3. **Dedup** - Usuwanie duplikatów
4. **Categorize** - Przypisywanie kategorii
5. **Select** - Wybór N artykułów na kategorię
6. **Generate** - Tworzenie HTML/Markdown
7. **Store** - Zapis do bazy i S3

### Integracja S3

Pliki są przechowywane w S3 z publicznym dostępem:

```typescript
import { storagePut } from "./server/storage";

const { url } = await storagePut(
  `newsletters/${date}.html`,
  htmlContent,
  "text/html"
);
```

### Dodawanie nowych kategorii

1. Edytuj `config.yaml`:
```yaml
categories:
  newcategory:
    keywords: ["keyword1", "keyword2"]
```

2. Zaktualizuj `scripts/filters.py` jeśli potrzeba

3. Dodaj emoji w `client/src/pages/Newsletter.tsx`:
```typescript
const categoryNames = {
  newcategory: "Nowa kategoria 🎯",
  // ...
};
```

## 🤝 Contributing

Ten projekt jest inspirowany [MachineCinemaPLNews](https://github.com/GameOwerMedia/MachineCinemaPLNews).

## 📄 Licencja

MIT License

## 🔗 Linki

- [Manus Platform](https://manus.im)
- [Original MachineCinemaPLNews](https://github.com/GameOwerMedia/MachineCinemaPLNews)
- [Dokumentacja tRPC](https://trpc.io)
- [Dokumentacja Drizzle ORM](https://orm.drizzle.team)

---

**Uwaga**: System jest skonfigurowany dla języka polskiego, ale może być łatwo dostosowany do innych języków poprzez edycję plików konfiguracyjnych i interfejsu użytkownika.
