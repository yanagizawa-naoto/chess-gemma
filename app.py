"""Streamlit UI for Gemma vs Gemma chess match."""
from __future__ import annotations
import html
import time
import streamlit as st
import chess
from dotenv import load_dotenv

from chess_game import GameState, PIECE_UNICODE
from agent import make_players

load_dotenv()
st.set_page_config(page_title="Gemma vs Gemma — Chess", layout="wide")

WHITE = chess.WHITE  # True
BLACK = chess.BLACK  # False


def init_state():
    if "game" not in st.session_state:
        st.session_state.game = GameState()
    if "players" not in st.session_state:
        quick, thinker = make_players()
        # Quick = White (first), Thinker = Black
        st.session_state.players = {WHITE: quick, BLACK: thinker}
    if "running" not in st.session_state:
        st.session_state.running = False
    if "error" not in st.session_state:
        st.session_state.error = None


GLOBAL_CSS = """
<style>
.chess-board { border-collapse: collapse; margin: 0; }
.chess-board td {
    width: 42px; height: 42px; text-align: center; vertical-align: middle;
    font-size: 30px; line-height: 1; font-weight: normal;
}
.chess-board td.light { background: #f0d9b5; }
.chess-board td.dark  { background: #b58863; }
.chess-board td.last.light { background: #f7ec6b; }
.chess-board td.last.dark  { background: #d9bf3e; }
.chess-board th {
    width: 20px; height: 18px; text-align: center;
    font-family: monospace; color: #555; padding: 2px; font-size: 11px;
    background: transparent;
}
.white-piece { color: #fafafa; text-shadow: 0 0 2px #000, 0 0 2px #000; }
.black-piece { color: #111; }

/* Bubbles */
.bubble-row { display: flex; margin: 8px 0; align-items: flex-end; }
.bubble-row.left { justify-content: flex-start; }
.bubble-row.right { justify-content: flex-end; }
.bubble-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    background: #fff; border: 2px solid #888;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0; margin: 0 6px;
}
.bubble-avatar.white { background: #fafafa; color: #111; border-color: #111; }
.bubble-avatar.black { background: #111; color: #fff; }
.bubble {
    padding: 9px 13px; border-radius: 18px; max-width: 80%;
    line-height: 1.45; box-shadow: 0 1px 2px rgba(0,0,0,0.12); font-size: 14px;
}
.bubble.quick { background: #8de08a; color: #1b3a1a; }
.bubble.thinker { background: #a3d3f5; color: #0e2a44; }
.bubble.thinking.quick { background: #d6f0d4; font-style: italic; opacity: 0.9; }
.bubble.thinking.thinker { background: #d8ebf8; font-style: italic; opacity: 0.9; }
.bubble .meta { font-size: 11px; opacity: 0.7; margin-bottom: 3px; }
.bubble .move-chip {
    display: inline-block; color: #fff; padding: 1px 8px; border-radius: 10px;
    font-family: monospace; font-weight: bold; margin-left: 6px; font-size: 12px;
}
.bubble.quick .move-chip { background: #2e7d32; }
.bubble.thinker .move-chip { background: #1565c0; }
.bubble .check-flag {
    display: inline-block; background: #d32f2f; color: #fff;
    padding: 1px 6px; border-radius: 8px; font-size: 10px; margin-left: 4px;
}
.bubble .mate-flag {
    display: inline-block; background: #6a1b9a; color: #fff;
    padding: 1px 6px; border-radius: 8px; font-size: 10px; margin-left: 4px;
}
.bubble .retry-flag {
    display: inline-block; background: #ffb74d; color: #4e2a00;
    padding: 1px 6px; border-radius: 8px; font-size: 10px; margin-left: 4px;
}
.bubble .fb-flag {
    display: inline-block; background: #e57373; color: #fff;
    padding: 1px 6px; border-radius: 8px; font-size: 10px; margin-left: 4px;
}
</style>
"""


def piece_html(piece):
    pair = PIECE_UNICODE.get(piece.piece_type, ("?", "?"))
    glyph = pair[0]  # use the "white" filled glyph for shape, color via CSS
    cls = "white-piece" if piece.color == chess.WHITE else "black-piece"
    return f'<span class="{cls}">{glyph}</span>'


def render_board_html(board, last_move=None):
    """last_move is a chess.Move or None."""
    last_from = last_move.from_square if last_move else None
    last_to = last_move.to_square if last_move else None
    parts = ['<table class="chess-board">']
    parts.append('<tr><th></th>' + ''.join(f'<th>{chr(ord("a") + f)}</th>' for f in range(8)) + '</tr>')
    for r in range(7, -1, -1):
        parts.append(f'<tr><th>{r + 1}</th>')
        for f in range(8):
            sq = chess.square(f, r)
            is_light = ((r + f) % 2 == 1)
            cls = ["light" if is_light else "dark"]
            if sq == last_from or sq == last_to:
                cls.append("last")
            piece = board.piece_at(sq)
            content = piece_html(piece) if piece else ""
            parts.append(f'<td class="{" ".join(cls)}">{content}</td>')
        parts.append('</tr>')
    parts.append('</table>')
    return '\n'.join(parts)


