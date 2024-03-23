from operations.local.logging import baton_log


def lemr_check_R_object_in_python(rObj):
    """This function's purpose is to see what R objects get converted/twisted into as Python
    objects in order to aid debugging mysterious issues that happen at the boundary between
    R and Python. I should have created this months ago.
    """
    baton_log.info("rObj:")
    baton_log.info(rObj)
    baton_log.info("rObj type:")
    baton_log.info(type(rObj))
    try:
        baton_log.info("rObj len:")
        baton_log.info(len(rObj))
    except:
        baton_log.info("rObj has no __len__ method.")
    try:
        baton_log.info("rObj str:")
        baton_log.info(str(rObj))
    except:
        baton_log.info("rObj has no __str__ or __repr__ method.")
    try:
        baton_log.info("rObj[0] type:")
        baton_log.info(type(rObj[0]))
    except:
        baton_log.info("rObj is not indexable.")
