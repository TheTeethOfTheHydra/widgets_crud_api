import tornado
import logging
import peewee
from server_config import *
from apscheduler.schedulers.tornado import TornadoScheduler
from playhouse._sqlite_ext import backup_to_file
from datetime import datetime
from tornado.options import define, options
from api import WidgetHandler, WidgetListHandler

define('address', default=SERVER_HOSTNAME_OR_IP, help='address to listen on')
define('port', default=SERVER_PORT, help='port to listen on')

logging.basicConfig(level=logging.INFO, filename=LOG_FILEPATH, filemode='a',
                    format='%(asctime)s - %(name)s - \
                    %(levelname)s - %(message)s')
logger = logging.getLogger('my_logger')


def make_app():
    return tornado.web.Application([
        (r"/widget/(\d+)", WidgetHandler),
        (r"/widget", WidgetListHandler),
    ])

# method to backup the Sqlite database file


def backup_database():
    db = peewee.SqliteDatabase(DATABASE_FILEPATH)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_file = DATABASE_BACKUPS_FILEPATH + f'widgets.{timestamp}.db'
    backup_to_file(db.connection(), backup_file)
    logger.info("Database backup completed.")


if __name__ == "__main__":
    logger.info("Starting Widgets CRUD REST API...")
    app = make_app()
    # configure tornado with or without ssl/tls securty
    if ENABLE_TLS:
        app.listen(options.port, address=options.address, ssl_options={
                   "certfile": TLS_CERTFILE, "keyfile": TLS_KEYFILE})
    else:
        app.listen(options.port, address=options.address)

    logger.info(
        f"Tornado web server running on {options.address}:{options.port}...")

    try:
        # schedule a periodic backup process for the sqlite database
        scheduler = TornadoScheduler()
        scheduler.add_job(backup_database, 'interval',
                          seconds=DATABASE_BACKUP_PERIOD_SECONDS)
        scheduler.start()
        tornado.ioloop.IOLoop.current().start()
    except KeyboardInterrupt:
        tornado.ioloop.IOLoop.current().stop()
        # make a final backup of the sqlite database as part of
        # tornado shutdown
        backup_database()
        logger.info("Tornado server stopped.")
