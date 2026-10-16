# Sviluppo di un codice Python per la pianificazione e il confronto economico dei percorsi di consegna di un'impresa agroalimentare

**Project Work n. 23** – Corso di laurea L-31 *Informatica per le Aziende Digitali*, Università Pegaso
Settori scientifico-disciplinari: INF/01, ING-INF/05, ING-IND/35
Tema n. 1: La digitalizzazione dell'impresa

Studente: **Giovanni Costa** – Università Telematica Pegaso – Anno accademico **2026/2027**
(la matricola è riportata nell'elaborato ufficiale e non è pubblicata nel repository)

Repository GitHub: **[link da inserire dopo la pubblicazione]** – Pagina dei risultati (GitHub Pages): **[link da inserire]**

> Documento tecnico (versione 5) da rileggere, verificare e personalizzare prima dell'adattamento al template
> ufficiale. Tutti i valori numerici sono prodotti da `python main.py` con i dati della cartella `data/`
> (distanze calcolate con il servizio di routing OSRM il 15/10/2026) e coincidono con `output/results.json`.

---

## 1. Introduzione

Nella distribuzione di prodotti agroalimentari freschi la pianificazione delle consegne è un'attività
quotidiana che incide direttamente sui costi: i clienti sono numerosi e di piccola dimensione, le merci sono
deperibili e ogni giro comporta chilometri, ore di lavoro e l'impiego di veicoli che costano anche quando sono
fermi. Le decisioni centrali sono due: in quale ordine servire i clienti e quanti veicoli impiegare.

Il lavoro sviluppa un prototipo in Python che affronta queste decisioni per un'impresa fittizia. Il programma
individua, mediante enumerazione completa, i percorsi che minimizzano la distanza complessiva per ciascuna
configurazione di flotta (un veicolo, oppure due veicoli identici di capacità minore). Successivamente, le
soluzioni ottenute vengono confrontate attraverso un modello economico parametrico. Il programma non minimizza
direttamente il costo: lo calcola sui percorsi ottimi in distanza. Inoltre:
- ricostruisce la sequenza delle consegne e l'evoluzione del carico di ogni veicolo;
- verifica come cambi la convenienza economica al variare dei prezzi unitari.

I risultati sono presentati in una pagina HTML generata automaticamente dal programma.

**Collegamento con il tema della digitalizzazione dell'impresa.** Il Project Work rientra nel tema «La
digitalizzazione dell'impresa». Nelle piccole imprese di distribuzione l'ordine delle consegne e il numero di
mezzi sono spesso decisi in base all'esperienza. Il prototipo mostra come la stessa decisione possa essere
supportata da un procedimento digitale esplicito e riproducibile:
- **dati digitali:** le località e le distanze stradali sono ottenute da servizi cartografici aperti
  (OpenStreetMap, OSRM) tramite interfacce di programmazione, e conservate con la loro fonte;
- **elaborazione algoritmica:** il calcolo dei percorsi ottimi sostituisce la stima manuale e ne garantisce
  l'ottimalità rispetto alla distanza;
- **valutazione economica automatica:** i costi e le analisi di sensibilità si aggiornano modificando un file
  di parametri, senza ricalcoli manuali;
- **comunicazione dei risultati:** una pagina web statica, pubblicabile senza server, rende i risultati
  consultabili da chi deve decidere.

Si tratta di un sistema di supporto alle decisioni di piccola scala, non di un software gestionale: il suo
valore sta nel rendere la scelta trasparente, verificabile e ripetibile quando cambiano dati o prezzi.

## 2. Contesto aziendale e area di studio

*SiciliaFresh Distribuzione* è un'impresa **simulata** che rifornisce di ortofrutta, latticini e prodotti da
forno piccoli esercizi commerciali, bar e ristoranti lungo la costa tirrenica della provincia di Messina, tra
Milazzo e Spadafora. Il deposito si trova a **San Pier Marina**, frazione costiera del comune di San Pier Niceto.

La traccia richiede che il deposito coincida con il comune di residenza: lo studente ha confermato che San Pier
Niceto, di cui San Pier Marina è frazione, è il proprio comune di residenza.

I clienti sono stati scelti tra le località costiere vicine al deposito, collegate dalla strada statale 113 e
da strade provinciali di pianura, per rappresentare una distribuzione su viabilità ordinaria, senza strade
montane o tortuose.

| ID | Località | Comune | Tipologia di cliente (simulata) | Quantità richiesta (kg) |
|----|----------|--------|----------------------------------|------------------------:|
| C1 | Milazzo | Milazzo | Rivendita ortofrutta e minimarket | 420 |
| C2 | Monforte Marina | Monforte San Giorgio | Bar-gastronomia | 180 |
| C3 | Torregrotta | Torregrotta | Ristorante e banco frutta | 350 |
| C4 | Venetico Marina | Venetico | Alimentari di quartiere | 250 |
| C5 | Spadafora | Spadafora | Ristorante sul lungomare | 300 |
|    | **Totale** | | | **1.500** |

Località e distanze stradali sono reali; azienda, clienti e quantità sono inventati a scopo didattico.

**Scelta delle «località limitrofe».** La traccia chiede «cinque località limitrofe reali», non cinque comuni
confinanti. Si sono quindi scelti cinque centri abitati reali vicini al deposito, raggiungibili in pochi chilometri
sulla viabilità ordinaria: le distanze stradali dal deposito vanno da 1,43 a 9,51 km. Monforte San Giorgio, di cui
Monforte Marina è frazione, figura tra i comuni confinanti con San Pier Niceto (voce «San Pier Niceto» di
Wikipedia, consultata il 14/10/2026). Le altre località sono comuni vicini lungo lo stesso tratto di costa. Si
sono esclusi i comuni confinanti dell'entroterra collinare, per rappresentare una distribuzione su viabilità
ordinaria.

### 2.1 Ricerca sul contesto

La traccia chiede di «eseguire una ricerca per descrivere l'impresa agroalimentare selezionata, i prodotti
distribuiti, la clientela servita e il relativo contesto logistico». Poiché l'impresa è simulata, la ricerca
riguarda il contesto reale in cui l'impresa simulata si colloca. Le parti tra parentesi quadre vanno completate
dallo studente con informazioni tratte da fonti verificabili, da citare nella bibliografia (§Fonti di contesto).
Le informazioni già presenti sono state verificate sulle fonti citate.

**Il settore agroalimentare nell'area.** **[Da completare: caratteristiche della produzione e della
distribuzione agroalimentare nella provincia di Messina e nella fascia tirrenica; dimensione e tipologia delle
imprese di distribuzione locali; ruolo dei piccoli esercizi commerciali e della ristorazione. Possibili tipi di
fonte: statistiche ufficiali (ad esempio ISTAT), Camera di commercio, Regione Siciliana, associazioni di
categoria. Un documento da consultare è la «Relazione previsionale e programmatica per l'esercizio 2026» della
Camera di Commercio di Messina, che contiene dati sulle imprese della provincia; i suoi dati non sono stati
riportati perché non è stato possibile verificarne il testo.]**

**I prodotti distribuiti.** Ortofrutta, latticini e prodotti da forno sono prodotti deperibili. Il trasporto
stradale di derrate deperibili a temperatura controllata è regolato dall'**Accordo ATP**:
- l'accordo è stato concluso a Ginevra il 1° settembre 1970 nell'ambito della Commissione economica per
  l'Europa delle Nazioni Unite ed è entrato in vigore il 21 novembre 1976;
- in Italia è stato ratificato con la legge 2 maggio 1977, n. 264, e reso esecutivo con il DPR 29 maggio 1979,
  n. 404;
- l'accordo stabilisce i requisiti dei mezzi di trasporto (allegato 1) e le temperature da rispettare per i
  prodotti surgelati e congelati (allegato 2) e per quelli né surgelati né congelati (allegato 3).

Per questo nel modello i veicoli sono furgoni refrigerati; i costi specifici della refrigerazione non sono
modellati separatamente, ma rientrano nei costi fissi e chilometrici ipotizzati. **[Da completare: temperature e
tempi di conservazione dei singoli prodotti, frequenza tipica delle consegne.]**

**La clientela servita.** **[Da completare: tipologie di clienti dell'area (minimarket, bar, ristoranti,
alimentari), dimensione tipica degli ordini, eventuale stagionalità legata al turismo estivo della costa.
Motivare le quantità ipotizzate in §2 e §7.3, che restano dati simulati.]**

**Il contesto logistico.** Elementi già documentati dal progetto:
- le cinque località e il deposito sono collegati dalla SS113 costiera e da strade provinciali di pianura (SP58,
  SP59, SP60, SP67), come risulta dalle strade percorse registrate in `data/distances_source.json`;
- le distanze stradali dal deposito vanno da 1,43 km (Monforte Marina) a 9,51 km (Milazzo);
- Milazzo è isolata a ovest rispetto agli altri clienti, raccolti a est del deposito.

- il prezzo del gasolio rilevato dal MIMIT il 16/10/2026 è, in media, di 2,265 €/l in Sicilia e di 2,256 €/l
  a livello nazionale (self-service): il costo del carburante nell'area è leggermente superiore alla media.

