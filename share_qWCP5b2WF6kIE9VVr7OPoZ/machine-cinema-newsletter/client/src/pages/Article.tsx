import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar, ExternalLink, ArrowLeft } from "lucide-react";
import { Link, useRoute } from "wouter";
import { APP_LOGO } from "@/const";

export default function Article() {
  const [, params] = useRoute("/article/:id");
  const articleId = params?.id ? parseInt(params.id) : 0;

  const { data: article, isLoading } = trpc.article.getById.useQuery(
    { id: articleId },
    { enabled: articleId > 0 }
  );

  const categoryColors: Record<string, string> = {
    creators: "bg-cyan-500",
    marketing: "bg-orange-500",
    bizdev: "bg-purple-500",
  };

  const categoryNames: Record<string, string> = {
    creators: "GenerativeAI Creators",
    marketing: "Marketing & Fun",
    bizdev: "Biznes & Dev",
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-black text-white">
          <div className="container mx-auto px-4 py-4">
            <Link href="/">
              <a className="flex items-center gap-3">
                <img src={APP_LOGO} alt="Logo" className="h-10 w-10" />
                <div>
                  <div className="text-2xl font-bold">MACHINE CINEMA</div>
                  <div className="text-xs text-cyan-400">POLAND</div>
                </div>
              </a>
            </Link>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-8"></div>
            <div className="h-64 bg-gray-200 rounded mb-8"></div>
            <div className="space-y-3">
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded"></div>
              <div className="h-4 bg-gray-200 rounded w-5/6"></div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-black text-white">
          <div className="container mx-auto px-4 py-4">
            <Link href="/">
              <a className="flex items-center gap-3">
                <img src={APP_LOGO} alt="Logo" className="h-10 w-10" />
                <div>
                  <div className="text-2xl font-bold">MACHINE CINEMA</div>
                  <div className="text-xs text-cyan-400">POLAND</div>
                </div>
              </a>
            </Link>
          </div>
        </header>
        <main className="container mx-auto px-4 py-8 text-center">
          <h1 className="text-2xl font-bold mb-4">Artykuł nie znaleziony</h1>
          <Link href="/">
            <a>
              <Button>Powrót do strony głównej</Button>
            </a>
          </Link>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-black text-white sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <Link href="/">
              <a className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <img src={APP_LOGO} alt="Logo" className="h-10 w-10" />
                <div>
                  <div className="text-2xl font-bold tracking-tight">MACHINE CINEMA</div>
                  <div className="text-xs text-cyan-400 tracking-wider">POLAND</div>
                </div>
              </a>
            </Link>
            <Link href="/">
              <a>
                <Button variant="ghost" className="text-white hover:text-cyan-400">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Powrót
                </Button>
              </a>
            </Link>
          </div>
        </div>
      </header>

      {/* Article Content */}
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <article className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Article Header */}
          <div className="p-8">
            <div className="flex items-center gap-3 mb-4">
              <Badge
                className={`${
                  categoryColors[article.category || ""] || "bg-gray-500"
                } text-white text-xs uppercase`}
              >
                {categoryNames[article.category || ""] || article.category}
              </Badge>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Calendar className="h-4 w-4" />
                <span>
                  {new Date(article.publishedAt || "").toLocaleDateString("pl-PL", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </span>
              </div>
            </div>

            <h1 className="text-4xl font-bold mb-4 leading-tight">{article.title}</h1>

            {article.source && (
              <div className="text-sm text-gray-600 mb-6">Źródło: {article.source}</div>
            )}
          </div>

          {/* Article Image */}
          {article.imageUrl ? (
            <div className="relative h-96 overflow-hidden">
              <img
                src={article.imageUrl}
                alt={article.title}
                className="w-full h-full object-cover"
              />
            </div>
          ) : (
            <div className="relative h-96 bg-gradient-to-br from-gray-800 to-gray-600">
              <div className="absolute inset-0 flex items-center justify-center text-white text-6xl font-bold opacity-20">
                AI
              </div>
            </div>
          )}

          {/* Article Body */}
          <div className="p-8">
            <div className="prose prose-lg max-w-none">
              <p className="text-xl text-gray-700 leading-relaxed mb-6">{article.summary}</p>

              {article.url && (
                <div className="mt-8 p-6 bg-cyan-50 rounded-lg border-l-4 border-cyan-500">
                  <p className="text-sm text-gray-600 mb-3">
                    Przeczytaj pełny artykuł w oryginalnym źródle:
                  </p>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-cyan-600 hover:text-cyan-700 font-semibold"
                  >
                    <ExternalLink className="h-5 w-5" />
                    Otwórz artykuł źródłowy
                  </a>
                </div>
              )}
            </div>
          </div>
        </article>

        {/* Back Button */}
        <div className="mt-8 text-center">
          <Link href="/">
            <a>
              <Button variant="outline" size="lg">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Powrót do wszystkich artykułów
              </Button>
            </a>
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-black text-white mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-sm text-gray-400">
            © {new Date().getFullYear()} Machine Cinema Poland. Wszystkie prawa zastrzeżone.
          </div>
        </div>
      </footer>
    </div>
  );
}
