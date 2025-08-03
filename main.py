import yfinance as yf
from rich.console import Console
from rich.table import Table
from rich import box
import matplotlib.pyplot as plt
import pickle
import os
from rich.text import Text

WATCHLIST_FILE = "watchlist.pkl"
console = Console()
plt.style.use('dark_background')

def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "rb") as f:
            return pickle.load(f)
    return set()

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "wb") as f:
        pickle.dump(watchlist, f)

def show_quote(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if 'longName' not in info:
            console.print(f"[red]Nie znaleziono spółki o tickerze {ticker}[/red]")
            return

        table = Table(title=f"{ticker.upper()} – {info.get('longName', '--')}", box=box.SIMPLE)
        table.add_column("Metric", style="bold")
        table.add_column("Value")

        metrics = {
            "Price": info.get("currentPrice"),
            "Market Cap": info.get("marketCap"),
            "PE Ratio": info.get("trailingPE"),
            "EPS": info.get("trailingEps"),
            "Sector": info.get("sector"),
            "52w High": info.get("fiftyTwoWeekHigh"),
            "52w Low": info.get("fiftyTwoWeekLow"),
        }

        for k, v in metrics.items():
            table.add_row(k, str(v) if v is not None else "--")
        console.print(table)
    except Exception as e:
        console.print(f"[red]Błąd pobierania danych: {e}[/red]")

def show_chart(ticker):
    try:
        import matplotlib.pyplot as plt
        plt.style.use('dark_background')
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        if hist.empty:
            console.print(f"[red]Brak danych do wykresu dla {ticker}[/red]")
            return
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(hist.index, hist["Close"], color='#1f77b4', linewidth=2.7, marker='o', markersize=4, label='Kurs zamknięcia')
        ax.set_title(f'{ticker.upper()} – Cena zamknięcia (ostatnie 6 miesięcy)', fontsize=16, fontweight="bold", color="white")
        ax.set_xlabel('Data', fontsize=13, color="white")
        ax.set_ylabel('Cena [USD]', fontsize=13, color="white")
        ax.grid(True, linestyle='--', linewidth=0.7, alpha=0.4)
        ax.legend(facecolor='#222222', edgecolor='white', fontsize=12)
        # Mniej dat na osi X dla czytelności:
        ax.xaxis.set_major_locator(plt.MaxNLocator(10))
        plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
        plt.tight_layout()
        plt.show()
    except Exception as e:
        console.print(f"[red]Błąd wyświetlania wykresu: {e}[/red]")



def print_help():
    console.print("""
Dostępne polecenia (w formacie: TICKER opcja [parametry]):
  <TICKER> quote               - Pokazuje notowania
  <TICKER> chart               - Pokazuje wykres (6m)
  <TICKER> watchlist add       - Dodaje spółkę do obserwowanych
  <TICKER> watchlist remove    - Usuwa spółkę z obserwowanych
  watchlist list               - Wyświetla listę obserwowanych
  help                        - Pokazuje tę pomoc
  exit, quit                  - Kończy program
""")

def main():
    watchlist = load_watchlist()
    console.print("[green]Witaj! Wpisuj polecenia w formacie: TICKER opcja. 'help' by zobaczyć listę.[/green]")

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold yellow]Do widzenia![/bold yellow]")
            break

        if not line:
            continue

        parts = line.split()
        if len(parts) == 0:
            continue

        # Obsługa poleceń bez tickerów, np. help, watchlist list, exit
        if parts[0].lower() in ("exit", "quit"):
            console.print("[bold yellow]Do widzenia![/bold yellow]")
            break
        if parts[0].lower() == "help":
            print_help()
            continue

        if parts[0].lower() == "watchlist":
            if len(parts) == 2 and parts[1].lower() == "list":
                if watchlist:
                    table = Table(title="Obserwowane spółki", box=box.SIMPLE)
                    table.add_column("Ticker", style="bold cyan")
                    table.add_column("Aktualna cena", justify="right")
                    table.add_column("Zmiana [%]", justify="right")
                    table.add_column("Różnica dzisiejsza", justify="right")

                    for ticker in sorted(watchlist):
                        try:
                            stock = yf.Ticker(ticker)
                            info = stock.info
                            price = info.get("currentPrice")
                            change = info.get("regularMarketChange")
                            change_percent = info.get("regularMarketChangePercent")

                            if price is None:
                                price_str = "-"
                            else:
                                price_str = f"{price:.2f}"

                            if change is None:
                                change_str = "-"
                            else:
                                change_str = f"{change:.2f}"

                            if change_percent is None:
                                change_percent_str = "-"
                            else:
                                change_percent_str = f"{change_percent*100:.2f}%"

                            def colorize(val):
                                try:
                                    v = float(val.strip('%'))
                                    if v > 0:
                                        return f"[green]{val}[/green]"
                                    elif v < 0:
                                        return f"[red]{val}[/red]"
                                    else:
                                        return val
                                except:
                                    return val

                            change_percent_str = colorize(change_percent_str)
                            change_str = colorize(change_str)

                            table.add_row(ticker, price_str, change_percent_str, change_str)

                        except Exception:
                            table.add_row(ticker, "-", "-", "-")

                    console.print(table)
                else:
                    console.print("[yellow]Lista obserwowanych jest pusta[/yellow]")
            else:
                console.print("[red]Nieznana składnia. Użyj: 'watchlist list'[/red]")



        # Teraz traktujemy pierwszą część jako ticker
        ticker = parts[0].upper()
        if len(parts) < 2:
            console.print(f"[red]Podaj opcję dla tickeru {ticker}. Np. 'quote' lub 'chart' lub 'watchlist add'[/red]")
            continue

        opcja = parts[1].lower()

        if opcja == "quote":
            show_quote(ticker)

        elif opcja == "chart":
            show_chart(ticker)

        elif opcja == "watchlist":
            if len(parts) < 3:
                console.print("[red]Użycie: <TICKER> watchlist add|remove[/red]")
                continue
            subcmd = parts[2].lower()
            if subcmd == "add":
                watchlist.add(ticker)
                save_watchlist(watchlist)
                console.print(f"[green]{ticker} dodane do obserwowanych[/green]")
            elif subcmd == "remove":
                if ticker in watchlist:
                    watchlist.remove(ticker)
                    save_watchlist(watchlist)
                    console.print(f"[green]{ticker} usunięty z obserwowanych[/green]")
                else:
                    console.print(f"[red]{ticker} nie było na liście obserwowanych[/red]")
            else:
                console.print("[red]Nieznana komenda watchlist. Użyj 'add' lub 'remove'.[/red]")

        else:
            console.print(f"[red]Nieznana opcja: {opcja}. Wpisz 'help' aby zobaczyć listę komend.[/red]")

if __name__ == "__main__":
    main()