**[Da completare: eventuali criticità della viabilità locale (traffico estivo, attraversamenti urbani, accesso
ai centri storici), orari tipici di consegna degli esercizi, vincoli di sosta per lo scarico.]**

## 3. Il problema logistico: un problema di consegna

Il problema è di **distribuzione**, non di raccolta. Ogni giorno:

1. ciascun veicolo parte dal deposito con la merce necessaria per tutti i clienti che gli sono assegnati
   (*carico iniziale*);
2. presso ogni cliente consegna la *quantità richiesta*, e il *carico residuo* a bordo diminuisce della stessa
   quantità;
3. ogni cliente è servito esattamente una volta;
4. al termine del giro il veicolo rientra al deposito; poiché non sono previsti ritiri né resi, il carico
   residuo al rientro è nullo.

Le quantità dei clienti rappresentano quindi una **domanda da soddisfare**. Il carico iniziale di un veicolo è
la somma delle quantità da consegnare ai suoi clienti e non può superare la *capacità massima* del veicolo.

Si confrontano due assetti della flotta:
- **Scenario A**: un solo furgone refrigerato da 1.600 kg, che serve tutti i clienti in un unico giro;
- **Scenario B**: due furgoni refrigerati identici da 900 kg ciascuno. Nessuno dei due può trasportare l'intera
  domanda di 1.500 kg, quindi i clienti vanno ripartiti ed entrambi i veicoli devono essere impiegati.

Nello Scenario A si sceglie l'ordine di visita; nello Scenario B si sceglie anche la ripartizione dei clienti
tra i veicoli.

## 4. Obiettivi

**Obiettivo generale.** Individuare e confrontare, per un'impresa agroalimentare simulata, le configurazioni
distributive ottimali con uno e con due veicoli, valutandone la convenienza economica.

| Obiettivo specifico | Criterio misurabile di completamento | Esito |
|---------------------|--------------------------------------|-------|
| Modellare la rete di distribuzione | Deposito e 5 clienti con punti di riferimento documentati; grafo pesato e direzionale | Raggiunto (§7) |
| Costruire la matrice delle distanze | 30 coppie origine–destinazione da fonte cartografica documentata, diagonale nulla, valori positivi | Raggiunto (§7.2), verificato da test |
| Risolvere il TSP (Scenario A) | 120 permutazioni esaminate; soluzione uguale al minimo enumerato | Raggiunto (§11.1) |
| Risolvere il CVRP con due veicoli (Scenario B) | 15 ripartizioni esaminate senza duplicati; ottimo uguale a quello di un'enumerazione indipendente | Raggiunto (§11.2) |
| Verificare i vincoli | Capacità, servizio unico, partenza e rientro al deposito, carico residuo mai negativo e nullo al rientro | Raggiunto (controlli e test, §16) |
| Calcolare i costi | Totale uguale alla somma di costo fisso, carburante, altri costi variabili e autista | Raggiunto (§12) |
| Analizzare la sensibilità | Almeno un prezzo unitario variato su un intervallo; pareggio calcolato e verificato | Raggiunto (§13): tre parametri |
| Visualizzare i risultati | Pagina HTML con grafi, sequenza delle consegne e grafici; valori uguali a `results.json` | Raggiunto (§15), verificato da test |
| Validare il software | Test automatici eseguiti e superati | Raggiunto: 32 test su 32 (§16) |

## 5. Pianificazione del progetto

La tabella riporta le fasi del lavoro. Le durate sono **stime di pianificazione**; le durate effettive vanno
completate dallo studente.

| Fase | Attività | Obiettivo | Risorse | Durata prevista (stima) | Durata effettiva | Output | Criterio di verifica |
|------|----------|-----------|---------|------------------------:|-----------------:|--------|----------------------|
| 1. Analisi del problema | Lettura della traccia, individuazione dei requisiti | Requisiti chiari e verificabili | Traccia PW 23, testi su TSP/VRP | 4 h | [da compilare] | Elenco dei requisiti | Ogni requisito associato a un componente (Appendice A) |
| 2. Definizione dell'istanza | Scelta di deposito, clienti, quantità e capacità | Istanza conforme alle condizioni della traccia | Conoscenza del territorio, OpenStreetMap | 3 h | [da compilare] | `locations.csv`, `deliveries.csv`, `config.json` | Condizioni di capacità verificate dal programma |
| 3. Raccolta dei dati geografici | Geocodifica dei punti, calcolo della matrice con OSRM, controllo delle strade e confronto con Valhalla | Distanze stradali documentate | Nominatim, OSRM, Valhalla, `tools/fetch_distances.py`, `tools/check_distances.py` | 4 h | [da compilare] | `distances.csv`, `distances_source.json`, `distances_check.json` | 30 coppie presenti; solo viabilità ordinaria; scarti contenuti tra i due motori |
| 4. Modellazione matematica | Formulazione di TSP, CVRP, carico residuo e costi | Modello coerente con il codice | Bibliografia (§Bibliografia) | 4 h | [da compilare] | §8 del rapporto | Formule verificate sui risultati |
| 5. Sviluppo Python | Caricamento dati, enumerazione, verifiche, sequenza delle consegne | Programma corretto e leggibile | Python 3, libreria standard | 10 h | [da compilare] | `src/`, `main.py` | Test automatici superati |
| 6. Analisi economica | Modello dei costi, confronto, sensibilità | Confronto trasparente e riproducibile | `costs.json`, fonti economiche [da integrare] | 4 h | [da compilare] | `economics.py`, §12–13 | Somme e pareggi verificati da test |
| 7. Sviluppo HTML | Generazione della pagina, grafi, grafici, interazioni | Presentazione chiara dei risultati | HTML, CSS, JavaScript | 10 h | [da compilare] | `output/` | Pagina coerente con `results.json`; controllo visivo |
| 8. Testing | Test automatici e verifiche manuali e visive | Affidabilità del prodotto | `unittest`, browser | 5 h | [da compilare] | `tests/`, §16 | Tutti i test superati |
| 9. Documentazione | README e rapporto | Riproducibilità e comunicazione | Editor di testo | 8 h | [da compilare] | `README.md`, rapporto | Comandi verificati; valori uguali all'output |
| 10. Validazione finale | Controllo incrociato dati–codice–output–rapporto | Coerenza complessiva | Tutti i file del progetto | 3 h | [da compilare] | Versione consegnata | Matrice di conformità completa |

Le fasi 5–8 sono state svolte in modo iterativo: ogni modifica ai dati o al codice è stata seguita dalla
rigenerazione dell'output e dall'esecuzione dei test. Le durate effettive non sono state registrate durante lo
sviluppo: i valori della colonna «Durata prevista» sono stime di pianificazione, non ore svolte, e la colonna
«Durata effettiva» va compilata dallo studente.

**Stato delle attività**

| Attività | Stato |
|----------|-------|
| Fasi 1–8: analisi, istanza, dati geografici, modello, sviluppo Python, analisi economica, pagina HTML, test | Completate (versione 5 del prototipo) |
| Fase 9: README e rapporto tecnico | Completata in bozza; personalizzazione a cura dello studente |
| Conferma del comune di residenza | Completata (confermato dallo studente) |
| Scelta delle «località limitrofe» | Completata: interpretazione motivata in §2 |
| Prezzo del carburante osservato (MIMIT, 16/10/2026) | Completata |
| Esecuzione di test e programma sul computer dello studente | **Da svolgere** (studente) |
| Fonti per i parametri economici non osservati, durate effettive, completamento della ricerca sul contesto | **Da svolgere** (studente) |
| Adattamento al template Pegaso | **Da svolgere** (studente) |
| Fase 10: pubblicazione su GitHub e GitHub Pages, inserimento dei link | **Da svolgere** (previa autorizzazione) |

## 6. Risorse e strumenti

