# Manual vs Generated Report Audit

- Manual PDF: `C:\Users\User\Downloads\Presentazione1.pptx-1.pdf`
- Generated PDF: `outputs\slides\final_report.pdf`
- Manual pages: 163
- Generated pages: 161

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
| 2 | Indice | 2 | Indice | 0.68 | no |
| 3 | Introduzione | 3 | Introduzione | 1.00 | no |
| 4 | Descrizione del problema | 4 | Descrizione del problema | 0.72 | no |
| 5 | Ambiente di valutazione | 5 | Ambiente di valutazione | 1.00 | no |
| 6 | Deliveroo | 6 | Deliveroo | 0.85 | no |
| 7 | Glovo | 7 | Glovo | 0.94 | no |
| 8 | Valutazione euristica | 8 | Valutazione euristica | 1.00 | no |
| 9 | Obiettivo | 9 | Obiettivo | 1.00 | no |
| 10 | Set di euristiche | 10 | Set di euristiche | 0.69 | no |
| 11 | Valutatori | 11 | Valutatori | 1.00 | no |
| 12 | Tabella dei valutatori | 12 | Tabella dei valutatori | 0.70 | no |
| 13 | Composizione valutatori - dati demograﬁci | 13 | Composizione valutatori - dati demografici | 0.69 | no |
| 14 | Composizione valutatori - occupazione ed esperienza | 14 | Composizione valutatori - profilo ed esperienza | 0.60 | no |
| 15 | Matrice di expertise | 15 | Matrice di expertise | 0.67 | no |
| 16 | Problemi riscontrati | 16 | Problemi riscontrati | 1.00 | no |
| 17 | Criteri di prioritizzazione | 17 | Criteri di prioritizzazione | 0.73 | no |
| 18 | Classiﬁcazione in fasce di priorità | 18 | Classificazione in fasce di priorità | 0.69 | no |
| 19 | Problemi Deliveroo (1/4) | 19 | Problemi Deliveroo (1/2) | 0.83 | no |
| 20 | Problemi Deliveroo (2/4) | 19 | Problemi Deliveroo (1/2) | 0.81 | no |
| 21 | Problemi Deliveroo (3/4) | 20 | Problemi Deliveroo (2/2) | 0.68 | no |
| 22 | Problemi Deliveroo (4/4) | 20 | Problemi Deliveroo (2/2) | 0.68 | no |
| 23 | Problemi rilevanti - Deliveroo | 23 | Problemi rilevanti - Deliveroo | 0.68 | no |
| 24 | Distribuzione delle euristiche - Deliveroo | 28 | Distribuzione delle euristiche - Deliveroo | 0.68 | no |
| 25 | Matrice problemi-valutatori Deliveroo | 26 | Matrice problemi-valutatori Deliveroo | 0.70 | no |
| 26 | Dark pattern - Misdirection | 33 | Dark pattern osservati - Glovo | 0.43 | yes |
| 27 | Problemi Glovo (1/4) | 21 | Problemi Glovo (1/2) | 0.65 | no |
| 28 | Problemi Glovo (2/4) | 21 | Problemi Glovo (1/2) | 0.82 | no |
| 29 | Problemi Glovo (3/4) | 22 | Problemi Glovo (2/2) | 0.69 | no |
| 30 | Problemi Glovo (4/4) | 22 | Problemi Glovo (2/2) | 0.77 | no |
| 31 | Problemi rilevanti - Glovo | 24 | Problemi rilevanti - Glovo | 0.67 | no |
| 32 | Distribuzione delle euristiche - Glovo | 29 | Distribuzione delle euristiche - Glovo | 0.70 | no |
| 33 | Matrice problemi-valutatori Glovo | 27 | Matrice problemi-valutatori Glovo | 0.69 | no |
| 34 | Dark pattern - Disguised Ads | 31 | Dark pattern e frizioni persuasive | 0.41 | yes |
| 35 | Valutazione euristica - Conclusioni e confronti | 156 | Valutazione quantitativa - conclusioni e confronti | 0.53 | yes |
| 36 | Test utente | 36 | Test utente | 1.00 | no |
| 37 | Obiettivo | 37 | Obiettivo | 0.69 | no |
| 38 | I tre task | 40 | Lista task utente | 0.40 | yes |
| 39 | 1° Task | 47 | Glovo - Task 2 | 0.42 | yes |
| 40 | Deliveroo | 6 | Deliveroo | 0.62 | no |
| 41 | Glovo | 7 | Glovo | 0.62 | no |
| 42 | 2° Task | 47 | Glovo - Task 2 | 0.40 | yes |
| 43 | Deliveroo | 6 | Deliveroo | 0.62 | no |
| 44 | Glovo | 7 | Glovo | 0.62 | no |
| 45 | 3° Task | 48 | Glovo - Task 3 | 0.41 | yes |
| 46 | Deliveroo | 6 | Deliveroo | 0.62 | no |
| 47 | Glovo | 7 | Glovo | 0.62 | no |
| 48 | Composizione del campione - 1/4 | 50 | Composizione del campione | 0.64 | no |
| 49 | Composizione del campione - 2/4 | 50 | Composizione del campione | 0.64 | no |
| 50 | Composizione del campione - 3/4 | 50 | Composizione del campione | 0.64 | no |
| 51 | Composizione del campione - 4/4 | 50 | Composizione del campione | 0.63 | no |
| 52 | Composizione del campione utenti | 53 | Composizione del campione utenti | 0.71 | no |
| 53 | Composizione utenti - occupazione e familiarità | 54 | Composizione utenti - familiarita e profilo | 0.49 | yes |
| 54 | Efficacia | 56 | Metodo - efficacia | 0.45 | yes |
| 55 | Efficacia | 63 | Efficacia - Task 2 | 0.46 | yes |
| 56 | Efficacia - Task 1 | 62 | Efficacia - Task 1 | 0.67 | no |
| 57 | Efficacia - Task 2 | 63 | Efficacia - Task 2 | 0.67 | no |
| 58 | Efficacia - Task 3 | 64 | Efficacia - Task 3 | 0.67 | no |
| 59 | Efficacia Assoluta - Task 1 | 67 | Efficacia assoluta - Task 1 | 0.67 | no |
| 60 | Efficacia Assoluta - Task 2 | 68 | Efficacia assoluta - Task 2 | 0.67 | no |
| 61 | Efficacia Assoluta - Task 3 | 69 | Efficacia assoluta - Task 3 | 0.68 | no |
| 62 | Efficienza | 70 | Metodo - efficienza | 0.46 | yes |
| 63 | Efficienza - Tempi users | 72 | Efficienza - riepilogo | 0.49 | yes |
| 64 | Efficienza - Tempi users | 72 | Efficienza - riepilogo | 0.48 | yes |
| 65 | Efficienza - Task 1 | 77 | Efficienza - Task 1 | 0.69 | no |
| 66 | Efficienza - Task 2 | 79 | Efficienza - Task 2 | 0.69 | no |
| 67 | Efficienza - Task 3 | 81 | Efficienza - Task 3 | 0.68 | no |
| 68 | Efficienza Assoluta - Task 1 | 84 | Efficienza assoluta - Task 1 | 0.64 | no |
| 69 | Efficienza Assoluta - Task 2 | 85 | Efficienza assoluta - Task 2 | 0.65 | no |
| 70 | Efficienza Assoluta - Task 3 | 86 | Efficienza assoluta - Task 3 | 0.64 | no |
| 71 | Test utente - Conclusioni e confronti | 156 | Valutazione quantitativa - conclusioni e confronti | 0.43 | yes |
| 72 | Test utente - Conclusioni e confronti | 156 | Valutazione quantitativa - conclusioni e confronti | 0.43 | yes |
| 73 | Questionario | 89 | Questionario | 0.97 | no |
| 74 | Introduzione al questionario | 90 | Introduzione al questionario | 0.66 | no |
| 75 | Risultati del questionario | 148 | Sintesi dei risultati del questionario | 0.51 | yes |
| 76 | Domanda 1 - Fastidioso - Piacevole | 98 | Domanda 1 - fastidioso-piacevole | 0.93 | no |
| 77 | Domanda 2 - Incomprensibile - Comprensibile | 99 | Domanda 2 - incomprensibile-comprensibile | 0.94 | no |
| 78 | Domanda 3 - Creativo - Privo di fantasia | 100 | Domanda 3 - creativo-privo di fantasia | 0.93 | no |
| 79 | Domanda 4 - Facile da apprendere - Difficile da | 101 | Domanda 4 - facile da apprendere-difficile da apprendere | 0.87 | no |
| 80 | Domanda 5 - Di grande valore - Di poco valore | 102 | Domanda 5 - di grande valore-di poco valore | 0.94 | no |
| 81 | Domanda 6 - Noioso - Appassionante | 103 | Domanda 6 - noioso-appassionante | 0.93 | no |
| 82 | Domanda 7 - Non interessante - Interessante | 104 | Domanda 7 - non interessante-interessante | 0.94 | no |
| 83 | Domanda 8 - Imprevedibile - Prevedibile | 105 | Domanda 8 - imprevedibile-prevedibile | 0.93 | no |
| 84 | Domanda 9 - Veloce - Lento | 106 | Domanda 9 - veloce-lento | 0.92 | no |
| 85 | Domanda 10 - Originale - Convenzionale | 107 | Domanda 10 - originale-convenzionale | 0.93 | no |
| 86 | Domanda 11 - Ostruttivo - Di supporto | 108 | Domanda 11 - ostruttivo-di supporto | 0.93 | no |
| 87 | Domanda 12 - Buono - Scarso | 109 | Domanda 12 - buono-scarso | 0.92 | no |
| 88 | Domanda 13 - Complicato - Facile | 110 | Domanda 13 - complicato-facile | 0.93 | no |
| 89 | Domanda 14 - Repellente - Attraente | 111 | Domanda 14 - repellente-attraente | 0.93 | no |
| 90 | Domanda 15 - Usuale - Moderno | 112 | Domanda 15 - usuale-moderno | 0.93 | no |
| 91 | Domanda 16 - Sgradevole - Gradevole | 113 | Domanda 16 - sgradevole-gradevole | 0.93 | no |
| 92 | Domanda 17 - Sicuro - Insicuro | 114 | Domanda 17 - sicuro-insicuro | 0.93 | no |
| 93 | Domanda 18 - Attivante - Soporifero | 115 | Domanda 18 - attivante-soporifero | 0.93 | no |
| 94 | Domanda 19 - Conforme alle aspettative - Non conforme alle | 116 | Domanda 19 - conforme alle aspettative-non conforme alle | 0.94 | no |
| 95 | Domanda 20 - Inefficiente - Efficiente | 117 | Domanda 20 - inefficiente-efficiente | 0.93 | no |
| 96 | Domanda 21 - Chiaro - Confuso | 118 | Domanda 21 - chiaro-confuso | 0.93 | no |
| 97 | Domanda 22 - Non pragmatico - Pragmatico | 119 | Domanda 22 - non pragmatico-pragmatico | 0.93 | no |
| 98 | Domanda 23 - Ordinato - Sovraccarico | 120 | Domanda 23 - ordinato-sovraccarico | 0.93 | no |
| 99 | Domanda 24 - Invitante - Non invitante | 121 | Domanda 24 - invitante-non invitante | 0.93 | no |
| 100 | Domanda 25 - Congeniale - Ostile | 122 | Domanda 25 - congeniale-ostile | 0.93 | no |
| 101 | Domanda 26 - Conservativo - Innovativo | 123 | Domanda 26 - conservativo-innovativo | 0.93 | no |
| 102 | Confronto tra sistemi | 124 | Confronto tra sistemi | 0.64 | no |
| 103 | Confronto statistico - Domanda 1 | 97 | Confronto statistico UEQ - Q23 | 0.54 | yes |
| 104 | Confronto statistico - Domanda 4 | 94 | Confronto statistico UEQ - Q04 | 0.56 | no |
| 105 | Confronto statistico - Domanda 9 | 97 | Confronto statistico UEQ - Q23 | 0.54 | yes |
| 106 | Confronto statistico - Domanda 13 | 96 | Confronto statistico UEQ - Q13 | 0.55 | yes |
| 107 | Confronto statistico - Domanda 23 | 97 | Confronto statistico UEQ - Q23 | 0.56 | no |
| 108 | La Scala UEQ | 40 | Lista task utente | 0.30 | yes |
| 109 | UEQ - Analisi dei sottogruppi - Deliveroo | 126 | UEQ - Analisi dei sottogruppi - Deliveroo | 0.79 | no |
| 110 | UEQ - Analisi dei dati - Deliveroo (1/2) | 135 | UEQ - Analisi dei dati - Deliveroo (1/3) | 0.86 | no |
| 111 | UEQ - Analisi dei dati - Deliveroo (2/2) | 137 | UEQ - Analisi dei dati - Deliveroo (3/3) | 0.84 | no |
| 112 | UEQ - Media risultati Deliveroo | 23 | Problemi rilevanti - Deliveroo | 0.40 | yes |
| 113 | UEQ - Distribuzione delle risposte per domanda Deliveroo | 129 | UEQ - distribuzione risposte raw 1..7 - Deliveroo | 0.54 | yes |
| 114 | Benchmark UEQ - Deliveroo | 149 | Benchmark UEQ - Deliveroo | 0.67 | no |
| 115 | UEQ - Analisi dei sottogruppi - Glovo | 127 | UEQ - Analisi dei sottogruppi - Glovo | 0.78 | no |
| 116 | UEQ - Analisi dei dati - Glovo (1/2) | 138 | UEQ - Analisi dei dati - Glovo (1/3) | 0.87 | no |
| 117 | UEQ - Analisi dei dati - Glovo (2/2) | 139 | UEQ - Analisi dei dati - Glovo (2/3) | 0.65 | no |
| 118 | UEQ - Media risultati Glovo | 132 | UEQ - media trasformata per domanda - Glovo | 0.41 | yes |
| 119 | UEQ - Distribuzione delle risposte per domanda Glovo | 130 | UEQ - distribuzione risposte raw 1..7 - Glovo | 0.54 | yes |
| 120 | Benchmark UEQ - Glovo | 150 | Benchmark UEQ - Glovo | 0.66 | no |
| 121 | Net Promoter Score | 152 | Net Promoter Score: raccomandabilita | 0.42 | yes |
| 122 | Net Promoter Score - Deliveroo e Glovo | 128 | UEQ - confronto scale Deliveroo vs Glovo | 0.42 | yes |
| 123 | Conclusioni | 49 | Conclusione del protocollo | 0.33 | yes |
| 124 | Appendici | 2 | Indice | 0.32 | yes |
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
| 141 | Appendice B - Modulo autorizzazione foto e | 41 | Deliveroo - introduzione task | 0.37 | yes |
| 142 | Appendice C - Valutazione dei problemi di | 38 | Presentazione dei task e protocollo di test | 0.47 | yes |
| 143 | Appendice C - Valutazione dei problemi di | 38 | Presentazione dei task e protocollo di test | 0.46 | yes |
| 144 | Presentazione dei task per lo user test | 38 | Presentazione dei task e protocollo di test | 0.65 | no |
| 145 | Introduzione e come funziona | 3 | Introduzione | 0.56 | no |
| 146 | Introduzione e come funziona | 3 | Introduzione | 0.56 | no |
| 147 | Di seguito, le task presentate agli utenti - Deliveroo | 40 | Lista task utente | 0.36 | yes |
| 148 | Deliveroo - Task 1 | 42 | Deliveroo - Task 1 | 0.76 | no |
| 149 | Deliveroo - Task 2 | 43 | Deliveroo - Task 2 | 0.69 | no |
| 150 | Deliveroo - Task 3 | 44 | Deliveroo - Task 3 | 0.67 | no |
| 151 | Di seguito, le task presentate agli utenti - Glovo | 40 | Lista task utente | 0.35 | yes |
| 152 | Glovo - Task 1 | 46 | Glovo - Task 1 | 0.76 | no |
| 153 | Glovo - Task 2 | 47 | Glovo - Task 2 | 0.69 | no |
| 154 | Glovo - Task 3 | 48 | Glovo - Task 3 | 0.66 | no |
| 155 | Conclusione | 3 | Introduzione | 0.48 | yes |
| 156 | Questionario | 89 | Questionario | 0.96 | no |
| 157 | Page 157 | 1 | Progetto HCI | 0.22 | yes |
| 158 | Page 158 | 1 | Progetto HCI | 0.22 | yes |
| 159 | Page 159 | 1 | Progetto HCI | 0.22 | yes |
| 160 | Page 160 | 1 | Progetto HCI | 0.22 | yes |
| 161 | Page 161 | 1 | Progetto HCI | 0.22 | yes |
| 162 | Links | 153 | Sintesi finale | 0.28 | yes |
| 163 | Grazie | 3 | Introduzione | 0.28 | yes |

