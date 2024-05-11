from enum import StrEnum


class MessageTypeEnum(StrEnum):
    ChessInformationMessageType = "42"
    UnknownMessageType = "unknown"
    FirstPingMessageType = "0"
    EmptyPostPingMessageType = "4"
