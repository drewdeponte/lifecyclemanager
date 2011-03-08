from trac.core import *
from trac.config import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
    add_stylesheet
from trac.web.main import IRequestHandler
from trac.wiki.formatter import *
from trac.util import escape, Markup
import os
import re
import string
import fileinput
import codecs
from fnmatch import filter

class DocsModule(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'docs'

    def get_navigation_items(self, req):
        yield 'mainnav', 'docs', Markup('<a href="%s">Docs</a>',
            self.env.href.docs())

    # IRequestHandler methods
    def match_request(self, req):
        if (req.path_info == '/docs'):
            return 1
        elif (string.find(req.path_info, '/docs/pdf/') != -1):
            return 1
        elif (string.find(req.path_info, '/docs/html/') != -1):
            return 1
        elif (string.find(req.path_info, '/docs/irc/') != -1):
            return 1
        else:
            return None

    def process_request(self, req):
        htdocs_dir = self.config.get('docs', 'htdocs_dir')

        # Handle processing of /pdf/somefilename requests
        if (string.find(req.path_info, "docs/pdf/") != -1):
            pdf_file_name = (string.split(req.path_info, '/')[3])
            req.send_file(htdocs_dir + '/pdf/' + pdf_file_name)
            return None

        elif (string.find(req.path_info, "docs/html/") != -1):
            html_file_name = req.path_info[string.rindex(req.path_info, 'docs/html/') + 10:]
            if html_file_name.endswith('.html'):
                html = codecs.open(htdocs_dir + '/html/' + html_file_name, 'r', 'utf-8', 'replace')
                content = re.compile(r'^.*<body >\s*<p>\s*(.*)<p>\s*<br>\s*<hr>\s*<address>.*$', re.MULTILINE | re.IGNORECASE | re.DOTALL).match(html.read())
                html.close()
                if content is not None:
                    req.hdf.set_unescaped('content', content.group(1))
                else:
                    req.hdf['content'] = 'No content'
                return 'htmldoc.cs', None
            else:
                req.send_file(htdocs_dir + '/html/' + html_file_name)
                return None

        elif (string.find(req.path_info, "docs/irc/") != -1):
            irc_file_name = (string.split(req.path_info, '/')[3])
            irc = codecs.open(htdocs_dir + '/irc/' + irc_file_name, 'r', 'utf-8', 'replace')
            content = ''
            try:
                for line in irc:
                    content += wiki_to_html(line, self.env, req)
            finally:
                irc.close()
            if content is not None:
                req.hdf.set_unescaped('content', content)
            else:
                req.hdf['content'] = 'No content'
            return 'ircdoc.cs', None

        # Handle the default case
        else:
            pdfs_dir = htdocs_dir + '/pdf/'
            pdfs = filter(os.listdir(pdfs_dir), "*.pdf")
            pdfs.sort()
            pdfs = map(lambda x: x.rstrip('.pdf'), pdfs)
            req.hdf['pdfs'] = pdfs

            irc_dir = htdocs_dir + '/irc/'
            irc = filter(os.listdir(irc_dir), "lifecyclemanager-dev.log.*")
            irc.sort()
            req.hdf['irc'] = irc

            add_stylesheet(req, 'hw/css/docs.css')
            return 'docs.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided
        ClearSilver templates.
        """

        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        return [('docs', self.config.get('docs', 'htdocs_dir'))]
