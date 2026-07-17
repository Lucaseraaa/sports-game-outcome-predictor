# sports-game-outcome-predictor
Progetto di Laboratorio di Informatica applicata AA 2025/2026. Il progetto consiste in un applicazione Web realizzata in Flask, che possa prevede i risultati delle partite della Serie A.

## Regole per la gestione dei branch
Devono essere utilizzate 3 tipologie di branch per la gestione del progetto:
- main;
- developing;
- feature.

Il branch main viene utilizzato solamente per il deploy dell'applicazione, il developing per la versione di staging e feature per aggiungere, modificare ed eliminare codice. In particolare utilizziamo la seguente nomenclatura per denominare i branch nella parte di feature:
- new/name: i branch che iniziano con "new/" implicano l'aggiunta di nuove caratteristiche dell'applicazione (come nuove parti dell'interfaccia grafica, nuovi notebook, ecc...);
- fix/name: questo tipo di branch vengono utilizzati per correggere una feature già presente nel sistema, ma imprecisa o scorretta, e rendono necessaria una modifica.

# Gestione del progetto
Per la corretta organizzazione del progetto, esso viene diviso in moduli, ognuno con una funzione specifica, che verrà descritta a seguito.

## Notebook
Il modulo di notebook viene utilizzato per le operazioni di **data analysis** e di **machine learning**, data la sua comodità in questi ambiti: è infatti possibile visualizzare le variabili e le strutture dati graficamente (utile per i dataframe di Pandas e i grafici di Matplotlib); inoltre è possibile separare il codice in varie "celle", opportunamente commentate per separare le diverse funzionalità che vogliamo implementare. 

### App 
Questo modulo contiene l'app vera e propria, ossia il sito web creato con Flask, che permette di visualizzare previsioni di risultati delle partite di Serie A, attraverso l'ausilio del modello creato nei notebook. L'applicazione utilizza come fonte di dati delle nuove partite le API di [highlighty](https://highlightly.net/). Per il corretto funzionamento delle API è stato creato un file .env (non messo in gitignore per comodità, data la necessità di presentare il progetto) che contiene le credenziali necessarie. 

# Deploy

## Locale
Per il deploy in locale utilizzare i seguenti comandi (all'interno di un ambiente virtuale):

```bash
pip install -r requirements.txt 
python -m app
```

L'applicazione verrà esposta al seguente indirizzo `localhost:5000`.

## Docker
Per lanciare l'applicazione in Docker è necessario effettuare una build dell'immagine e successivamente lanciarla, con 
i seguenti comandi:

```bash
docker build -t sports-outcome-player .
docker run --rm -p 8000:8000 sports-outcome-player
```