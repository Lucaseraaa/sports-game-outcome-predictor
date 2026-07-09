from flask.views import MethodView
from flask import render_template, request
import plotly.graph_objects as go
import plotly.io as pio

class BetView(MethodView):

    def get(self):
        """
        Metodo che mostra il simulatore generando il grafico 
        """
        budget_iniziale = float(request.args.get('bankroll', 1000))
        puntata_fissa = float(request.args.get('stake', 20))

        # Storico simulato (Sostituisci poi con i tuoi dati reali)
        storico_scommesse = [
            {"match": "Juventus - Inter", "prediction": "1X", "quota": 1.45, "esito": "Vinta", "guadagno": puntata_fissa * 0.45, "bilancio_flow": budget_iniziale + (puntata_fissa * 0.45)},
            {"match": "Milan - Napoli", "prediction": "X", "quota": 3.20, "esito": "Persa", "guadagno": -puntata_fissa, "bilancio_flow": budget_iniziale + (puntata_fissa * 0.45) - puntata_fissa},
            {"match": "Roma - Lazio", "prediction": "2", "quota": 2.10, "esito": "Vinta", "guadagno": puntata_fissa * 1.10, "bilancio_flow": budget_iniziale + (puntata_fissa * 0.45) - puntata_fissa + (puntata_fissa * 1.10)},
        ]

        # Calcoli KPI
        totale_scommesse = len(storico_scommesse)
        scommesse_vinte = sum(1 for s in storico_scommesse if s["esito"] == "Vinta")
        win_rate = (scommesse_vinte / totale_scommesse * 100) if totale_scommesse > 0 else 0
        bilancio_finale = storico_scommesse[-1]["bilancio_flow"] if storico_scommesse else budget_iniziale
        profitto_totale = bilancio_finale - budget_iniziale
        roi = (profitto_totale / (puntata_fissa * totale_scommesse) * 100) if totale_scommesse > 0 else 0

        # Grafico scommesse
        x_dati = [i for i in range(totale_scommesse + 1)]
        y_dati = [budget_iniziale] + [s["bilancio_flow"] for s in storico_scommesse]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x_dati, 
            y=y_dati, 
            mode='lines+markers',
            line=dict(color='#34d399', width=3),
            marker=dict(color='#34d399', size=6),
            fill='tozeroy',
            fillcolor='rgba(52, 211, 153, 0.03)', 
            name='Bilancio'
        ))

        # Personalizzazione del layout per farlo combaciare con il tema scuro
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=10, b=20),
            height=280,
            showlegend=False,
            xaxis=dict(
                gridcolor='rgba(75, 85, 99, 0.2)', 
                tickfont=dict(color='#9ca3af'),
                title=dict(text="Numero Scommesse", font=dict(color='#9ca3af', size=11))
            ),
            yaxis=dict(
                gridcolor='rgba(75, 85, 99, 0.2)', 
                tickfont=dict(color='#9ca3af'),
                title=dict(text="Budget (€)", font=dict(color='#9ca3af', size=11))
            )
        )


        grafico_html = pio.to_html(fig, full_html=False, include_plotlyjs='cdn')

        return render_template(
            "bet.html",
            budget_iniziale=budget_iniziale,
            puntata_fissa=puntata_fissa,
            totale_scommesse=totale_scommesse,
            win_rate=round(win_rate, 1),
            profitto_totale=round(profitto_totale, 2),
            bilancio_finale=round(bilancio_finale, 2),
            roi=round(roi, 1),
            storico=storico_scommesse,
            grafico_html=grafico_html 
        )