| Risorsa | Funzione nel progetto | Motivo della scelta | Vantaggi | Limiti | Alternative scartate |
|---------|----------------------|---------------------|----------|--------|----------------------|
| Python 3 e libreria standard (`itertools`, `csv`, `json`, `unittest`, `urllib`) | Calcolo, gestione dei dati, test | Linguaggio richiesto; nessuna installazione aggiuntiva | Riproducibilità; codice leggibile | Prestazioni non adatte a istanze grandi | Librerie esterne (es. pandas, OR-Tools): non necessarie, e i solutori sono esclusi dalla traccia |
| OpenStreetMap e Nominatim | Coordinate e punti di riferimento | Dati aperti e citabili tramite identificativo | Riferimenti verificabili (ID OSM) | Qualità dipendente dai contributori | Coordinate lette a mano: meno documentabili |
| OSRM (server pubblico) | Matrice delle distanze stradali e strade percorse | Motore di instradamento open source su dati OSM | Matrice completa e direzionale in una richiesta; strade percorse documentate | Percorso più rapido secondo il modello, non misurato sul campo; servizio dimostrativo senza garanzie | Lettura manuale da un servizio cartografico, coppia per coppia: lenta e più soggetta a errori |
| Valhalla (server pubblico FOSSGIS) | Controllo indipendente della matrice | Secondo motore di instradamento gratuito, senza chiave di accesso | Verifica del motore di calcolo su tutte le 30 coppie | Usa gli stessi dati OpenStreetMap: non è un controllo indipendente dei dati | Servizi commerciali (es. Google Maps): richiedono chiavi e condizioni d'uso specifiche |
| HTML, CSS e JavaScript nativo | Pagina dei risultati, interazioni, animazioni | Pagina statica pubblicabile senza server | Nessuna dipendenza; funziona anche senza JavaScript | Grafici da costruire a mano in SVG | Framework frontend e librerie di grafici: non necessari |
| Google Fonts (Manrope, Space Grotesk) | Tipografia | Caratteri leggibili e coerenti | Migliore gerarchia visiva | Richiede connessione; in assenza si usano i caratteri di sistema | — |
| `unittest` e browser Chromium (anche in modalità headless) | Test automatici e verifiche visive | Strumenti standard e gratuiti | Verifiche ripetibili | Un solo motore di rendering verificato | — |
| Letteratura scientifica (§Bibliografia) | Inquadramento teorico | Fonti di riferimento sui problemi TSP e VRP | Terminologia e definizioni corrette | — | — |
| Assistente di intelligenza artificiale | Supporto alla scrittura del codice, alla verifica e alla redazione dei testi | **[Da descrivere dallo studente]** | **[Da descrivere]** | Risultati da verificare personalmente | — |

## 7. Definizione dell'istanza

### 7.1 Località e punti di riferimento

| ID | Località | Punto di riferimento | Lat, Lon | Riferimento OSM |
|----|----------|----------------------|----------|-----------------|
| D | San Pier Marina (San Pier Niceto) | Nodo della frazione | 38.2031170, 15.3253471 | node/2698850276 |
| C1 | Milazzo | Municipio, Atrio del Carmine | 38.2204827, 15.2421668 | node/2363131885 |
| C2 | Monforte Marina (Monforte San Giorgio) | Nodo della frazione | 38.2066237, 15.3379597 | node/2273443920 |
| C3 | Torregrotta | Municipio, Via Mezzasalma | 38.1917335, 15.3525949 | node/2470169235 |
| C4 | Venetico Marina (Venetico) | Ufficio postale, Via Paolo Sindoni | 38.2193263, 15.3686303 | node/2471012203 |
| C5 | Spadafora | Municipio, Piazza Vittorio Emanuele III | 38.2222359, 15.3748423 | node/2470582569 |

Per Venetico Marina si è usato l'ufficio postale perché il nodo "Venetico" di OSM indica il borgo collinare.
Il motore di instradamento ha agganciato ciascun punto alla strada più vicina, a una distanza compresa tra 5,9 e
19,8 m.

### 7.2 Distanze stradali

Le distanze sono state calcolate con **OSRM** (*Open Source Routing Machine*), servizio pubblico
`router.project-osrm.org`, sulla rete stradale di OpenStreetMap, profilo auto. Per ogni coppia ordinata OSRM
restituisce la lunghezza del **percorso più rapido** secondo il proprio modello, non necessariamente del più
corto. Il servizio è stato interrogato il **15/10/2026** (`tools/fetch_distances.py`). La risposta completa e l'elenco delle
strade percorse per ciascuna coppia sono conservati in `data/distances_source.json`.

Si tratta di distanze **calcolate da un motore di instradamento su dati cartografici**, non di misure
effettuate sul campo. Sui dati sono stati eseguiti questi controlli:
- la matrice contiene tutte le 30 coppie direzionali;
- la diagonale è nulla e non ci sono valori negativi o nulli fuori diagonale;
- ogni valore coincide con la risposta OSRM arrotondata ai 10 m;
- tutte le coppie usano la SS113 costiera e strade provinciali di pianura (SP58, SP59, SP60, SP67), senza
  tratti montani o autostradali.

Questi controlli sono codificati nei test (§16).

**Controllo con un secondo motore di instradamento.** Tutte le 30 coppie sono state ricalcolate con Valhalla
(server pubblico FOSSGIS, profilo auto; `tools/check_distances.py`, risultati in `data/distances_check.json`).
Valhalla usa gli stessi dati OpenStreetMap: il controllo è indipendente rispetto al motore di calcolo e al
criterio di scelta del percorso, non rispetto ai dati cartografici. Esito:
- 30 coppie su 30 confrontate, differenza media 0,06 km;
- 27 coppie entro il 5%;
- gli scarti maggiori (fino a 0,40 km, pari al 10,3%) riguardano tutti Torregrotta, l'unica località
  nell'entroterra, dove i due motori scelgono vie urbane diverse.

La matrice OSRM resta la fonte principale e non è stata modificata. Come prova di robustezza, gli ottimi sono
stati ricalcolati sulla matrice Valhalla (senza modificare il progetto):
- lo Scenario B mantiene gli stessi percorsi (37,93 km);
- lo Scenario A sceglie un ordine diverso di lunghezza praticamente uguale (34,33 km);
- la conclusione economica non cambia (A più conveniente di 24,03 €).

L'ordine di visita dello Scenario A è sensibile a piccole variazioni delle distanze, perché 12 sequenze
distano meno di 0,5 km dall'ottimo; la distanza ottima e il confronto economico invece non lo sono.

| da \ a | D | C1 | C2 | C3 | C4 | C5 |
|--------|---:|---:|---:|---:|---:|---:|
| **D** | 0 | 9,51 | 1,43 | 4,49 | 4,49 | 5,23 |
| **C1** | 9,95 | 0 | 10,99 | 14,05 | 14,05 | 14,79 |
| **C2** | 1,75 | 10,85 | 0 | 3,02 | 3,49 | 4,22 |
| **C3** | 4,86 | 13,96 | 3,35 | 0 | 4,46 | 5,19 |
| **C4** | 4,75 | 13,85 | 3,24 | 4,47 | 0 | 0,80 |
| **C5** | 5,56 | 14,66 | 4,05 | 5,28 | 0,88 | 0 |

La matrice è **direzionale**: in 14 coppie su 15 andata e ritorno differiscono (fino a 0,44 km), per effetto di
sensi unici, svincoli e attraversamenti urbani. La matrice non è stata resa simmetrica.

### 7.3 Quantità e capacità

| Condizione della traccia | Esito (verificato dal programma) |
|--------------------------|----------------------------------|
| Il veicolo dello Scenario A trasporta tutte le consegne | 1.500 kg ≤ 1.600 kg ✓ |
| Nessun veicolo dello Scenario B trasporta da solo tutte le consegne | 1.500 kg > 900 kg ✓ |
| Esiste almeno una ripartizione ammissibile tra i due veicoli | 6 ripartizioni su 15 ✓ |
| Ogni consegna è trasportabile da un veicolo dello Scenario B | 420 kg ≤ 900 kg ✓ |
| Ogni cliente è servito esattamente una volta | controllato su ogni soluzione ✓ |

La capacità complessiva dello Scenario B (1.800 kg) supera la domanda solo del 20%: il vincolo di capacità è
stringente ed esclude 9 ripartizioni su 15.

## 8. Modello matematico

### 8.1 Grafo e notazione

La rete è un **grafo pesato e direzionale** $G = (V, A)$: i nodi sono il deposito $0$ e i clienti
$C = \{1, \dots, n\}$ ($n = 5$), gli archi sono tutte le coppie ordinate di nodi distinti e il peso dell'arco
$(i, j)$ è la distanza stradale $d_{ij}$, in generale diversa da $d_{ji}$. Le distanze sono raccolte nella
**matrice delle distanze** $D = [d_{ij}]$.

- $q_i$: quantità richiesta dal cliente $i$ (kg); $Q_A = 1.600$ kg, $Q_B = 900$ kg: capacità massime.
- $\Pi(S)$: insieme delle permutazioni di un sottoinsieme $S \subseteq C$. Un percorso
  $\pi = (\pi_1, \dots, \pi_k) \in \Pi(S)$ parte dal deposito, visita i clienti nell'ordine dato e torna al
  deposito; la sua lunghezza è

$$L(\pi) = d_{0,\pi_1} + \sum_{h=1}^{k-1} d_{\pi_h,\pi_{h+1}} + d_{\pi_k,0}.$$

### 8.2 Scenario A – Traveling Salesman Problem

Il **Traveling Salesman Problem (TSP)** chiede il ciclo di lunghezza minima che visita una sola volta ogni
nodo e torna al punto di partenza. La **funzione obiettivo** è la lunghezza del giro:

$$\min_{\pi \in \Pi(C)} L(\pi), \qquad \text{con } \sum_{i \in C} q_i \le Q_A.$$

Con distanze direzionali il problema è un **TSP asimmetrico**: un percorso e il suo inverso possono avere
lunghezze diverse. Le **soluzioni ammissibili** sono $n! = 120$.