## Manual Slides Needing Review

| manual | title | best generated | score |
| --- | --- | --- | --- |
| 26 | Dark pattern - Misdirection | 33 | 0.43 |
| 34 | Dark pattern - Disguised Ads | 31 | 0.41 |
| 35 | Valutazione euristica - Conclusioni e confronti | 156 | 0.53 |
| 38 | I tre task | 40 | 0.40 |
| 39 | 1° Task | 47 | 0.42 |
| 42 | 2° Task | 47 | 0.40 |
| 45 | 3° Task | 48 | 0.41 |
| 53 | Composizione utenti - occupazione e familiarità | 54 | 0.49 |
| 54 | Efficacia | 56 | 0.45 |
| 55 | Efficacia | 63 | 0.46 |
| 62 | Efficienza | 70 | 0.46 |
| 63 | Efficienza - Tempi users | 72 | 0.49 |
| 64 | Efficienza - Tempi users | 72 | 0.48 |
| 71 | Test utente - Conclusioni e confronti | 156 | 0.43 |
| 72 | Test utente - Conclusioni e confronti | 156 | 0.43 |
| 75 | Risultati del questionario | 148 | 0.51 |
| 103 | Confronto statistico - Domanda 1 | 97 | 0.54 |
| 105 | Confronto statistico - Domanda 9 | 97 | 0.54 |
| 106 | Confronto statistico - Domanda 13 | 96 | 0.55 |
| 108 | La Scala UEQ | 40 | 0.30 |
| 112 | UEQ - Media risultati Deliveroo | 23 | 0.40 |
| 113 | UEQ - Distribuzione delle risposte per domanda Deliveroo | 129 | 0.54 |
| 118 | UEQ - Media risultati Glovo | 132 | 0.41 |
| 119 | UEQ - Distribuzione delle risposte per domanda Glovo | 130 | 0.54 |
| 121 | Net Promoter Score | 152 | 0.42 |
| 122 | Net Promoter Score - Deliveroo e Glovo | 128 | 0.42 |
| 123 | Conclusioni | 49 | 0.33 |
| 124 | Appendici | 2 | 0.32 |
| 141 | Appendice B - Modulo autorizzazione foto e | 41 | 0.37 |
| 142 | Appendice C - Valutazione dei problemi di | 38 | 0.47 |
| 143 | Appendice C - Valutazione dei problemi di | 38 | 0.46 |
| 147 | Di seguito, le task presentate agli utenti - Deliveroo | 40 | 0.36 |
| 151 | Di seguito, le task presentate agli utenti - Glovo | 40 | 0.35 |
| 155 | Conclusione | 3 | 0.48 |
| 157 | Page 157 | 1 | 0.22 |
| 158 | Page 158 | 1 | 0.22 |
| 159 | Page 159 | 1 | 0.22 |
| 160 | Page 160 | 1 | 0.22 |
| 161 | Page 161 | 1 | 0.22 |
| 162 | Links | 153 | 0.28 |
| 163 | Grazie | 3 | 0.28 |

