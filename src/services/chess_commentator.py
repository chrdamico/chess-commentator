import datetime

import chess
import numpy as np
import sounddevice
from piper import PiperVoice

from conf.settings import settings
from entities.types import FenPosition
from services.llm_manager import LLMManager
from utils.logger import global_logger


class ChessCommentator:
    COMMENTARY_VOICE = PiperVoice.load(settings.VOICE_MODEL_FILE_LOCATION)
    EVALUATION_COMMENTARY_COOLDOWN_MINUTES = 10

    def __init__(self):
        self.current_position = None
        self.llm_manager = LLMManager()
        self.time_last_spoken_eval = datetime.datetime.min

        self.startup_has_happened = False

    def process_position_data(
        self, fen_position: FenPosition, last_move: str, black_name: str, white_name: str
    ) -> None:
        """
        Handles main logic on commentating on received main data.
        :param fen_position: Received position of the board
        :param last_move: Last move of the board
        :param black_name: Name of the player with the black pieces
        :param white_name: Name of the player with the white pieces
        """
        received_board_position = chess.Board(fen=fen_position)

        if not self.current_position:
            self._commentate_startup(
                fen_position=fen_position, last_move=last_move, black_name=black_name, white_name=white_name
            )
            self.startup_has_happened = True
            return

        if self.current_position == received_board_position:
            return

        san_received_move = self.current_position.parse_san(last_move)
        if san_received_move not in self.current_position.legal_moves:
            self._commentate_new_game(fen_position=fen_position, black_name=black_name, white_name=white_name)
        else:
            self._commentate(fen_position=fen_position, last_move=last_move)

        self.current_position = received_board_position

    def process_position_evaluation_data(self, engine_name: str, position_evaluation: str, best_line: str) -> None:
        """
        Handles logic of commentating on new received position evaluation. Since evaluation data comes very often, it
        will only be vocalized after a timeout
        :param engine_name: Name of the engine that provides the evaluation
        :param position_evaluation: Evaluation of the position
        :param best_line: Best line proposed by the evaluating engine
        """
        if self.startup_has_happened and datetime.datetime.now() - self.time_last_spoken_eval > datetime.timedelta(
            minutes=self.EVALUATION_COMMENTARY_COOLDOWN_MINUTES
        ):
            self._commentate_eval_data(
                engine_name=engine_name, position_evaluation=position_evaluation, best_line=best_line
            )
            self.time_last_spoken_eval = datetime.datetime.now()

    def _commentate_startup(self, fen_position: str, last_move: str, black_name: str, white_name: str) -> None:
        """
        Gets commentary message at startup and vocalizes it
        """
        message = self.llm_manager.generate_startup_commentating_message(
            fen_position=fen_position, last_move=last_move, black_name=black_name, white_name=white_name
        )
        self._vocalize_commentary(message=message)

    def _commentate_new_game(self, fen_position: FenPosition, black_name: str, white_name: str) -> None:
        """
        Gets commentary message when a new game starts and vocalizes it
        """
        message = self.llm_manager.generate_new_game_commentating_message(
            fen_position=fen_position, black_name=black_name, white_name=white_name
        )
        self._vocalize_commentary(message=message)

    def _commentate(self, fen_position: FenPosition, last_move: str) -> None:
        """
        Gets commentary message on a new move and vocalizes it
        """
        message = self.llm_manager.generate_commentating_message(fen_position=fen_position, last_move=last_move)
        self._vocalize_commentary(message=message)

    def _commentate_eval_data(self, engine_name: str, position_evaluation: str, best_line: str) -> None:
        """
        Gets commentary message on new eval data and vocalizes it.
        """
        message = self.llm_manager.generate_eval_commentating_message(
            engine_name=engine_name, position_evaluation=position_evaluation, best_line=best_line
        )
        self._vocalize_commentary(message=message)

    @classmethod
    def _vocalize_commentary(cls, message: str) -> None:
        """
        Takes the commentary and speaks it out loud. If environment is set to SILENT_MODE, just logs the commentary
        instead
        :param message: Received commentary message
        """
        if not settings.SILENT_MODE:
            stream = sounddevice.OutputStream(
                samplerate=cls.COMMENTARY_VOICE.config.sample_rate, channels=1, dtype="int16"
            )
            stream.start()

            for audio_bytes in cls.COMMENTARY_VOICE.synthesize_stream_raw(message):
                int_data = np.frombuffer(audio_bytes, dtype=np.int16)
                stream.write(int_data)

            stream.stop()
            stream.close()
        else:
            global_logger.info(message)
