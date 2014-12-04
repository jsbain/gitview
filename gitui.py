# coding: utf-8
#
'''whats working now:
    working with existing repo, along current branch, stage, unstage, commit changes.
    todo:
        auto install dulwich and gittle, as per shellista.. but install more recent dulwich
        make pull less dangerous.  currently, simply overwrites existing tree. maybe need fetch rather than pull, and locL merge ability...
        add delete button for untracked files, which actually deletes.
        show log, diff, and open old ref
        merge
        display last commit time
        pull table out as separate view
        encapsulate and organize
        '''
import ui,os,console, editor

### temporary during development
import dropdown
reload(dropdown)
import repo_finder
reload(repo_finder)
###

from repo_finder import FilteredDirDropdown

from dropdown import DropdownView
from dulwich import porcelain
from dulwich.client import default_user_agent_string
from dulwich.index import build_index_from_tree
from gittle import Gittle
import itertools
import threading

import keychain
import posix
import urlparse,urllib2   #for push
from uidialog import UIDialog

SAVE_PASSWORDS=True
class repoView (object):
    def __init__(self):
        self.g=None
        self.g_original=None
        self.view=None
        self.list=[[],[],[],[],[],[]]
        
    def _object_store(self):
        return self.g.repo.object_store
    def _repo(self):
        return self.g.repo
    def refresh_gittle(self):
        #untracked
        #unstaged modified
        #staged add
        #staged rm
        #staged modify
        #unmodified 
        self.g=self._get_repo()
        def refresh_thread():
             if self.g:
                self.list[0]=list(self.g.untracked_files)
                #self.view['tableview1'].reload()
                self.list[1]=porcelain.status(self.g.path).unstaged
                #self.view['tableview1'].reload()
                self.list[2]=porcelain.status(self.g.path).staged['add']
                #self.view['tableview1'].reload()
                self.list[3]=porcelain.status(self.g.path).staged['delete']
                #self.view['tableview1'].reload()
                self.list[4]=porcelain.status(self.g.path).staged['modify']
                #self.view['tableview1'].reload()
                self.list[5]=list(self.g.tracked_files-set(itertools.chain(*self.list[1:4])))

        #threading.Thread(target=refresh_thread).start()
        refresh_thread()
    def refresh(self):
        # update internal table shit
        #use porcelain status for staged, modified
        # gittle for untr and unmod  g.tracked_files -g.modified_files, g.untracked_files
        self.refresh_gittle()
        self.view['tableview1'].reload()
        #console.hud_alert('pull refresh')
        
    def tableview_number_of_sections(self, tableview):
        # untracked, mod unstg, staged, tracked
        return 6

    def tableview_number_of_rows(self, tableview, section):
        if not self.g:
            return 0
        # Return the number of rows in the section
        return len(self.list[section])
            
    def label_for_cell(self,section,row):
        return '    '+self.list[section][row]

    def tableview_cell_for_row(self, tableview, section, row):
        # Create and return a cell for the given section/row
        cell = ui.TableViewCell()
        cell.text_label.text = self.label_for_cell(section,row)
        cvf=cell.content_view.frame
        def delact(sender):
            porcelain.rm(self._repo(),[str(self.list[section][row])])
            self.refresh()
            console.hud_alert('del {} {}'.format(section,row))
        def unstage(sender):
            self.unstage(self._repo(),[str(self.list[section][row])])
            self.refresh()
            console.hud_alert('unstage {} {}'.format(section,row))
        def addact(sender):
            porcelain.add(self._repo(),str(self.list[section][row]))
            self.refresh()
            console.hud_alert('add')
        def openact(sender):
            full_file=os.path.join(self._repo_path(),str(self.list[section][row]))
            editor.open_file(full_file)
            console.hud_alert('open')
            console.hide_output()
        if section in (0,1,3):
            b=ui.Button(frame=(cvf[2]-32,0,32,cvf[3]))
            b.image=ui.Image.named('ionicons-plus-32')
            b.tint_color=(0.00, 0.50, 1.00)
            b.flex='ltb'
            cell.content_view.add_subview(b)
            b.action=addact
        if section in (2,3,4):
            b=ui.Button(frame=(cvf[2]-32*3.5,0,32,cvf[3]))
            b.image=ui.Image.named('ionicons-ios7-undo-32')
            b.tint_color=(0.00, 0.50, 1.00)
            b.flex='ltb'
            cell.content_view.add_subview(b)
            b.action=unstage
        if section in (1,2,4,5):
            b=ui.Button(frame=(cvf[2]-32*2.5,0,32,cvf[3]))
            b.image=ui.Image.named('ionicons-close-32')
            b.tint_color='red'
            b.flex='ltb'
            cell.content_view.add_subview(b)
            b.action=delact
        
        b=ui.Button(frame=(cvf[2]-32*4.5,0,32,cvf[3]))
        b.image=ui.Image.named('ionicons-document-32')
        b.tint_color='gray'
        b.flex='ltb'
        cell.content_view.add_subview(b)
        b.action=openact
        return cell

    def tableview_title_for_header(self, tableview, section):
        # Return a title for the given section.
        # If this is not implemented, no section headers will be shown.
        sections=['UNTRACKED','MODIFIED','STAGED: ADD','STAGED: RM','STAGED: modify','UNMODIFIED']
        return sections[section]

    def tableview_can_delete(self, tableview, section, row):
        # Return True if the user should be able to delete the given row.
        return False  

    def tableview_can_move(self, tableview, section, row):
        # Return True if a reordering control should be shown for the given row (in editing mode).
        return False 

    def tableview_delete(self, tableview, section, row):
        # Called when the user confirms deletion of the given row.
        pass

    def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
        # Called when the user moves a row with the reordering control (in editing mode).
        pass 
    
    def scrollview_did_scroll(self, scrollview):
        # You can use the content_offset attribute to determine the current scroll position
        if scrollview.content_offset[1]<-40:
            self.refresh()
            
