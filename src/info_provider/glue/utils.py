import grp
import logging
import os
import pwd
import string

def create_file_from_template(dest_file, template_file, params):
    logging.debug("Creating file %s from template %s with parameters %s", dest_file, template_file, params)
    # open files
    ftemplate = open(template_file)
    fconfig = open(dest_file, "w")
    # read from template ...
    logging.debug("Reading from template ...")
    src = string.Template(ftemplate.read())
    # ... substitute values ...       
    logging.debug("Substitute parameters ...")
    out = src.substitute(params)
    # ... and write to the configuration file
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

def as_gigabytes(numbytes):
    return int(round(1.0 * numbytes / 1000000000))

def as_kilobytes(numbytes):
    return int(round(1.0 * numbytes / 1000))
