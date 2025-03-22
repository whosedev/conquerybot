# ConqueryBot

Bot Discord z systemem poziomów i ekonomii.

## Instalacja

1. Zainstaluj wymagane pakiety:
```bash
pip install -r requirements.txt
```

2. Skonfiguruj plik .env z odpowiednimi danymi:
- DISCORD_TOKEN - token bota Discord
- DB_HOST - adres hosta bazy danych
- DB_PORT - port bazy danych
- DB_NAME - nazwa bazy danych
- DB_USER - użytkownik bazy danych
- DB_PASSWORD - hasło do bazy danych

3. Uruchom bota:
```bash
python main.py
```

## Struktura projektu

- `main.py` - główny plik bota
- `cogs/` - katalog z modułami bota
- `utils/` - katalog z funkcjami pomocniczymi
- `.env` - plik z danymi wrażliwymi
- `requirements.txt` - lista zależności 