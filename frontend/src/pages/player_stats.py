import pandas as pd
import streamlit as st

from utils.api_client import api_client

# from utils.auth_guard import chec_authentification
from utils.log_init import get_page_logger

st.title("Player stats")
logger = get_page_logger("list_players")

# check_authentification()


if st.query_params.id_player:
    joueur = api_client.get(f"/player/{st.query_params.id_player}").get("data")
    kd = api_client.get(f"/game/players/{st.query_params.id_player}/win-loss")
    st.subheader(joueur["username"])
    col1, col2 = st.columns(2)

    with col1:
        st.metric("ELO", joueur["elo"])
        st.metric("K/D", round(kd.get("data"), 2))

    with col2:
        st.write(joueur["email"])
        st.checkbox("Joueur de pokémon?", value=joueur["pokemon_fan"], disabled=True)

    matchs = api_client.get(f"/game/?id_player={st.query_params.id_player}").get("data")
    df = pd.DataFrame(matchs)
    gagnant = df.winner.map(
        lambda x: int(st.query_params.id_player) == x["id_player"] if x is not None else None
    )
    df.player1 = df.player1.map(lambda x: f"{x['username']} ({x['elo']})")
    df.player2 = df.player2.map(lambda x: f"{x['username']} ({x['elo']})")
    df.winner = gagnant.map(lambda x: "Win" if x else "Loss" if x is not None else "None")
    st.dataframe(df.iloc[:, [1, 2, 3, 4]], hide_index=True)
