#####################
#This code is taken from https://github.com/samwyse/sspp/blob/master/__init__.py
#####################

import os
from glob import glob
from keyword import iskeyword
from os.path import dirname, join, split, splitext

basedir = dirname(__file__)

__all__ = []
#for name in glob(join(basedir, '*.py')):
cwd = os.getcwd()+"/plugins"
for name in filter(os.path.isdir, os.listdir(cwd)):
    print 'Name: ',name
    directory = cwd + "/" + name
    module = name
    
    #module = splitext(split(name)[-1])[0]
    #print 'Module: ', module
    if not module.startswith('_') and not iskeyword(module):
        try:
            __import__(__name__+'.'+module) #TODO need to be able to check if the plug in has the required methods before importing
        except:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning('Ignoring exception while loading the %r plug-in.', module)
        else:
            __all__.append(module)
__all__.sort()
