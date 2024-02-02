import os
from dotenv import load_dotenv
from ast import literal_eval

load_dotenv()

BROKER_URL = os.getenv('BROKER_URL')
BROKER_PORT = int(os.getenv('BROKER_PORT'))
BROKER_CA_CERT = os.getenv('BROKER_CA_CERT')
BROKER_KEY = os.getenv('BROKER_KEY')
BROKER_CERT = os.getenv('BROKER_CERT')
TOPIC_CAMERA = literal_eval(os.getenv('BROKER_TOPICS'))