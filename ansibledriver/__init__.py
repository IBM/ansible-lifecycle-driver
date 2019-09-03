from ansibledriver.app import create_app

def create_wsgi_app():
    ignition_app = create_app()
    # For wsgi deployments
    return ignition_app.connexion_app
