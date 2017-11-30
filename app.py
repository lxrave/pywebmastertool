import os
import glob
from flask import Flask, send_file, abort


app = Flask(__name__, static_folder='dist/assets')
default_locale = 'en_US'


@app.route('/')
def default_html():
    files = glob.glob(os.path.join('dist', '*%s*.html' % default_locale))
    if not files:
        abort(404)
    return send_file(
        files[0],
        mimetype='text/html',
        add_etags=True,
        cache_timeout=1
    )


@app.route('/<string:locale>')
def html_by_locale(locale):
    files = glob.glob(os.path.join('dist', '*%s*.html' % locale))
    if not files:
        abort(404)
    return send_file(
        files[0],
        mimetype='text/html',
        add_etags=True,
        cache_timeout=1
    )


@app.route('/pdf/<string:locale>')
def pdf_by_locale(locale):
    files = glob.glob(os.path.join('pdf', '*%s*.pdf' % locale))
    if not files:
        abort(404)
    return send_file(
        files[0],
        mimetype='application/pdf',
        add_etags=True,
        cache_timeout=1
    )


if __name__ == "__main__":
    app.run()