#Get the parent git repo, if there is one
    def _repo_path(self):
        return os.path.join(self.view['repo'].base, self.view['repo'].text)
        
    def _get_repo(self):
        try:
            return Gittle(self._find_repo(self._repo_path()))
        except:
            return None
            
    def _find_repo(self,path):
        try:
            subdirs = os.walk(path).next()[1]
        except StopIteration:
            return None
        if '.git' in subdirs:
            return path
        else:
            parent = os.path.dirname(path)
            if parent == path:
                return None
            else:
                return self._find_repo(parent)
    def confirm(self,fcn,title='Are you sure?'):
        d=UIDialog(root=self.view,title=title,items={},ok_action=fcn)
        d.ok.title='Yes'
    def init_repo(self,repo_name):
        from shutil import rmtree
        gitpath=os.path.join(self.view['repo'].base,repo_name,'.git')
        if os.path.exists(gitpath):
            def fcn(somedict):
                rmtree(gitpath)
                self.init_repo_if_empty(repo_name,gitpath)
            self.confirm(fcn,'Repo already exists at {}. Erase?'.format(repo_name))
        else:
            self.init_repo_if_empty(repo_name,gitpath)
    def init_repo_if_empty(self,repo_name,gitpath):
        if not os.path.exists(gitpath):
            self.g= Gittle.init(gitpath,bare=False )
            self.g.commit('name','email','initial commit')
            self.view['repo'].text=repo_name
            console.hud_alert('Repo {} created'.format(repo_name))
            self.refresh()
        
    def git_status(self,args):
        if len(args) == 0:
            repo = _get_repo()
            status = porcelain.status(repo.repo)
            print status
        else:
            print command_help['git_staged']

    def branch_iterator(self):
        self.g=self._get_repo()
        if self.g:
            return self.g.branches.iterkeys()
            
    def remotes_iterator(self):
        self.g=self._get_repo()
        if self.g:
            return self.g.remotes.iterkeys()
            
    def remote_branches_iterator(self):
        self.g=self._get_repo()
        if self.g:
            return self.g.remote_branches.iterkeys()
            
    def did_select_repo(self,sender):
        self.g=self._get_repo()
        if self.g:
            r.view['branch'].text=self.g.active_branch
            author,author_email=self._get_last_committer()
            self.view['user'].text=author
            self.view['email'].text=author_email
            remote, remote_branch=self.remote_for_head()
            self.view['remote'].text=remote
            self.view['remotebranch'].text=remote_branch
        else:
            console.hud_alert('no repo here.  pull to clone')
            r.view['branch'].text=''
            self.g=None
        self.refresh()
    def _get_last_committer(self):
        try:
            last_commit=self.g.repo.object_store [self.g.repo.head()]
            if last_commit.author:
                author,author_email=(last_commit.author.split('>')[0]+'<').split('<')[0:2]
            elif last_commit.committer:
                author,author_email=(last_commit.committer.split('>')[0]+'<').split('<')[0:2]
            return author,author_email
        except KeyError, AttributeError:
            return '',''
    def commit(self,sender):
        if list(itertools.chain(*porcelain.status(self.g.path).staged.itervalues())):
            self.g=self._get_repo()
            user=self.view['user'].text
            email=self.view['email'].text
            message=self.view['message'].text
            author = "{0} <{1}>".format(user, email)
            porcelain.commit(self.g.path,message,author,author)
            console.hud_alert('committed')
            self.view['message'].text=''
            self.refresh()
        else:
            console.hud_alert('nothing to commit!',icon='error')
        
    def reset(self,sender):
        porcelain.reset(self.g.path,mode='hard',committish='HEAD')
        self.refresh()

    def unstage(self,repo,paths=None):
        from dulwich import porcelain
        from dulwich.index import index_entry_from_stat
    # if tree_entry does not exist, this was an add, so remove index entry to undo
    # if index_ entry does not exist, this was a remove.. add back in
        if paths:
            for path in paths:
                #print path
                full_path = os.path.join(repo.path, path)
                index=repo.open_index()
                tree_id=repo.object_store[repo.head()]._tree
                try:
                    tree_entry=repo.object_store[tree_id]._entries[path]
                except KeyError:
                    try:
                        del(index[path])
                        index.write()
                    except KeyError:
                        console.hud_alert('file not in index...')
                    return
                try:
                    index_entry=list(index[path])
                except KeyError:
                    if os.path.exists(full_path):
                        index_entry=list(index_entry_from_stat(posix.lstat(full_path),tree_entry[1]  ,0    ))
                    else:
                        index_entry=[[0]*11,tree_entry[1],0]
                index_entry[4]=tree_entry[0] #mode
                index_entry[7]=len(repo.object_store [tree_entry[1]].data) #size
                index_entry[8]=tree_entry[1] #sha
                index_entry[0]=repo.object_store[repo.head()].commit_time #ctime
                index_entry[1]=repo.object_store[repo.head()].commit_time #mtime
                index[path]=index_entry
                index.write()
                
    def unstage_all(self):
        # files to unstage consist of whatever was in new tree, plus whatever was in old index (added files to old branch)
        repo=self._repo()
        index=repo.open_index()
        tree_id=repo.object_store[repo.head()]._tree
        for entry in repo.object_store.iter_tree_contents(tree_id):
            self.unstage(self._repo(),[entry.path])
            
        for entry in index.iteritems():
            self.unstage(self._repo(),[entry[0]])
        
    def branch_did_change(self,sender):
        # set head to branch
        repo=self._get_repo()
        branch=self.view['branch'].text
        if branch==repo.active_branch:
            return
        if branch in self.branch_iterator():
            self._repo().refs.set_symbolic_ref('HEAD', 'refs/heads/'+branch)
            self.unstage_all()
            self.refresh()
            console.hud_alert('branch')
        elif branch in self._repo():
            
            indexfile = repo.repo.index_path()

            tree = repo.repo[str(branch)].tree

            build_index_from_tree(repo.repo.path, indexfile, repo.repo.object_store, tree)
            
            #self._repo().refs.set_symbolic_ref('HEAD', branch)
            #self.unstage_all()
            #self.refresh()
            console.hud_alert('commitish')
        else:
            #todo: prompt to confirm
            self.create_branch() 
    def remote_for_head(self):
        refs=self._repo().refs.as_dict().iteritems()

        try:
            head=self._repo().head()
            remote, remote_branch=[ k.split('/')[-2:]  for k,v in refs if v==head and k.startswith('refs/remotes')][0]
            return remote,remote_branch
        except IndexError, KeyError:
            return '',''

    def checkout(self,sender):
        repo =self._get_repo()
        cwd=os.path.abspath('.')
        os.chdir(r._get_repo().path)
        #repo.clean_working()
        repo.switch_branch(self.view['branch'].text)
        self.refresh()
        os.chdir(cwd)
        editor.open_file(editor.get_path())
        console.hud_alert('checked out')
        
    def create_branch(self):
        #TODO: Add tracking as a parameter
        repo=self._get_repo()
        branch=self.view['branch'].text
        console.hud_alert( "Creating branch {0}".format(branch))
        repo.create_branch(repo.active_branch, branch, tracking=None)
        #Recursive call to checkout the branch we just created
        self.checkout(self)

    def pull_action(self,sender):
        if self.g:
            self.pull()
        else:
            self.clone()
    def clone(self,clonedict):
        remote=clonedict['remote url']
        local=clonedict['local path']
        repo_name= os.path.join(self.view['repo'].base, local)

        if remote:
            try:
                repo = Gittle.clone(remote, repo_name, bare=False)
        
                #Set the origin
                config = repo.repo.get_config()
                config.set(('remote','origin'),'url',remote)
                config.write_to_path()
                self.view['repo'].txt=repo_name
                self.refresh()
            except Exception as e:
                console.hud_alert(e.message)
        
    def clone_action(self,sender):
        d=UIDialog(root=self.view,title='Clone repo',items={'remote url':'https://github.com/','local path':''},ok_action=self.clone)
        
    def new_action(self,sender):
        def ok(somedict):
            self.init_repo(somedict['repo name'])
        d=UIDialog(root=self.view,title='Clone repo',items={'repo name':''},ok_action=ok)
        
    def pull(self):
        repo = self._get_repo()

        remote=self.view['remote'].text
        if remote in self.remotes_iterator():
            uri=repo.remotes.get(remote,'')
        else:
            print remote, 'adding'
            uri=remote
            #Set the origin
            config = repo.repo.get_config()
            config.set(('remote','origin'),'url',uri)
            config.write_to_path()
        repo.pull(origin_uri=uri)
        console.hud_alert('pulled from ',remote) 
        self.refresh()
        
    @ui.in_background
    def push_action(self,sender):

        user, sep, pw =  (None,None,None)
        repo = self._get_repo()
        
        remote=self.view['remote'].text
        if remote in self.remotes_iterator():
            remote = repo.remotes.get(remote,'')

        branch_name = os.path.join('refs','heads', repo.active_branch)  #'refs/heads/%s' % repo.active_branch
        # tODO  use remote branch_name 
        print "Attempting to push to: {0}, branch: {1}".format(remote, branch_name)

        netloc = urlparse.urlparse(remote).netloc

        keychainservice = 'shellista.git.{0}'.format(netloc)

        if sep and not user:
            # -u : clears keychain for this server
            for service in keychain.get_services():
                if service[0]==keychainservice:
                    keychain.delete_password(*service)

        #Attempt to retrieve user
        if not user and SAVE_PASSWORDS:
            try:
                user = dict(keychain.get_services())[keychainservice]
            except KeyError:
                user, pw = console.login_alert('Enter credentials for {0}'.format(netloc))

        if user:
            if not pw and SAVE_PASSWORDS:
                pw = keychain.get_password(keychainservice, user)

            #Check again, did we retrieve a password?
            if not pw:
                user, pw = console.login_alert('Enter credentials for {0}'.format(netloc), login=user)
                #pw = getpass.getpass('Enter password for {0}: '.format(user))

            opener = auth_urllib2_opener(None, remote, user, pw)

            porcelain.push(repo.path, remote, branch_name, opener=opener)
            keychain.set_password(keychainservice, user, pw)

        else:
            porcelain.push(repo.repo, result.url, branch_name)
        console.hud_alert('pushed')


