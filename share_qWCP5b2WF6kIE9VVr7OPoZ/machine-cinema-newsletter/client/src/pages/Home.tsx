import { trpc } from "@/lib/trpc";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Search, Menu } from "lucide-react";
import { Link } from "wouter";
import { APP_LOGO, APP_TITLE } from "@/const";
import { useState } from "react";

export default function Home() {
  const [searchOpen, setSearchOpen] = useState(false);
  const { data: newsletters, isLoading } = trpc.newsletter.list.useQuery();
  const { data: latestArticles } = trpc.article.getLatest.useQuery({ limit: 12 });

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-black text-white sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link href="/">
              <a className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                <img src={APP_LOGO} alt="Logo" className="h-10 w-10" />
                <div>
                  <div className="text-2xl font-bold tracking-tight">MACHINE CINEMA</div>
                  <div className="text-xs text-cyan-400 tracking-wider">POLAND</div>
                </div>
              </a>
            </Link>

            {/* Navigation */}
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/">
                <a className="hover:text-cyan-400 transition-colors">Aktualności</a>
              </Link>
              <Link href="/kategorie">
                <a className="hover:text-cyan-400 transition-colors">Kategorie</a>
              </Link>
              <Link href="/admin">
                <a className="hover:text-cyan-400 transition-colors">Panel</a>
              </Link>
            </nav>

            {/* Actions */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSearchOpen(!searchOpen)}
                className="hover:text-cyan-400 transition-colors"
              >
                <Search className="h-5 w-5" />
              </button>
              <Button className="bg-cyan-500 hover:bg-cyan-600 text-white hidden md:inline-flex">
                Subskrybuj
              </Button>
              <button className="md:hidden">
                <Menu className="h-6 w-6" />
              </button>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        {searchOpen && (
          <div className="border-t border-gray-800 bg-gray-900">
            <div className="container mx-auto px-4 py-4">
              <input
                type="text"
                placeholder="Szukaj wiadomości AI..."
                className="w-full bg-gray-800 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-cyan-500"
                autoFocus
              />
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <section className="mb-12">
          <h2 className="text-3xl font-bold mb-6">Najnowsze Wiadomości AI</h2>
          
          {isLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="h-64 animate-pulse bg-gray-200" />
              ))}
            </div>
          ) : latestArticles && latestArticles.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {latestArticles.map((article: any) => (
                <Link key={article.id} href={`/article/${article.id}`}>
                  <a>
                    <Card className="overflow-hidden hover:shadow-lg transition-shadow group">
                      {/* Article Image */}
                      <div className="relative h-48 overflow-hidden">
                        {article.imageUrl ? (
                          <img
                            src={article.imageUrl}
                            alt={article.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                            onError={(e) => {
                              // Fallback to gradient if image fails
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-gray-800 to-gray-600 flex items-center justify-center">
                            <span className="text-white text-4xl font-bold opacity-20">AI</span>
                          </div>
                        )}
                        {/* Category Badge */}
                        <Badge
                          className={`absolute top-3 left-3 ${
                            categoryColors[article.category] || "bg-gray-500"
                          } text-white text-xs uppercase`}
                        >
                          {categoryNames[article.category] || article.category}
                        </Badge>
                      </div>

                      {/* Article Content */}
                      <div className="p-4">
                        <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                          <Calendar className="h-4 w-4" />
                          <span>
                            {new Date(article.publishedAt).toLocaleDateString("pl-PL", {
                              year: "numeric",
                              month: "long",
                              day: "numeric",
                            })}
                          </span>
                        </div>
                        <h3 className="font-bold text-lg mb-2 group-hover:text-cyan-600 transition-colors line-clamp-2">
                          {article.title}
                        </h3>
                        <p className="text-gray-600 text-sm line-clamp-3">{article.summary}</p>
                        {article.source && (
                          <div className="mt-3 text-xs text-gray-500">
                            Źródło: {article.source}
                          </div>
                        )}
                      </div>
                    </Card>
                  </a>
                </Link>
              ))}
            </div>
          ) : (
            <Card className="p-12 text-center">
              <div className="text-gray-400 mb-4">
                <Calendar className="h-16 w-16 mx-auto mb-4" />
                <p className="text-lg">Brak artykułów</p>
                <p className="text-sm mt-2">Wkrótce pojawią się najnowsze wiadomości AI</p>
              </div>
            </Card>
          )}
        </section>

        {/* Newsletter Archive */}
        {newsletters && newsletters.length > 0 && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold mb-6">Archiwum Newsletterów</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {newsletters.slice(0, 4).map((newsletter) => (
                <Link key={newsletter.id} href={`/newsletter/${newsletter.id}`}>
                  <a>
                    <Card className="p-4 hover:shadow-lg transition-shadow hover:border-cyan-500">
                      <div className="text-sm text-gray-500 mb-2">{newsletter.date}</div>
                      <h3 className="font-semibold text-sm mb-2 line-clamp-2">
                        {newsletter.title}
                      </h3>
                      <div className="text-xs text-cyan-600">
                        {newsletter.itemCount} artykułów
                      </div>
                    </Card>
                  </a>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* CTA Section */}
        <section className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-lg p-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Dołącz do Naszej Społeczności</h2>
          <p className="mb-6 text-lg">
            Otrzymuj najnowsze wiadomości AI bezpośrednio na swoją skrzynkę
          </p>
          <Button className="bg-white text-cyan-600 hover:bg-gray-100 font-semibold px-8">
            Subskrybuj Newsletter
          </Button>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-black text-white mt-16">
        <div className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <h3 className="font-bold text-lg mb-4">Machine Cinema Poland</h3>
              <p className="text-gray-400 text-sm">
                Codzienny przegląd najważniejszych wiadomości ze świata sztucznej inteligencji
              </p>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4">Kategorie</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>
                  <a href="#" className="hover:text-cyan-400 transition-colors">
                    GenerativeAI Creators
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-cyan-400 transition-colors">
                    Marketing & Fun
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-cyan-400 transition-colors">
                    Biznes & Dev
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold text-lg mb-4">Linki</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>
                  <Link href="/admin">
                    <a className="hover:text-cyan-400 transition-colors">Panel Admina</a>
                  </Link>
                </li>
                <li>
                  <a
                    href="https://github.com/GameOwerMedia/MachineCinemaPLNews"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:text-cyan-400 transition-colors"
                  >
                    GitHub
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            © {new Date().getFullYear()} Machine Cinema Poland. Wszystkie prawa zastrzeżone.
          </div>
        </div>
      </footer>
    </div>
  );
}
