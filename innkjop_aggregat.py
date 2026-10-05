"""Innkjøpsordningene for litteratur — innkjøpte titler per år.

Leser bare data/innkjop_serie.csv, som ligger ved siden av denne filen i
repoet. Ingen tilgang til $HABITUS_DATA, ingen titler, ingen forfattere.

Datafilen bygges av mart/innkjop_serie.py i kulturradet/innkjop, og skal ikke
redigeres for hånd.

Kjør lokalt (venv fra innkjop-prosjektet):
    ..\\innkjop\\.venv\\Scripts\\python.exe -m streamlit run innkjop_aggregat.py
"""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent / "data" / "innkjop_serie.csv"
SPLITT_AAR = 2021  # året skjønnlitteraturen ble delt i fire ordninger

st.set_page_config(page_title="Innkjøpsordningene — innkjøpte titler", layout="wide")


def tall(x: float) -> str:
    return f"{x:,.0f}".replace(",", " ")


@st.cache_data
def last(sti: str) -> pd.DataFrame:
    return pd.read_csv(sti)


if not DATA.exists():
    st.error(f"Finner ikke {DATA.name}. Kjør mart/innkjop_serie.py først.")
    st.stop()

d = last(str(DATA))

st.title("Innkjøpsordningene for litteratur")
st.caption(
    "Antall titler kjøpt inn per år. Enheten er tittelen: en parallellutgave "
    "i trykt bok og e-bok telles én gang."
)

per_aar = d.groupby("aar", as_index=False)[["utvalg", "innkjopt"]].sum()
siste = per_aar.iloc[-1]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Periode", f"{per_aar['aar'].min()}–{per_aar['aar'].max()}")
k2.metric(f"Innkjøpte titler {int(siste['aar'])}", tall(siste["innkjopt"]))
k3.metric(f"Påmeldte titler {int(siste['aar'])}", tall(siste["utvalg"]))
k4.metric("Innkjøpt i hele serien", tall(per_aar["innkjopt"].sum()))

fane_total, fane_gruppe, fane_ordning = st.tabs(
    ["Samlet", "Etter ordningstype", "Etter ordning"]
)

with fane_total:
    maal = st.radio(
        "", ["Innkjøpte titler", "Påmeldte titler"],
        horizontal=True, label_visibility="collapsed",
    )
    felt = "innkjopt" if maal == "Innkjøpte titler" else "utvalg"

    st.altair_chart(
        alt.Chart(per_aar)
        .mark_bar(color="#1f2937")
        .encode(
            x=alt.X("aar:O", title="År"),
            y=alt.Y(f"{felt}:Q", title=maal),
            tooltip=[
                alt.Tooltip("aar:O", title="År"),
                alt.Tooltip(f"{felt}:Q", title=maal, format=",.0f"),
            ],
        )
        .properties(height=440),
        use_container_width=True,
    )

with fane_gruppe:
    st.caption(
        "Inndelingen følger innkjøpsordningen, ikke innholdet i boka. En "
        "oversatt tegneserie er kjøpt inn gjennom ordningen for oversatt "
        "litteratur og telles der, ikke under tegneserier."
    )
    gruppe = d.groupby(["aar", "ordningsgruppe"], as_index=False)["innkjopt"].sum()

    st.altair_chart(
        alt.Chart(gruppe)
        .mark_line(point=True)
        .encode(
            x=alt.X("aar:O", title="År"),
            y=alt.Y("innkjopt:Q", title="Innkjøpte titler"),
            color=alt.Color("ordningsgruppe:N", title="Type innkjøpsordning"),
            tooltip=[
                alt.Tooltip("aar:O", title="År"),
                alt.Tooltip("ordningsgruppe:N", title="Type innkjøpsordning"),
                alt.Tooltip("innkjopt:Q", title="Innkjøpte titler", format=",.0f"),
            ],
        )
        .properties(height=440),
        use_container_width=True,
    )

    st.dataframe(
        gruppe.pivot(index="aar", columns="ordningsgruppe", values="innkjopt")
        .fillna(0).astype(int),
        use_container_width=True,
    )

with fane_ordning:
    st.caption(
        f"Skjønnlitteraturen var én ordning til og med {SPLITT_AAR - 1}, og ble "
        f"delt i automatisk og selektiv, for barn og unge og for voksne, fra "
        f"{SPLITT_AAR}. Oppdelingen vises derfor bare fra da."
    )
    fin = d[d["aar"] >= SPLITT_AAR]
    tab = (
        fin.pivot_table(index="aar", columns="ordning_navn",
                        values="innkjopt", aggfunc="sum")
        .fillna(0).astype(int)
    )
    tab = tab.loc[:, (tab != 0).any(axis=0)]
    st.dataframe(tab, use_container_width=True)

with st.expander("Om statistikken"):
    st.markdown(
        """
Populasjonen er titler påmeldt innkjøpsordningene for litteratur.

Enhet i statistikken er tittelen. En parallellutgave i trykt bok og e-bok
telles én gang.

Et år er **rundeåret**, altså året for påmeldingsfristen til den runden
tittelen er vurdert i. Ikke året vedtaket ble fattet. En runde kan være åpen
for påmelding ut kalenderåret, og behandlingen fortsetter etter at runden er
lukket, så tellingen gjøres på et fast tidspunkt og tallet for et år kan bli
justert opp i ettertid.

Serien starter i 2018. Saksbehandlingssystemet ble tatt i bruk midt i 2017, og
det året dekker derfor bare et halvt år. Tall for tidligere år finnes i andre
kilder og inngår ikke her.

Tallene er gruppert etter **type innkjøpsordning**, ikke etter innholdet i
boka. En oversatt tegneserie er kjøpt inn gjennom ordningen for oversatt
litteratur og telles der. «Tegneserier» betyr altså titler kjøpt inn gjennom
tegneserieordningen, ikke alle tegneserier som er kjøpt inn.

Skjønnlitteraturen var én ordning til og med 2020 og ble delt i fire fra 2021:
automatisk og selektiv, for barn og unge og for voksne. Hele perioden vises
derfor samlet per ordningstype.

Tallene bygger på to uttrekk fra saksbehandlingssystemene: 2018–2023 hentet i
juni 2025, 2024 og 2025 hentet i oktober 2026.
"""
    )

st.caption("Ved bruk av statistikken skal Kulturdirektoratet oppgis som kilde.")