import collections
import time
import sass
import os
import shutil
import glob
import json
import ntpath
import subprocess
from babel.support import Translations
from jinja2 import Environment, FileSystemLoader
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from weasyprint import HTML
from utils import colored_print, copytree, rand_string


inputs = {
    'templates': 'templates',
    'data': 'data',
    'assets': 'assets',
    'sass': 'sass',
    'locale_dir': 'i18n'
}

outputs = {
    'html': {
        'root': 'dist',
        'assets': 'assets',
        'css': 'css',
    },
    'pdf': {
        'root': 'pdf'
    }
}


def extend_jinja_filters(jinja_env):

    def check_patient_risk(risks):
        if not isinstance(risks, collections.Iterable):
            return False
        return bool([item for item in risks if item['value'] < 25])

    def dot_color(val):
        if val <= 16.6:
            return 'red'
        elif 16.6 < val <= 33.3:
            return 'orange'
        elif 33.3 < val <= 66.6:
            return 'yellow'
        else:
            return 'blue'

    jinja_env.filters['check_patient_risk'] = check_patient_risk
    jinja_env.filters['dot_color'] = dot_color


class SassHandler(PatternMatchingEventHandler):

    time_indicator = 0
    locale_domain = 'messages'

    def __init__(self, *args, **kwargs):
        super(SassHandler, self).__init__(*args, **kwargs)
        self.sass = inputs['sass']
        self.assets = inputs['assets']
        self.templates = inputs['templates']
        self.data = inputs['data']

        self.html_output = outputs['html']['root']
        self.html_assets = os.path.join(self.html_output, outputs['html']['assets'])
        self.html_css = os.path.join(self.html_assets, outputs['html']['css'])
        self.css_relative = os.path.join(outputs['html']['assets'], outputs['html']['css'])

        self.pdf_output = outputs['pdf']['root']

        # Jinja with i18n initialization
        self.locale_dir = inputs['locale_dir']
        self.locales_list = [
            name for name in os.listdir(self.locale_dir)
            if os.path.isdir(os.path.join(self.locale_dir, name))
        ]

    def _initialize(self):
        colored_print('Initializing... ', 'OKGREEN')
        # Init html dest dir
        if os.path.isdir(self.html_output):
            shutil.rmtree(self.html_output)
        os.mkdir(self.html_output)
        copytree(self.assets, self.html_assets)
        os.mkdir(self.html_css)
        # Init pdf dir
        if os.path.isdir(self.pdf_output):
            shutil.rmtree(self.pdf_output)
        os.mkdir(self.pdf_output)

    def _compile_sass(self):
        colored_print('Recompiling SaSS... ', 'OKGREEN')
        css_filename = os.path.join(self.html_css, 'main.' + rand_string(12) + '.css')
        try:
            compiled = sass.compile(
                filename=os.path.join(self.sass, 'main.scss'),
                output_style='compressed'
            )
            with open(css_filename, 'w') as f:
                f.write(compiled)
        except Exception as e:
            colored_print(e, 'WARNING')
        return css_filename

    def _get_data(self, filename):
        with open(os.path.join(self.data, filename + '.json')) as f:
            try:
                return json.load(f)
            except ValueError as e:
                colored_print(
                    'Check JSON format of `%s.json` file' % filename,
                    'FAIL'
                )
                colored_print(e, 'FAIL')
                return {}

    def _renew_localization(self):
        """
        For create translation template use command
            pybabel extract -F ./babel.cfg -o ./i18n/messages.pot ./
        For initialize new locale use
            pybabel init -l en_US -d ./i18n -i ./i18n/messages.pot
        For updating locale files use
            pybabel update -l en_US -d ./i18n -i ./i18n/messages.pot
        For compiling use
            pybabel compile -f -d ./i18n
        """
        colored_print('Re-extract localization messages...', 'OKGREEN')
        params = ['pybabel', 'extract', '-F', './babel.cfg', '-o',
                  os.path.join(self.locale_dir, self.locale_domain + '.pot'), './']
        subprocess.call(params)
        for loc in self.locales_list:
            colored_print('Update `%s` localization file...' % loc, 'OKGREEN')
            params = ['pybabel', 'update', '-l', loc, '-d', self.locale_dir,
                      '-i', os.path.join(self.locale_dir, self.locale_domain + '.pot')]
            subprocess.call(params)
        colored_print('Recompile localization files...', 'OKGREEN')
        params = ['pybabel', 'compile', '-f', '-d', self.locale_dir]
        subprocess.call(params)

    def _init_jinja(self):
        lang = os.environ['LANG']
        if not lang:
            lang = self.locales_list
        self.translations = Translations.load(self.locale_dir, lang)
        self.jinja_env = Environment(
            extensions=[
                'jinja2.ext.i18n',
                'jinja2.ext.autoescape',
                'jinja2.ext.with_'
            ],
            loader=FileSystemLoader(self.templates)
        )
        self.jinja_env.install_gettext_translations(self.translations, newstyle=True)
        extend_jinja_filters(self.jinja_env)

    def _compile_html(self, css_file):
        for locale in self.locales_list:
            os.environ['LANG'] = locale
            self._init_jinja()
            templates = glob.glob(os.path.join(self.templates, '*.html'))
            for template in templates:
                colored_print(
                    'Compiling `%s` file to Html for `%s` locale' % (template, locale),
                    'OKGREEN'
                )
                template = ntpath.basename(template)
                name = os.path.splitext(template)
                data = self._get_data(name[0])
                data['css_path'] = os.path.join(
                    self.css_relative,
                    ntpath.basename(css_file)
                )
                data['locale'] = locale
                rendered = 'ERROR HAPPENED'
                try:
                    rendered = self.jinja_env.get_template(template).render(**data)
                except Exception as e:
                    colored_print(
                        'Jinja render error. Check template `%s`' % template,
                        'FAIL'
                    )
                    colored_print(e, 'FAIL')
                filename = os.path.join(
                    self.html_output,
                    ''.join([name[0], '_', locale, '.html'])
                )
                with open(filename, 'w') as f:
                    f.write(rendered.encode('utf-8'))
                colored_print(
                    'compiled and saved to `%s`' % filename,
                    'OKGREEN'
                )

    def _make_pdf(self):
        colored_print('Generating PDFs...', 'OKGREEN')
        html_files = glob.glob(os.path.join(self.html_output, '*.html'))
        for html_file in html_files:
            pdf_filename = os.path.splitext(ntpath.basename(html_file))[0]
            pdf_filename += rand_string(5)
            pdf_filename += '.pdf'
            try:
                HTML(html_file).write_pdf(os.path.join(self.pdf_output, pdf_filename), zoom=1.75)
            except Exception as e:
                colored_print('PDF `%s` generation failed' % pdf_filename, 'FAIL')

    def process(self, event):
        start_time = time.time()
        colored_print('*' * 60, 'OKBLUE')
        colored_print(time.ctime() + ' : Start process.', 'OKGREEN')

        self._initialize()
        css_file = self._compile_sass()
        self._renew_localization()
        self._compile_html(css_file)
        self._make_pdf()

        colored_print('Finished in ' + str(time.time() - start_time), 'OKGREEN')
        colored_print('*' * 60, 'OKBLUE')

    def on_any_event(self, event):
        if time.time() - SassHandler.time_indicator > 5:
            self.process(event)
        SassHandler.time_indicator = time.time()


def run():
    observer = Observer()
    observer.schedule(
        SassHandler(patterns=[
            '*.*'
        ]),
        path=inputs['sass'],
        recursive=True
    )
    observer.schedule(
        SassHandler(patterns=[
            '*.*'
        ]),
        path=inputs['templates']
    )
    observer.schedule(
        SassHandler(patterns=[
            '*.*'
        ]),
        path=inputs['assets']
    )
    observer.schedule(
        SassHandler(patterns=[
            '*.json'
        ]),
        path=inputs['data']
    )
    observer.schedule(
        SassHandler(patterns=[
            '*.*',
            '*.pot'
        ]),
        path=inputs['locale_dir'],
        recursive=True
    )
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
