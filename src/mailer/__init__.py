"""
AllergyNewsLetter 메일러 모듈
"""

from .gmail_sender import GmailSender, SendResult, get_sender

__all__ = [
    "GmailSender",
    "SendResult",
    "get_sender",
]
