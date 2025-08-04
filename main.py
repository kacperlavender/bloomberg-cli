import yfinance as yf
from rich.console import Console
from rich.table import Table
from rich import box
import matplotlib.pyplot as plt
import pickle
import os
from rich.text import Text
import requests
from dotenv import load_dotenv

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
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


def show_chart_terminal(ticker):
    try:
        import plotext as plt
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        if hist.empty:
            console.print(f"[red]Brak danych do wykresu dla {ticker}[/red]")
            return

        dates = [d.strftime("%d/%m/%Y") for d in hist.index]
        prices = hist["Close"].tolist()

        plt.clf()
        # plt.canvas_color("black")
        # plt.axes_color("black")
        plt.canvas_color("black")      # super-ciemne tło AMOLED
        plt.axes_color("black")        # tak samo osie
        plt.ticks_color("white")
        plt.plot(
            dates, prices,
            marker='dot',
            color='cyan',   # Linia i markery są w tym samym kolorze
            # label='Cena'
        )
        # plt.title(f"{ticker.upper()} - Cena zamknięcia (6 miesięcy)")
        # plt.xlabel("Data")
        # plt.ylabel("Cena [USD]")
        plt.show()
    except Exception as e:
        console.print(f"[red]Błąd wyświetlania wykresu w terminalu: {e}[/red]")



