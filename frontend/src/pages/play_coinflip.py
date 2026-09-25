"""
Streamlit page for playing a coin flip game.

Allows a player to select an opponent and play a game of Heads or Tails.

Endpoints used:
    GET /player
    POST /game
"""

import time

import streamlit as st

from utils.api_client import api_client
from utils.auth_guard import check_authentification
from utils.log_init import get_page_logger

st.title("Play a Coin flip")
logger = get_page_logger("play_game")

check_authentification()

player = st.session_state.get("player")

response = api_client.get("/player/")

if response["status_code"] != 200:
    st.error("Error loading players")
    st.stop()

players = response["data"]
opponents = [
    j for j in players if j["id_player"] != player["id_player"] and j["username"] != "admin"
]

if not opponents:
    st.warning("No opponents available")
    st.stop()

opponent = st.selectbox("Choose an opponent", opponents, format_func=lambda j: j["username"])

bet = st.radio("Heads or Tails", ["heads", "tails"])

if st.button("Play"):
    logger.info("Play a game")
    with st.spinner("Wait for it..."):
        time.sleep(1)

    response = api_client.post(
        "/game/",
        json={
            "id_opponent": opponent["id_player"],
            "game_mode": "coinflip",
            "params": {"choice": bet},
        },
    )

    if response["status_code"] != 200:
        st.error(response["data"])
        st.stop()

    data = response["data"]

    st.write(f"**{data['description']}**")

    if data["winner"] == player["username"]:
        st.success(f"""🎉 **You win!**\n\nYour new Elo rating is {data["new_elo1"]}""")
        st.balloons()
    elif data["winner"] == opponent["username"]:
        st.warning(f"""😢 **You lose**\n\nYour new Elo rating is {data["new_elo1"]}""")
    else:
        st.info("Draw, no change in Elo rating")

    logger.info("Game is over")


if st.button("Back to menu", type="primary"):
    st.switch_page("pages/player_menu.py")
