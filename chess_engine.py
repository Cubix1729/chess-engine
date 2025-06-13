from typing import Generator
from collections import OrderedDict, defaultdict
from math import inf
import time
import random
import chess.polyglot
import chess


# Main constants

MAX_ENGINE_DEPTH = 5  # maximum search depth for the main Negamax algorithm
QUIESCENCE_DEPTH = 3  # maximum depth for the quiescence search algorithm
NULL_MOVE_REDUCTION = 2  # depth reduction for null-move pruning
PATH_TO_OPENING_BOOK = "./engines/komodo.bin"  # path to the opening book used (in Polyglot format)


player_coefs = {chess.WHITE: 1, chess.BLACK: -1}

piece_values = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
}

black_pawn_pst = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

black_knight_pst = [
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-30, 0, 10, 15, 15, 10, 0, -20],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 10, 15, 15, 10, 0, -20],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
]

black_bishop_pst = [
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
]

black_rook_pst = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
]

black_queen_pst = [
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-10, 5, 5, 5, 5, 5, 0, -5],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
]

black_king_mg_pst = [
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
]

black_king_eg_pst = [
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10, 0, 0, -10, -20, 30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -30, 0, 0, 0, 0, -30, -30],
    [-50, -40, -30, -20, -20, -30, -40, -50],
]

king_mg_pst = {
    chess.WHITE: [row[::-1] for row in black_king_mg_pst][::-1],
    chess.BLACK: black_king_mg_pst,
}  # for opening and middlegame

king_eg_pst = {
    chess.WHITE: [row[::-1] for row in black_king_eg_pst][::-1],
    chess.BLACK: black_king_eg_pst,
}  # for endgame

piece_square_tables = {
    chess.PAWN: {
        chess.WHITE: [row[::-1] for row in black_pawn_pst[::-1]],
        chess.BLACK: black_pawn_pst,
    },
    chess.KNIGHT: {
        chess.WHITE: [row[::-1] for row in black_knight_pst[::-1]],
        chess.BLACK: black_knight_pst,
    },
    chess.BISHOP: {
        chess.WHITE: [row[::-1] for row in black_bishop_pst[::-1]],
        chess.BLACK: black_bishop_pst,
    },
    chess.ROOK: {
        chess.WHITE: [row[::-1] for row in black_rook_pst[::-1]],
        chess.BLACK: black_rook_pst,
    },
    chess.QUEEN: {
        chess.WHITE: [row[::-1] for row in black_queen_pst[::-1]],
        chess.BLACK: black_queen_pst,
    },
    chess.KING: king_mg_pst,
}

piece_mobility_weights = {
    chess.QUEEN: 1,
    chess.ROOK: 2,
    chess.BISHOP: 4,
    chess.KNIGHT: 4,
    chess.PAWN: 0,
    chess.KING: -1,  # penalise king mobility in the middlegame (the king shouldn't be active in the middlegame)
}

king_attackers_values = {
    chess.QUEEN: 6,
    chess.ROOK: 4,
    chess.BISHOP: 3,
    chess.KNIGHT: 3,
    chess.PAWN: 1,
}

# fmt: off
attack_units_to_centipawns = [
      0,   0,   1,   2,   3,   5,   7,   9,  12,  15,
     18,  22,  26,  30,  35,  39,  44,  50,  56,  62,
     68,  75,  82,  85,  89,  97, 105, 113, 122, 131,
    140, 150, 169, 180, 191, 202, 213, 225, 237, 248,
    260, 272, 283, 295, 307, 319, 330, 342, 354, 366,
    377, 389, 401, 412, 424, 436, 448, 459, 471, 483,
    494, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500,
    500, 500, 500, 500, 500, 500, 500, 500, 500, 500
]
# fmt: on


class LRUTable:
    def __init__(self, max_size: int = 100000):
        self.table = OrderedDict()
        self.max_size = max_size

    def get(self, key):
        if key in self.table:
            self.table.move_to_end(key)
            return self.table[key]
        return None

    def store(self, key, value):
        if key in self.table:
            self.table.move_to_end(key)
        self.table[key] = value
        if len(self.table) > self.max_size:
            self.table.popitem(last=False)

    def reset(self):
        self.table = OrderedDict()

    def __contains__(self, key):
        return key in self.table


transposition_table = LRUTable(max_size=200000)

# Transposition table flags
EXACT_FLAG = "EXACT"
UPPERBOUND_FLAG = "UPPERBOUND"
LOWERBOUND_FLAG = "LOWERBOUND"


# Game variables
killer_moves = defaultdict(list)

