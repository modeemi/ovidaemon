from twisted.internet import reactor, protocol
from twisted.protocols import basic, ident
#from twisted.application import service, internet
import re
import random

def generate_random_token():
    return ''.join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for i in range(100))

class Kerberos(basic.LineReceiver):
    """Modeemin ovenaukaisuvilpe"""

    def __init__(self,
                 is_allowed_host,
                 is_allowed_user,
                 allow_access):
        self._is_allowed_host = is_allowed_host
        self._is_allowed_user = is_allowed_user
        self._allow_access = allow_access

    def _ident_connected(self, ident_client):
        print "Ident connected: %s" % (ident_client)
        port_on_server = self.transport.getHost().port
        if self._is_allowed_host(self.transport.getPeer()):
            port_on_client = self.transport.getPeer().port
            # KLUDGE. WTH? port_on_server is not the port we're actually listening at? hardcoded for now.
            ident_client.lookup(port_on_client, 420) \
                        .addCallback(self._ident_received) \
                        .addErrback(self._ident_failed)
        else:
            self._ident_failed(self, None)

    # ident_client may be None
    def _ident_failed(self, ident_client):
        if self.transport:
            if not self._allowed:
                if self.transport.connected:
                    self.deny_access()
                self.transport.loseConnection()

    def tokenPassed(self):
        print "Token passed"

    def _ident_succeeded(self):
        self._allowed = True
        self.sendLine(self.expect_token)
        print "allowing access, sent token"

    def _ident_received(self, (type, info)):
        (system_type, user_info) = re.split(":", info)
        print "ident info received %s" % (info)
        self._user_info = user_info
        allow = self._is_allowed_user(system_type, user_info)
        if allow:
            self._ident_succeeded()
        else:
            self._ident_failed(None)

    def connectionMade(self):
        print "Connected %s %s" % (self, self.transport)
        self.expect_token = generate_random_token()
        self.factory.clients.append(self)
        self._allowed = False
        self._user_info = None
        ident_factory.connectTCP(self.transport.getPeer().host, 113) \
            .addCallback(self._ident_connected) \
            .addErrback(self._ident_failed)

    def connectionLost(self, reason):
        print "Disconnected"
        self.factory.clients.remove(self)

    def deny_access(self):
        print "no access for %s" % (self._user_info)
        self.sendLine("Kerberos bites off your head.")
        self.transport.loseConnection()

    def lineReceived(self, data):
        print "hello data %s" % (data)
        if data == self.expect_token:
            self.sendLine("You shall live another day.")
            self.transport.loseConnection()
            self._allow_access(self._user_info)
        else:
            self.deny_access()

ident_factory = protocol.ClientCreator(reactor, ident.IdentClient)

def make_server_factory(is_allowed_host, is_allowed_user, allow_access):
    kerberos_factory = protocol.ServerFactory()
    kerberos_factory.protocol = lambda: Kerberos(is_allowed_host,
                                                 is_allowed_user,
                                                 allow_access)
    kerberos_factory.clients = []

    return kerberos_factory

def main():
    allowed_hosts = ["127.0.0.1", 
                     "130.230.72.140", # coffee
                     "130.230.72.137", # battery
                     "130.230.72.137"] # cherry

    allowed_users = ["root", "flux"]

    def is_allowed_host(peer):
        return allowed_hosts.count(peer.host) > 0

    def is_allowed_user(system_type, user_info):
        print "system_type=%s, user_info=%s" % (system_type, user_info)
        return system_type == "UNIX" and allowed_users.count(user_info) > 0

    def allow_access(user_info):
        print "Access granted to %s" % user_info

    factory = make_server_factory(is_allowed_host, is_allowed_user, allow_access)

    reactor.listenTCP(8000, factory)
    reactor.run()
    
if __name__ == "__main__":
    main()
