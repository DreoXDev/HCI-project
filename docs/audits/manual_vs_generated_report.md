# Manual vs Generated Report Audit

- Manual PDF: `C:\Users\User\Downloads\Presentazione1.pptx-1.pdf`
- Generated PDF: `C:\Users\User\Downloads\final_report.pptx.pdf`
- Manual pages: 163
- Generated pages: 121

## Source Of Truth Rules

| Tipo contenuto | Source of truth preferita |
| --- | --- |
| Dati numerici, metriche, grafici, UEQ, benchmark, p-value | Toolchain / CSV / Python |
| Testi editoriali approvati a mano | Presentazione manuale, se piu curata e non obsoleta |
| Titoli sezioni e ordine finale delle macro-sezioni | Presentazione manuale, se coerente con la struttura finale |
| Dati App Store, download, rating, date | Config/dati aggiornati della toolchain, non testo vecchio manuale |
| Appendici e materiali finali | Presentazione manuale, salvo duplicati/ridondanze |
| Layout/stile grafico generale | Template PPTX + config tema |

## Estimated Page Mapping

| manual | manual title | generated | generated title | score | review |
| --- | --- | --- | --- | --- | --- |
| 1 | Progetto HCI | 1 | Progetto HCI | 0.97 | no |
| 2 | Indice | 2 | Indice | 0.71 | no |
| 3 | Introduzione | 3 | Introduzione | 1.00 | no |
| 4 | Descrizione del problema | 4 | Descrizione del problema | 0.72 | no |
| 5 | Ambiente di valutazione | 5 | Ambiente di valutazione | 1.00 | no |
| 6 | Deliveroo | 6 | Deliveroo | 0.85 | no |
| 7 | Glovo | 7 | Glovo | 0.94 | no |
| 8 | Valutazione euristica | 8 | Valutazione euristica | 1.00 | no |
| 9 | Obiettivo | 9 | Obiettivo | 1.00 | no |
| 10 | Set di euristiche | 10 | Set di euristiche | 0.69 | no |
| 11 | Valutatori | 11 | Valutatori | 1.00 | no |
| 12 | Tabella dei valutatori | 12 | Tabella dei valutatori | 0.71 | no |
| 13 | Composizione valutatori - dati demograﬁci | 13 | Composizione valutatori - dati demograﬁci | 0.71 | no |
| 14 | Composizione valutatori - occupazione ed esperienza | 14 | Composizione valutatori - proﬁlo ed esperienza | 0.60 | no |
| 15 | Matrice di expertise | 15 | Matrice di expertise | 0.67 | no |
| 16 | Problemi riscontrati | 16 | Problemi riscontrati | 1.00 | no |
| 17 | Criteri di prioritizzazione | 17 | Criteri di prioritizzazione | 0.73 | no |
| 18 | Classiﬁcazione in fasce di priorità | 18 | Classiﬁcazione in fasce di priorità | 0.70 | no |
| 19 | Problemi Deliveroo (1/4) | 19 | Problemi Deliveroo (1/4) | 0.95 | no |
| 20 | Problemi Deliveroo (2/4) | 20 | Problemi Deliveroo (2/4) | 0.96 | no |
| 21 | Problemi Deliveroo (3/4) | 21 | Problemi Deliveroo (3/4) | 0.78 | no |
| 22 | Problemi Deliveroo (4/4) | 22 | Problemi Deliveroo (4/4) | 0.90 | no |
| 23 | Problemi rilevanti - Deliveroo | 28 | Problemi rilevanti - Deliveroo | 0.67 | no |
| 24 | Distribuzione delle euristiche - Deliveroo | 33 | Distribuzione delle euristiche | 0.63 | no |
| 25 | Matrice problemi-valutatori Deliveroo | 31 | Matrice problemi-valutatori Deliveroo | 0.69 | no |
| 26 | Dark pattern - Misdirection | 35 | Dark pattern e frizioni | 0.49 | yes |
| 27 | Problemi Glovo (1/4) | 23 | Problemi Glovo (1/4) | 0.66 | no |
| 28 | Problemi Glovo (2/4) | 24 | Problemi Glovo (2/4) | 0.80 | no |
| 29 | Problemi Glovo (3/4) | 25 | Problemi Glovo (3/4) | 0.66 | no |
| 30 | Problemi Glovo (4/4) | 26 | Problemi Glovo (4/4) | 0.88 | no |
| 31 | Problemi rilevanti - Glovo | 29 | Problemi rilevanti - Glovo | 0.68 | no |
| 32 | Distribuzione delle euristiche - Glovo | 33 | Distribuzione delle euristiche | 0.67 | no |
| 33 | Matrice problemi-valutatori Glovo | 32 | Matrice problemi-valutatori Glovo | 0.70 | no |
| 34 | Dark pattern - Disguised Ads | 35 | Dark pattern e frizioni | 0.45 | yes |
| 35 | Valutazione euristica - Conclusioni e confronti | 8 | Valutazione euristica | 0.39 | yes |
| 36 | Test utente | 40 | Test utente | 0.99 | no |
| 37 | Obiettivo | 41 | Obiettivo | 0.68 | no |
| 38 | I tre task | 58 | Errori - Task 1 | 0.39 | yes |
| 39 | 1° Task | 58 | Errori - Task 1 | 0.35 | yes |
| 40 | Deliveroo | 6 | Deliveroo | 0.62 | no |
| 41 | Glovo | 7 | Glovo | 0.62 | no |
| 42 | 2° Task | 58 | Errori - Task 1 | 0.40 | yes |
| 43 | Deliveroo | 6 | Deliveroo | 0.62 | no |
| 44 | Glovo | 7 | Glovo | 0.62 | no |
| 45 | 3° Task | 58 | Errori - Task 1 | 0.40 | yes |
| 46 | Deliveroo | 6 | Deliveroo | 0.62 | no |
| 47 | Glovo | 7 | Glovo | 0.62 | no |
| 48 | Composizione del campione - 1/4 | 54 | Composizione del campione | 0.63 | no |
| 49 | Composizione del campione - 2/4 | 54 | Composizione del campione | 0.64 | no |
| 50 | Composizione del campione - 3/4 | 54 | Composizione del campione | 0.64 | no |
| 51 | Composizione del campione - 4/4 | 54 | Composizione del campione | 0.63 | no |
| 52 | Composizione del campione utenti | 54 | Composizione del campione | 0.64 | no |
| 53 | Composizione utenti - occupazione e familiarità | 76 | Composizione utenti - familiarità e proﬁlo | 0.48 | yes |
| 54 | Efficacia | 56 | Efficacia | 0.69 | no |
| 55 | Efficacia | 56 | Efficacia | 0.76 | no |
| 56 | Efficacia - Task 1 | 57 | Efficacia - Task 1 | 0.67 | no |
| 57 | Efficacia - Task 2 | 59 | Efficacia - Task 2 | 0.67 | no |
| 58 | Efficacia - Task 3 | 61 | Efficacia - Task 3 | 0.67 | no |
| 59 | Efficacia Assoluta - Task 1 | 57 | Efficacia - Task 1 | 0.53 | yes |
| 60 | Efficacia Assoluta - Task 2 | 59 | Efficacia - Task 2 | 0.53 | yes |
| 61 | Efficacia Assoluta - Task 3 | 61 | Efficacia - Task 3 | 0.54 | yes |
| 62 | Efficienza | 63 | Efficienza | 0.70 | no |
| 63 | Efficienza - Tempi users | 64 | Efficienza - Task 1 | 0.46 | yes |
| 64 | Efficienza - Tempi users | 64 | Efficienza - Task 1 | 0.46 | yes |
| 65 | Efficienza - Task 1 | 64 | Efficienza - Task 1 | 0.67 | no |
| 66 | Efficienza - Task 2 | 65 | Efficienza - Task 2 | 0.67 | no |
| 67 | Efficienza - Task 3 | 66 | Efficienza - Task 3 | 0.67 | no |
| 68 | Efficienza Assoluta - Task 1 | 64 | Efficienza - Task 1 | 0.56 | no |
| 69 | Efficienza Assoluta - Task 2 | 65 | Efficienza - Task 2 | 0.57 | no |
| 70 | Efficienza Assoluta - Task 3 | 66 | Efficienza - Task 3 | 0.57 | no |
| 71 | Test utente - Conclusioni e confronti | 105 | Conclusioni: confronto complessivo | 0.36 | yes |
| 72 | Test utente - Conclusioni e confronti | 105 | Conclusioni: confronto complessivo | 0.36 | yes |
| 73 | Questionario | 73 | Questionario | 1.00 | no |
| 74 | Introduzione al questionario | 74 | Questionario | 0.41 | yes |
| 75 | Risultati del questionario | 96 | Sintesi dei risultati del questionario | 0.51 | yes |
| 76 | Domanda 1 - Fastidioso - Piacevole | 77 | Domanda 1 | 0.45 | yes |
| 77 | Domanda 2 - Incomprensibile - Comprensibile | 86 | Domanda 21 | 0.33 | yes |
| 78 | Domanda 3 - Creativo - Privo di fantasia | 78 | Domanda 3 | 0.43 | yes |
| 79 | Domanda 4 - Facile da apprendere - Difficile da | 91 | Confronto statistico - Domanda 4 | 0.33 | yes |
| 80 | Domanda 5 - Di grande valore - Di poco valore | 79 | Domanda 5 | 0.41 | yes |
| 81 | Domanda 6 - Noioso - Appassionante | 78 | Domanda 3 | 0.38 | yes |
| 82 | Domanda 7 - Non interessante - Interessante | 80 | Domanda 7 | 0.42 | yes |
| 83 | Domanda 8 - Imprevedibile - Prevedibile | 83 | Domanda 13 | 0.35 | yes |
| 84 | Domanda 9 - Veloce - Lento | 81 | Domanda 9 | 0.51 | yes |
| 85 | Domanda 10 - Originale - Convenzionale | 83 | Domanda 13 | 0.37 | yes |
| 86 | Domanda 11 - Ostruttivo - Di supporto | 82 | Domanda 11 | 0.46 | yes |
| 87 | Domanda 12 - Buono - Scarso | 85 | Domanda 17 | 0.47 | yes |
| 88 | Domanda 13 - Complicato - Facile | 83 | Domanda 13 | 0.48 | yes |
| 89 | Domanda 14 - Repellente - Attraente | 86 | Domanda 21 | 0.40 | yes |
| 90 | Domanda 15 - Usuale - Moderno | 84 | Domanda 15 | 0.49 | yes |
| 91 | Domanda 16 - Sgradevole - Gradevole | 77 | Domanda 1 | 0.39 | yes |
| 92 | Domanda 17 - Sicuro - Insicuro | 85 | Domanda 17 | 0.49 | yes |
| 93 | Domanda 18 - Attivante - Soporifero | 85 | Domanda 17 | 0.41 | yes |
| 94 | Domanda 19 - Conforme alle aspettative - Non conforme alle | 33 | Distribuzione delle euristiche | 0.28 | yes |
| 95 | Domanda 20 - Inefficiente - Efficiente | 86 | Domanda 21 | 0.36 | yes |
| 96 | Domanda 21 - Chiaro - Confuso | 86 | Domanda 21 | 0.50 | yes |
| 97 | Domanda 22 - Non pragmatico - Pragmatico | 88 | Domanda 25 | 0.35 | yes |
| 98 | Domanda 23 - Ordinato - Sovraccarico | 87 | Domanda 23 | 0.46 | yes |
| 99 | Domanda 24 - Invitante - Non invitante | 88 | Domanda 25 | 0.37 | yes |
| 100 | Domanda 25 - Congeniale - Ostile | 88 | Domanda 25 | 0.47 | yes |
| 101 | Domanda 26 - Conservativo - Innovativo | 86 | Domanda 21 | 0.36 | yes |
| 102 | Confronto tra sistemi | 89 | Confronto tra sistemi | 0.65 | no |
| 103 | Confronto statistico - Domanda 1 | 90 | Confronto statistico - Domanda 1 | 0.74 | no |
| 104 | Confronto statistico - Domanda 4 | 91 | Confronto statistico - Domanda 4 | 0.77 | no |
| 105 | Confronto statistico - Domanda 9 | 92 | Confronto statistico - Domanda 9 | 0.74 | no |
| 106 | Confronto statistico - Domanda 13 | 93 | Confronto statistico - Domanda 13 | 0.75 | no |
| 107 | Confronto statistico - Domanda 23 | 94 | Confronto statistico - Domanda 23 | 0.73 | no |
| 108 | La Scala UEQ | 97 | La scala UEQ | 0.64 | no |
| 109 | UEQ - Analisi dei sottogruppi - Deliveroo | 98 | Scala UEQ - analisi dei sottogruppi | 0.56 | no |
| 110 | UEQ - Analisi dei dati - Deliveroo (1/2) | 99 | Analisi dei dati UEQ | 0.42 | yes |
| 111 | UEQ - Analisi dei dati - Deliveroo (2/2) | 99 | Analisi dei dati UEQ | 0.42 | yes |
| 112 | UEQ - Media risultati Deliveroo | 100 | Media risultati UEQ | 0.52 | yes |
| 113 | UEQ - Distribuzione delle risposte per domanda Deliveroo | 33 | Distribuzione delle euristiche | 0.50 | yes |
| 114 | Benchmark UEQ - Deliveroo | 22 | Problemi Deliveroo (4/4) | 0.35 | yes |
| 115 | UEQ - Analisi dei sottogruppi - Glovo | 98 | Scala UEQ - analisi dei sottogruppi | 0.57 | no |
| 116 | UEQ - Analisi dei dati - Glovo (1/2) | 99 | Analisi dei dati UEQ | 0.41 | yes |
| 117 | UEQ - Analisi dei dati - Glovo (2/2) | 99 | Analisi dei dati UEQ | 0.41 | yes |
| 118 | UEQ - Media risultati Glovo | 100 | Media risultati UEQ | 0.50 | yes |
| 119 | UEQ - Distribuzione delle risposte per domanda Glovo | 33 | Distribuzione delle euristiche | 0.49 | yes |
| 120 | Benchmark UEQ - Glovo | 23 | Problemi Glovo (1/4) | 0.29 | yes |
| 121 | Net Promoter Score | 103 | Net Promoter Score: raccomandabilita | 0.42 | yes |
| 122 | Net Promoter Score - Deliveroo e Glovo | 103 | Net Promoter Score: raccomandabilita | 0.38 | yes |
| 123 | Conclusioni | 73 | Questionario | 0.30 | yes |
| 124 | Appendici | 109 | Appendice | 0.86 | no |
| 125 | Appendice A - Valutazione euristica EU1 | 8 | Valutazione euristica | 0.67 | no |
| 126 | Appendice A - Valutazione euristica EU1 | 8 | Valutazione euristica | 0.67 | no |
| 127 | Appendice A - Valutazione euristica EU2 | 8 | Valutazione euristica | 0.67 | no |
| 128 | Appendice A - Valutazione euristica EU2 | 8 | Valutazione euristica | 0.67 | no |
| 129 | Appendice A - Valutazione euristica EU3 | 8 | Valutazione euristica | 0.67 | no |
| 130 | Appendice A - Valutazione euristica EU3 | 8 | Valutazione euristica | 0.67 | no |
| 131 | Appendice A - Valutazione euristica EU4 | 8 | Valutazione euristica | 0.67 | no |
| 132 | Appendice A - Valutazione euristica EU4 | 8 | Valutazione euristica | 0.67 | no |
| 133 | Appendice A - Valutazione euristica ED1 | 8 | Valutazione euristica | 0.67 | no |
| 134 | Appendice A - Valutazione euristica ED1 | 8 | Valutazione euristica | 0.67 | no |
| 135 | Appendice A - Valutazione euristica ED2 | 8 | Valutazione euristica | 0.67 | no |
| 136 | Appendice A - Valutazione euristica ED2 | 8 | Valutazione euristica | 0.67 | no |
| 137 | Appendice A - Valutazione euristica ED3 | 8 | Valutazione euristica | 0.67 | no |
| 138 | Appendice A - Valutazione euristica ED3 | 8 | Valutazione euristica | 0.67 | no |
| 139 | Appendice A - Valutazione euristica ED4 | 8 | Valutazione euristica | 0.67 | no |
| 140 | Appendice A - Valutazione euristica ED4 | 8 | Valutazione euristica | 0.67 | no |
| 141 | Appendice B - Modulo autorizzazione foto e | 117 | Appendice A8 - Export valutazione problemi | 0.38 | yes |
| 142 | Appendice C - Valutazione dei problemi di | 117 | Appendice A8 - Export valutazione problemi | 0.55 | no |
| 143 | Appendice C - Valutazione dei problemi di | 117 | Appendice A8 - Export valutazione problemi | 0.55 | no |
| 144 | Presentazione dei task per lo user test | 15 | Matrice di expertise | 0.37 | yes |
| 145 | Introduzione e come funziona | 3 | Introduzione | 0.56 | no |
| 146 | Introduzione e come funziona | 3 | Introduzione | 0.56 | no |
| 147 | Di seguito, le task presentate agli utenti - Deliveroo | 100 | Media risultati UEQ | 0.31 | yes |
| 148 | Deliveroo - Task 1 | 58 | Errori - Task 1 | 0.52 | yes |
| 149 | Deliveroo - Task 2 | 60 | Errori - Task 2 | 0.51 | yes |
| 150 | Deliveroo - Task 3 | 62 | Errori - Task 3 | 0.51 | yes |
| 151 | Di seguito, le task presentate agli utenti - Glovo | 100 | Media risultati UEQ | 0.31 | yes |
| 152 | Glovo - Task 1 | 58 | Errori - Task 1 | 0.49 | yes |
| 153 | Glovo - Task 2 | 60 | Errori - Task 2 | 0.48 | yes |
| 154 | Glovo - Task 3 | 62 | Errori - Task 3 | 0.48 | yes |
| 155 | Conclusione | 3 | Introduzione | 0.48 | yes |
| 156 | Questionario | 73 | Questionario | 0.96 | no |
| 157 | Page 157 | 45 | Page 45 | 0.83 | no |
| 158 | Page 158 | 45 | Page 45 | 0.83 | no |
| 159 | Page 159 | 45 | Page 45 | 0.83 | no |
| 160 | Page 160 | 46 | Page 46 | 0.83 | no |
| 161 | Page 161 | 46 | Page 46 | 0.83 | no |
| 162 | Links | 104 | Sintesi ﬁnale | 0.25 | yes |
| 163 | Grazie | 100 | Media risultati UEQ | 0.28 | yes |

