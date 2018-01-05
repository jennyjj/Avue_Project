# -*- coding: utf-8 -*-
"""
    flask_principal
    ~~~~~~~~~~~~~~~
    Identity management for Flask.
    :copyright: (c) 2012 by Ali Afshar.
    :license: MIT, see LICENSE for more details.
"""

from __future__ import with_statement

__version__ = '0.3.5'

import sys

from functools import partial, wraps
from collections import deque

from collections import namedtuple

from flask import g, session, current_app, abort, request
from flask.signals import Namespace

PY3 = sys.version_info[0] == 3

signals = Namespace()


identity_changed = signals.signal('identity-changed', doc="""
Signal sent when the identity for a request has been changed.
Actual name: ``identity-changed``
Authentication providers should send this signal when authentication has been
successfully performed. Flask-Principal connects to this signal and
causes the identity to be saved in the session.
For example::
    from flaskext.principal import Identity, identity_changed
    def login_view(req):
        username = req.form.get('username')
        # check the credentials
        identity_changed.send(app, identity=Identity(username))
""")


identity_loaded = signals.signal('identity-loaded', doc="""
Signal sent when the identity has been initialised for a request.
Actual name: ``identity-loaded``
Identity information providers should connect to this signal to perform two
major activities:
    1. Populate the identity object with the necessary authorization provisions.
    2. Load any additional user information.
For example::
    from flaskext.principal import identity_loaded, RoleNeed, UserNeed
    @identity_loaded.connect
    def on_identity_loaded(sender, identity):
        # Get the user information from the db
        user = db.get(identity.name)
        # Update the roles that a user can provide
        for role in user.roles:
            identity.provides.add(RoleNeed(role.name))
        # Save the user somewhere so we only look it up once
        identity.user = user
""")


Need = namedtuple('Need', ['method', 'value'])
"""A required need
This is just a named tuple, and practically any tuple will do.
The ``method`` attribute can be used to look up element 0, and the ``value``
attribute can be used to look up element 1.
"""


UserNeed = partial(Need, 'id')
UserNeed.__doc__ = """A need with the method preset to `"id"`."""


RoleNeed = partial(Need, 'role')
RoleNeed.__doc__ = """A need with the method preset to `"role"`."""


TypeNeed = partial(Need, 'type')
TypeNeed.__doc__ = """A need with the method preset to `"type"`."""


ActionNeed = partial(Need, 'action')
ActionNeed.__doc__ = """A need with the method preset to `"action"`."""


ItemNeed = namedtuple('ItemNeed', ['method', 'value', 'type'])
"""A required item need
An item need is just a named tuple, and practically any tuple will do. In
addition to other Needs, there is a type, for example this could be specified
as::
    ItemNeed('update', 27, 'posts')
    ('update', 27, 'posts') # or like this
And that might describe the permission to update a particular blog post. In
reality, the developer is free to choose whatever convention the permissions
are.
"""


class PermissionDenied(RuntimeError):
    """Permission denied to the resource"""


class Identity(object):
    """Represent the user's identity.
    :param id: The user id
    :param auth_type: The authentication type used to confirm the user's
                      identity.
    The identity is used to represent the user's identity in the system. This
    object is created on login, or on the start of the request as loaded from
    the user's session.
    Once loaded it is sent using the `identity-loaded` signal, and should be
    populated with additional required information.
    Needs that are provided by this identity should be added to the `provides`
    set after loading.
    """
    def __init__(self, id, auth_type=None):
        self.id = id
        self.auth_type = auth_type
        self.provides = set()

    def can(self, permission):
        """Whether the identity has access to the permission.
        :param permission: The permission to test provision for.
        """
        return permission.allows(self)

    def __repr__(self):
        return '<{0} id="{1}" auth_type="{2}" provides={3}>'.format(
            self.__class__.__name__, self.id, self.auth_type, self.provides

class Principal(object):
    """Principal extension
    :param app: The flask application to extend
    :param use_sessions: Whether to use sessions to extract and store
                         identification.
    :param skip_static: Whether to ignore static endpoints.
    """
    def __init__(self, app=None, use_sessions=True, skip_static=False):
        self.identity_loaders = deque()
        self.identity_savers = deque()
        # XXX This will probably vanish for a better API
        self.use_sessions = use_sessions
        self.skip_static = skip_static

        if app is not None:
            self.init_app(app)

    def _init_app(self, app):
        from warnings import warn
        warn(DeprecationWarning(
            '_init_app is deprecated, use the new init_app '
            'method instead.'), stacklevel=1
        )
        self.init_app(app)

    def init_app(self, app):
        if hasattr(app, 'static_url_path'):
            self._static_path = app.static_url_path
        else:
            self._static_path = app.static_path

        app.before_request(self._on_before_request)
        identity_changed.connect(self._on_identity_changed, app)

        if self.use_sessions:
            self.identity_loader(session_identity_loader)
            self.identity_saver(session_identity_saver)

    def set_identity(self, identity):
        """Set the current identity.
        :param identity: The identity to set
        """

        self._set_thread_identity(identity)
        for saver in self.identity_savers:
            saver(identity)

    def identity_loader(self, f):
        """Decorator to define a function as an identity loader.
        An identity loader function is called before request to find any
        provided identities. The first found identity is used to load from.
        For example::
            app = Flask(__name__)
            principals = Principal(app)
            @principals.identity_loader
            def load_identity_from_weird_usecase():
                return Identity('ali')
        """
        self.identity_loaders.appendleft(f)
        return f

    def identity_saver(self, f):
        """Decorator to define a function as an identity saver.
        An identity loader saver is called when the identity is set to persist
        it for the next request.
        For example::
            app = Flask(__name__)
            principals = Principal(app)
            @principals.identity_saver
            def save_identity_to_weird_usecase(identity):
                my_special_cookie['identity'] = identity
        """
        self.identity_savers.appendleft(f)
        return f

    def _set_thread_identity(self, identity):
        g.identity = identity
        identity_loaded.send(current_app._get_current_object(),
                             identity=identity)

    def _on_identity_changed(self, app, identity):
        if self._is_static_route():
            return

        self.set_identity(identity)

    def _on_before_request(self):
        if self._is_static_route():
            return

        g.identity = AnonymousIdentity()
        for loader in self.identity_loaders:
            identity = loader()
            if identity is not None:
                self.set_identity(identity)
                return

    def _is_static_route(self):
        return (
            self.skip_static and
            (self._static_path and request.path.startswith(self._static_path))
        )
