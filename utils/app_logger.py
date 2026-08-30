import logging
from logging.handlers import RotatingFileHandler
from config import LOG_FILE, APP_NAME

# initialize logger
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(module)s] - %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

if not any(isinstance(handler, RotatingFileHandler) for handler in logger.handlers):
    # file handler with rotation (logs will rotate when they reach 20KB, keeping 1 backup)
    # you can modify maxBytes based on what equals about 100 lines (e.g., 10 to 20 KB)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=20000, backupCount=1, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
    # file handler for console output (prints to screen)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.WARNING) # prints warnings and errors automatically
    logger.addHandler(console_handler)

def log(level, message, console=False):
    """
    دالة وسيطة لتتوافق مع كودك القديم، لكنها تستخدم المكتبة المحترفة في الخلفية
    """
    # إذا طلب المستخدم كونسول إجباري لرسالة عادية
    if console:
        print(f"{level}: {message}\nFor more details, check: {LOG_FILE}")
        
    level_upper = level.upper()
    if level_upper == "INFO":
        logger.info(message, stacklevel=2)
    elif level_upper == "WARNING":
        logger.warning(message, stacklevel=2)
    elif level_upper == "ERROR":
        logger.error(message, stacklevel=2)
    else:
        logger.debug(message, stacklevel=2)