## Manual Slides Needing Review

| manual | title | best generated | score |
| --- | --- | --- | --- |
| 26 | Dark pattern - Misdirection | 35 | 0.49 |
| 34 | Dark pattern - Disguised Ads | 35 | 0.45 |
| 35 | Valutazione euristica - Conclusioni e confronti | 8 | 0.39 |
| 38 | I tre task | 58 | 0.39 |
| 39 | 1° Task | 58 | 0.35 |
| 42 | 2° Task | 58 | 0.40 |
| 45 | 3° Task | 58 | 0.40 |
| 53 | Composizione utenti - occupazione e familiarità | 76 | 0.48 |
| 59 | Efficacia Assoluta - Task 1 | 57 | 0.53 |
| 60 | Efficacia Assoluta - Task 2 | 59 | 0.53 |
| 61 | Efficacia Assoluta - Task 3 | 61 | 0.54 |
| 63 | Efficienza - Tempi users | 64 | 0.46 |
| 64 | Efficienza - Tempi users | 64 | 0.46 |
| 71 | Test utente - Conclusioni e confronti | 105 | 0.36 |
| 72 | Test utente - Conclusioni e confronti | 105 | 0.36 |
| 74 | Introduzione al questionario | 74 | 0.41 |
| 75 | Risultati del questionario | 96 | 0.51 |
| 76 | Domanda 1 - Fastidioso - Piacevole | 77 | 0.45 |
| 77 | Domanda 2 - Incomprensibile - Comprensibile | 86 | 0.33 |
| 78 | Domanda 3 - Creativo - Privo di fantasia | 78 | 0.43 |
| 79 | Domanda 4 - Facile da apprendere - Difficile da | 91 | 0.33 |
| 80 | Domanda 5 - Di grande valore - Di poco valore | 79 | 0.41 |
| 81 | Domanda 6 - Noioso - Appassionante | 78 | 0.38 |
| 82 | Domanda 7 - Non interessante - Interessante | 80 | 0.42 |
| 83 | Domanda 8 - Imprevedibile - Prevedibile | 83 | 0.35 |
| 84 | Domanda 9 - Veloce - Lento | 81 | 0.51 |
| 85 | Domanda 10 - Originale - Convenzionale | 83 | 0.37 |
| 86 | Domanda 11 - Ostruttivo - Di supporto | 82 | 0.46 |
| 87 | Domanda 12 - Buono - Scarso | 85 | 0.47 |
| 88 | Domanda 13 - Complicato - Facile | 83 | 0.48 |
| 89 | Domanda 14 - Repellente - Attraente | 86 | 0.40 |
| 90 | Domanda 15 - Usuale - Moderno | 84 | 0.49 |
| 91 | Domanda 16 - Sgradevole - Gradevole | 77 | 0.39 |
| 92 | Domanda 17 - Sicuro - Insicuro | 85 | 0.49 |
| 93 | Domanda 18 - Attivante - Soporifero | 85 | 0.41 |
| 94 | Domanda 19 - Conforme alle aspettative - Non conforme alle | 33 | 0.28 |
| 95 | Domanda 20 - Inefficiente - Efficiente | 86 | 0.36 |
| 96 | Domanda 21 - Chiaro - Confuso | 86 | 0.50 |
| 97 | Domanda 22 - Non pragmatico - Pragmatico | 88 | 0.35 |
| 98 | Domanda 23 - Ordinato - Sovraccarico | 87 | 0.46 |
| 99 | Domanda 24 - Invitante - Non invitante | 88 | 0.37 |
| 100 | Domanda 25 - Congeniale - Ostile | 88 | 0.47 |
| 101 | Domanda 26 - Conservativo - Innovativo | 86 | 0.36 |
| 110 | UEQ - Analisi dei dati - Deliveroo (1/2) | 99 | 0.42 |
| 111 | UEQ - Analisi dei dati - Deliveroo (2/2) | 99 | 0.42 |
| 112 | UEQ - Media risultati Deliveroo | 100 | 0.52 |
| 113 | UEQ - Distribuzione delle risposte per domanda Deliveroo | 33 | 0.50 |
| 114 | Benchmark UEQ - Deliveroo | 22 | 0.35 |
| 116 | UEQ - Analisi dei dati - Glovo (1/2) | 99 | 0.41 |
| 117 | UEQ - Analisi dei dati - Glovo (2/2) | 99 | 0.41 |
| 118 | UEQ - Media risultati Glovo | 100 | 0.50 |
| 119 | UEQ - Distribuzione delle risposte per domanda Glovo | 33 | 0.49 |
| 120 | Benchmark UEQ - Glovo | 23 | 0.29 |
| 121 | Net Promoter Score | 103 | 0.42 |
| 122 | Net Promoter Score - Deliveroo e Glovo | 103 | 0.38 |
| 123 | Conclusioni | 73 | 0.30 |
| 141 | Appendice B - Modulo autorizzazione foto e | 117 | 0.38 |
| 144 | Presentazione dei task per lo user test | 15 | 0.37 |
| 147 | Di seguito, le task presentate agli utenti - Deliveroo | 100 | 0.31 |
| 148 | Deliveroo - Task 1 | 58 | 0.52 |
| 149 | Deliveroo - Task 2 | 60 | 0.51 |
| 150 | Deliveroo - Task 3 | 62 | 0.51 |
| 151 | Di seguito, le task presentate agli utenti - Glovo | 100 | 0.31 |
| 152 | Glovo - Task 1 | 58 | 0.49 |
| 153 | Glovo - Task 2 | 60 | 0.48 |
| 154 | Glovo - Task 3 | 62 | 0.48 |
| 155 | Conclusione | 3 | 0.48 |
| 162 | Links | 104 | 0.25 |
| 163 | Grazie | 100 | 0.28 |

