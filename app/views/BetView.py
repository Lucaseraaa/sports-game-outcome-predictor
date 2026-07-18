from flask.views import MethodView
from flask import render_template, request
import plotly.graph_objects as go
import plotly.io as pio
from app.api.Odds import Odds

import warnings

# Silenzia solo gli UserWarning specifici di scikit-learn relativi ai nomi delle feature
warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

class BetView(MethodView):

    def get(self):


        # Leggiamo i parametri pulendo eventuali virgole inserite dall'utente
        budget_iniziale = request.args.get('bankroll', '7600').replace(',', '.')
        puntata_fissa = request.args.get('stake', '10').replace(',', '.')

        try:
            budget_iniziale = float(budget_iniziale)
        except ValueError:
            budget_iniziale = 7600
            
        try:
            puntata_fissa = float(puntata_fissa)
        except ValueError:
            puntata_fissa = 10.0


        odds_manager = Odds(
            odds_dataframe_path="app/static/odds.csv",
            match_dataframe_path="app/static/result.csv"
        )

        
        # Calcolo sulle stagioni di test
        risultati_24_25 = odds_manager.backtest("2024-2025", budget_iniziale, puntata_fissa)
        
        budget_intermedio = risultati_24_25["flow_rf"][-1]
        risultati_25_26 = odds_manager.backtest("2025-2026", budget_intermedio, puntata_fissa)

        # Unione delle tabelle
        storico_totale_rf = risultati_24_25["storico_rf"] + risultati_25_26["storico_rf"]

        # Flussi sequenziali completi per Plotly 
        flow_rf = risultati_24_25["flow_rf"] + risultati_25_26["flow_rf"][1:]
        flow_logistic = risultati_24_25["flow_logistic"] + risultati_25_26["flow_logistic"][1:]
        flow_xgb = risultati_24_25["flow_xgb"] + risultati_25_26["flow_xgb"][1:]

        #Calcolo metriche globali KPI basate sul Random Forest
        totale_scommesse = len(storico_totale_rf)
        bilancio_finale = flow_rf[-1] if totale_scommesse > 0 else budget_iniziale
        profitto_totale = bilancio_finale - budget_iniziale

        # Volume di gioco totale 
        volume_gioco = puntata_fissa * totale_scommesse
        
        # Moltiplicatore del capitale iniziale 
        moltiplicatore_capitale = (bilancio_finale / budget_iniziale) if budget_iniziale > 0 else 1.0


        # Disegno del grafico comparativo
        x_dati = list(range(totale_scommesse + 1))
        fig = go.Figure()

        # Random Forest
        fig.add_trace(go.Scatter(x=x_dati, y=flow_rf, mode='lines', line=dict(color='#34d399', width=3), name='Random Forest'))
        # Regressione Logistica
        fig.add_trace(go.Scatter(x=x_dati, y=flow_logistic, mode='lines', line=dict(color='#ef4444', width=3), name='Regr. Logistica'))
        # XGBoost
        fig.add_trace(go.Scatter(x=x_dati, y=flow_xgb, mode='lines', line=dict(color='#3b82f6', width=3), name='XGBoost'))

        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=15, b=25), height=320, showlegend=True,
            legend=dict(font=dict(color='#9ca3af', size=11), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(gridcolor='rgba(75, 85, 99, 0.15)', tickfont=dict(color='#9ca3af'), title=dict(text="Progressione Match di Test", font=dict(color='#9ca3af', size=11))),
            yaxis=dict(gridcolor='rgba(75, 85, 99, 0.15)', tickfont=dict(color='#9ca3af'), title=dict(text="Bilancio (€)", font=dict(color='#9ca3af', size=11)))
        )

        grafico_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

    

        return render_template(
            "bet.html",
            budget_iniziale=budget_iniziale,
            puntata_fissa=puntata_fissa,
            totale_scommesse=totale_scommesse,
            profitto_totale=round(profitto_totale, 2),
            bilancio_finale=round(bilancio_finale, 2),
            volume_gioco=round(volume_gioco, 2),
            moltiplicatore=round(moltiplicatore_capitale, 2),
            storico=storico_totale_rf,
            grafico_html=grafico_html 
        )