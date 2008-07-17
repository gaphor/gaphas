"""
Some extra picklers needed to gracefully dump and load a canvas.
"""


import new, copy_reg


# Allow instancemethod to be pickled:

def construct_instancemethod(funcname, self, clazz):
    func = getattr(clazz, funcname)
    return new.instancemethod(func, self, clazz)

def reduce_instancemethod(im):
    return save_construct_instancemethod, (im.im_func.__name__, im.im_self, im.im_class)

copy_reg.pickle(new.instancemethod, reduce_instancemethod, construct_instancemethod)


# vim:sw=4:et:ai
