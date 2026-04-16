# Chess: Gemma vs Gemma

Two Gemma-backed agents playing standard chess against each other, differentiated only by prompting.
Same architecture as the [othello-gemma](https://github.com/yanagizawa-naoto/othello-gemma),
[shogi-gemma](https://github.com/yanagizawa-naoto/shogi-gemma), and
[go-gemma](https://github.com/yanagizawa-naoto/go-gemma) companion projects.

Built on top of [python-chess](https://python-chess.readthedocs.io/) — which gives us legal-move
generation, check/stalemate/50-move/threefold detection, castling, en-passant, promotions, and PGN/FEN
for free.

## Players

Both players use the **same underlying Gemma model**. Differentiation via prompting only.

| Player | Color | Style | Output |
|---|---|---|---|
| **Quick** | ♔ White | Intuitive / immediate | `{intent, move}` |
| **Thinker** | ♚ Black | Deliberate / CoT | Considers king safety, piece activity, material, opponent response. `{thinking, summary, move}` |

### Move notation

Standard **UCI**. Regex:

```
^[a-h][1-8][a-h][1-8][qrbn]?$
```

- Normal: `e2e4`
- Promotion: `e7e8q` (q/r/b/n)
- Castling: `e1g1` (white kingside), `e1c1`, `e8g8`, `e8c8`

## Rules

- Standard FIDE rules (inherited from `python-chess`)
- Game ends on checkmate / stalemate / 50-move rule / threefold repetition / insufficient material
- Move cap: 300 plies (safety)

## Results

Tournament results will be added here after the 100-game balanced run completes (see
`simulate.py`).

## Quick start

```bash
git clone https://github.com/yanagizawa-naoto/chess-gemma
cd chess-gemma
cp .env.example .env
# edit with your endpoint details
uv sync
uv run streamlit run app.py       # interactive viewer
uv run python simulate.py 100 20  # 100 games, concurrency 20
```

### Required environment variables

See `.env.example`:

- `GEMMA_API_KEY`
- `GEMMA_BASE_URL` (OpenAI-compatible endpoint)
- `GEMMA_MODEL`

## Files

| File | Purpose |
|---|---|
| `chess_game.py` | Thin wrapper on `python-chess` with GameState + history tracking |
| `agent.py` | Quick / Thinker players with JSON-schema-constrained UCI output + retry |
| `app.py` | Streamlit viewer (unicode piece board, last-move highlight, chat bubbles) |
| `simulate.py` | Async parallel tournament with per-call timeout and balanced colors |

## License

MIT
