# SiciliaFresh – Pianificazione e confronto economico delle consegne

Project Work **PW 23** – Corso di laurea L-31 *Informatica per le Aziende Digitali* (Università Telematica Pegaso),
anno accademico 2026/2027. Autore: Giovanni Costa.

Prototipo Python che pianifica le consegne giornaliere di un'impresa agroalimentare **fittizia** con deposito a
**San Pier Marina (frazione di San Pier Niceto, ME)** e cinque clienti lungo la costa tirrenica: Milazzo,
Monforte Marina, Torregrotta, Venetico Marina e Spadafora. Il programma:

1. individua con **enumerazione completa** il percorso più breve con **un veicolo** (Scenario A, TSP);
2. individua con **enumerazione completa** la combinazione di percorsi più breve con **due veicoli identici**
   di capacità ridotta (Scenario B, VRP con vincoli di capacità);
3. ricostruisce per ogni veicolo la **sequenza delle consegne**: carico iniziale alla partenza, quantità
   consegnata a ogni cliente, carico residuo dopo ogni consegna e rientro a vuoto;
4. confronta i costi giornalieri dei due scenari e ripete il confronto al variare di alcuni prezzi unitari
   (analisi di sensibilità con calcolo dell'eventuale punto di pareggio);
5. genera una pagina HTML statica con dati, grafi dei percorsi (un colore per veicolo), sequenza delle
   consegne, selettore degli scenari e grafici economici.

**Metodo in una frase.** Il programma individua, mediante enumerazione completa, i percorsi che minimizzano la
distanza complessiva per ciascuna configurazione di flotta; successivamente le soluzioni ottenute vengono
confrontate attraverso un modello economico parametrico. Il programma non minimizza direttamente il costo.

Il deposito è nel mio comune di residenza (San Pier Niceto, di cui San Pier Marina è frazione).

**Natura dei dati.** Le località sono **reali**. Le distanze stradali sono **calcolate da un servizio di
routing** (motore OSRM sulla rete OpenStreetMap, interrogato il 26/10/2026; solo SS113 e strade provinciali di
pianura): non sono misure effettuate sul campo né stime. Un secondo motore (Valhalla, stessi dati OpenStreetMap)
conferma la matrice: differenza media 0,08 km sulle 30 coppie. Il **prezzo del gasolio è osservato**: 2,275 €/l,
media regionale della Sicilia per il self-service rilevata dal MIMIT il 26/10/2026 (`data/fuel_price_source.json`).
Azienda, clienti, quantità e gli altri parametri di costo sono **simulati** a scopo didattico.

**Risultati con i dati attuali.** Scenario A (un veicolo): 34,37 km, 129,91 € al giorno. Scenario B (due veicoli):
37,58 km, 153,64 € al giorno. Lo Scenario A risparmia 23,73 € al giorno; la convenienza si inverte solo se il costo
fisso giornaliero del veicolo grande supera 98,73 €.

## Requisiti software

- Python **3.8 o superiore** (Windows, macOS o Linux).
- **Nessuna libreria esterna**: solo la libreria standard (`itertools`, `csv`, `json`, `unittest`, `urllib`…).
  `requirements.txt` è presente per convenzione ma non elenca pacchetti.
- Connessione internet **non necessaria** per eseguire il programma; serve solo se si vogliono
  rilevare di nuovo le distanze con `tools/fetch_distances.py`.

## Esecuzione su Windows

1. Installare Python da <https://www.python.org/downloads/> spuntando **"Add python.exe to PATH"**.
2. Aprire la cartella del progetto in Esplora risorse, scrivere `cmd` nella barra dell'indirizzo e premere Invio.
3. Eseguire:

   ```bash
   python main.py
   ```

Il programma stampa il riepilogo nel terminale, scrive `output/results.json` e `output/index.html` e apre la
pagina nel browser predefinito. In alternativa: doppio clic su `esegui.bat`.
Con `python main.py --no-open` i file vengono generati senza aprire il browser.

## Test automatici

```bash
python -m unittest -v
```

Il comando va lanciato dalla cartella del progetto. I 32 test (`tests/test_routing.py`) verificano:
calcolo della distanza, gestione della matrice direzionale, minimo su istanze risolvibili a mano, esaustività
dell'enumerazione (confronto con un'implementazione indipendente), assenza di ripartizioni duplicate tra
veicoli identici, conteggio delle combinazioni, capacità e completezza delle consegne, carico residuo
(carico iniziale uguale alla somma delle consegne, mai negativo, nullo al rientro, ogni cliente riceve la sua
quantità), configurazione concordata di deposito e clienti, completezza della matrice e coincidenza con la
fonte OSRM, rilevazione delle violazioni dei vincoli, istanze non risolvibili, coerenza dei costi e dei punti
di pareggio, dati mancanti o non validi, corrispondenza tra pagina HTML e `results.json`, colori distinti e
coerenti dei due veicoli, disposizione dei nodi coerente con la geografia e identica nei due scenari,
esistenza dei file collegati dalla pagina.

