from __future__ import annotations
from dataclasses import dataclass
from hashlib import pbkdf2_hmac, sha256
from hmac import compare_digest
from secrets import token_urlsafe
from time import time

@dataclass(frozen=True)
class Principal:
    subject:str; roles:frozenset[str]; tenant:str

class Authenticator:
    """Minimal local auth primitive; production deployments should put an OIDC/IdP in front."""
    def __init__(self): self._tokens={}; self._users={}
    def create_user(self,subject,tenant,roles): self._users[subject]=(tenant,frozenset(roles))
    def issue(self,subject,ttl=3600):
        if subject not in self._users: raise KeyError(subject)
        raw=token_urlsafe(32); self._tokens[sha256(raw.encode()).hexdigest()]=(subject,time()+ttl); return raw
    def authenticate(self,token):
        item=self._tokens.get(sha256(token.encode()).hexdigest())
        if not item or item[1]<time(): return None
        subject=item[0]; tenant,roles=self._users[subject]; return Principal(subject,roles,tenant)
    @staticmethod
    def require(principal,role):
        if principal is None or role not in principal.roles: raise PermissionError('insufficient role')


def hash_password(password,salt=None):
    salt=salt or token_urlsafe(16); h=pbkdf2_hmac('sha256',password.encode(),salt.encode(),310000); return salt+'$'+h.hex()
def verify_password(password,encoded):
    salt,expected=encoded.split('$',1); actual=pbkdf2_hmac('sha256',password.encode(),salt.encode(),310000).hex(); return compare_digest(actual,expected)
