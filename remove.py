"""remove -- remove command for vellum.
"""
import os
import shutil

def remove(scribe, paths=[], force=False):
    """
    Takes a dict with "paths" and "force" and then removes each of
    those paths, forcing removal if directories are not empty.  Paths
    can be files or directories. WARNING: If force is true,
    directories will be removed along with ALL OF THEIR CONTENTS.
    """
    assert isinstance(paths, list), "remove expects a list as the expression"
    for a_path in paths:
        a_path = os.path.expanduser(scribe.interpolate('remove', a_path))
        scribe.log("remove: %s" % a_path)
        if (os.path.exists(a_path) and not scribe.option("dry_run")):
            if os.path.isdir(a_path):
                try:
                    os.rmdir(a_path)
                except OSError:
                    if force:
                        scribe.log(" remove: forcing the removal of non-empty directory %s" % a_path)
                        shutil.rmtree(a_path)
                    else:
                        scribe.log(" remove: %s is a non-empty directory." % (a_path))
            else:
                try:
                    os.unlink(a_path)
                except Exception, e:
                    err_msg = "  %s: %s. Could not remove %s"
                    scribe.log(err_msg % (e.__class__.__name__, e.args, a_path))

