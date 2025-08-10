import logging
import colorlog

handler = colorlog.StreamHandler()
handler.setFormatter(
    colorlog.ColoredFormatter(
        "%(asctime)s.%(msecs)03d %(log_color)s%(levelname)-5s%(reset)s %(yellow)s%(name)-10s%(reset)s %(cyan)s%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)


def logger(name):
    logger = colorlog.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
