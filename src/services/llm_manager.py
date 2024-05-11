from langchain.memory import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, MessagesPlaceholder

from langchain_openai import ChatOpenAI

from conf.settings import settings
from entities.types import FenPosition


class LLMManager:
    BASE_PROMPT = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are commentating a chess game"
                "You will receive information from the user about the state of board, new moves, engine evaluation "
                "and the identify of the players. Make your best to comment the game giving insightful commentary in "
                "a way that is casual. When the provided evaluation changes by a lot, point it out and emphasize how "
                "one of the players has made a mistake. Do not make up name of the players, stick with names that you "
                "are specifically told. You will slowly get told more information. Keep messages short, do not invent"
                "continuation of the game. Always trust what the user says it will give you correct information about"
                "the game. Good commentary should comment on the last move made and say what it is achieving. Reference"
                "the evaluation of the engines (if available) when commenting.",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    STARTUP_PROMPT = PromptTemplate.from_template(
        "We are now starting the commentary for the first time. Current game is between {white_name} (with the "
        "white pieces) and {black_name} with the black pieces. The current position is {fen_position}. Just commentate"
        "on the position. Do not make up moves. Repeat the name of the players",
        input_types={"last_move": str, "fen_position": FenPosition, "black_name": str, "white_name": str},
    )

    NEW_GAME_PROMPT = PromptTemplate.from_template(
        "Another move has been made. Last move is {last_move}. Current board position is {fen_position}",
        input_types={
            "last_move": str,
            "fen_position": FenPosition,
        },
    )

    COMMENTATING_PROMPT = PromptTemplate.from_template(
        "The previous game is over and a new one is starting. "
        "Current game is between {white_name} (with the white pieces) and {black_name} with the black pieces. "
        "The current position is {fen_position}",
        input_types={
            "black_name": str,
            "white_name": str,
            "fen_position": FenPosition,
        },
    )

    EVALUATION_UPDATE_PROMPT = PromptTemplate.from_template(
        "This is the opinion of a chess engine on the current position. "
        "The evaluating engine is {engine_name}. "
        "They believe that the current position evaluation is {position_evaluation}. "
        "They believe that the best line is {best_line}",
        input_types={
            "engine_name": str,
            "position_evaluation": str,
            "best_line": str,
        },
    )

    MODEL_TEMPERATURE = 0

    def __init__(self):
        self.chat_history = ChatMessageHistory()

        self.chain = self.BASE_PROMPT | ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY, model="gpt-4-turbo", temperature=self.MODEL_TEMPERATURE
        )

    def generate_startup_commentating_message(
        self, fen_position: str, last_move: str, black_name: str, white_name: str
    ) -> str:
        self.chat_history.add_user_message(
            self.STARTUP_PROMPT.format(
                last_move=last_move, fen_position=fen_position, black_name=black_name, white_name=white_name
            )
        )
        response = self.chain.invoke(input={"messages": self.chat_history.messages})
        return response.content

    def generate_commentating_message(self, fen_position: FenPosition, last_move: str) -> str:
        self.chat_history.add_user_message(
            self.COMMENTATING_PROMPT.format(last_move=last_move, fen_position=fen_position)
        )
        response = self.chain.invoke(input={"messages": self.chat_history.messages})
        return response.content

    def generate_new_game_commentating_message(
        self, fen_position: FenPosition, black_name: str, white_name: str
    ) -> str:
        self.chat_history.add_user_message(
            self.NEW_GAME_PROMPT.format(black_name=black_name, white_name=white_name, fen_position=fen_position)
        )
        response = self.chain.invoke(input={"messages": self.chat_history.messages})
        return response.content

    def generate_eval_commentating_message(self, engine_name: str, position_evaluation: str, best_line: str) -> str:
        self.chat_history.add_user_message(
            self.EVALUATION_UPDATE_PROMPT.format(
                engine_name=engine_name, position_evaluation=position_evaluation, best_line=best_line
            )
        )
        response = self.chain.invoke(input={"messages": self.chat_history.messages})
        return response.content
