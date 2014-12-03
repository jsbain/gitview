gitview
=======

Pythonista git wrapper

basic usage:  
      add to action menu, in which case it opens repo of currently editing file.
      can browse repos from dropdown menu, or type name of repo.
      push clone button to pop up a dialog for cloning, or push new repo buton to create a new repo.  by default repos are named relative to main script folder
      
      change branch from the branch drop down.  note a few deliberate quirks:
          selecting a branch does NOT check it out, it only updates the index.  this allows a crude sort of merge capability (checkout branch a, then switch to master, then stage and commit... now master has a copy of branch a's files.  however note that sha will be different, and branch a history wont be reflected in master.  this is sort of a rebase method.)
          also, you can type a sha here, and the specific sha will be checked out, without clicking check out button.... so be careful with that.  this would allow past history to be loaded.
        typing a remote url in the remote box will save an origin shortcut after doing a pull.  remote branch doesnt work at all, currently -- so also be careful with pull.  i think any matching named branches get overwritten.
        pushing can only push if the remote already has a so named branch.
        push will reuse saved credentials from shellista, or may prompt.
        commit commits any staged changes in the index to the tree.  user, email and message are required for each commit.  user and email will persist per repo, stored in local keychain.
        use the repo manager to identify untracked, unstaged modifications, etc.   pressing the document button opens a file in the editor.  pressing X deletes from the repo.  pressing the undo button undoes a staging action.  pressing + will add untracked changes, or stage modifications.
         pull to refresh repo manager state, when editing in editor.  most other actins reset automatically.
         
install
=======
use GitHubGet or other tool to download repo.
first run install_gitview once to load dulwich,etc to site-packages
run gitui to run
                                                                                                                    
todo
====
handle remote branches better in pull
log browser
diff working tree
warnings for certain actions.
show sha's, last commit message/date when switching branches
modularize /organize code bettery

                                                                                                        