## Generated Slides Without Strong Manual Match

| generated | title | fingerprint |
| --- | --- | --- |
| 25 | criticità trasversali comuni | 754f3b156b8a |
| 30 | Valutazione quantitativa | 6ad35964502d |
| 32 | Dark pattern osservati - Deliveroo | a1416472c18f |
| 34 | Impatto dei dark pattern sul flusso d'ordine | c082fb423a0a |
| 35 | Sintesi della valutazione euristica | 33edf82dece2 |
| 39 | Protocollo operativo del test | 22ee823a16cd |
| 45 | Glovo - introduzione task | e4b2c97c46de |
| 51 | Profilo degli utenti coinvolti - 1/2 | 587fdf309333 |
| 52 | Profilo degli utenti coinvolti - 2/2 | 1f7af31c2299 |
| 55 | Familiarita degli utenti con il food delivery | a2aa5d12b78b |
| 57 | Legenda efficacia | 0561f65d7667 |
| 58 | Efficacia - matrice esiti utenti/task | b3c79acbd9d5 |
| 59 | Errori - Task 1 | 57dca93cc47b |
| 60 | Successo e distribuzione tempi | 101231b8ca4a |
| 61 | Efficacia relativa - sintesi | aeccdebce46b |
| 65 | Metodo - efficacia assoluta | 3b57535ea4b9 |
| 66 | Efficacia assoluta - sintesi | 831d27f254ca |
| 71 | Efficienza - riepilogo tempi mediani | 24a728e8e808 |
| 73 | Efficienza - descrittive tempi | 917919cd5217 |
| 74 | Efficienza - tempi utenti completi (1/2) | a2e86d55a597 |
| 75 | Efficienza - tempi utenti completi (2/2) | c82a7ff842d8 |
| 76 | Efficienza statistica - sintesi | 948a04e334f2 |
| 78 | Efficienza - linee appaiate Task 1 | bb26af9724a9 |
| 80 | Efficienza - linee appaiate Task 2 | 7e1fe702d687 |
| 82 | Efficienza - linee appaiate Task 3 | 74d3e0c52181 |
| 83 | Efficienza assoluta - confronto con OET | cae1c61d4e36 |
| 87 | Confronto statistico - Task utente | d765ba4f950e |
| 88 | Efficacia ed efficienza: lettura congiunta | 6d24f38595ba |
| 91 | Scala UEQ e metodo di scoring | d8195cdccc38 |
| 92 | Item UEQ selezionati - metodo | bc6d7496881f |
| 93 | Confronto statistico UEQ - Q01 | 72c5e220b42d |
| 95 | Confronto statistico UEQ - Q09 | bea9045e508c |
| 125 | UEQ - confronto sintetico delle scale | 11a94f602e58 |
| 131 | UEQ - media trasformata per domanda - | 0b20243cd6f7 |
| 133 | UEQ - confronto item-by-item trasformato Deliveroo vs | a9dff81b8b81 |
| 134 | UEQ - benchmark confronto finale | e9da9db445d3 |
| 136 | UEQ - Analisi dei dati - Deliveroo (2/3) | 8d765bc691f3 |
| 140 | UEQ - Analisi dei dati - Glovo (3/3) | 1d93bb64c00d |
| 141 | UEQ - confronto dimensioni | 22f1937d8d2b |
| 142 | UEQ - test per dimensione | 006ebb4549ef |
| 143 | Benchmark UEQ - confronto sintetico | 3bb0e8b85651 |
| 144 | UEQ benchmark - qualità pragmatica/edonica | 7dd68f1e9211 |
| 145 | UEQ benchmark - lettura operativa | 564add38cad2 |
| 146 | Sottogruppi UEQ - heatmap differenze | 9647f9ed794b |
| 147 | Sottogruppi - sintesi esplorativa | ca8f8e75f693 |
| 151 | UEQ: conferme e contraddizioni rispetto ai test | 98d8401f4f06 |
| 154 | Conclusioni: confronto complessivo | 9999ba2e0cad |
| 155 | Confronto statistico complessivo | 336a7afa8c48 |
| 157 | Matrice decisionale Deliveroo vs Glovo | 572f0037d935 |
| 158 | Evidenze integrate | 17f52cef1405 |
| 159 | Verdetto operativo | 825ebaec6cf0 |
| 160 | Raccomandazioni prioritarie | 9e478381aa7c |
| 161 | Verdetto finale | 8aa9d59374cb |

