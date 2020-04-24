
from eapi.sessions import session
import eapi

eapi.sessions.SSL_WARNINGS = False

def test_session_new(target):

    session.new(target, auth=("ops", "ops"))


def test_session_ssl(target, certificate):
    session.new(target, cert=certificate, verify=False)
    session.send(target, ["show users"])