def bubble_html(h):
    is_white = h["player"] == chess.WHITE
    # Quick = white (left), Thinker = black (right)
    side = "left" if is_white else "right"
    avatar_cls = "white" if is_white else "black"
    avatar_glyph = "♔" if is_white else "♚"
    name = "Quick" if is_white else "Thinker"
    bubble_kind = "quick" if is_white else "thinker"
    move = h["move"]
    summary = html.escape(h.get("comment") or "(出力なし)")
    flags = ""
    if h.get("checkmate"):
        flags += '<span class="mate-flag">詰み!</span>'
    elif h.get("delivered_check"):
        flags += '<span class="check-flag">王手!</span>'
    if h.get("retries", 0) > 0:
        if h.get("forced_fallback"):
            flags += '<span class="fb-flag">⚠ FB</span>'
        else:
            flags += f'<span class="retry-flag">🔁{h["retries"]}</span>'
    inner = (
        f'<div class="meta">{name}</div>'
        f'<div>{summary}</div>'
        f'<div style="margin-top:4px"><span class="move-chip">{move}</span>{flags}</div>'
    )
    avatar = f'<div class="bubble-avatar {avatar_cls}">{avatar_glyph}</div>'
    bubble = f'<div class="bubble {bubble_kind}">{inner}</div>'
    if side == "left":
        return f'<div class="bubble-row left">{avatar}{bubble}</div>'
    return f'<div class="bubble-row right">{bubble}{avatar}</div>'


def thinking_bubble_html(player):
    is_white = player == chess.WHITE
    side = "left" if is_white else "right"
    avatar_cls = "white" if is_white else "black"
    avatar_glyph = "♔" if is_white else "♚"
    name = "Quick" if is_white else "Thinker"
    bubble_kind = "quick" if is_white else "thinker"
    bubble = f'<div class="bubble thinking {bubble_kind}"><div class="meta">{name}</div>考え中…</div>'
    avatar = f'<div class="bubble-avatar {avatar_cls}">{avatar_glyph}</div>'
    if side == "left":
        return f'<div class="bubble-row left">{avatar}{bubble}</div>'
    return f'<div class="bubble-row right">{bubble}{avatar}</div>'


def render_feed(game, thinking_player=None):
    parts = []
    if thinking_player is not None:
        parts.append(thinking_bubble_html(thinking_player))
    for h in reversed(game.history):
        parts.append(bubble_html(h))
    return "\n".join(parts)


def step_one_move(feed_placeholder, game):
    if game.is_over:
        st.session_state.running = False
        return
    color = game.turn
    legal = game.legal_uci()
    player = st.session_state.players[color]
    feed_placeholder.markdown(render_feed(game, thinking_player=color), unsafe_allow_html=True)
    try:
        resp = player.choose_move_streaming(game.board, legal)
    except Exception as e:
        st.session_state.error = f"{player.name} エラー: {e}"
        st.session_state.running = False
        return
    try:
        game.play(
            resp.move, reasoning=resp.reasoning, raw_text=resp.raw_text, comment=resp.comment,
            retries=resp.retries, forced_fallback=resp.forced_fallback,
        )
    except ValueError as e:
        st.session_state.error = f"内部エラー: {e}"
        st.session_state.running = False


def main():
    init_state()
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    game: GameState = st.session_state.game

    col_left, col_right = st.columns([1, 1])

    with col_left:
        if game.is_over:
            w = game.winner()
            if w == chess.WHITE:
                st.markdown("### 🏆 ♔ Quick (White) 勝ち")
            elif w == chess.BLACK:
                st.markdown("### 🏆 ♚ Thinker (Black) 勝ち")
            else:
                st.markdown("### 🤝 引き分け")
        else:
            turn_label = "♔ Quick (White)" if game.turn == chess.WHITE else "♚ Thinker (Black)"
            check = " 王手中!" if game.board.is_check() else ""
            st.markdown(f"### 手数 {len(game.history)} → 次: **{turn_label}**{check}")

        last_move = None
        if game.history:
            last_move = chess.Move.from_uci(game.history[-1]["move"])
        st.markdown(render_board_html(game.board, last_move=last_move), unsafe_allow_html=True)

        bcol1, bcol2, bcol3, bcol4 = st.columns(4)
        with bcol1:
            if st.button("▶", help="自動再生", disabled=st.session_state.running or game.is_over, use_container_width=True):
                st.session_state.running = True
                st.rerun()
        with bcol2:
            if st.button("⏸", help="停止", disabled=not st.session_state.running, use_container_width=True):
                st.session_state.running = False
                st.rerun()
        with bcol3:
            if st.button("⏭", help="1手進める", disabled=st.session_state.running or game.is_over, use_container_width=True):
                st.session_state._do_step_once = True
                st.rerun()
        with bcol4:
            if st.button("🔄", help="リセット", use_container_width=True):
                st.session_state.game = GameState()
                st.session_state.running = False
                st.session_state.error = None
                st.session_state.pop("_do_step_once", None)
                st.rerun()

        if st.session_state.error:
            st.error(st.session_state.error)

    with col_right:
        feed_placeholder = st.empty()
        feed_placeholder.markdown(render_feed(game), unsafe_allow_html=True)

        do_step_once = st.session_state.pop("_do_step_once", False)
        do_autoplay_step = st.session_state.running and not game.is_over

        if do_autoplay_step or do_step_once:
            if do_autoplay_step and game.history:
                time.sleep(1.5)
            step_one_move(feed_placeholder, game)
            st.rerun()


if __name__ == "__main__":
    main()