La traccia ammette come criterio la distanza o il tempo di percorrenza complessivo. Si è scelta la **distanza**,
perché è il dato documentato coppia per coppia. Nel modello economico il tempo di guida è stimato come
distanza diviso velocità media costante: minimizzare la distanza equivale quindi a minimizzare il tempo di guida
stimato. I tempi restituiti da OSRM sono usati solo come controllo della velocità media (§12.2), non
nell'ottimizzazione.

### 8.3 Scenario B – Capacitated Vehicle Routing Problem

Il **Vehicle Routing Problem (VRP)**, introdotto da Dantzig e Ramser (1959), estende il TSP a una flotta di
veicoli con origine e destinazione nel deposito. Nel **Capacitated VRP (CVRP)** il carico di ogni veicolo non
può superarne la capacità. Con due veicoli identici:

$$\min_{\{S_1, S_2\}} \;\Big[ \min_{\pi_1 \in \Pi(S_1)} L(\pi_1) + \min_{\pi_2 \in \Pi(S_2)} L(\pi_2) \Big]$$

soggetto a

$$S_1 \cup S_2 = C, \quad S_1 \cap S_2 = \emptyset, \quad S_1, S_2 \neq \emptyset, \quad
\sum_{i \in S_k} q_i \le Q_B \;\; (k = 1, 2).$$

### 8.4 Carico iniziale e carico residuo

Per un veicolo che serve i clienti di $S$ nell'ordine $\pi$, il **carico iniziale** e il **carico residuo**
dopo la $h$-esima consegna sono:

$$R_0 = \sum_{i \in S} q_i \le Q, \qquad R_h = R_{h-1} - q_{\pi_h} \quad (h = 1, \dots, k), \qquad R_k = 0.$$

Il vincolo di capacità coincide quindi con $R_0 \le Q$: in un problema di sola consegna il carico è massimo
alla partenza e decresce lungo il giro. Il carico residuo non entra nella funzione obiettivo. Viene calcolato
dopo l'ottimizzazione, a partire dall'ordine di visita trovato, per descrivere le consegne e verificarne la
correttezza.

### 8.5 Complessità computazionale

TSP e CVRP sono problemi **NP-difficili**: non sono noti algoritmi esatti di complessità polinomiale e il
numero di soluzioni cresce in modo fattoriale ($n!$ sequenze per il TSP). Con cinque clienti l'enumerazione
completa è immediata e garantisce l'ottimo, perché esamina ogni soluzione ammissibile. Con dieci clienti le
sole permutazioni sarebbero oltre 3,6 milioni.

## 9. Algoritmo di enumerazione completa

**Scenario A.** `itertools.permutations` genera le 120 sequenze; per ciascuna si calcola $L(\pi)$ e si conserva
la minima. In caso di parità si tiene la prima sequenza incontrata e si riporta il numero di soluzioni
equivalenti.

**Scenario B.**
1. *Ripartizioni.* Le assegnazioni ordinate dei cinque clienti ai due veicoli sono $2^5 = 32$, di cui 2 con
   un veicolo vuoto. I veicoli sono identici, quindi $(S_1, S_2)$ e $(S_2, S_1)$ sono la stessa soluzione. Il
   primo cliente è sempre assegnato al veicolo 1 e si enumerano le $2^4 = 16$ combinazioni degli altri,
   escludendo quella con il veicolo 2 vuoto: si ottengono $2^{n-1} - 1 = 15$ ripartizioni, senza perdite né
   duplicati.
2. *Capacità.* Si scartano le ripartizioni in cui un carico iniziale supera 900 kg: ne restano 6.
3. *Percorsi.* Per ogni ripartizione ammissibile si valutano tutte le coppie di permutazioni
   ($|S_1|! \cdot |S_2|!$). Le 6 ripartizioni ammissibili sono tutte del tipo 2 + 3 clienti, quindi le
   combinazioni di percorsi valutate sono $6 \times 2! \times 3! = 72$.

**Verifiche integrate.** Su ogni soluzione il programma controlla:
- partenza e rientro al deposito;
- servizio unico di ogni cliente, senza esclusioni;
- rispetto delle capacità;
- coincidenza con il minimo enumerato;
- per la sequenza delle consegne, che il carico residuo non diventi mai negativo e sia nullo al rientro.

Istanze non risolvibili o dati non validi producono errori espliciti.

## 10. Implementazione Python

| Componente | Responsabilità |
|------------|----------------|
| `data/*.csv`, `data/*.json` | Località, distanze, quantità, capacità e ipotesi economiche, modificabili senza toccare il codice |
| `src/data_loader.py` | Lettura e validazione dei dati |
| `src/routing.py` | Enumerazione completa, verifiche, funzione `delivery_schedule` per carico iniziale e residuo |
| `src/economics.py` | Modello dei costi, confronto, sensibilità e punto di pareggio |
| `src/visualization.py` | Generazione della pagina HTML, dei grafi e dei grafici SVG |
| `output/styles.css`, `output/app.js` | Stile e interazioni (JavaScript nativo, senza librerie) |
| `main.py` | Esecuzione dell'analisi, riepilogo, scrittura di `results.json` e `index.html` |
| `tools/fetch_distances.py` | Calcolo facoltativo delle distanze con OSRM |
| `tools/check_distances.py` | Controllo facoltativo della matrice con Valhalla |
| `tests/test_routing.py` | 32 test automatici (`unittest`) |

La funzione `delivery_schedule` riceve un percorso già ottimizzato e restituisce, per ogni fermata, la
quantità consegnata, il carico residuo e i chilometri del tratto. Non introduce una simulazione separata e non
modifica la funzione obiettivo. Python scrive nell'HTML tutti i valori, e `app.js` aggiunge solo comportamento.

### 10.1 Esecuzione e visualizzazione

**Requisiti.** Python 3.8 o successivo; nessuna libreria esterna. La connessione internet non è necessaria per
il calcolo: serve solo per i caratteri tipografici della pagina (in assenza si usano i caratteri di sistema) e
per gli script facoltativi di calcolo e controllo delle distanze.