def market_summary():
    indices = {
        '^GSPC': 'S&P 500',
        '^DJI': 'Dow Jones',
        '^IXIC': 'Nasdaq',
        '^WIG20.WA': 'WIG20',
    }

    table = Table(title="Market Summary", box=box.SIMPLE)
    table.add_column("Index")
    table.add_column("Value", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("Change %", justify="right")

    for symbol, name in indices.items():
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice") or info.get("previousClose")
        change = info.get("regularMarketChange")
        change_percent = info.get("regularMarketChangePercent")

        price_str = f"{price:.2f}" if price else "-"
        change_str = f"{change:.2f}" if change else "-"
        change_pct_str = f"{change_percent*100:.2f}%" if change_percent else "-"

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

        change_str = colorize(change_str)
        change_pct_str = colorize(change_pct_str)

        table.add_row(name, price_str, change_str, change_pct_str)

    console.print(table)

def get_news(ticker):
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from=2023-01-01&to=2025-12-31&token={FINNHUB_API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code != 200:
            console.print(f"[red]Błąd pobierania newsów: {response.status_code}[/red]")
            return

        news = response.json()
        if not news:
            console.print(f"[yellow]Brak aktualnych wiadomości dla {ticker}[/yellow]")
            return

        table = Table(title=f"News dla {ticker}", box=box.SIMPLE)
        table.add_column("Data", style="dim")
        table.add_column("Tytuł")
        table.add_column("Link", overflow="fold")

        for item in sorted(news, key=lambda x: x['datetime'], reverse=True)[:5]:
            date_str = item.get('datetime')
            from datetime import datetime
            date_fmt = datetime.utcfromtimestamp(item['datetime']).strftime('%Y-%m-%d')
            title = item.get('headline') or item.get('summary') or "-"
            url = item.get('url') or "-"
            table.add_row(date_fmt, title, url)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Błąd pobierania newsów: {e}[/red]")

def show_eq_line(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        price = info.get("currentPrice")
        day_change = info.get("regularMarketChange")
        day_change_pct = info.get("regularMarketChangePercent")

        # Pobierz tydzień historii
        hist = stock.history(period="7d")
        week_change_pct_str = "-"

        if not hist.empty and len(hist) >= 2:
            price_today = hist['Close'].iloc[-1]
            price_week_ago = hist['Close'].iloc[0]

            week_change_pct = ((price_today - price_week_ago) / price_week_ago) * 100 if price_week_ago else None
            if week_change_pct is not None:
                week_change_pct_str = f"{week_change_pct:+.2f}%"
        else:
            week_change_pct_str = "-"

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

        price_str = f"{price:.2f}" if price is not None else "-"
        day_change_pct_str = f"{day_change_pct*100:+.2f}%" if day_change_pct is not None else "-"
        day_change_str = f"{day_change:+.2f}" if day_change is not None else "-"

        output = (
            f"{ticker.upper()}  "
            f"{price_str}  "
            f"{colorize(day_change_pct_str)}  "
            f"{colorize(day_change_str)}  "
            f"{colorize(week_change_pct_str)}"
        )
        console.print(output)
    except Exception as e:
        console.print(f"[red]Błąd EQ: {e}[/red]")

WALLET_FILE = "wallet.pkl"

def load_wallet():
    if os.path.exists(WALLET_FILE):
        with open(WALLET_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_wallet(wallet):
    with open(WALLET_FILE, "wb") as f:
        pickle.dump(wallet, f)

def wallet_add(ticker, quantity, price):
    wallet = load_wallet()
    if ticker in wallet:
        wallet[ticker].append([quantity, price])
    else:
        wallet[ticker] = [[quantity, price]]
    save_wallet(wallet)
    console.print(f"[green]Dodano {quantity} akcji {ticker} po {price}[/green]")

def wallet_remove(ticker):
    wallet = load_wallet()
    if ticker in wallet:
        del wallet[ticker]
        save_wallet(wallet)
        console.print(f"[green]Usunięto {ticker} z portfela[/green]")
    else:
        console.print(f"[yellow]{ticker} nie był w portfelu[/yellow]")

def wallet_summary():
    wallet = load_wallet()
    if not wallet:
        console.print("[yellow]Portfel jest pusty[/yellow]")
        return
    table = Table(title="Portfel inwestycyjny", box=box.SIMPLE)
    table.add_column("Ticker", style="bold cyan")
    table.add_column("Ilość", justify="right")
    table.add_column("Śr. cena zakupu", justify="right")
    table.add_column("Wartość zakupu", justify="right")
    table.add_column("Aktualna cena", justify="right")
    table.add_column("Wartość rynkowa", justify="right")
    table.add_column("Zysk / Strata", justify="right")
    table.add_column("Zysk %", justify="right")
    total_value = 0
    total_cost = 0
    for ticker, pozycje in wallet.items():
        qty_sum = sum(q for q, p in pozycje)
        avg_price = sum(q * p for q, p in pozycje) / qty_sum if qty_sum else 0
        cost = qty_sum * avg_price
        try:
            price = yf.Ticker(ticker).info.get("currentPrice") or 0
        except:
            price = 0
        market_value = qty_sum * price
        zysk = market_value - cost
        zysk_pct = (zysk / cost * 100) if cost else 0
        table.add_row(
            ticker, str(qty_sum), f"{avg_price:.2f}", f"{cost:.2f}", 
            f"{price:.2f}", f"{market_value:.2f}", 
            f"[green]{zysk:+.2f}[/green]" if zysk >= 0 else f"[red]{zysk:+.2f}[/red]",
            f"[green]{zysk_pct:+.2f}%[/green]" if zysk_pct >= 0 else f"[red]{zysk_pct:+.2f}%[/red]"
        )
        total_value += market_value
        total_cost += cost
    table.add_row(
        "[b]SUMA[/b]", "", "", f"{total_cost:.2f}", "", f"{total_value:.2f}",
        f"[green]{(total_value-total_cost):+.2f}[/green]" if total_value-total_cost >= 0 else f"[red]{(total_value-total_cost):+.2f}[/red]",
        f"[green]{((total_value-total_cost)/total_cost*100):+.2f}%[/green]" if total_cost else "-"
    )
    console.print(table)



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

         # Dodaj tutaj obsługę portfela:
        if parts[0].lower() == "wallet":
            if len(parts) == 1:
                wallet_summary()
            elif parts[1].lower() == "add" and len(parts) >= 5:
                ticker = parts[2].upper()
                try:
                    quantity = float(parts[3])
                    price = float(parts[4])
                    wallet_add(ticker, quantity, price)
                except:
                    console.print("[red]Podaj poprawne liczby: wallet add <TICKER> <ILOŚĆ> <CENA>[/red]")
            elif parts[1].lower() == "remove" and len(parts) >= 3:
                ticker = parts[2].upper()
                wallet_remove(ticker)
            else:
                console.print("[yellow]Dostępne komendy: wallet, wallet add <TICKER> ILOŚĆ CENA, wallet remove <TICKER>[/yellow]")
            continue  # kontynuuj, nie przetwarzaj dalej


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



        if parts[0].lower() == "market" and len(parts) > 1 and parts[1].lower() == "summary":
            market_summary()
            continue

        # Poza tym
        ticker = parts[0].upper()
        if len(parts) < 2:
            console.print(f"[red]Podaj opcję dla tickeru {ticker}. Np. 'quote', 'chart', 'news', 'watchlist add'[/red]")
            continue

        opcja = parts[1].lower()

        

        if opcja == "news":
            get_news(ticker)
        elif opcja == "quote":
            show_quote(ticker)
        elif opcja == "chart":
            show_chart_terminal(ticker)  # Wykres w terminalu
        elif opcja == "chart-gui":
            show_chart(ticker)           # Klasyczny wykres matplotlib
        elif opcja == "eq":
            show_eq_line(ticker)
        # dalej jak było...


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
