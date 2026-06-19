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

### feature-engineering.ipynb
Il notebook in questione viene utilizzato per le operazioni di data analysis, ovvero per trasformare il dataset utilizzato in un dataset che contenga degli indici di nostro interesse (quelli da noi ritenuti più importanti per il nostro obiettivo). vengono poi visualizzati dei grafici che descrivono alcuni comportamenti statistici del dataset. 