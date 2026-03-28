from socket import create_connection

from utils import log, send_notification
from config import PROTOCOL, CANCEL_FILE


def has_internet_connection():
    """تحقق مما إذا كان هناك اتصال بالإنترنت"""
    for target in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
        for attempt in range(2):            
            try:
                with create_connection(target, timeout=5):
                    return True
            except (OSError, TimeoutError, ConnectionRefusedError):
                continue
    log("INFO", "No internet connection detected.", console=False)
    return False


def wait_for_internet():
    from time import sleep
    for i in range(300): # 10 minutes max wait
        if CANCEL_FILE.exists():
            CANCEL_FILE.unlink(missing_ok=True)
            send_notification(
                "Time Sync Cancelled",
                "❌ Sync process cancelled.",
                tag="sync-cancelled",
                group="sync-cancelled"
            )
            log("INFO", "Time sync cancelled by user.", console=False)
            return False

        if has_internet_connection():
            return True

        if i == 5:
            send_notification(
                "No Internet Connection",
                "⏳ Waiting for internet connection...",
                actions=[
                    ("Cancel", f"{PROTOCOL}://cancel")
                ],
                tag="sync-status",
                group="sync-status"
            )

        sleep(2) # Wait before retrying
    
    return False


def is_internet_available(auto_sync=True):
    """
    التحقق من الإنترنت:
    - يعود بـ True فوراً إذا وجد اتصال.
    - في الوضع التلقائي (auto): ينتظر الاتصال ويعود بالنتيجة.
    - في الوضع اليدوي: يعود بـ False فوراً مع تسجيل Log.
    """
    # 1. تحقق سريع: إذا كان الإنترنت متاحاً الآن، اخرج بـ True
    if has_internet_connection():
        return True

    # 2. إذا لم يتوفر إنترنت، نحدد التصرف بناءً على نوع التشغيل
    if auto_sync:
        # وضع التلقائي: ننتظر (دالة wait_for_internet هي التي تقرر النجاح أو الفشل بعد مهلة)
        log("INFO", "No internet. Waiting for connection (Auto-sync mode)...", console=False)
        result = wait_for_internet()
    else:
        # وضع اليدوي: فشل فوري
        result = False

    # 3. إعادة النتيجة النهائية (True أو False)
    return result