**Esecuzione su Windows.**
1. Installare Python da <https://www.python.org/downloads/>, selezionando l'opzione «Add python.exe to PATH».
2. Scaricare il repository (oppure estrarre l'archivio ZIP) e aprire la cartella del progetto.
3. Aprire il Prompt dei comandi nella cartella (scrivendo `cmd` nella barra degli indirizzi di Esplora risorse)
   ed eseguire `python main.py`. In alternativa, fare doppio clic su `esegui.bat`.
4. Il programma stampa il riepilogo dei risultati, scrive `output/results.json` e `output/index.html` e apre
   la pagina nel browser predefinito (`python main.py --no-open` genera i file senza aprirla).
5. Per eseguire i test automatici: `python -m unittest -v`, dalla cartella del progetto.

**Visualizzazione della pagina HTML.**
- *In locale:* aprire con un doppio clic il file `output/index.html`. La pagina è statica: non richiede un
  server e funziona anche con JavaScript disattivato, mostrando in quel caso entrambi gli scenari.
- *Online:* **[link GitHub Pages da inserire dopo la pubblicazione]**. Il file `index.html` nella radice del
  repository reindirizza a `output/index.html`.

**Aggiornamento dei risultati.** Dopo ogni modifica dei file in `data/` (località, distanze, quantità,
capacità, costi) è sufficiente rieseguire `python main.py`: risultati, grafi e grafici vengono ricalcolati.
Gli script `tools/fetch_distances.py` e `tools/check_distances.py` ricalcolano e controllano la matrice delle
distanze e richiedono la connessione internet.

## 11. Risultati dell'ottimizzazione

### 11.1 Scenario A

Sono state valutate 120 permutazioni, tutte ammissibili. Il percorso ottimale misura **34,32 km**:

| Fermata | Località | Tratto (km) | Consegna (kg) | Carico residuo (kg) |
|--------:|----------|------------:|--------------:|--------------------:|
| — | Partenza da San Pier Marina | — | — | 1.500 (carico iniziale) |
| 1 | Monforte Marina | 1,43 | 180 | 1.320 |
| 2 | Torregrotta | 3,02 | 350 | 970 |
| 3 | Venetico Marina | 4,46 | 250 | 720 |
| 4 | Spadafora | 0,80 | 300 | 420 |
| 5 | Milazzo | 14,66 | 420 | 0 |
| — | Rientro a San Pier Marina | 9,95 | — | 0 |

Il carico iniziale (1.500 kg) occupa il 94% della capacità. Due permutazioni hanno la stessa lunghezza
minima: la seconda inverte Venetico Marina e Spadafora (5,19 + 0,88 + 13,85 km contro 4,46 + 0,80 + 14,66 km,
19,92 km in entrambi i casi). La parità dipende dai valori arrotondati ai 10 m.

### 11.2 Scenario B

Sono state esaminate 15 ripartizioni, di cui 6 ammissibili, e 72 combinazioni di percorsi.

| Clienti del veicolo 1 | Carico iniziale | Clienti del veicolo 2 | Carico iniziale | Miglior distanza (km) |
|-----------------------|----------------:|-----------------------|----------------:|----------------------:|
| Milazzo, Monforte Marina | 600 | Torregrotta, Venetico Marina, Spadafora | 900 | **37,54** |
| Milazzo, Torregrotta | 770 | Monforte Marina, Venetico Marina, Spadafora | 730 | 39,49 |
| Milazzo, Venetico Marina | 670 | Monforte Marina, Torregrotta, Spadafora | 830 | 43,49 |
| Milazzo, Spadafora | 720 | Monforte Marina, Torregrotta, Venetico Marina | 780 | 43,50 |
| Milazzo, Monforte Marina, Venetico Marina | 850 | Torregrotta, Spadafora | 650 | 43,77 |
| Milazzo, Monforte Marina, Spadafora | 900 | Torregrotta, Venetico Marina | 600 | 43,78 |

Sequenza delle consegne della soluzione ottimale:

| Veicolo | Fermata | Località | Tratto (km) | Consegna (kg) | Carico residuo (kg) |
|---------|--------:|----------|------------:|--------------:|--------------------:|
| 1 | — | Partenza | — | — | 600 |
| 1 | 1 | Monforte Marina | 1,43 | 180 | 420 |
| 1 | 2 | Milazzo | 10,85 | 420 | 0 |
| 1 | — | Rientro | 9,95 | — | 0 |
| 2 | — | Partenza | — | — | 900 |
| 2 | 1 | Torregrotta | 4,49 | 350 | 550 |
| 2 | 2 | Venetico Marina | 4,46 | 250 | 300 |
| 2 | 3 | Spadafora | 0,80 | 300 | 0 |
| 2 | — | Rientro | 5,56 | — | 0 |

Il veicolo 1 percorre 22,23 km, il veicolo 2 15,31 km, per un totale di **37,54 km**. Il veicolo 2 parte a pieno
carico (900 kg su 900), il veicolo 1 al 67%. Il veicolo 2 può servire Venetico Marina e Spadafora in entrambi gli
ordini con la stessa lunghezza (4,49 + 4,46 + 0,80 + 5,56 e 4,49 + 5,19 + 0,88 + 4,75, entrambe 15,31 km). La
seconda ripartizione migliore è più lunga di 1,95 km.

### 11.3 Confronto delle distanze

Lo Scenario B percorre 3,22 km in più dello Scenario A (**+9,38%**).

## 12. Analisi economica

### 12.1 Modello dei costi

Il programma individua, mediante enumerazione completa, i percorsi che minimizzano la distanza complessiva per
ciascuna configurazione di flotta. Successivamente, le soluzioni ottenute vengono confrontate attraverso un
modello economico parametrico: il costo è **calcolato** sui percorsi ottimi, non minimizzato. Il costo
giornaliero di un veicolo che percorre $D$ km con $m$ consegne è:

$$C = F + D \cdot (c \cdot p + o) + w \cdot \left(\frac{D}{s} + m \cdot \frac{\tau}{60}\right)$$

Il **costo fisso** $F$ comprende la quota giornaliera di noleggio o ammortamento, assicurazione, bollo e
manutenzione programmata. I **costi variabili** sono il carburante (consumo $c$ per prezzo $p$), gli altri costi
chilometrici $o$ e l'autista (costo orario $w$, velocità media $s$, tempo di scarico per consegna $\tau$). Il
costo di uno scenario è la somma dei costi dei suoi veicoli; nello Scenario B ogni veicolo ha il proprio autista.

### 12.2 Parametri: un prezzo osservato e alcune ipotesi

Il **prezzo del gasolio è un valore osservato**: 2,265 €/l, media regionale della Sicilia per il gasolio
self-service rilevata dal Ministero delle Imprese e del Made in Italy (Osservatorio prezzi carburanti) il
16/10/2026. Si è preferito il valore regionale a quello nazionale (2,256 €/l nella stessa data), perché più vicino
all'area di consegna. La fonte e i valori della pagina MIMIT sono registrati in `data/fuel_price_source.json`.
Il prezzo pubblicato include le imposte: un'impresa che recupera l'IVA sosterrebbe un costo netto inferiore, aspetto
non modellato.

Tutti gli altri parametri sono **ipotesi didattiche**, non tariffe ufficiali né dati aziendali osservati
(`data/costs.json`):

| Parametro | Scenario A | Scenario B |
|-----------|-----------:|-----------:|
| Costo fisso $F$ | 75 €/giorno | 50 €/giorno per veicolo |
| Consumo $c$ | 0,11 l/km | 0,08 l/km |
| Altri costi variabili $o$ | 0,12 €/km | 0,08 €/km |
| Prezzo del gasolio $p$ (**osservato**, MIMIT) | 2,265 €/l | 2,265 €/l |
| Costo orario dell'autista $w$ | 20 €/h | 20 €/h |
| Velocità media $s$ | 40 km/h | 40 km/h |
| Tempo di scarico per consegna $\tau$ | 15 min | 15 min |

Il prezzo al litro è convertito in costo per chilometro moltiplicandolo per il consumo del veicolo: 0,249 €/km per
il furgone dello Scenario A (0,11 l/km) e 0,181 €/km per quelli dello Scenario B (0,08 l/km). Gli «altri costi
variabili» comprendono solo pneumatici, manutenzione e usura, quindi il carburante non è conteggiato due volte.

**[Indicare, se disponibili, le fonti per il costo del lavoro (ad esempio il contratto collettivo di
riferimento) e per i costi dei veicoli (listini di noleggio, consumi dichiarati). In mancanza, restano ipotesi
dichiarate come tali.]**

La velocità ipotizzata è coerente con i tempi stimati da OSRM per i percorsi ottimali: 39,9 km/h per lo
Scenario A, 38,1 e 42,1 km/h per i due veicoli dello Scenario B. Anche quei tempi sono stime di modello, non
misure.

### 12.3 Risultati

| Voce | Scenario A | Scenario B |
|------|-----------:|-----------:|
| Distanza | 34,32 km | 37,54 km |
| Ore di lavoro (guida + scarico) | 2,11 h | 2,19 h |
| Costo fisso | 75,00 € | 100,00 € |
| Autista | 42,16 € | 43,77 € |
| Carburante | 8,55 € | 6,80 € |
| Altri costi al km | 4,12 € | 3,00 € |
| **Costo complessivo** | **129,83 €** | **153,58 €** |

Nello Scenario B il veicolo 1 costa 76,92 € e il veicolo 2 76,65 €. Lo **Scenario A risulta il più
conveniente**: risparmia **23,75 €** al giorno, e lo Scenario B costa il **18,29%** in più.

## 13. Analisi di sensibilità

Il confronto è stato ripetuto variando un prezzo unitario alla volta, a percorsi invariati. Il costo è lineare
in ogni parametro, quindi la differenza $\Delta(x) = C_B(x) - C_A(x)$ è una retta e il **punto di pareggio** si
calcola in forma chiusa:

$$x^* = -\frac{\Delta(0)}{\Delta(1) - \Delta(0)}.$$

| Parametro | Intervallo | Δ = B − A agli estremi | Esito |
|-----------|------------|------------------------|-------|
| Prezzo del gasolio (base 2,265 €/l, osservato) | 1,60 – 2,90 €/l | da 24,26 € a 23,26 € | Nessun pareggio; la retta si annullerebbe a circa 33,0 €/l |
| Costo orario dell'autista | 12 – 32 €/h | da 23,10 € a 24,71 € | Nessun pareggio; pareggio matematico negativo (circa −275 €/h) |
| Costo fisso giornaliero del veicolo A | 50 – 130 €/giorno | da 48,75 € a −31,25 € | **Pareggio a 98,75 €/giorno** |

Per il carburante la pendenza di $\Delta$ è $c_B D_B - c_A D_A = 0{,}08 \cdot 37{,}54 - 0{,}11 \cdot 34{,}32
\approx -0{,}77$: ogni euro di aumento del prezzo riduce lo svantaggio di B di soli 0,77 €. Il punto di pareggio
sul costo fisso non è stato forzato: è un esito del modello. Negli altri due casi il programma segnala
correttamente che il pareggio non esiste nell'intervallo.

## 14. Valutazione critica dei risultati

**Punti di forza del modello.**
- Il risultato è ottimo in senso esatto rispetto alla distanza, e l'ottimalità è verificabile: ogni soluzione
  ammissibile viene esaminata e il programma controlla che la soluzione scelta coincida con il minimo enumerato.
- Le distanze sono reali, direzionali e tracciabili coppia per coppia, con un secondo motore di controllo.
- Il modello dei costi è trasparente: ogni voce è una formula esplicita con parametri modificabili, e la
  linearità consente di calcolare esattamente i punti di pareggio.
- Il programma usa solo la libreria standard ed è riproducibile con un solo comando.

**Struttura del costo.** Con le ipotesi adottate il costo dipende soprattutto dalla disponibilità dei mezzi e
del personale, non dai chilometri:

| Quota sul costo totale | Scenario A | Scenario B |
|------------------------|-----------:|-----------:|
| Costo fisso | 57,8% | 65,1% |
| Autista | 32,5% | 28,5% |
| Costi chilometrici (carburante e altri) | 9,8% | 6,4% |

La differenza tra gli scenari si scompone in +25,00 € di costo fisso, +1,61 € di lavoro e −2,86 € di costi
chilometrici. I veicoli piccoli consumano meno, ma il loro vantaggio è di un ordine di grandezza inferiore al
costo fisso del secondo mezzo.

**Vantaggi della soluzione ottimale (Scenario A).** Un solo giro di 34,32 km serve tutti i clienti con un unico
mezzo e un solo autista. La capacità è sfruttata al 94%, contro l'83% complessivo dello Scenario B (67% e 100%
nei due veicoli). Il costo per kg consegnato è di 0,087 € contro 0,102 €.

