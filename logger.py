import logging
import logging.handlers
import os
import config

if not os.path.exists(config.LOG_DIR):
    os.makedirs(config.LOG_DIR)

logger = logging.getLogger(config.NAME)
logger.setLevel(logging.DEBUG)

#set log file
fileFomatter = logging.Formatter('[%(levelname)s][%(filename)s:%(lineno)s][%(asctime)s] %(message)s')
fileHandler = logging.handlers.TimedRotatingFileHandler(config.LOG_PATH, when='midnight', interval=1, encoding='utf-8', backupCount=config.DF_BACKUP_CNT)
fileHandler.setFormatter(fileFomatter)
fileHandler.setLevel(logging.DEBUG)
logger.addHandler(fileHandler)

#set log stream
streamFomatter = logging.Formatter('[%(levelname)s] %(message)s')
streamHandler = logging.StreamHandler()
streamHandler.setFormatter(streamFomatter)
streamHandler.setLevel(logging.INFO)
logger.addHandler(streamHandler)

def info(msg) :  
    logger.info(msg)

def debug(msg) :  
    logger.debug(msg)

def warning(msg) :  
    logger.warning(msg)

def error(msg) :  
    logger.error(msg)

def critical(msg) :  
    logger.critical(msg)
