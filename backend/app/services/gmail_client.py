from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from ..config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def build_service(account) -> any:
    """
    account: SQLAlchemy modeli (access_token, refresh_token va h.k. bor)
    """
    creds = Credentials(
        token=account.access_token,
        refresh_token=account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )
    # cache_discovery=False — docker ichida discovery cache muammolarini chetlash
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_unread(service, max_results=25):
    """
    INBOX dagi o‘qilmagan xabarlar ro‘yxati.
    """
    res = (
        service.users()
        .messages()
        .list(userId="me", q="label:INBOX is:unread", maxResults=max_results)
        .execute()
    )
    return res.get("messages", [])


def get_message(service, msg_id):
    """
    To‘liq xabarni (headers + body) olib keladi.
    """
    return (
        service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    )


def modify_labels(service, msg_id, remove_unread=True):
    """
    Label'larni o‘zgartirish (o‘qilgan deb belgilash uchun UNREAD ni olib tashlaymiz).
    """
    body = {}
    if remove_unread:
        body["removeLabelIds"] = ["UNREAD"]
    return (
        service.users().messages().modify(userId="me", id=msg_id, body=body).execute()
    )


def send_reply(service, thread_id: str, raw_message_b64: str):
    """
    Base64-urlsafe kodlangan xatni shu thread ichida jo‘natadi.
    """
    return (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw_message_b64, "threadId": thread_id})
        .execute()
    )
