from twisted.internet import reactor, protocol
from twisted.protocols import basic, ident
#from twisted.application import service, internet
import re

class Kerberos(basic.LineReceiver):
    """Modeemin ovenaukaisuvilpe"""

    def __init__(self,
                 is_allowed_user,
                 is_allowed_host):
        self._is_allowed_host = is_allowed_host
        self._is_allowed_user = is_allowed_user

    def _ident_connected(self, ident_client):
        print "Ident connected: %s" % (ident_client)
        port_on_server = ident_client.transport.getHost().port
        if self._is_allowed_host(ident_client.transport.getPeer()):
            port_on_client = ident_client.transport.getPeer().port
            ident_client.lookup(port_on_server, port_on_client) \
                        .addCallback(self._ident_received) \
                        .addErrback(self._ident_failed)
        else:
            self._ident_failed(self, None)

    # ident_client may be None
    def _ident_failed(self, ident_client):
        if self.transport:
            if self.transport.connected:
                self.transport.write("No.\n")
            self.transport.loseConnection()
        print "disallow access"

    def _ident_succeeded(self):
        self.transport.write("Yes!\n")
        self.transport.loseConnection()
        print "allow access"

    def _ident_received(self, (type, info)):
        (system_type, user_info) = re.split(":", info)
        print "ident info received %s" % (info)
        if self._is_allowed_user(system_type, user_info):
            self._ident_succeeded()
        else:
            self._ident_failed(None)

    def connectionMade(self):
        print "Connected %s %s" % (self, self.transport)
        self.factory.clients.append(self)
        ident_factory.connectTCP(self.transport.getPeer().host, 113) \
            .addCallback(self._ident_connected) \
            .addErrback(self._ident_failed)

    def connectionLost(self, reason):
        print "Disconnected"
        self.factory.clients.remove(self)

    def lineReceived(self, data):
        print "hello"
        #self.transport.write(data)

ident_factory = protocol.ClientCreator(reactor, ident.IdentClient)

def make_server_factory(is_allowed_host, is_allowed_user):
    kerberos_factory = protocol.ServerFactory()
    kerberos_factory.protocol = lambda: Kerberos(is_allowed_user,
                                                 is_allowed_host)
    kerberos_factory.clients = []

    return kerberos_factory

def main():
    allowed_hosts = ["127.0.0.1", 
                     "130.230.72.140", # coffee
                     "130.230.72.137", # battery
                     "130.230.72.137"] # cherry

    allowed_users = ["root", "flux"]

    def is_allowed_host(peer):
        return allowed_hosts.count(peer.host)

    def is_allowed_user(system_type, user_info):
        print "system_type=%s, user_info=%s" % (system_type, user_info)
        return system_type == "UNIX" and allowed_users.count(user_info) > 0

    factory = make_server_factory(is_allowed_host, is_allowed_user)

    reactor.listenTCP(8000, factory)
    reactor.run()
    
if __name__ == "__main__":
    main()