history_table = [[0 for i in range(64)] for j in range(64)]  # initialise a 64x64 history table

is_in_endgame = False


# Pawn structure hashing initialisation

pawn_zobrist_table = [[random.getrandbits(64) for i in range(2)] for j in range(64)]

pawn_hash_table = LRUTable(max_size=100000)


def pawn_hash(pos: chess.Board) -> int:
    """Returns a Zobrist hash corresponding to the pawn structure in the position"""
    key = 0
    for square, piece in pos.piece_map().items():
        if piece.piece_type != chess.PAWN:
            continue

        color_index = 0 if piece.color == chess.WHITE else 1
        key ^= pawn_zobrist_table[square][color_index]

    return key


def in_endgame(pos: chess.Board) -> bool:
    """Evaluates if the position is in endgame or not (using a material threshold)"""
    return (
        sum(
            [
                piece_values[piece.piece_type]
                for piece in pos.piece_map().values()
                if piece.piece_type != chess.KING
            ]
        )
        < 2300
    )


def is_isolated_pawn(pos: chess.Board, pawn_sq: chess.Square, color: chess.Color) -> bool:
    """Checks if the pawn of the given color at the given square is isolated"""
    file = chess.square_file(pawn_sq)
    adj_files = [file - 1, file + 1]
    for adj_file in adj_files:
        if adj_file in range(8):  # valid file (exists in the board)
            for rank in range(8):
                square = chess.square(adj_file, rank)
                if pos.piece_at(square) == chess.Piece(chess.PAWN, color):  # adjacent friendly pawn
                    return False

    return True


def is_doubled_pawn(pos: chess.Board, pawn_sq: chess.Square, color: chess.Color) -> bool:
    """Checks if the pawn of the given color at the given square is doubled with one or several other pawns"""
    pawn_file = chess.square_file(pawn_sq)
    pawn_rank = chess.square_rank(pawn_sq)
    for rank in range(8):
        if rank != pawn_rank:
            square = chess.square(pawn_file, rank)
            if pos.piece_at(square) == chess.Piece(
                chess.PAWN, color
            ):  # another pawn in the same file
                return True

    return False


def is_passed_pawn(pos: chess.Board, pawn_sq: chess.Square, color: chess.Color) -> bool:
    pawn_file = chess.square_file(pawn_sq)
    pawn_rank = chess.square_rank(pawn_sq)
    ahead_ranks = range(pawn_rank + 1, 8) if color == chess.WHITE else range(pawn_rank, -1, -1)
    adj_files = [pawn_file - 1, pawn_file, pawn_file + 1]
    for rank in ahead_ranks:
        for file in adj_files:
            if file in range(8):
                square = chess.square(file, rank)
                if pos.piece_at(square) == chess.Piece(chess.PAWN, not color):  # ennemy pawn
                    return False

    return True


def calculate_pawn_structure(pos: chess.Board) -> int:
    score = 0
    for square, piece in pos.piece_map().items():
        if piece.piece_type != chess.PAWN:
            continue

        piece_color = piece.color
        if is_passed_pawn(pos, square, piece_color):
            advancement = (
                chess.square_rank(square)
                if piece_color == chess.WHITE
                else 7 - chess.square_rank(square)
            )
            if not piece_square_tables[chess.KING] == king_eg_pst:  # not in endgame
                score += player_coefs[piece_color] * advancement * 8
            else:  # endgame
                score += player_coefs[piece_color] * advancement * 15
        elif is_isolated_pawn(pos, square, piece_color):
            score -= player_coefs[piece_color] * 18
        if is_doubled_pawn(pos, square, piece_color):
            score -= player_coefs[piece_color] * 15

    return score


def is_open_file(pos: chess.Board, file: int) -> bool:
    """Returns True if the file is open in that position"""
    for rank in range(8):
        square = chess.square(file, rank)
        piece = pos.piece_at(square)
        if piece is not None and piece.piece_type == chess.PAWN:  # There is a pawn in that file
            return False
    return True


def is_semi_open_file(pos: chess.Board, file: int, color: chess.Color) -> bool:
    """Returns True if the file is semi-open in that position for the given color"""
    for rank in range(8):
        square = chess.square(file, rank)
        if pos.piece_at(square) == chess.Piece(
            chess.PAWN, color
        ):  # There is a friendly pawn in that file
            return False

    return True


