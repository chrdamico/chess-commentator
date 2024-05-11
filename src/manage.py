import threading

import click

from conf.settings import settings
from services.socket_connection import SocketConnector
from utils.logger import init_logger


@click.group()
def cli():
    pass


def setup():
    init_logger(settings.LOG_LEVEL)


@click.command(name="connect-socket")
def run():
    setup()
    socket_connection = SocketConnector()

    try:
        socket_connection.connect()
        # Check to keep the connection alive running on a separate thread
        keep_alive_thread = threading.Thread(target=socket_connection.keep_alive)
        keep_alive_thread.start()
    except KeyboardInterrupt:
        socket_connection.stop_thread_event.set()
        keep_alive_thread.join()
        socket_connection.disconnect()


@click.command(name="run-from-local-dump")
def run_from_local_dump():
    setup()
    socket_connection = SocketConnector()
    socket_connection.run_from_local_dump(dump_data_filepath=settings.LOCAL_SOURCE_FILE_PATH)


cli.add_command(run)
cli.add_command(run_from_local_dump)

if __name__ == "__main__":
    cli()