def auth_urllib2_opener(config, top_level_url, username, password):
    if config is not None:
        proxy_server = config.get("http", "proxy")
    else:
        proxy_server = None

    # create a password manager
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

        # Add the username and password.
        # If we knew the realm, we could use it instead of None.
        #top_level_url = "http://example.com/foo/"
        password_mgr.add_password(None, top_level_url, username, password)

        handler = urllib2.HTTPBasicAuthHandler(password_mgr)

    handlers = [handler]
    if proxy_server is not None:
        handlers.append(urllib2.ProxyHandler({"http": proxy_server}))
    opener = urllib2.build_opener(*handlers)
    if config is not None:
        user_agent = config.get("http", "useragent")
    else:
        user_agent = None
    if user_agent is None:
        user_agent = default_user_agent_string()
    opener.addheaders = [('User-agent', user_agent)]
    return opener




r=repoView()
v=ui.load_view('gitui')
r.view=v
fdd=v['repo']
fdd.filter='.git'
fdd.textfield.action=r.did_select_repo
v['branch'].items=r.branch_iterator
v['remotebranch'].items=r.remote_branches_iterator
v['remote'].items=r.remotes_iterator
v['tableview1'].data_source=v['tableview1'].delegate=r
v['commit'].action=r.commit
v['branch'].action=r.branch_did_change
v['checkout'].action=r.checkout
v['pull'].action=r.pull_action
v['push'].action=r.push_action
v['clone'].action=r.clone_action
v['new'].action=r.new_action
#load current repo
editorpath=os.path.split(editor.get_path())[0]
if editorpath.startswith('/var'):
    editorpath=os.path.join('/private',editorpath[1:])
repo_path=r._find_repo(editorpath)
if repo_path:
    rel_repo_path=os.path.relpath(editorpath,v['repo'].base)
    v['repo'].text=rel_repo_path
    
    
v.present('panel')

r.did_select_repo(v['repo'])