def calculate_rook_activity(pos: chess.Board) -> int:
    """Returns a score corresponding to the rook activity in this position
    (gives bonuses for rooks in open/semi-open files)"""
    score = 0

    for square, piece in pos.piece_map().items():
        if piece.piece_type != chess.ROOK:
            continue

        piece_color = piece.color
        file = chess.square_file(square)
        if is_open_file(pos, file):
            score += player_coefs[piece_color] * 25

        elif is_semi_open_file(pos, file, piece_color):
            score += player_coefs[piece_color] * 15

    return score


def calculate_activity_score(pos: chess.Board) -> int:
    """Returns a piece activity / mobility score for the position"""
    score = 0
    legal_moves = list(pos.legal_moves)
    for move in legal_moves:
        piece_moved = pos.piece_at(move.from_square)
        score += player_coefs[pos.turn] * piece_mobility_weights[piece_moved.piece_type]
    pos.push(chess.Move.null())  # change the turn to evaluate for the other side
    opponent_legal_moves = list(pos.legal_moves)
    for move in opponent_legal_moves:
        piece_moved = pos.piece_at(move.from_square)
        score += player_coefs[pos.turn] * piece_mobility_weights[piece_moved.piece_type]
    pos.pop()  # switch back the turn
    return score


def calculate_king_safety(pos: chess.Board, color: chess.Color, king_pos: chess.Square) -> int:
    """Evaluates a king safety malus in the given position for the given color
    (See https://www.chessprogramming.org/King_Safety#Attack_Units)"""
    king_zone_squares = [
        king_pos + 1,
        king_pos - 1,
        king_pos + 8,
        king_pos - 8,
        king_pos + 7,
        king_pos - 7,
        king_pos + 9,
        king_pos - 9,
    ]
    if color == chess.WHITE:
        king_zone_squares.extend([king_pos + 16, king_pos + 24])
    else:
        king_zone_squares.extend([king_pos - 16, king_pos - 24])

    attack_units = 0
    for square in king_zone_squares:
        if square in chess.SQUARES:  # square exists
            attackers = pos.attackers(not color, square)
            for attacker_square in attackers:
                attacker = pos.piece_at(attacker_square)
                attack_units += king_attackers_values.get(attacker.piece_type, 0)

    return -attack_units_to_centipawns[attack_units] * player_coefs[color]


def calculate_center_control(pos: chess.Board) -> int:
    """Evaluates a center control score in the given chess position"""
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    extended_center_squares = [
        chess.C3,
        chess.C4,
        chess.C5,
        chess.C6,
        chess.D6,
        chess.E6,
        chess.F6,
        chess.F5,
        chess.F4,
        chess.F3,
        chess.E3,
        chess.D3,
    ]
    score = 0
    for square in center_squares:
        for color in [chess.WHITE, chess.BLACK]:
            attackers = pos.attackers(color, square)
            score += player_coefs[color] * len(attackers) * 6

    for square in extended_center_squares:
        for color in [chess.WHITE, chess.BLACK]:
            attackers = pos.attackers(color, square)
            score += player_coefs[color] * len(attackers) * 3

    return score


def calculate_piece_score(pos: chess.Board) -> int:
    """Returns a score corresponding to the values and positions of the pieces"""
    score = 0
    for square, piece in pos.piece_map().items():
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        piece_type = piece.piece_type
        piece_color = piece.color
        score += player_coefs[piece_color] * (
            piece_values.get(piece_type, 0)
            + piece_square_tables[piece_type][piece_color][rank][file]
        )

        if piece_type == chess.KING:
            if piece_color == chess.WHITE:
                white_king_pos = square
            else:
                black_king_pos = square

    return score, white_king_pos, black_king_pos


def evaluate_pos(pos: chess.Board) -> int:
    """The main position (board) evaluation function"""
    if not pos.is_game_over():
        piece_score, white_king_pos, black_king_pos = calculate_piece_score(pos)
        pos_pawn_hash = pawn_hash(pos)
        if pos_pawn_hash in pawn_hash_table:
            pawn_score = pawn_hash_table[pos_pawn_hash]
        else:
            pawn_score = calculate_pawn_structure(pos)
        score = 0
        score += piece_score
        score += calculate_king_safety(pos, chess.WHITE, white_king_pos)
        score += calculate_king_safety(pos, chess.BLACK, black_king_pos)
        if not is_in_endgame:  # still in middlegame
            # score += calculate_rook_activity(pos)  # TODO: reactivate (with more optimisation)
            score += calculate_activity_score(pos)
        score += calculate_center_control(pos)
        score += pawn_score
        return score
    elif pos.outcome().winner is None:  # draw
        return 0
    else:  # checkmate
        return -player_coefs[pos.turn] * (
            int(pos.is_checkmate()) * 20000 - pos.fullmove_number
        )  # prioritise quicker mates


