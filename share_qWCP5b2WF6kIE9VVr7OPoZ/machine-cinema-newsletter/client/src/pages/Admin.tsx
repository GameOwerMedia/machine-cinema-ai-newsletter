import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { trpc } from "@/lib/trpc";
import { Calendar, ArrowLeft, Plus, RefreshCw } from "lucide-react";
import { useState } from "react";
import { Link, useLocation } from "wouter";
import { toast } from "sonner";

export default function Admin() {
  const { user, isAuthenticated } = useAuth();
  const [, setLocation] = useLocation();
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  
  const { data: newsletters, isLoading, refetch } = trpc.newsletter.list.useQuery();
  const fetchNewsMutation = trpc.news.fetchNews.useMutation({
    onSuccess: (data) => {
      toast.success(`Pobrano ${data.articlesAdded} nowych artykułów!`);
      refetch();
    },
    onError: (error) => {
      toast.error(`Błąd: ${error.message}`);
    },
  });

  const generateMutation = trpc.newsletter.generate.useMutation({
    onSuccess: () => {
      toast.success("Newsletter został wygenerowany!");
      refetch();
    },
    onError: (error) => {
      toast.error(`Błąd: ${error.message}`);
    },
  });

  // Redirect if not admin
  if (isAuthenticated && user?.role !== 'admin') {
    setLocation('/');
    return null;
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <Card className="max-w-md">
          <CardHeader>
            <CardTitle>Wymagane uwierzytelnienie</CardTitle>
            <CardDescription>Musisz być zalogowany jako administrator</CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Powrót do strony głównej
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleGenerate = () => {
    generateMutation.mutate({ date: selectedDate });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
        <div className="container py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Calendar className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">Panel Administracyjny</h1>
              <p className="text-sm text-muted-foreground">Zarządzanie newsletterami</p>
            </div>
          </div>
          <Link href="/">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Powrót
            </Button>
          </Link>
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-12">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Fetch News Section */}
          <Card className="border-cyan-200 bg-cyan-50/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-cyan-900">
                <RefreshCw className="h-5 w-5" />
                Pobierz wiadomości AI
              </CardTitle>
              <CardDescription>
                Automatycznie pobierz najnowsze wiadomości AI z RSS i dodaj do bazy danych
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => fetchNewsMutation.mutate()}
                disabled={fetchNewsMutation.isPending}
                className="bg-cyan-600 hover:bg-cyan-700"
                size="lg"
              >
                {fetchNewsMutation.isPending ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Pobieranie...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Pobierz wiadomości teraz
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Generate Newsletter Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Generuj nowy newsletter
              </CardTitle>
              <CardDescription>
                Utwórz nowy newsletter dla wybranej daty
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="date">Data newslettera</Label>
                <Input
                  id="date"
                  type="date"
                  value={selectedDate}
                  onChange={(e) => setSelectedDate(e.target.value)}
                  className="max-w-xs"
                />
              </div>
              <Button
                onClick={handleGenerate}
                disabled={generateMutation.isPending}
              >
                {generateMutation.isPending ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Generowanie...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    Generuj newsletter
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Existing Newsletters */}
          <Card>
            <CardHeader>
              <CardTitle>Istniejące newslettery</CardTitle>
              <CardDescription>
                Lista wszystkich wygenerowanych newsletterów
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map(i => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : newsletters && newsletters.length > 0 ? (
                <div className="space-y-2">
                  {newsletters.map((newsletter) => (
                    <Link key={newsletter.id} href={`/newsletter/${newsletter.id}`}>
                      <div className="flex items-center justify-between p-4 rounded-lg border hover:bg-accent cursor-pointer transition-colors">
                        <div>
                          <p className="font-medium">{newsletter.title}</p>
                          <p className="text-sm text-muted-foreground">
                            {newsletter.date} • {newsletter.itemCount} artykułów
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {newsletter.published ? (
                            <span className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded">
                              Opublikowany
                            </span>
                          ) : (
                            <span className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded">
                              Szkic
                            </span>
                          )}
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Calendar className="h-12 w-12 mx-auto mb-3 opacity-50" />
                  <p>Brak newsletterów</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
            <CardHeader>
              <CardTitle className="text-blue-900 dark:text-blue-100">
                Instrukcje
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-blue-800 dark:text-blue-200 space-y-2">
              <p>
                <strong>1.</strong> Wybierz datę dla nowego newslettera
              </p>
              <p>
                <strong>2.</strong> Kliknij "Generuj newsletter" aby utworzyć nowy wpis
              </p>
              <p>
                <strong>3.</strong> System automatycznie pobierze najnowsze wiadomości AI
              </p>
              <p>
                <strong>4.</strong> Newsletter zostanie zapisany w bazie danych i będzie dostępny w archiwum
              </p>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
