import json
import threading
import time
from pathlib import Path

import websocket
from websocket import WebSocket

from conf.settings import settings
from entities.entities import MessageTypeEnum
from services.chess_commentator import ChessCommentator
from utils.logger import global_logger


class SocketConnector:
    TCEC_SOCKET_URL = "wss://tcec-chess.com/socket.io/?EIO=3&transport=websocket"
    KEEP_ALIVE_SLEEP_TIME_SECONDS = 1
    PING_INTERVAL_SECONDS = 5
    PING_TIMEOUT_SECONDS = 10

    MESSAGE_TYPE_MAX_LENGTH = 3
    DUMP_FILEPATH = Path(__file__).parent.parent / "dump.txt"

    RUN_FROM_LOCAL_TIME_INTERVAL_SECONDS = 1

    def __init__(self):
        self.socket = websocket.WebSocketApp(
            self.TCEC_SOCKET_URL,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self.stop_thread_event = threading.Event()
        self.handlers_by_message_type = {MessageTypeEnum.ChessInformationMessageType: self._chess_information_handler}

        self.chess_commentator = ChessCommentator()

    def connect(self) -> None:
        """
        Connects to the websocket
        """
        global_logger.info("Starting socket connection")
        self.socket.run_forever(ping_interval=self.PING_TIMEOUT_SECONDS, ping_timeout=self.PING_INTERVAL_SECONDS)

    def run_from_local_dump(self, dump_data_filepath: Path) -> None:
        """
        Fakes running the websocket by getting data from a local dump file. Useful during development
        """
        global_logger.info("Starting to run from local dump")
        with open(dump_data_filepath, "r") as file:
            input_messages = file.readlines()

        for input_message in input_messages:
            self._handle_message(input_message)
            time.sleep(self.RUN_FROM_LOCAL_TIME_INTERVAL_SECONDS)

    def disconnect(self) -> None:
        """
        Disconnect from the websocket
        """
        global_logger.info("Stopping socket connection")
        self.socket.close()

    def keep_alive(self) -> None:
        """
        Monitors the WebSocket connection and attempts to reconnect if it has been closed.
        This runs in a separate thread to continuously check connection status.
        """
        while not self.stop_thread_event.is_set():
            if not self.socket.sock or not self.socket.sock.connected:
                global_logger.warning("Connection lost, attempting to reconnect...")
                self.reconnect()
            time.sleep(self.KEEP_ALIVE_SLEEP_TIME_SECONDS)

    def reconnect(self) -> None:
        """
        Safely attempts to reconnect the WebSocket.
        """
        self.disconnect()  # Ensure the connection is cleanly closed before reconnecting
        self.connect()

    def _on_open(self, _websocket: WebSocket) -> None:
        """
        Called on opening of WebSocket connection
        :param _websocket: websocket of the connection being opened
        """
        global_logger.info("WebSocket connection opened.")

        def run():
            while not self.stop_thread_event.is_set():
                # Perform tasks, such as sending a periodic message
                time.sleep(self.KEEP_ALIVE_SLEEP_TIME_SECONDS)

        thread = threading.Thread(target=run)
        thread.start()

    def _on_message(self, _websocket: WebSocket, message: str) -> None:
        """
        Called on receiving messages from the WebSocket
        :param _websocket: websocket that messages are received from
        :param message: Content of th emessage
        """
        global_logger.info("Message received")
        if settings.DUMP_RAW_MESSAGES:
            self._dump_message(message=message)

        self._handle_message(message=message)

    @classmethod
    def _dump_message(cls, message: str) -> None:
        """
        Dump received messages to a local text file.
        :param message: Message to append to current file
        """
        Path(settings.DATA_DUMP_FILE_PATH.parent).mkdir(parents=True, exist_ok=True)
        with open(settings.DATA_DUMP_FILE_PATH, "a") as file:
            file.write(message)
            file.write("\n")

    def _handle_message(self, message: str) -> None:
        """
        Handles received messages
        :param message: received message
        """
        message_type = self._get_message_type(message)
        handler = self.handlers_by_message_type.get(message_type)
        if handler:
            handler(message)
        else:
            global_logger.warning(f"No handler available for message_type: {message_type}")

    @classmethod
    def _get_message_type(cls, message: str) -> MessageTypeEnum:
        """
        Gets the message type from a received message
        :param message: Received message
        :return: message type of the received message (if unknown, returns MessageTypeEnum.UnknownMessageType
        """
        message_type = (
            message[: message.find("[")]
            if "[" in message and message.find("[") < cls.MESSAGE_TYPE_MAX_LENGTH
            else message[0]
        )
        try:
            return MessageTypeEnum(message_type)
        except ValueError:
            global_logger.warning(f"Unknown message type: {message_type}")
            return MessageTypeEnum.UnknownMessageType

    def _chess_information_handler(self, message: str) -> None:
        """
        Handles messages that contain chess information
        :param message: received message
        """
        payload = json.loads(message[2:])
        if payload[0] == "pgn":  # contains the game data
            self._handle_game_data(game_data=payload[1])
        if payload[0] == "liveeval":  # contains evaluation of commentating engines
            self._handle_live_eval_data(live_eval_data=payload[1])

    def _handle_game_data(self, game_data: json) -> None:
        """
        Extract relevant information from the game data and passes it to chess_commentator
        :param game_data: json containing game data
        """
        white_name = game_data["Headers"]["White"]
        black_name = game_data["Headers"]["Black"]

        last_move_data = game_data["Moves"][0]
        last_move = last_move_data["m"]
        current_fen = last_move_data["fen"]

        self.chess_commentator.process_position_data(
            fen_position=current_fen, last_move=last_move, white_name=white_name, black_name=black_name
        )

    def _handle_live_eval_data(self, live_eval_data: json) -> None:
        """
        Extract relevant information from live evaluation data and passes it to chess_commentator
        :param live_eval_data: json containing live evaluation data
        """
        engine_name = live_eval_data["engine"]
        position_evaluation = live_eval_data["eval"]
        best_line = live_eval_data["pv"]

        self.chess_commentator.process_position_evaluation_data(
            engine_name=engine_name, position_evaluation=position_evaluation, best_line=best_line
        )

    @staticmethod
    def _on_error(_websocket: WebSocket, error: str) -> None:
        """
        Called on any error of the websocket. Just logs the error
        :param _websocket: Currently active websocket
        :param error: String with error message
        """
        global_logger.error("Error: ", error)

    @staticmethod
    def _on_close(_websocket: WebSocket, close_status_code: str, close_msg: str) -> None:
        """
        Called on close of the websocket. Just logs that closing happened, status code and reason for closing
        :param _websocket: websocket that was closed
        :param close_status_code: received status message on close
        :param close_msg: Received message on close
        """
        # Log info on closing
        global_logger.info("Socket was closed")
        global_logger.info(f"close status code: {close_status_code}")
        global_logger.info(f"close msg: {close_msg}")
