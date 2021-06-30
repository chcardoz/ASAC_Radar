import zlib
import pickle
import hashlib
from zmq import *


def h4mac(key, message, alg):
    '''
        4 x Hashed message authentication code
        Author: Ralph Ritoch
        H(H(K) ^ H(M) ^ H(K + M + K))
    '''
    a1 = hashlib.new(alg)
    a2 = hashlib.new(alg)
    a3 = hashlib.new(alg)
    a4 = hashlib.new(alg)

    a1.update(key)
    a2.update(message)
    a3.update(key + message + key)

    a4.update(bytes([_a ^ _b ^ _c for _a, _b, _c in zip(
        a1.digest(), a2.digest(), a3.digest())]))

    return a4


def send_dataframe(socket: Socket, obj, secret='', flags=0, alg='sha256'):
    """send pandas dataframe"""

    p = pickle.dumps(obj, -1)
    h = h4mac(secret.encode(), p, alg).hexdigest().upper()
    s = h.encode() + b'\n' + p
    z = zlib.compress(s)
    return socket.send(z, flags=flags)


def recv_dataframe(socket: Socket, secret='', flags=0, alg='sha256'):
    """receive pandas dataframe"""

    z = socket.recv(flags)
    s = zlib.decompress(z)
    h = s[:s.find(b'\n')]
    p = s[(s.find(b'\n')+1):]

    if h4mac(secret.encode(), p, alg).hexdigest().upper() != h.decode():
        raise Exception("Signature mismatch")

    return pickle.loads(p)
