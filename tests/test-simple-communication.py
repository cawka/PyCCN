# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */

import unittest
import ndn

class Server:
    def __init__ (self):
        self.face = ndn.Face ()
        self.face.setInterestFilter ("/forty", self.onInterest)
        
    def onInterest (self, baseName, interest):
        key = ndn.Key.getDefault ()
        keyLocator = ndn.KeyLocator.getDefault ()
        
        si = ndn.SignedInfo ()
        si.publisherPublicKeyDigest = key.publicKeyID
        si.type = ndn.CONTENT_DATA
        si.freshnessSeconds = 5
        si.keyLocator = keyLocator
        
        co = ndn.Data (name = "/forty/two", content = "Frou")

        co.signedInfo = si

        co.sign (key)
        
        self.face.put (co)

class Client:
    def __init__ (self):
        self.face = ndn.Face ()

        self.dataReceived = False
        self.timeoutReceived = False

        self.face.expressInterest ("/forty/two", self.onData, self.onTimeout)

    def setEventLoop (self, eventLoop):
        self.eventLoop = eventLoop
                
    def onData (self, interest, data):
        self.dataReceived = True
        self.eventLoop.stop ()

    def onTimeout (self, interest):
        self.timeoutReceived = True
        self.eventLoop.stop ()
        
class Basic(unittest.TestCase):
    def test_send_receive (self):
        server = Server ()
        client = Client ()
    
        event_loop = ndn.EventLoop (server.face, client.face)
        client.setEventLoop (event_loop)
        event_loop.run ()

        self.assertTrue (client.dataReceived)
        self.assertFalse (client.timeoutReceived)

if __name__ == '__main__':
    unittest.main()