## Same Title But Different Text

| manual | generated | title | score |
| --- | --- | --- | --- |
| 1 | 1 | Progetto HCI | 0.97 |
| 2 | 2 | Indice | 0.68 |
| 4 | 4 | Descrizione del problema | 0.72 |
| 6 | 6 | Deliveroo | 0.85 |
| 7 | 7 | Glovo | 0.94 |
| 10 | 10 | Set di euristiche | 0.69 |
| 12 | 12 | Tabella dei valutatori | 0.70 |
| 15 | 15 | Matrice di expertise | 0.67 |
| 17 | 17 | Criteri di prioritizzazione | 0.73 |
| 23 | 23 | Problemi rilevanti - Deliveroo | 0.68 |
| 24 | 28 | Distribuzione delle euristiche - Deliveroo | 0.68 |
| 25 | 26 | Matrice problemi-valutatori Deliveroo | 0.70 |
| 31 | 24 | Problemi rilevanti - Glovo | 0.67 |
| 32 | 29 | Distribuzione delle euristiche - Glovo | 0.70 |
| 33 | 27 | Matrice problemi-valutatori Glovo | 0.69 |
| 37 | 37 | Obiettivo | 0.69 |
| 40 | 6 | Deliveroo | 0.62 |
| 41 | 7 | Glovo | 0.62 |
| 43 | 6 | Deliveroo | 0.62 |
| 44 | 7 | Glovo | 0.62 |
| 46 | 6 | Deliveroo | 0.62 |
| 47 | 7 | Glovo | 0.62 |
| 52 | 53 | Composizione del campione utenti | 0.71 |
| 56 | 62 | Efficacia - Task 1 | 0.67 |
| 57 | 63 | Efficacia - Task 2 | 0.67 |
| 58 | 64 | Efficacia - Task 3 | 0.67 |
| 59 | 67 | Efficacia Assoluta - Task 1 | 0.67 |
| 60 | 68 | Efficacia Assoluta - Task 2 | 0.67 |
| 61 | 69 | Efficacia Assoluta - Task 3 | 0.68 |
| 65 | 77 | Efficienza - Task 1 | 0.69 |
| 66 | 79 | Efficienza - Task 2 | 0.69 |
| 67 | 81 | Efficienza - Task 3 | 0.68 |
| 68 | 84 | Efficienza Assoluta - Task 1 | 0.64 |
| 69 | 85 | Efficienza Assoluta - Task 2 | 0.65 |
| 70 | 86 | Efficienza Assoluta - Task 3 | 0.64 |
| 74 | 90 | Introduzione al questionario | 0.66 |
| 102 | 124 | Confronto tra sistemi | 0.64 |
| 109 | 126 | UEQ - Analisi dei sottogruppi - Deliveroo | 0.79 |
| 114 | 149 | Benchmark UEQ - Deliveroo | 0.67 |
| 115 | 127 | UEQ - Analisi dei sottogruppi - Glovo | 0.78 |
| 120 | 150 | Benchmark UEQ - Glovo | 0.66 |
| 148 | 42 | Deliveroo - Task 1 | 0.76 |
| 149 | 43 | Deliveroo - Task 2 | 0.69 |
| 150 | 44 | Deliveroo - Task 3 | 0.67 |
| 152 | 46 | Glovo - Task 1 | 0.76 |
| 153 | 47 | Glovo - Task 2 | 0.69 |
| 154 | 48 | Glovo - Task 3 | 0.66 |