## Struttura delle cartelle

```
siciliafresh-project/
├── main.py                    punto di ingresso: carica, risolve, calcola, genera l'output
├── esegui.bat                 avvio con doppio clic su Windows
├── index.html                 reindirizza a output/index.html (utile per GitHub Pages)
├── .nojekyll                  file vuoto: GitHub Pages pubblica i file così come sono
├── requirements.txt           nessuna dipendenza esterna
├── data/
│   ├── locations.csv          deposito e clienti: coordinate reali (lat, lon), riferimento OSM e punto di riferimento
│   ├── distances.csv          matrice direzionale 6x6 delle distanze stradali (km)
│   ├── distances_source.json  richiesta OSRM, data, risposta completa e strade percorse per coppia
│   ├── distances_check.json   controllo indipendente con Valhalla (confronto coppia per coppia)
│   ├── deliveries.csv         quantità richieste dai clienti (kg)
│   ├── config.json            azienda, data dell'analisi, capacità dei veicoli, stato e fonte delle distanze
│   ├── costs.json             parametri economici (osservati e ipotetici) e intervalli di sensibilità
│   └── fuel_price_source.json fonte del prezzo del gasolio (MIMIT, 26/10/2026)
├── src/
│   ├── data_loader.py         lettura e validazione dei dati
│   ├── routing.py             enumerazione completa, vincoli, verifiche, sequenza delle consegne
│   ├── economics.py           modello dei costi, confronto, sensibilità, punto di pareggio
│   └── visualization.py       generazione della pagina HTML e degli SVG (grafi e grafici)
├── tools/
│   ├── fetch_distances.py     calcola le distanze con OSRM (facoltativo, richiede internet)
│   └── check_distances.py     confronta la matrice con Valhalla (facoltativo, richiede internet)
├── output/
│   ├── index.html             pagina dei risultati (generata da main.py)
│   ├── results.json           risultati completi, incluse le sequenze delle consegne (generati da main.py)
│   ├── styles.css             foglio di stile (statico)
│   └── app.js                 interazioni e animazioni (statico, JavaScript nativo)
├── tests/test_routing.py      test automatici (unittest)
└── docs/project_report.md     rapporto tecnico del progetto
```

## Dati di input

| File | Contenuto | Note |
|------|-----------|------|
| `locations.csv` | `id`, `name`, `role` (`deposito`/`cliente`), `lat`, `lon`, `osm_ref`, `ref_point` | Un solo deposito. La posizione dei nodi nei grafi è ricavata da `lat`/`lon` (colonne `x`, `y` facoltative) |
| `distances.csv` | Matrice completa: riga = origine, colonna = destinazione | Diagonale 0, valori positivi; può essere asimmetrica |
| `deliveries.csv` | `id`, `demand_kg` (quantità richiesta dal cliente, da consegnare), `description` | Una riga per ogni cliente, quantità > 0 |
| `config.json` | Data dell'analisi riportata nella pagina, capacità dei veicoli (kg), stato e fonte delle distanze | `status`: `VERIFIED` o altro valore (mostra un avviso) |
| `costs.json` | Prezzi e parametri dei veicoli, intervalli di sensibilità | Gasolio osservato (MIMIT); altri valori ipotetici, non tariffe ufficiali. `parameter_types` indica la natura di ogni parametro |

Ad ogni esecuzione il programma controlla che i dati siano completi e coerenti e che l'istanza rispetti le
condizioni della traccia (il veicolo A trasporta tutto; nessun veicolo B trasporta tutto da solo; esiste una
ripartizione ammissibile; ogni consegna entra in un veicolo B). In caso contrario si ferma con un messaggio
di errore esplicito e non genera risultati.

