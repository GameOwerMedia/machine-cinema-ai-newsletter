import { useParams, Link } from "wouter";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ExternalLink } from "lucide-react";

export default function Newsletter() {
  const params = useParams<{ id: string }>();
  const newsletterId = Number(params.id);

  const { data, isLoading, error } = trpc.newsletter.getWithArticles.useQuery(
    { id: newsletterId },
    { enabled: !isNaN(newsletterId) }
  );

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 py-12">
        <div className="container max-w-4xl">
          <Skeleton className="h-12 w-64 mb-8" />
          <Skeleton className="h-8 w-32 mb-4" />
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 py-12">
        <div className="container max-w-4xl">
          <Card>
            <CardHeader>
              <CardTitle>Błąd</CardTitle>
              <CardDescription>Nie można załadować newslettera</CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/">
                <Button variant="outline">
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Powrót do strony głównej
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  const { newsletter, articles } = data;

  // Group articles by category
  const categorizedArticles = articles.reduce((acc, article) => {
    const cat = article.category || "general";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(article);
    return acc;
  }, {} as Record<string, typeof articles>);

  const categoryNames = {
    creators: "GenerativeAI creators 🧠",
    marketing: "Marketing / fun 🚀",
    bizdev: "Biznes & dev 💼",
    general: "Ogólne",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 py-12">
      <div className="container max-w-4xl">
        <Link href="/">
          <Button variant="ghost" className="mb-6">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Powrót do archiwum
          </Button>
        </Link>

        <header className="mb-12 text-center">
          <h1 className="text-4xl font-bold mb-2 bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400">
            {newsletter.title}
          </h1>
          <p className="text-lg text-muted-foreground">{newsletter.date}</p>
        </header>

        <main className="space-y-8">
          {Object.entries(categorizedArticles).map(([category, categoryArticles]) => (
            <section key={category}>
              <h2 className="text-2xl font-bold mb-4 text-foreground">
                {categoryNames[category as keyof typeof categoryNames] || category}
              </h2>
              <div className="space-y-4">
                {categoryArticles.map((article) => (
                  <Card key={article.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <CardTitle className="text-xl">
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-blue-600 dark:hover:text-blue-400 flex items-start gap-2"
                        >
                          {article.title}
                          <ExternalLink className="h-4 w-4 mt-1 flex-shrink-0" />
                        </a>
                      </CardTitle>
                      {article.source && (
                        <CardDescription>Źródło: {article.source}</CardDescription>
                      )}
                    </CardHeader>
                    {article.summary && (
                      <CardContent>
                        <p className="text-muted-foreground">{article.summary}</p>
                      </CardContent>
                    )}
                  </Card>
                ))}
              </div>
            </section>
          ))}

          {articles.length === 0 && (
            <Card>
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">
                  Brak artykułów w tym newsletterze
                </p>
              </CardContent>
            </Card>
          )}
        </main>

        {(newsletter.htmlFileUrl || newsletter.mdFileUrl) && (
          <footer className="mt-12 flex gap-4 justify-center">
            {newsletter.htmlFileUrl && (
              <Button asChild variant="outline">
                <a href={newsletter.htmlFileUrl} target="_blank" rel="noopener noreferrer">
                  Pobierz HTML
                </a>
              </Button>
            )}
            {newsletter.mdFileUrl && (
              <Button asChild variant="outline">
                <a href={newsletter.mdFileUrl} target="_blank" rel="noopener noreferrer">
                  Pobierz Markdown
                </a>
              </Button>
            )}
          </footer>
        )}
      </div>
    </div>
  );
}
