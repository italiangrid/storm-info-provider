import os
import pwd
import grp
import string
import logging

def create_file_from_template(dest_file, template_file, params):
    logging.debug("Creating file %s from template %s with params %s", 
        dest_file, template_file, params)
    # open files
    ftemplate = open(template_file)
    fconfig = open(dest_file, "w")
    # read from template ...
    logging.debug("Reading from template ...")
    src = string.Template(ftemplate.read())
    # ... substitute values ...       
    logging.debug("Substitute params ...")
    out = src.substitute(params)
    # ... and write to the config file
    logging.debug("Writing on target file ...")
    fconfig.write(out)
    # close files
    ftemplate.close()
    fconfig.close()
    return dest_file

def set_owner(user, filepath):
    logging.debug("chown %s:%s %s", user, user, filepath)
    return os.chown(filepath, pwd.getpwnam(user).pw_uid, 
        grp.getgrnam(user).gr_gid)