def get_capture_score(pos: chess.Board, move: chess.Move) -> int:
    """Helper function used for sorting moves"""
    if not pos.is_capture(move):
        return 0
    elif pos.is_en_passant(move):
        return piece_values[chess.PAWN]
    else:
        return (
            piece_values[pos.piece_at(move.to_square).piece_type]
            - piece_values.get(pos.piece_at(move.from_square).piece_type, 200) // 10
        )  # MVV-LVA


def get_move_score(pos: chess.Board, move: chess.Move, ply: int) -> int:
    """Function for move ordering built on top of get_capture_score"""
    score = get_capture_score(pos, move)
    if pos.gives_check(move):
        score += 50
    if move in killer_moves[ply]:
        score += 1000
    score += (
        history_table[move.from_square][move.to_square] // 10
    )  # prioritise other moves (killer, captures, etc...)
    pos_hash = chess.polyglot.zobrist_hash(pos)
    if pos_hash in transposition_table:
        best_pos_move = transposition_table.get(pos_hash)[1]
        if move == best_pos_move:
            score += 2000  # TT moves first
    return score


def sorted_legal_moves(pos: chess.Board, ply: int) -> Generator[chess.Move, None, None]:
    """Gets the legal moves in a position, with ordering"""
    legal_moves = list(pos.legal_moves)
    return sorted(legal_moves, key=lambda move: get_move_score(pos, move, ply), reverse=True)


nodes_searched = 0  # node counter


def quiescence(
    pos: chess.Board, alpha: int, beta: int, color: int, depth: int = QUIESCENCE_DEPTH
) -> int:
    """Function for quiescence search, which helps avoiding the horizon effect"""
    global nodes_searched
    nodes_searched += 1

    stand_pat = color * evaluate_pos(pos)

    if depth == 0:
        return stand_pat

    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    for move in pos.legal_moves:
        if not (
            pos.is_capture(move) or move.promotion is not None or pos.gives_check(move)
        ):  # quiet move (not a capture, check or promotion)
            continue

        pos.push(move)
        score = -quiescence(pos, -beta, -alpha, -color, depth - 1)
        pos.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def nega_max(
    pos: chess.Board,
    depth: int = MAX_ENGINE_DEPTH,
    alpha: int = -inf,
    beta: int = inf,
    color: int = +1,
    time_stop: int = +inf,
    ply: int = 0,
) -> tuple[chess.Move, int]:
    """The main AI (NegaMax) algorithm with alpha-beta pruning"""
    global nodes_searched
    nodes_searched += 1

    if pos.is_game_over():
        return None, color * evaluate_pos(pos)
    if depth == 0:
        return None, quiescence(pos=pos, alpha=alpha, beta=beta, color=color)

    pos_hash = chess.polyglot.zobrist_hash(pos)
    if pos_hash in transposition_table:
        entry = transposition_table.get(pos_hash)
        if entry[0] >= depth:
            if entry[3] == EXACT_FLAG:
                return entry[1], entry[2]  # move, score
            elif entry[3] == LOWERBOUND_FLAG and entry[2] >= beta:
                return entry[1], entry[2]  # move, score
            elif entry[3] == UPPERBOUND_FLAG and entry[2] <= alpha:
                return entry[1], entry[2]  # move, score

    original_alpha = alpha
    max_val = -inf
    best_move = None
    pv_line = None

    for move in sorted_legal_moves(pos, ply):
        if time.time() >= time_stop:
            return None, None

        # Null-move pruning
        if depth >= 3 and not pos.is_check() and not is_in_endgame:
            pos.push(chess.Move.null())  # null-move
            _, score = nega_max(
                pos=pos,
                depth=depth - 1 - NULL_MOVE_REDUCTION,
                alpha=-beta,
                beta=-alpha,
                color=-color,
                time_stop=time_stop,
                ply=ply + 1,
            )
            if score is None:  # prevent error when timeout reached
                return None, None
            score = -score
            pos.pop()

            if score >= beta:
                return None, beta  # beta cutoff

        pos.push(move)
        _, score = nega_max(
            pos=pos,
            depth=depth - 1,
            alpha=-beta,
            beta=-alpha,
            color=-color,
            time_stop=time_stop,
            ply=ply + 1,
        )
        if score is None:  # prevent error when timeout reached
            return None, None
        score = -score

        pos.pop()
        if score > max_val:
            max_val = score
            best_move = move
        if score > alpha:
            alpha = score
        if alpha >= beta:
            history_table[move.from_square][move.to_square] += depth * depth
            if not pos.is_capture(move):
                if not move in killer_moves[ply]:
                    if len(killer_moves[ply]) < 2:
                        killer_moves[ply].append(move)
                    else:
                        killer_moves[ply][1] = killer_moves[ply][0]
                        killer_moves[ply][0] = move

            break  # cut-off

    if max_val <= original_alpha:
        flag = UPPERBOUND_FLAG
    elif max_val >= beta:
        flag = LOWERBOUND_FLAG
    else:
        flag = EXACT_FLAG

    if pos_hash not in transposition_table or (
        pos_hash in transposition_table and transposition_table.get(pos_hash)[0] <= depth
    ):  # only overwrite if deeper search
        transposition_table.store(pos_hash, (depth, best_move, max_val, flag))

    return best_move, max_val


