import logging
from ansibledriver.app import create_app

def create_wsgi_app():
    ignition_app = create_app()

    logging.getLogger("connexion").setLevel("INFO")
    logging.getLogger("ignition.service.management").setLevel("INFO")

    # For wsgi deployments
    return ignition_app.connexion_app