**Svantaggi dello Scenario B e suoi possibili punti di forza.** Lo Scenario B percorre più strada perché due
veicoli ripetono i tratti di uscita e rientro dal deposito, e paga due costi fissi. Ha però caratteristiche che
il modello non valuta economicamente:
- ogni giro dura circa un'ora (1,06 e 1,13 h, contro 2,11 h del giro unico), quindi l'ultimo cliente viene
  servito prima: un aspetto rilevante per prodotti deperibili;
- c'è ridondanza in caso di guasto di un mezzo;
- c'è un margine di capacità sul veicolo 1 (300 kg) per eventuali ordini aggiuntivi.

**Effetto della capacità.** Il vincolo di 900 kg determina la ripartizione ottimale. Il veicolo 2 è saturo, e
solo 6 ripartizioni su 15 sono ammissibili. Con capacità poco inferiori lo Scenario B potrebbe diventare non
risolvibile; con capacità superiori aumenterebbero le alternative.

**Effetto della distribuzione geografica.** I clienti sono disposti lungo un corridoio costiero quasi lineare,
con Milazzo isolata a ovest e gli altri clienti raccolti a est del deposito. La soluzione B dedica un veicolo a
Milazzo, abbinandola alla vicinissima Monforte Marina (1,43 km dal deposito), e l'altro ai clienti a est. La
distanza aggiuntiva resta quindi contenuta (+9,38%). Il carico più alto (420 kg) è proprio quello del cliente
più lontano, e la capacità di 900 kg impedisce di accorparlo agli altri tre clienti orientali. In
un'area più dispersa la differenza di chilometri, e quindi il peso dei costi variabili, sarebbe maggiore.

**Distanza o costo come obiettivo.** Il programma minimizza la distanza e calcola il costo sulle soluzioni
trovate; non esegue un'ottimizzazione del costo. Si può però osservare che, in questo modello, la scelta non
altererebbe i risultati all'interno di ciascuno scenario. I veicoli hanno gli stessi parametri e il numero di
consegne è fisso (cinque), quindi il costo di uno scenario si scrive come quota fissa più un coefficiente per
chilometro totale:
- $C_A = 75 + 0{,}869 \cdot D_A + 25$;
- $C_B = 100 + 0{,}761 \cdot D_B + 25$ (€, con $D$ in km).

Il costo cresce dunque con la distanza, e il percorso più corto risulta anche il più economico tra quelli dello
stesso scenario. È una proprietà di questo modello, non una scelta dell'algoritmo. La conclusione
cambierebbe con veicoli eterogenei, pedaggi, tempi dipendenti dal traffico o un autista pagato a giornata
anziché a ore. In quest'ultimo caso i due giri brevi dello Scenario B sarebbero ancora più penalizzati.

**Sensibilità.** La convenienza dello Scenario A è robusta rispetto ai prezzi del carburante e del lavoro negli
intervalli considerati. Si inverte solo se il costo fisso del veicolo grande supera 98,75 €/giorno, cioè quasi
un terzo in più del valore ipotizzato. Il dato economico decisivo da verificare con fonti reali è quindi il costo
giornaliero dei mezzi.

**Scalabilità dell'enumerazione completa.** Con $n$ clienti il TSP richiede $n!$ sequenze. Con due veicoli
identici le combinazioni di percorsi da esaminare, prima del filtro di capacità, sono $(n-1) \cdot n!/2$:
240 per $n = 5$, oltre 16 milioni per $n = 10$ e circa 2,6 miliardi per $n = 12$. Il metodo è quindi adatto
all'istanza della traccia, ma non a una rete di distribuzione reale con decine di clienti. Lì servirebbero metodi
esatti più efficienti (programmazione dinamica, *branch and bound*) o euristiche, che la traccia esclude.

**Robustezza rispetto ai dati di distanza.** Ricalcolando gli ottimi con le distanze di un secondo motore
(§7.2) cambia solo l'ordine di visita dello Scenario A, tra soluzioni quasi equivalenti; la distanza ottima, i
percorsi dello Scenario B e la conclusione economica restano invariati.

**Limiti che influenzano l'interpretazione economica.**
- I costi sono ipotetici, e la conclusione dipende in larga misura dal rapporto tra i costi fissi dei due tipi
  di furgone.
- Le quantità sono simulate e riferite a una sola giornata tipo, senza variabilità della domanda.
- L'autista è pagato a ore effettive, mentre un contratto giornaliero cambierebbe il confronto.
- I tempi sono stimati con una velocità media costante, senza traffico dinamico.

**Limiti che influenzano la fattibilità operativa.**
- Non sono modellate le finestre temporali di consegna né gli orari di apertura dei clienti.
- Mancano vincoli sulla catena del freddo e sul tempo massimo di permanenza della merce a bordo.
- Il tempo di scarico è uguale per tutti i clienti e indipendente dalla quantità.
- Non c'è traffico dinamico: velocità e tempi non variano con l'ora del giorno.
- Prodotti deperibili: il giro unico dello Scenario A dura circa 2,1 ore e l'ultimo cliente viene servito dopo
  quasi due ore dalla partenza. Il modello non verifica temperature né tempi massimi di trasporto, che per alcuni
  prodotti freschi potrebbero favorire giri più brevi.
- Non sono modellati vincoli temporali sugli autisti (durata del turno, pause) né sui veicoli.
- Le distanze sono calcolate da un motore di instradamento e possono cambiare con lavori o modifiche alla
  viabilità.
- L'enumerazione completa ha scalabilità limitata: già con poche decine di clienti servirebbero metodi esatti
  più efficienti o euristiche.

## 15. Interfaccia HTML

La pagina `output/index.html` è statica: si apre con un doppio clic, non richiede un server e funziona anche
senza JavaScript, mostrando in quel caso entrambi gli scenari.

- **Colori.** Ogni veicolo ha un colore proprio: arancione terracotta per il veicolo 1 (e per il veicolo unico
  dello Scenario A), blu petrolio per il veicolo 2. Il colore si ripete in modo coerente in percorsi, frecce,
  cerchi e numeri delle fermate, legenda, schede dei veicoli e indicatori di carico, ed è definito una sola
  volta in variabili CSS. I percorsi usano linee continue. L'identificazione non è affidata al solo colore:
  ogni fermata ha un numero, ogni scheda il nome del veicolo, ogni tooltip il veicolo e la fermata. La coppia
  di colori è stata verificata per contrasto e distinguibilità nelle principali forme di daltonismo. Nei
  grafici economici gli scenari sono indicati da due toni del colore del marchio, per non confonderli con i
  veicoli.
- **Grafo.** È schematico e non in scala, e la pagina lo dichiara. La posizione dei nodi è ricavata dalle
  coordinate reali: l'ordine ovest–est segue la longitudine e quello nord–sud la latitudine. La scala orizzontale
  è compressa in modo non proporzionale, per allargare il gruppo di località vicine a est del deposito. I nodi
  hanno la stessa posizione nei due scenari; cambiano solo i percorsi. I km mostrati provengono sempre dalla
  matrice stradale, non dalle coordinate del disegno. Il deposito è un quadrato scuro con l'icona di un
  magazzino, i clienti sono cerchi numerati secondo l'ordine di consegna. Gli archi sono leggermente curvi, con
  una freccia a metà che indica il senso di marcia; la curvatura aumenta di poco solo se un arco passerebbe
  troppo vicino a un nodo che non collega. Le etichette riportano i km stradali del tratto e sono
  collocate automaticamente per evitare sovrapposizioni con nodi, frecce e linee. Sotto ogni cliente compare
  la consegna ("consegna 420 kg"). Il tooltip del cliente indica veicolo, fermata, quantità consegnata e carico
  residuo; quello del deposito indica il carico iniziale di ogni veicolo e il rientro a vuoto.
- **Sequenza delle consegne.** Per ogni veicolo una timeline mostra:
  - la partenza con il carico iniziale;
  - per ogni fermata: numero, località, quantità consegnata, carico residuo (anche come barra che si svuota) e
    km dal punto precedente;
  - il rientro con i km totali.

  Si aggiorna con il selettore dello scenario.
- **Altre sezioni:**
  - sintesi con il risparmio giornaliero come indicatore principale;
  - dati logistici con matrice delle distanze e verifiche dell'istanza;
  - analisi economica con grafico per voce di costo e analisi di sensibilità;
  - metodologia e conclusioni.