## Similar Text In Different Order

| manual | generated | manual title | generated title | score |
| --- | --- | --- | --- | --- |
| 24 | 28 | Distribuzione delle euristiche - Deliveroo | Distribuzione delle euristiche - Deliveroo | 0.68 |
| 27 | 21 | Problemi Glovo (1/4) | Problemi Glovo (1/2) | 0.65 |
| 28 | 21 | Problemi Glovo (2/4) | Problemi Glovo (1/2) | 0.82 |
| 29 | 22 | Problemi Glovo (3/4) | Problemi Glovo (2/2) | 0.69 |
| 30 | 22 | Problemi Glovo (4/4) | Problemi Glovo (2/2) | 0.77 |
| 31 | 24 | Problemi rilevanti - Glovo | Problemi rilevanti - Glovo | 0.67 |
| 32 | 29 | Distribuzione delle euristiche - Glovo | Distribuzione delle euristiche - Glovo | 0.70 |
| 33 | 27 | Matrice problemi-valutatori Glovo | Matrice problemi-valutatori Glovo | 0.69 |
| 40 | 6 | Deliveroo | Deliveroo | 0.62 |
| 41 | 7 | Glovo | Glovo | 0.62 |
| 43 | 6 | Deliveroo | Deliveroo | 0.62 |
| 44 | 7 | Glovo | Glovo | 0.62 |
| 46 | 6 | Deliveroo | Deliveroo | 0.62 |
| 47 | 7 | Glovo | Glovo | 0.62 |
| 56 | 62 | Efficacia - Task 1 | Efficacia - Task 1 | 0.67 |
| 57 | 63 | Efficacia - Task 2 | Efficacia - Task 2 | 0.67 |
| 58 | 64 | Efficacia - Task 3 | Efficacia - Task 3 | 0.67 |
| 59 | 67 | Efficacia Assoluta - Task 1 | Efficacia assoluta - Task 1 | 0.67 |
| 60 | 68 | Efficacia Assoluta - Task 2 | Efficacia assoluta - Task 2 | 0.67 |
| 61 | 69 | Efficacia Assoluta - Task 3 | Efficacia assoluta - Task 3 | 0.68 |
| 65 | 77 | Efficienza - Task 1 | Efficienza - Task 1 | 0.69 |
| 66 | 79 | Efficienza - Task 2 | Efficienza - Task 2 | 0.69 |
| 67 | 81 | Efficienza - Task 3 | Efficienza - Task 3 | 0.68 |
| 68 | 84 | Efficienza Assoluta - Task 1 | Efficienza assoluta - Task 1 | 0.64 |
| 69 | 85 | Efficienza Assoluta - Task 2 | Efficienza assoluta - Task 2 | 0.65 |
| 70 | 86 | Efficienza Assoluta - Task 3 | Efficienza assoluta - Task 3 | 0.64 |
| 73 | 89 | Questionario | Questionario | 0.97 |
| 74 | 90 | Introduzione al questionario | Introduzione al questionario | 0.66 |
| 76 | 98 | Domanda 1 - Fastidioso - Piacevole | Domanda 1 - fastidioso-piacevole | 0.93 |
| 77 | 99 | Domanda 2 - Incomprensibile - Comprensibile | Domanda 2 - incomprensibile-comprensibile | 0.94 |
| 78 | 100 | Domanda 3 - Creativo - Privo di fantasia | Domanda 3 - creativo-privo di fantasia | 0.93 |
| 79 | 101 | Domanda 4 - Facile da apprendere - Difficile da | Domanda 4 - facile da apprendere-difficile da apprendere | 0.87 |
| 80 | 102 | Domanda 5 - Di grande valore - Di poco valore | Domanda 5 - di grande valore-di poco valore | 0.94 |
| 81 | 103 | Domanda 6 - Noioso - Appassionante | Domanda 6 - noioso-appassionante | 0.93 |
| 82 | 104 | Domanda 7 - Non interessante - Interessante | Domanda 7 - non interessante-interessante | 0.94 |
| 83 | 105 | Domanda 8 - Imprevedibile - Prevedibile | Domanda 8 - imprevedibile-prevedibile | 0.93 |
| 84 | 106 | Domanda 9 - Veloce - Lento | Domanda 9 - veloce-lento | 0.92 |
| 85 | 107 | Domanda 10 - Originale - Convenzionale | Domanda 10 - originale-convenzionale | 0.93 |
| 86 | 108 | Domanda 11 - Ostruttivo - Di supporto | Domanda 11 - ostruttivo-di supporto | 0.93 |
| 87 | 109 | Domanda 12 - Buono - Scarso | Domanda 12 - buono-scarso | 0.92 |
| 88 | 110 | Domanda 13 - Complicato - Facile | Domanda 13 - complicato-facile | 0.93 |
| 89 | 111 | Domanda 14 - Repellente - Attraente | Domanda 14 - repellente-attraente | 0.93 |
| 90 | 112 | Domanda 15 - Usuale - Moderno | Domanda 15 - usuale-moderno | 0.93 |
| 91 | 113 | Domanda 16 - Sgradevole - Gradevole | Domanda 16 - sgradevole-gradevole | 0.93 |
| 92 | 114 | Domanda 17 - Sicuro - Insicuro | Domanda 17 - sicuro-insicuro | 0.93 |
| 93 | 115 | Domanda 18 - Attivante - Soporifero | Domanda 18 - attivante-soporifero | 0.93 |
| 94 | 116 | Domanda 19 - Conforme alle aspettative - Non conforme alle | Domanda 19 - conforme alle aspettative-non conforme alle | 0.94 |
| 95 | 117 | Domanda 20 - Inefficiente - Efficiente | Domanda 20 - inefficiente-efficiente | 0.93 |
| 96 | 118 | Domanda 21 - Chiaro - Confuso | Domanda 21 - chiaro-confuso | 0.93 |
| 97 | 119 | Domanda 22 - Non pragmatico - Pragmatico | Domanda 22 - non pragmatico-pragmatico | 0.93 |
| 98 | 120 | Domanda 23 - Ordinato - Sovraccarico | Domanda 23 - ordinato-sovraccarico | 0.93 |
| 99 | 121 | Domanda 24 - Invitante - Non invitante | Domanda 24 - invitante-non invitante | 0.93 |
| 100 | 122 | Domanda 25 - Congeniale - Ostile | Domanda 25 - congeniale-ostile | 0.93 |
| 101 | 123 | Domanda 26 - Conservativo - Innovativo | Domanda 26 - conservativo-innovativo | 0.93 |
| 102 | 124 | Confronto tra sistemi | Confronto tra sistemi | 0.64 |
| 104 | 94 | Confronto statistico - Domanda 4 | Confronto statistico UEQ - Q04 | 0.56 |
| 107 | 97 | Confronto statistico - Domanda 23 | Confronto statistico UEQ - Q23 | 0.56 |
| 109 | 126 | UEQ - Analisi dei sottogruppi - Deliveroo | UEQ - Analisi dei sottogruppi - Deliveroo | 0.79 |
| 110 | 135 | UEQ - Analisi dei dati - Deliveroo (1/2) | UEQ - Analisi dei dati - Deliveroo (1/3) | 0.86 |
| 111 | 137 | UEQ - Analisi dei dati - Deliveroo (2/2) | UEQ - Analisi dei dati - Deliveroo (3/3) | 0.84 |
| 114 | 149 | Benchmark UEQ - Deliveroo | Benchmark UEQ - Deliveroo | 0.67 |
| 115 | 127 | UEQ - Analisi dei sottogruppi - Glovo | UEQ - Analisi dei sottogruppi - Glovo | 0.78 |
| 116 | 138 | UEQ - Analisi dei dati - Glovo (1/2) | UEQ - Analisi dei dati - Glovo (1/3) | 0.87 |
| 117 | 139 | UEQ - Analisi dei dati - Glovo (2/2) | UEQ - Analisi dei dati - Glovo (2/3) | 0.65 |
| 120 | 150 | Benchmark UEQ - Glovo | Benchmark UEQ - Glovo | 0.66 |
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
| 144 | 38 | Presentazione dei task per lo user test | Presentazione dei task e protocollo di test | 0.65 |
| 145 | 3 | Introduzione e come funziona | Introduzione | 0.56 |
| 146 | 3 | Introduzione e come funziona | Introduzione | 0.56 |
| 148 | 42 | Deliveroo - Task 1 | Deliveroo - Task 1 | 0.76 |
| 149 | 43 | Deliveroo - Task 2 | Deliveroo - Task 2 | 0.69 |
| 150 | 44 | Deliveroo - Task 3 | Deliveroo - Task 3 | 0.67 |
| 152 | 46 | Glovo - Task 1 | Glovo - Task 1 | 0.76 |
| 153 | 47 | Glovo - Task 2 | Glovo - Task 2 | 0.69 |
| 154 | 48 | Glovo - Task 3 | Glovo - Task 3 | 0.66 |
| 156 | 89 | Questionario | Questionario | 0.96 |

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
