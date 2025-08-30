import logging
import colorlog

log_handler = colorlog.StreamHandler()
log_handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(asctime)s.%(msecs)03d %(log_color)s%(levelname)-5s%(reset)s %(yellow)s%(name)-10s%(reset)s %(cyan)s%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)


def logger(name):
    logger = colorlog.getLogger(name)
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
