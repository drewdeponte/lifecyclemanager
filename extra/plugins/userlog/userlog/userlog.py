import posixpath
from trac.core import *
from trac.config import *
from trac.config import BoolOption
from trac.web.chrome import ITemplateProvider, \
    add_stylesheet
from trac.web.main import IRequestHandler
from trac.wiki import wiki_to_html, wiki_to_oneliner
from trac.mimeview import Mimeview, is_binary
from trac.util import escape, Markup
from trac.util.datefmt import format_datetime, pretty_timedelta
from trac.util.text import unicode_urlencode, shorten_line, CRLF
from trac.versioncontrol.diff import get_diff_options, unified_diff
from trac.versioncontrol import Node, Changeset
import re

class UserLogModule(Component):
    implements(IRequestHandler, ITemplateProvider)
    
    wiki_format_messages = BoolOption('changeset', 'wiki_format_messages',
                                      'true',
        """Whether wiki formatting should be applied to changeset messages.
        
        If this option is disabled, changeset messages will be rendered as
        pre-formatted text.""")

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/userlog(?:/(\w+).*|$)', req.path_info)
        if match:
            req.args['user'] = match.group(1) or '/'
            return True

    def process_request(self, req):
        user = req.args.get('user')
        sort = req.args.get('sort', 'ASC')
        
        db = self.env.get_db_cnx()
        
        changesets = self._get_userlog(req, db, user, sort)
        toc_links = []
        for rev, _, _, _ in changesets:
            toc_links.append({'anchor': rev,
                              'title': 'Revision %s' % rev})
            
        changeset_ranges = self._get_changeset_ranges(changesets)
        changeset_links = []
        for start, end in changeset_ranges:
            if start != end:
                title = 'Changeset [%s:%s]' % (start, end)
            else:
                title = 'Changeset [%s]' % start
            link = req.href.changeset(old=start, old_path='/',
                                      new=end, new_path='/')
            changeset_links.append({'href': link,
                                    'title': title})
            
        req.hdf['user'] = user
        req.hdf['changesets'] = changesets
        req.hdf['toc_links'] = toc_links
        req.hdf['changeset_links'] = changeset_links
        add_stylesheet(req, 'common/css/wiki.css')
        add_stylesheet(req, 'userlog/css/userlog.css')
        return 'userlog.cs', None
    
    def _get_userlog(self, req, db, user, sort):
        mimeview = Mimeview(self.env)
        repos = self.env.get_repository()
        diff_options = get_diff_options(req)
        cursor = db.cursor()
        cursor.execute("SELECT rev, time, message FROM revision "
                       "WHERE author='%s' ORDER BY time %s" % (user, sort))
                       # Have to sort by time because rev is a text field
                       # and sorts lexicographically rather than numerically
        changesets = []
        for rev, time, message in cursor:
            if self.wiki_format_messages:
                message = wiki_to_html(message, self.env, req,
                                              escape_newlines=True)
            else:
                message = html.PRE(message)
            prev = repos.get_node('/', rev).get_previous()
            if prev:
                prev_rev = prev[1]
            else:
                prev_rev = rev
            diffs = []
            changes = repos.get_changes(old_path='/', old_rev=prev_rev,
                                        new_path='/', new_rev=rev)
            for old_node, new_node, kind, change in changes:
                if kind == Node.DIRECTORY:
                    if change == Changeset.ADD:
                        diffs.append(('%s added' % new_node.path, ''))
                    elif change == Changeset.DELETE:
                        diffs.append(('%s deleted' % old_node.path, ''))
                    continue

                new_content = old_content = ''
                new_node_info = old_node_info = ('','')
                
                if old_node:
                    old_content = old_node.get_content().read()
                    if is_binary(old_content):
                        continue
                    old_node_info = (old_node.path, old_node.rev)
                    old_content = mimeview.to_unicode(old_content,
                                                      old_node.content_type)
                if new_node:
                    new_content = new_node.get_content().read()
                    if is_binary(new_content):
                        continue
                    new_node_info = (new_node.path, new_node.rev)
                    new_path = new_node.path
                    new_content = mimeview.to_unicode(new_content,
                                                      new_node.content_type)
                else:
                    old_node_path = repos.normalize_path(old_node.path)
                    diff_old_path = repos.normalize_path('/')
                    new_path = posixpath.join('/', old_node_path[len(diff_old_path)+1:])

                if old_content != new_content:
                    context = 3
                    options = diff_options[1]
                    for option in options:
                        if option.startswith('-U'):
                            context = int(option[2:])
                            break
                    if not old_node_info[0]:
                        old_node_info = new_node_info # support for 'A'dd changes
                    diff = 'Index: ' + new_path + CRLF
                    diff += '=' * 67 + CRLF
                    diff += '--- %s (revision %s)' % old_node_info + CRLF
                    diff += '+++ %s (revision %s)' % new_node_info + CRLF
                    for line in unified_diff(old_content.splitlines(),
                                             new_content.splitlines(), context,
                                             ignore_blank_lines='-B' in options,
                                             ignore_case='-i' in options,
                                             ignore_space_changes='-b' in options):
                        diff += line + CRLF
                    if change == Changeset.ADD:
                        diffs.append(('%s added' % (new_node.path,), diff))
                    elif change == Changeset.DELETE:
                        diffs.append(('%s deleted' % (old_node.path,), diff))
                    else:
                        diffs.append(('%s edited' % (new_node.path,), diff))
            changesets.append((int(rev), format_datetime(time), message, diffs))
        return changesets
    
    def _get_changeset_ranges(self, changesets):
        ranges = []  # will be a list of pairs: (start, end) 
        for rev, _, _, _ in changesets:
            # if rev is more than two greater than last max
            # or list is empty
            if ranges == [] or rev > (ranges[-1][1] + 1):
                # create a new tuple
                ranges.append((rev, rev))
            # else if rev is greater (by one) than last max
            elif rev == (ranges[-1][1] + 1):
                ranges[-1] = (ranges[-1][0], rev)
        return ranges

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided
        ClearSilver templates.
        """

        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('userlog', resource_filename(__name__, 'htdocs'))]