def iterative_deepening(
    pos: chess.Board, max_time: float, max_depth: int = MAX_ENGINE_DEPTH
) -> chess.Move:
    """Applies iterative deepening to find the best move in a limited time"""
    global nodes_searched
    nodes_searched = 0

    t1 = time.time()
    time_stop = t1 + max_time
    for depth in range(1, max_depth + 1):
        if depth > 1:
            move, score = nega_max(pos, depth, color=player_coefs[pos.turn], time_stop=time_stop)
        else:  # NOTE: no timeout limit for depth 1, so best_move is always defined
            move, score = nega_max(pos, depth, color=player_coefs[pos.turn])
        if move is not None:  # no timeout during search
            best_move = move
            time_elapsed = time.time() - t1
            info_string = "info"
            info_string += f" depth {depth}"
            info_string += (
                f" score cp {player_coefs[pos.turn] * score}"  # evaluation must be absolute
            )
            info_string += f" time {int(time_elapsed)}"
            info_string += f" nodes {nodes_searched}"
            try:
                info_string += f" nps {int(nodes_searched / time_elapsed)}"
            except ZeroDivisionError:
                pass
            print(info_string)

        if time.time() >= time_stop:
            break

    return best_move


def main() -> None:
    """Main UCI interface"""
    global killer_moves, history_table, is_in_endgame
    board = chess.Board()
    while True:
        args = input().split()
        if args[0] == "uci":
            print("id name SomePythonBot")
            print("uciok")

        elif args[0] == "isready":
            print("readyok")

        elif args[0] == "ucinewgame":
            is_in_endgame = False
            piece_square_tables[chess.KING] = king_mg_pst
            transposition_table.reset()
            pawn_hash_table.reset()
            killer_moves = defaultdict(list)
            history_table = [
                [0 for i in range(64)] for j in range(64)
            ]  # reinitialise the 64x64 history table

        elif args[0] == "quit":
            break

        elif args[:2] == ["position", "startpos"]:
            if len(args) == 2:  # starting position
                board = chess.Board()
            elif args[1] == "fen":  # from FEN
                board = chess.Board(args[2])
            elif args[2] == "moves":  # from sequence of moves
                board = chess.Board()
                for move_str in args[3:]:
                    board.push_uci(move_str)

        elif args[0] == "go":
            if len(args) == 9:
                wtime, btime, winc, binc = [int(i) / 1000 for i in args[2::2]]
                if board.turn == chess.WHITE:
                    time_left = wtime
                    increment = winc
                else:
                    time_left = btime
                    increment = binc
                max_time = min(time_left / 40 + increment, time_left / 2 - 1)

            elif len(args) == 3 and args[1] == "movetime":
                max_time = int(args[2]) / 1000

            else:
                raise ValueError(
                    "unsupported arguments for UCI command 'go'"
                )  # shouldn't be raised

            best_move = None

            if PATH_TO_OPENING_BOOK:
                with chess.polyglot.open_reader(PATH_TO_OPENING_BOOK) as reader:
                    entries = {}
                    for entry in reader.find_all(board):
                        entries[entry.move] = entry.weight

                if entries:
                    max_weight = max(entries.values())
                    best_entries = [move for move in entries.keys() if entries[move] == max_weight]
                    best_move = random.choice(best_entries)
                    time.sleep(1)  # simulate thinking time

            if best_move is None:  # no opening book move, so perform normal search
                best_move = iterative_deepening(board, max_time=max_time)

            print(f"bestmove {best_move}")

            if not is_in_endgame:
                if in_endgame(board):
                    is_in_endgame = True
                    piece_square_tables[chess.KING] = king_eg_pst  # switch to endgame king table


if __name__ == "__main__":
    main()
