import logging
from flask import Blueprint, request
from flask.ext.babel import gettext, get_locale
from elasticsearch import TransportError
from exactitude import countries, languages
from followthemoney import model
from followthemoney.exc import InvalidData
from jwt import ExpiredSignatureError

from aleph import __version__
from aleph.core import settings, url_for
from aleph.authz import Authz
from aleph.model import Collection
from aleph.logic.statistics import get_instance_stats
from aleph.views.cache import enable_cache
from aleph.views.util import jsonify

blueprint = Blueprint('base_api', __name__)
log = logging.getLogger(__name__)


@blueprint.route('/api/2/metadata')
def metadata():
    locale = get_locale()
    enable_cache(vary_user=False)

    auth = {}
    if settings.PASSWORD_LOGIN:
        auth['password_login_uri'] = url_for('sessions_api.password_login')
        auth['registration_uri'] = url_for('roles_api.create_code')
    if settings.OAUTH:
        auth['oauth_uri'] = url_for('sessions_api.oauth_init')

    country_names = {}
    for code, label in countries.names.items():
        country_names[code] = locale.territories.get(code.upper(), label)

    language_names = {}
    for code, label in languages.names.items():
        language_names[code] = locale.languages.get(code, label)

    return jsonify({
        'status': 'ok',
        'maintenance': request.authz.in_maintenance,
        'app': {
            'title': settings.APP_TITLE,
            'version': __version__,
            'ui_uri': settings.APP_UI_URL,
            'samples': settings.SAMPLE_SEARCHES,
            'logo': settings.APP_LOGO,
            'favicon': settings.APP_FAVICON,
            'locale': str(locale),
            'locales': settings.UI_LANGUAGES
        },
        'categories': Collection.CATEGORIES,
        'statistics': get_instance_stats(Authz.from_role(None)),
        'countries': country_names,
        'languages': language_names,
        'schemata': model,
        'auth': auth
    })


@blueprint.route('/api/2/statistics')
def statistics():
    enable_cache(vary_user=True)
    return jsonify(get_instance_stats(request.authz))


@blueprint.route('/api/1/<path:path>')
def api_v1_message(path):
    return jsonify({
        'status': 'error',
        'message': gettext('/api/1/ is deprecated, please use /api/2/.')
    }, status=501)


@blueprint.app_errorhandler(403)
def handle_authz_error(err):
    return jsonify({
        'status': 'error',
        'message': gettext('You are not authorized to do this.'),
        'roles': request.authz.roles
    }, status=403)


@blueprint.app_errorhandler(404)
def handle_not_found_error(err):
    return jsonify({
        'status': 'error',
        'message': gettext('This path does not exist.')
    }, status=404)


@blueprint.app_errorhandler(InvalidData)
def handle_invalid_data(err):
    return jsonify({
        'status': 'error',
        'errors': err.errors
    }, status=400)


@blueprint.app_errorhandler(ExpiredSignatureError)
def handle_jwt_expired(err):
    return jsonify({
        'status': 'error',
        'errors': gettext('Access token has expired.')
    }, status=401)


@blueprint.app_errorhandler(TransportError)
def handle_es_error(err):
    message = err.error
    try:
        status = int(err.status_code)
    except Exception:
        status = 500
    try:
        for cause in err.info.get('error', {}).get('root_cause', []):
            message = cause.get('reason', message)
    except Exception as ex:
        log.debug(ex)
    return jsonify({
        'status': 'error',
        'message': message
    }, status=status)
