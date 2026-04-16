"""Wrapper around python-chess providing GameState with history tracking."""
from __future__ import annotations
from dataclasses import dataclass, field
import chess


PIECE_UNICODE = {
    chess.KING:   ("♔", "♚"),
    chess.QUEEN:  ("♕", "♛"),
    chess.ROOK:   ("♖", "♜"),
    chess.BISHOP: ("♗", "♝"),
    chess.KNIGHT: ("♘", "♞"),
    chess.PAWN:   ("♙", "♟"),
}


def piece_symbol(piece: chess.Piece) -> str:
    """Return unicode symbol (white gets outlined, black filled)."""
    pair = PIECE_UNICODE.get(piece.piece_type, ("?", "?"))
    return pair[0] if piece.color == chess.WHITE else pair[1]


def board_to_ascii(board: chess.Board) -> str:
    """Return a readable 8x8 board display with ranks 8..1 top-to-bottom."""
    lines = ["  a b c d e f g h"]
    for r in range(7, -1, -1):
        row = []
        for f in range(8):
            sq = chess.square(f, r)
            piece = board.piece_at(sq)
            row.append(piece.symbol() if piece else ".")
        lines.append(f"{r + 1} {' '.join(row)}")
    lines.append("")
    lines.append(f"Turn: {'white' if board.turn == chess.WHITE else 'black'}")
    if board.is_check():
        lines.append("(check!)")
    return "\n".join(lines)


@dataclass
class GameState:
    board: chess.Board = field(default_factory=chess.Board)
    history: list = field(default_factory=list)

    @property
    def is_over(self) -> bool:
        return self.board.is_game_over() or len(self.history) >= 300

    @property
    def turn(self) -> bool:
        return self.board.turn

    def legal_uci(self) -> list[str]:
        return [m.uci() for m in self.board.legal_moves]

    def play(self, uci: str, *, reasoning: str = "", raw_text: str = "",
             comment: str = "", retries: int = 0, forced_fallback: bool = False) -> None:
        move = chess.Move.from_uci(uci)
        if move not in self.board.legal_moves:
            raise ValueError(f"Illegal move {uci}")
        player = self.board.turn
        gave_check = self.board.gives_check(move)
        self.board.push(move)
        self.history.append({
            "player": player,
            "move": uci,
            "reasoning": reasoning,
            "comment": comment,
            "raw_text": raw_text,
            "board_fen": self.board.fen(),
            "retries": retries,
            "forced_fallback": forced_fallback,
            "delivered_check": gave_check,
            "checkmate": self.board.is_checkmate(),
        })

    def winner(self):
        """Return chess.WHITE / chess.BLACK / 'draw' / None."""
        if not self.is_over:
            return None
        if self.board.is_checkmate():
            return not self.board.turn  # side who just moved wins
        # stalemate, insufficient material, 50-move, threefold, move cap → draw
        return "draw"