- **Animazioni.** Comparsa delle sezioni, disegno progressivo dei percorsi nel colore del veicolo e contatori
  dei valori principali. Sono disattivate con l'impostazione "riduci movimento" e nella stampa.

## 16. Verifica e validazione

Verifiche eseguite il 15 e 16/10/2026 su Windows 11 con Python 3.12.1. **[Ripetere `python -m unittest -v` e
`python main.py` sul proprio computer prima della consegna e riportarne l'esito.]**

| Gruppo | Procedura | Risultato | Limitazioni |
|--------|-----------|-----------|-------------|
| Test automatici | 32 test `unittest` | 32 superati | Coprono i casi previsti, non ogni possibile errore |
| Verifiche manuali dell'algoritmo | Istanze di 3 clienti risolte a mano; conteggio $6 \times 2! \times 3! = 72$; somma dei tratti dei percorsi | Coerenti | Limitate a istanze piccole |
| Dati geografici | Completezza delle 30 coppie, coincidenza con la risposta OSRM, strade percorse, distanza di aggancio ≤ 19,8 m; confronto con Valhalla e ricalcolo degli ottimi | Conformi; scarto medio 0,06 km; conclusione invariata | Dati calcolati da servizi di routing sugli stessi dati OpenStreetMap, non misure sul campo |
| Dati di input | Validazione automatica e test con dati mancanti o non validi | Errori rilevati con messaggi espliciti | Verifica formale |
| Controlli economici | Somme delle componenti, pareggi, scomposizione della differenza (+25,00 + 1,61 − 2,86 = 23,75 €); conversione del prezzo al litro in costo per km | Coerenti | Modello semplificato |
| Pagina HTML | Test di corrispondenza HTML–JSON, dei colori e dei file collegati; apertura nel browser; prova del selettore e dei tooltip; schermate a 1440 e 500 px; controllo dello sbordamento a 375 px; pagina senza JavaScript e con movimento ridotto | Nessun errore JavaScript; valori coincidenti; nessuna sovrapposizione nei grafi; nessuno sbordamento | Un solo motore di rendering (Chromium); nessuno smartphone reale |

| Area dei test automatici | Contenuto |
|--------------------------|-----------|
| Distanze e matrice direzionale | Somma degli archi; scelta del verso corretto; matrice non resa simmetrica |
| Ottimo su istanze manuali | TSP di 3 clienti (5 km); CVRP con 3 ripartizioni (7 km) |
| Esaustività | 120 permutazioni; confronto con un'enumerazione indipendente delle 32 assegnazioni ordinate |
| Ripartizioni | 15 senza duplicati né veicoli vuoti; combinazioni pari a $\sum |S_1|! \cdot |S_2|!$ |
| Vincoli | Capacità, completezza, partenza e rientro; rilevazione delle violazioni; istanze non risolvibili |
| Carico residuo | Carico iniziale uguale alla somma delle consegne; diminuzione a ogni consegna; mai negativo; nullo al rientro; ogni cliente riceve esattamente la sua quantità; totale consegnato 1.500 kg; errore se il carico iniziale supera la capacità |
| Configurazione | Deposito San Pier Marina; i cinque clienti concordati; 30 distanze positive e coincidenti con OSRM |
| Costi | Calcolo a mano; totale uguale alla somma delle componenti; percentuali; costi uguali al pareggio |
| Dati non validi | Valori mancanti, non numerici o negativi, righe o colonne mancanti, domanda nulla, file assente |
| Pagina | Valori uguali a `results.json`; file collegati esistenti; colori distinti dei veicoli, uguali in CSS, grafo e legenda; nessun tratteggio come codifica |
| Disposizione del grafo | Ordine ovest–est e nord–sud coerente con le coordinate; Monforte Marina circa alla stessa altezza del deposito; nodi nella stessa posizione nei due scenari |

## 17. Sviluppi futuri

- Rilevare costi reali dei mezzi, a partire dal costo fisso giornaliero, che è il parametro decisivo.
- Introdurre finestre temporali e tempi di scarico dipendenti dalla quantità.
- Ottimizzare direttamente il costo con veicoli eterogenei o retribuzioni giornaliere.
- Confrontare le distanze con un servizio basato su dati cartografici diversi da OpenStreetMap.
- Per istanze più grandi, adottare metodi esatti più efficienti, come la programmazione dinamica di Held e Karp
  (1962), prima di ricorrere a euristiche.

## 18. Conclusioni

Il prototipo risolve in modo esatto e verificabile i due scenari richiesti dalla traccia. Si basa su distanze
stradali reali e direzionali lungo la costa tirrenica, rispetta i vincoli di capacità, evita il doppio conteggio
dovuto ai veicoli identici e ricostruisce per ogni veicolo la sequenza delle consegne con il carico residuo.

Con i dati e le ipotesi adottati un solo veicolo è preferibile sia per distanza (34,32 km contro 37,54 km) sia
per costo (129,83 € contro 153,58 € al giorno, con il prezzo del gasolio rilevato dal MIMIT). La scelta è robusta rispetto ai prezzi del carburante e del
lavoro e dipende soprattutto dal costo fisso dei mezzi. Lo Scenario B conserva però vantaggi operativi
(consegne più rapide, ridondanza) che il modello economico non quantifica.

**Elementi distintivi.** Il progetto non introduce tecniche nuove. Integra strumenti semplici in un sistema
di supporto alle decisioni chiaro e riproducibile:
- un'ambientazione geografica locale reale;
- una matrice stradale direzionale documentata coppia per coppia;
- il confronto tra due configurazioni di flotta, con analisi di sensibilità;
- la rappresentazione della sequenza delle consegne e del carico residuo;
- un'interfaccia che rende leggibili gli stessi risultati calcolati dal programma.

## Contributo personale dello studente

Lo studente ha definito i requisiti del lavoro e ne ha guidato le versioni successive. In particolare:
- ha scelto il deposito nel proprio comune di residenza e le località clienti lungo la costa, chiedendo di
  escludere località montane e strade tortuose;
- ha esaminato le versioni intermedie del prototipo e individuato le correzioni necessarie: colori distinti per
  i due veicoli, rappresentazione delle consegne con il carico residuo, disposizione geografica dei nodi nel
  grafo, distinzione tra ottimizzazione della distanza e confronto economico;
- ha indicato l'uso del prezzo ufficiale del gasolio rilevato dal MIMIT e i criteri di valutazione Pegaso a cui
  allineare il rapporto.

**[Da completare dallo studente, con parole proprie e senza attribuirsi attività non svolte:**
- **le scelte progettuali compiute personalmente (ad esempio località, quantità, ipotesi di costo, struttura del
  rapporto);**
- **le verifiche svolte personalmente (esecuzione dei comandi, controllo di distanze e risultati, lettura del
  codice);**
- **gli strumenti utilizzati e il modo in cui sono stati usati;**
- **le difficoltà incontrate e come sono state risolte.]**

## Nota sull'uso di strumenti di intelligenza artificiale

Il progetto è stato sviluppato con il supporto di un assistente di intelligenza artificiale (Claude, di
Anthropic, usato tramite l'applicazione Claude Code). L'assistente ha scritto il codice Python, HTML, CSS e
JavaScript, ha eseguito le richieste ai servizi OSRM, Valhalla e MIMIT, ha eseguito i test e redatto le bozze dei
testi. Lo studente ha fornito i requisiti e i dati di partenza, ha preso le decisioni progettuali e ha esaminato i
risultati, chiedendo le correzioni descritte nella sezione precedente.

**[Da completare dallo studente secondo le indicazioni dell'Ateneo: verifiche personali svolte sui risultati
(ad esempio esecuzione dei comandi, controllo di alcune distanze, lettura del codice) e grado di revisione dei
testi.]**

## Checklist finale prima della consegna

- [x] Verificare che San Pier Niceto, comune di cui San Pier Marina è frazione, corrisponda al comune di residenza anagrafica dello studente (confermato dallo studente).
- [x] Motivare la scelta delle «località limitrofe reali» (§2). Facoltativo: confermare l'interpretazione con il tutor.
- [ ] Eseguire `python -m unittest -v` e `python main.py` sul proprio computer e riportarne l'esito nel §16.
- [x] Inserire i dati personali (nell'elaborato ufficiale; nel repository solo nome e anno accademico).
- [ ] Compilare durate effettive (§5) e completare contributo personale e nota sull'uso dell'IA.
- [ ] Completare la ricerca sul contesto (§2.1) con fonti reali e citarle in bibliografia.
- [x] Usare un prezzo del carburante osservato da fonte ufficiale (MIMIT, 16/10/2026).
- [ ] Motivare con fonti gli altri parametri di costo (§12.2); in mancanza, lasciarli dichiarati come ipotesi.
- [x] Controllare le voci bibliografiche segnate «da verificare» (verificate il 16/10/2026).
- [ ] Adattare il rapporto al template ufficiale Pegaso.
- [ ] Pubblicare il repository su GitHub, attivare GitHub Pages e inserire i link nel frontespizio e nel §10.1.

## Bibliografia e sitografia

*Le voci vanno controllate sulle edizioni e sulle pagine effettivamente consultate prima della consegna.*

**Fonti teoriche**
- Dantzig, G. B., Ramser, J. H. (1959). The Truck Dispatching Problem. *Management Science*, 6(1), 80–91.
- Held, M., Karp, R. M. (1962). A Dynamic Programming Approach to Sequencing Problems. *Journal of the Society
  for Industrial and Applied Mathematics*, 10(1), 196–210.
- Applegate, D. L., Bixby, R. E., Chvátal, V., Cook, W. J. (2006). *The Traveling Salesman Problem: A
  Computational Study*. Princeton University Press.
- Toth, P., Vigo, D. (a cura di) (2014). *Vehicle Routing: Problems, Methods, and Applications* (2ª ed.). SIAM.

**Fonti geografiche**
- OpenStreetMap contributors. Dati cartografici, licenza ODbL. <https://www.openstreetmap.org> (consultato il 15/10/2026).
- Nominatim, servizio di geocodifica di OpenStreetMap. <https://nominatim.openstreetmap.org> (consultato il 15/10/2026).
- Project OSRM, *Open Source Routing Machine*, servizio pubblico `router.project-osrm.org`, API *table* e *route*.
  <https://project-osrm.org> (consultato il 15/10/2026).
- Valhalla, motore di instradamento open source; server pubblico FOSSGIS `valhalla1.openstreetmap.de`, API
  *sources_to_targets*. <https://valhalla1.openstreetmap.de> (consultato il 16/10/2026).
- Luxen, D., Vetter, C. (2011). Real-time routing with OpenStreetMap data. In *Proceedings of the 19th ACM
  SIGSPATIAL International Conference on Advances in Geographic Information Systems* (GIS 2011, Chicago),
  513–516. Dati bibliografici verificati su DBLP (<https://dblp.org/rec/conf/gis/LuxenV11.html>).
- Wikipedia, voce «San Pier Niceto», sezione sui comuni confinanti. <https://it.wikipedia.org/wiki/San_Pier_Niceto>
  (consultata il 14/10/2026).

**Fonti di contesto**
- Accordo ATP sul trasporto internazionale delle derrate deperibili, Ginevra, 1° settembre 1970; legge 2 maggio
  1977, n. 264; DPR 29 maggio 1979, n. 404. Sintesi consultata su Certifico, «ATP Agreement – update October 2015».
  <https://www.certifico.com/trasporto/trasporto-atp/atp-agreement-update-october-2015> (consultata il 16/10/2026).
- **[Da integrare con le altre fonti usate per la ricerca sul contesto (§2.1).]**

**Fonti economiche**
- Ministero delle Imprese e del Made in Italy, Osservatorio prezzi carburanti. *Prezzi medi dei carburanti – Dati
  per regione*, aggiornamento 16-10-2026. <https://www.mimit.gov.it/it/prezzo-medio-carburanti/regioni>
  (consultato il 16/10/2026).
- Ministero delle Imprese e del Made in Italy, Osservatorio prezzi carburanti. *Prezzi medi nazionali*,
  16-10-2026. <https://www.mimit.gov.it/it/prezzi-carburanti-media-nazionale> (consultato il 16/10/2026).
- **[Da integrare: contratto collettivo di riferimento per il costo del lavoro, listini di noleggio o costi di
  esercizio dei veicoli commerciali. In assenza di fonti, i parametri restano ipotesi dichiarate (§12.2).]**

**Documentazione tecnica**
- Python Software Foundation. *itertools* e *unittest*. <https://docs.python.org/3/library/>
- Project OSRM. *OSRM HTTP API documentation*. <http://project-osrm.org/docs/v5.24.0/api/>
- Valhalla. *Time-Distance Matrix service API reference*. <https://valhalla.github.io/valhalla/api/matrix/> (consultata il 16/10/2026).
- MDN Web Docs. *Intersection Observer API*. <https://developer.mozilla.org/docs/Web/API/Intersection_Observer_API>

---

## Appendice A – Matrice di conformità alla traccia

| Requisito | File interessati | Stato | Note |
|-----------|------------------|-------|------|
| Impresa agroalimentare | `data/config.json`, §2 | Soddisfatto | Simulata e dichiarata come tale |
| Ricerca su impresa, prodotti, clientela e contesto logistico | §2.1 | **Parziale** | Contesto logistico, normativa sul trasporto di deperibili (ATP) e prezzi dei carburanti documentati; dati sul settore e sulla clientela da completare |
| Descrizione del processo di definizione dell'istanza e di sviluppo | §5, §7, §9, §10 | Soddisfatto | Fasi, scelte dei dati, algoritmo e implementazione |
| Un deposito e cinque clienti | `data/locations.csv`, `data/deliveries.csv` | Soddisfatto | Verificato da test |
| Deposito nel comune di residenza | `data/locations.csv` | Soddisfatto | San Pier Marina, frazione di San Pier Niceto, comune di residenza confermato dallo studente |
| Clienti in località limitrofe reali | `data/locations.csv`, §2 | Soddisfatto (interpretazione motivata) | Cinque centri reali a 1,43–9,51 km di strada; Monforte San Giorgio confinante, gli altri vicini lungo la costa |
| Distanze stradali effettive | `data/distances.csv`, `distances_source.json`, `distances_check.json` | Soddisfatto | Calcolate con OSRM su OpenStreetMap (non misurate sul campo), 30 coppie, direzionali; controllate con Valhalla |
| Rappresentazione mediante grafo | Route Explorer | Soddisfatto | Grafi SVG con colori per veicolo |
| Enumerazione completa in Python | `src/routing.py` | Soddisfatto | Solo libreria standard |
| Scenario con un veicolo | `solve_scenario_a()` | Soddisfatto | 120 permutazioni |
| Scenario con due veicoli identici | `solve_scenario_b()` | Soddisfatto | 15 ripartizioni, entrambi i veicoli usati |
| Vincoli di capacità | `routing.py`, `delivery_schedule()` | Soddisfatto | Carico iniziale ≤ capacità; residuo nullo al rientro |
| Percorsi ottimi | `routing.py`, test indipendente | Soddisfatto | Verificato a ogni esecuzione |
| Confronto economico | `src/economics.py` | Soddisfatto | Costi fissi e variabili |
| Voci di costo individuate e motivate | §12.1–12.2, `data/costs.json`, `data/fuel_price_source.json` | **Parziale** | Voci individuate e motivate; prezzo del gasolio osservato (MIMIT, 16/10/2026); altri valori ipotesi senza fonte |
| Variazione di almeno un prezzo unitario | `sensitivity()` | Soddisfatto | Tre parametri; un pareggio nell'intervallo |
| Pagina HTML con grafi e grafici | `output/` | Soddisfatto | Generata da `main.py` |
| Rapporto finale | `docs/project_report.md` | Bozza | Da personalizzare e adattare al template |
| Link al repository | Frontespizio | **Da completare** | Repository pronto in locale; pubblicazione da autorizzare |
| Link alla pagina HTML o indicazioni per visualizzarla | §10.1, `README.md`, `index.html`, `.nojekyll` | Soddisfatto (indicazioni) | Istruzioni di esecuzione e visualizzazione nel §10.1; link online da inserire dopo la pubblicazione |

## Appendice B – Corrispondenza con i criteri di valutazione

La valutazione spetta all'Università; la tabella indica dove il rapporto e il prodotto rispondono a ciascun
criterio e cosa resta da curare.

| Criterio | Dove è trattato | Elementi presenti | Da completare a cura dello studente |
|----------|-----------------|-------------------|-------------------------------------|
| Pianificazione delle fasi | §5 | Dieci fasi con attività, obiettivi, risorse, output e criteri di verifica; durate stimate distinte da quelle effettive; stato delle attività | Durate effettive |
| Organizzazione delle risorse | §6 | Funzione, motivazione, vantaggi, limiti e alternative di ogni risorsa | Descrizione dell'uso dell'IA |
| Individuazione degli obiettivi | §4 | Obiettivo generale e nove obiettivi specifici con criterio misurabile ed esito | — |
| Originalità | §18 (elementi distintivi), §15 | Ambientazione locale, matrice direzionale, carico residuo, interfaccia dedicata | Eventuali considerazioni personali |
| Accuratezza del prodotto | Appendice A, §16, checklist finale | Matrice di conformità; 32 test; controlli sui dati con due motori di instradamento | Conferma del comune di residenza e dell'interpretazione di "limitrofe" |
| Valutazione critica dei risultati | §14 | Struttura dei costi, capacità, geografia, distanza contro costo, sensibilità, limiti economici e operativi | Fonti per i parametri non osservati |
| Linguaggio disciplinare | §8–9, §12–14 | TSP, CVRP, grafo pesato e direzionale, funzione obiettivo, soluzione ammissibile e ottima, complessità, pareggio, costi fissi e variabili, carico residuo | Revisione finale dello stile |