## Modificare le distanze

- **Calcolo automatico:** aggiornare `lat`/`lon` in `locations.csv` ed eseguire
  `python tools/fetch_distances.py`. Lo script riscrive `distances.csv` e `distances_source.json`
  (con le strade percorse da ogni collegamento, utili per escludere tratti montani); aggiornare poi data e
  fonte in `config.json` → `distance_data`. Per il controllo con un secondo motore eseguire
  `python tools/check_distances.py`, che scrive `distances_check.json` senza modificare la matrice.
  Nei grafi la disposizione dei nodi è schematica: segue l'ordine ovest–est e nord–sud delle coordinate,
  ma non è in scala; i km mostrati provengono sempre da `distances.csv`.
- **Inserimento manuale** (es. da Google Maps): modificare `distances.csv` e descrivere fonte, criterio e
  data in `config.json`. Se i valori non sono documentati, impostare `"status"` a un valore diverso da
  `VERIFIED` (es. `UNVERIFIED`): pagina e terminale mostreranno un avviso.

## Modificare i parametri economici

In `data/costs.json`:
- `common`: prezzo del carburante (€/l, convertito in costo per km moltiplicandolo per il consumo del
  veicolo), costo orario dell'autista (€/h), velocità media (km/h), tempo di scarico per consegna (min);
- `vehicle_types`: per ciascuno scenario, costo fisso giornaliero (€/giorno), consumo (l/km),
  altri costi variabili (€/km);
- `sensitivity`: parametri da far variare, con `min`, `max`, `step`. Il parametro è un nome di `common`
  oppure un percorso puntato (es. `vehicle_types.scenario_A.fixed_cost_eur_per_day`).

## Rigenerare la pagina HTML

Dopo qualsiasi modifica ai dati eseguire di nuovo `python main.py`: `results.json` e `index.html` vengono
ricalcolati da zero. La pagina non contiene valori inseriti a mano.

## File di output

- `output/results.json`: tutti i risultati (verifiche sull'istanza, percorsi, distanze, carichi iniziali,
  sequenze delle consegne con quantità consegnate e carico residuo, numero di combinazioni, elenco delle
  ripartizioni, costi per componente e per veicolo, tabelle di sensibilità, pareggi).
- `output/index.html` + `styles.css` + `app.js`: pagina statica; si apre con doppio clic e non richiede un
  server. I caratteri Manrope e Space Grotesk sono caricati da Google Fonts: senza connessione la pagina usa i
  caratteri di sistema e resta completa. Senza JavaScript mostra entrambi gli scenari uno sotto l'altro;
  con l'impostazione di sistema "riduci movimento" le animazioni sono disattivate. I colori dei veicoli
  (`--v1` arancione, `--v2` blu petrolio) e degli scenari (`--sa`, `--sb`) sono definiti una sola volta
  all'inizio di `styles.css` e, con gli stessi valori, in `src/visualization.py`.

## Limiti

- Enumerazione completa: adatta solo a istanze piccole (crescita fattoriale con il numero di clienti).
- I percorsi sono ottimizzati sulla distanza; il confronto economico è successivo.
- Tempi stimati con una velocità media costante; nessuna finestra oraria, traffico o vincolo di orario di lavoro.
- Tempo di scarico uguale per ogni consegna; nessun vincolo sulla catena del freddo.
- Quantità e costi (a parte il gasolio) simulati: la conclusione economica dipende soprattutto dai costi fissi ipotizzati.
- Le distanze OSRM dipendono dalla versione dei dati OpenStreetMap al momento del calcolo e possono
  differire di poco da altri servizi cartografici.

## Pubblicazione

- Repository: <https://github.com/nowereal/siciliafresh-project>
- Dashboard (GitHub Pages): <https://nowereal.github.io/siciliafresh-project/>

La pagina è pubblicata da GitHub Pages dal branch `main`, cartella `(root)`
(*Settings → Pages → Build and deployment → Deploy from a branch*): il file `index.html` nella
radice reindirizza a `output/index.html`. Tutti i collegamenti della pagina sono relativi (`styles.css`,
`app.js`, `results.json`), quindi funziona anche in una sottocartella. Dopo ogni modifica dei dati rieseguire
`python main.py` e includere `output/` nel commit: GitHub Pages aggiorna il sito a ogni push sul branch `main`.

