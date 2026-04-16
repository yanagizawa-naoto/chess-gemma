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

## Results: 100-game balanced tournament

100 games with balanced color assignment (50 Quick=White, 50 Thinker=White), concurrency 20,
300-ply safety cap. Wall-clock: ~100 minutes.

| Outcome | Count | Share |
|---|---|---|
| 🤝 **Draws** | **74** | **74%** |
| ○ Thinker wins | 13 | 13% |
| ● Quick wins | 11 | 11% |
| ⚠ Errors | 2 | 2% (both `ReadTimeout`) |

Chess result breakdown (python-chess `board.result()`):

- `1/2-1/2` (draws by 50-move / threefold / insufficient material / stalemate): 53
- `*` (hit 300-ply cap): 21
- `1-0` (white wins by checkmate): 20
- `0-1` (black wins by checkmate): 4

### The first-move advantage dominates everything

| White side | Games | Quick wins | Thinker wins | Draws |
|---|---|---|---|---|
| **Quick = White** | 49 | **9** | 2 | 38 |
| **Thinker = White** | 49 | 2 | **11** | 36 |

Whoever plays White wins virtually all decisive games. The 20 checkmate-for-white results vs. 4 for
black show how much harder Gemma finds it to convert a game as Black — especially against even an
equally-weak opponent who gets the first move.

### Observations

- **74% of games end in draws** — roughly half by python-chess's automatic rules (50-move,
  threefold, stalemate, insufficient material), half by hitting the 300-move cap. Gemma can
  occasionally checkmate (24 decisive games) but nowhere near reliably.
- **Thinker edges Quick slightly (13 vs. 11)** but the gap is small — both players are roughly
  equally weak at chess, and the CoT hurts at least as much as it helps (Thinker's occasional
  over-analysis leads to time-wasting repetitions).
- **Huge color asymmetry**: White wins ~5× more often than Black. Consistent with chess's
  well-known first-move advantage, amplified by weak play where neutralising the opening edge
  requires precise defence.

### Performance

- Total API calls: 19,129
- Avg latency: 5.72 s
- Throughput: 3.2 calls/s
- Retries: 362 (1.9% — Gemma rarely returns an illegal UCI move)
- Fallbacks: 11
- Timeouts: 2 (both `ReadTimeout` after 90 s)
- Avg decisive-game length: ~100 moves (`1-0` / `0-1`); draws tend to hit the 300-ply cap at 219
  avg moves.

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
