# Guida manutenzione documentazione per AI

Usare questa guida ogni volta che si modifica codice, pipeline, formati dati o output. L'obiettivo e mantenere la documentazione coerente senza duplicare spiegazioni lunghe in piu file.

## Regola Base

- `README.md`: breve, con link.
- `Manuale.md`: solo dove mettere i file e quali comandi eseguire.
- `docs/project_map.md`: struttura del progetto.
- `docs/data_format.md`: formati CSV.
- `docs/analysis_pipeline.md`: sequenza comandi.
- `docs/<area>.md`: dettagli di una singola area.

## Checklist Prima di Finire

1. Il comando nuovo o modificato compare in `README.md` solo se e un comando principale.
2. Il comando compare in `Manuale.md` solo se serve nel flusso operativo minimo.
3. Il dettaglio tecnico e in un file `docs/`.
4. I path citati esistono o vengono generati dalla pipeline.
5. Non ci sono riferimenti a comandi rimossi.
6. Non ci sono output generati versionati per sbaglio.
7. `python -m pytest` passa.

## Template per Nuove Pagine Docs

````md
# Titolo

Breve scopo della pagina.

## Quando usarlo

Situazione in cui serve questa parte del toolkit.

## Input

```txt
path/input.csv
```

## Comandi

```powershell
python -m src.cli ...
```

## Output

```txt
path/output/
```

## Note

Decisioni di design, limiti e parti manuali.
````

## Template per Aggiornare un Comando

````md
Comando:

```powershell
python -m src.cli nome-comando --opzione valore
```

Input:

```txt
path/input
```

Output:

```txt
path/output
```

Errori comuni:

- Messaggio o condizione.
````

## Decisioni Correnti da Preservare

- La deduplicazione dei problemi euristici e manuale.
- I dark pattern non sono una pipeline automatica.
- `outputs/`, `reports/` e `data/processed/` contengono artefatti rigenerabili.
- `src/cli.py` e l'entry point centrale.
- `main.py` resta un wrapper sottile.
