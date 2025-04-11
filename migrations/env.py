import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# acesta este obiectul Alembic Config, care oferă
# acces la valorile din fișierul .ini utilizat.
config = context.config

# Interpretează fișierul de configurare pentru logarea în Python.
# Aceasta configurează loggerele, în esență.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')


def get_engine():
    try:
        #funcționează cu Flask-SQLAlchemy și Alchemical
        return current_app.extensions['migrate'].db.get_engine()
    except TypeError:
        #funcționează cu Flask-SQLAlchemy
        return current_app.extensions['migrate'].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')


# adăugați obiectul MetaData al modelului aici
# pentru suportul 'autogenerate'
# de exemplu: from myapp import mymodel
# target_metadata = mymodel.Base.metadata
config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

# alte valori din configurație, definite de necesitățile env.py,
# pot fi obținute:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    """Rulează migrațiile în modul 'offline'.

    Aceasta configurează contextul doar cu un URL
    și nu cu un Engine, deși un Engine este acceptabil
    și aici.  Prin sărirea creării Engine-ului
    nici nu avem nevoie de un DBAPI disponibil.

    Apelurile către context.execute() aici emit șirul dat în
    ieșirea scriptului.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=get_metadata(), literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Rulează migrațiile în modul 'online'.

    În acest scenariu trebuie să creăm un Engine
    și să asociem o conexiune cu contextul.

    """

    # acest callback este folosit pentru a preveni generarea unei auto-migrații
    # atunci când nu există modificări în schemă
    # referință: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('Nu au fost detectate modificări în schemă.')

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            process_revision_directives=process_revision_directives,
            **current_app.extensions['migrate'].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