## Generated Slides Without Strong Manual Match

| generated | title | fingerprint |
| --- | --- | --- |
| 27 | Sintesi della valutazione euristica | 006ad75e1fd3 |
| 30 | criticità trasversali comuni | 3809477ed5f8 |
| 34 | Valutazione quantitativa | 6ad35964502d |
| 36 | Dark pattern e frizioni persuasive | 9ab800de78b8 |
| 37 | Dark pattern osservati - Deliveroo | 69385a3ce341 |
| 38 | Dark pattern osservati - Glovo | 1980d5ffdd72 |
| 39 | Impatto dei dark pattern sul ﬂusso d'ordine | e539dcedfd41 |
| 42 | Page 42 | da39a3ee5e6b |
| 43 | Page 43 | da39a3ee5e6b |
| 44 | Page 44 | da39a3ee5e6b |
| 47 | Page 47 | da39a3ee5e6b |
| 48 | Page 48 | da39a3ee5e6b |
| 49 | Page 49 | da39a3ee5e6b |
| 50 | Page 50 | da39a3ee5e6b |
| 51 | Page 51 | da39a3ee5e6b |
| 52 | Page 52 | da39a3ee5e6b |
| 53 | Page 53 | da39a3ee5e6b |
| 55 | Legenda efficacia | c86b7489e532 |
| 67 | Successo e distribuzione tempi | 673371d340fd |
| 68 | Tempi, successo ed errori | 5d074dc770f7 |
| 69 | Confronto statistico dei task | 54f2cfae0f5b |
| 70 | Confronto statistico dei task - tabella | 6b2c7aba48ac |
| 71 | Efficacia ed efficienza: lettura congiunta | 02a15808a7f1 |
| 72 | Osservazioni qualitative durante i test | d2ef754baaa4 |
| 75 | Composizione utenti - dati demograﬁci | cdbf99268bba |
| 95 | Confronto statistico item chiave | e6b4c32cb360 |
| 101 | Interpretazione delle scale UEQ | 9672c553cb1e |
| 102 | UEQ: conferme e contraddizioni rispetto ai test | 4688a400a148 |
| 106 | Evidenze integrate | 3915b8c803b4 |
| 107 | Raccomandazioni prioritarie | 33d212c33261 |
| 108 | Verdetto ﬁnale | d8a4ff8d121b |
| 110 | Appendice A1 - Screenshot delle applicazioni | eb9ec6b93a4d |
| 111 | Appendice A2 - Evidenze visive problemi | ddce09ac3dae |
| 112 | Appendice A3 - Evidenze visive problemi Glovo | b3c0d938db01 |
| 113 | Appendice A4 - Evidenze visive dark pattern | 510d7c8a004f |
| 114 | Appendice A5 - Materiali dei test utente | f9c5136fbc58 |
| 115 | Appendice A6 - Tabelle complete tempi utente | 47ec2847747b |
| 116 | Appendice A7 - Note qualitative dei test | 58cda7188cff |
| 118 | Appendice A9 - Export questionario utenti | c7cadf105de4 |
| 119 | Appendice A10 - Tabelle dei calcoli statistici | 496b32a2a24b |
| 120 | Appendice A11 - Tabelle problemi complete | c521b6ed7494 |
| 121 | Appendice A12 - Repository e materiali ﬁnali | 22cdfd93cc8d |

