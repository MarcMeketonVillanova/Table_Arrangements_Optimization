import logging

def configure_logging(output_dir: str) -> None:

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # create file handler which logs even debug messages
    fh = logging.FileHandler(output_dir, mode='w')
    fh.setLevel(logging.INFO)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    # create formatter and add it to the handlers
    fh_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', "%Y-%m-%d %H:%M:%S")
    ch_formatter = logging.Formatter('%(levelname)s: %(message)s')
    fh.setFormatter(fh_formatter)
    ch.setFormatter(ch_formatter)
    # add the handlers to the logger
    root_logger.addHandler(fh)
    root_logger.addHandler(ch)
    return