## Same Title But Different Text

| manual | generated | title | score |
| --- | --- | --- | --- |
| 1 | 1 | Progetto HCI | 0.97 |
| 2 | 2 | Indice | 0.71 |
| 4 | 4 | Descrizione del problema | 0.72 |
| 6 | 6 | Deliveroo | 0.85 |
| 7 | 7 | Glovo | 0.94 |
| 10 | 10 | Set di euristiche | 0.69 |
| 12 | 12 | Tabella dei valutatori | 0.71 |
| 13 | 13 | Composizione valutatori - dati demograﬁci | 0.71 |
| 15 | 15 | Matrice di expertise | 0.67 |
| 17 | 17 | Criteri di prioritizzazione | 0.73 |
| 18 | 18 | Classiﬁcazione in fasce di priorità | 0.70 |
| 19 | 19 | Problemi Deliveroo (1/4) | 0.95 |
| 20 | 20 | Problemi Deliveroo (2/4) | 0.96 |
| 21 | 21 | Problemi Deliveroo (3/4) | 0.78 |
| 22 | 22 | Problemi Deliveroo (4/4) | 0.90 |
| 23 | 28 | Problemi rilevanti - Deliveroo | 0.67 |
| 25 | 31 | Matrice problemi-valutatori Deliveroo | 0.69 |
| 27 | 23 | Problemi Glovo (1/4) | 0.66 |
| 28 | 24 | Problemi Glovo (2/4) | 0.80 |
| 29 | 25 | Problemi Glovo (3/4) | 0.66 |
| 30 | 26 | Problemi Glovo (4/4) | 0.88 |
| 31 | 29 | Problemi rilevanti - Glovo | 0.68 |
| 33 | 32 | Matrice problemi-valutatori Glovo | 0.70 |
| 37 | 41 | Obiettivo | 0.68 |
| 40 | 6 | Deliveroo | 0.62 |
| 41 | 7 | Glovo | 0.62 |
| 43 | 6 | Deliveroo | 0.62 |
| 44 | 7 | Glovo | 0.62 |
| 46 | 6 | Deliveroo | 0.62 |
| 47 | 7 | Glovo | 0.62 |
| 54 | 56 | Efficacia | 0.69 |
| 55 | 56 | Efficacia | 0.76 |
| 56 | 57 | Efficacia - Task 1 | 0.67 |
| 57 | 59 | Efficacia - Task 2 | 0.67 |
| 58 | 61 | Efficacia - Task 3 | 0.67 |
| 62 | 63 | Efficienza | 0.70 |
| 65 | 64 | Efficienza - Task 1 | 0.67 |
| 66 | 65 | Efficienza - Task 2 | 0.67 |
| 67 | 66 | Efficienza - Task 3 | 0.67 |
| 102 | 89 | Confronto tra sistemi | 0.65 |
| 103 | 90 | Confronto statistico - Domanda 1 | 0.74 |
| 104 | 91 | Confronto statistico - Domanda 4 | 0.77 |
| 105 | 92 | Confronto statistico - Domanda 9 | 0.74 |
| 106 | 93 | Confronto statistico - Domanda 13 | 0.75 |
| 107 | 94 | Confronto statistico - Domanda 23 | 0.73 |
| 108 | 97 | La Scala UEQ | 0.64 |

## Similar Text In Different Order

| manual | generated | manual title | generated title | score |
| --- | --- | --- | --- | --- |
| 23 | 28 | Problemi rilevanti - Deliveroo | Problemi rilevanti - Deliveroo | 0.67 |
| 24 | 33 | Distribuzione delle euristiche - Deliveroo | Distribuzione delle euristiche | 0.63 |
| 25 | 31 | Matrice problemi-valutatori Deliveroo | Matrice problemi-valutatori Deliveroo | 0.69 |
| 27 | 23 | Problemi Glovo (1/4) | Problemi Glovo (1/4) | 0.66 |
| 28 | 24 | Problemi Glovo (2/4) | Problemi Glovo (2/4) | 0.80 |
| 29 | 25 | Problemi Glovo (3/4) | Problemi Glovo (3/4) | 0.66 |
| 30 | 26 | Problemi Glovo (4/4) | Problemi Glovo (4/4) | 0.88 |
| 36 | 40 | Test utente | Test utente | 0.99 |
| 37 | 41 | Obiettivo | Obiettivo | 0.68 |
| 40 | 6 | Deliveroo | Deliveroo | 0.62 |
| 41 | 7 | Glovo | Glovo | 0.62 |
| 43 | 6 | Deliveroo | Deliveroo | 0.62 |
| 44 | 7 | Glovo | Glovo | 0.62 |
| 46 | 6 | Deliveroo | Deliveroo | 0.62 |
| 47 | 7 | Glovo | Glovo | 0.62 |
| 48 | 54 | Composizione del campione - 1/4 | Composizione del campione | 0.63 |
| 49 | 54 | Composizione del campione - 2/4 | Composizione del campione | 0.64 |
| 50 | 54 | Composizione del campione - 3/4 | Composizione del campione | 0.64 |
| 51 | 54 | Composizione del campione - 4/4 | Composizione del campione | 0.63 |
| 58 | 61 | Efficacia - Task 3 | Efficacia - Task 3 | 0.67 |
| 68 | 64 | Efficienza Assoluta - Task 1 | Efficienza - Task 1 | 0.56 |
| 69 | 65 | Efficienza Assoluta - Task 2 | Efficienza - Task 2 | 0.57 |
| 70 | 66 | Efficienza Assoluta - Task 3 | Efficienza - Task 3 | 0.57 |
| 102 | 89 | Confronto tra sistemi | Confronto tra sistemi | 0.65 |
| 103 | 90 | Confronto statistico - Domanda 1 | Confronto statistico - Domanda 1 | 0.74 |
| 104 | 91 | Confronto statistico - Domanda 4 | Confronto statistico - Domanda 4 | 0.77 |
| 105 | 92 | Confronto statistico - Domanda 9 | Confronto statistico - Domanda 9 | 0.74 |
| 106 | 93 | Confronto statistico - Domanda 13 | Confronto statistico - Domanda 13 | 0.75 |
| 107 | 94 | Confronto statistico - Domanda 23 | Confronto statistico - Domanda 23 | 0.73 |
| 108 | 97 | La Scala UEQ | La scala UEQ | 0.64 |
| 109 | 98 | UEQ - Analisi dei sottogruppi - Deliveroo | Scala UEQ - analisi dei sottogruppi | 0.56 |
| 115 | 98 | UEQ - Analisi dei sottogruppi - Glovo | Scala UEQ - analisi dei sottogruppi | 0.57 |
| 124 | 109 | Appendici | Appendice | 0.86 |
| 125 | 8 | Appendice A - Valutazione euristica EU1 | Valutazione euristica | 0.67 |
| 126 | 8 | Appendice A - Valutazione euristica EU1 | Valutazione euristica | 0.67 |
| 127 | 8 | Appendice A - Valutazione euristica EU2 | Valutazione euristica | 0.67 |
| 128 | 8 | Appendice A - Valutazione euristica EU2 | Valutazione euristica | 0.67 |
| 129 | 8 | Appendice A - Valutazione euristica EU3 | Valutazione euristica | 0.67 |
| 130 | 8 | Appendice A - Valutazione euristica EU3 | Valutazione euristica | 0.67 |
| 131 | 8 | Appendice A - Valutazione euristica EU4 | Valutazione euristica | 0.67 |
| 132 | 8 | Appendice A - Valutazione euristica EU4 | Valutazione euristica | 0.67 |
| 133 | 8 | Appendice A - Valutazione euristica ED1 | Valutazione euristica | 0.67 |
| 134 | 8 | Appendice A - Valutazione euristica ED1 | Valutazione euristica | 0.67 |
| 135 | 8 | Appendice A - Valutazione euristica ED2 | Valutazione euristica | 0.67 |
| 136 | 8 | Appendice A - Valutazione euristica ED2 | Valutazione euristica | 0.67 |
| 137 | 8 | Appendice A - Valutazione euristica ED3 | Valutazione euristica | 0.67 |
| 138 | 8 | Appendice A - Valutazione euristica ED3 | Valutazione euristica | 0.67 |
| 139 | 8 | Appendice A - Valutazione euristica ED4 | Valutazione euristica | 0.67 |
| 140 | 8 | Appendice A - Valutazione euristica ED4 | Valutazione euristica | 0.67 |
| 142 | 117 | Appendice C - Valutazione dei problemi di | Appendice A8 - Export valutazione problemi | 0.55 |
| 143 | 117 | Appendice C - Valutazione dei problemi di | Appendice A8 - Export valutazione problemi | 0.55 |
| 145 | 3 | Introduzione e come funziona | Introduzione | 0.56 |
| 146 | 3 | Introduzione e come funziona | Introduzione | 0.56 |
| 156 | 73 | Questionario | Questionario | 0.96 |
| 157 | 45 | Page 157 | Page 45 | 0.83 |
| 158 | 45 | Page 158 | Page 45 | 0.83 |
| 159 | 45 | Page 159 | Page 45 | 0.83 |
| 160 | 46 | Page 160 | Page 46 | 0.83 |
| 161 | 46 | Page 161 | Page 46 | 0.83 |

## Possible Static Text Candidates

Review the same-title/different-text rows above. Copy manual text only when it is editorially better and does not reintroduce stale app-store numbers, old benchmark categories, or obsolete UEQ wording.

## Possible Slide Toggles

Use the generated-only and manual-only lists to decide which slide ids should be enabled, disabled, or moved in `config/slides.yaml` and `config/appendices.yaml`.

## UEQ Sanity Checks

- Scala trasformata UEQ: usare risultati su range -3..+3, non medie raw 1..7.
- Mapping item -> scale: mantenere la mappa ufficiale in config/ueq_items.yml.
- Benchmark category: usare soglie ufficiali centralizzate in config/ueq_benchmark_thresholds.yml e src.analysis.ueq_benchmark.
- P-value e test per dimensione: derivare dai CSV/table output della pipeline.
- N valido: verificare il numero utenti finiti/importati prima di commentare differenze sottili.
- Deck finale: nessuna slide ufficiale UEQ deve presentare raw mean 1..7 come risultato principale.

## Notes

This audit is heuristic. It is intended to guide review, not to replace manual editorial judgment.
