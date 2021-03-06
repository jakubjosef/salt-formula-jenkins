import logging
logger = logging.getLogger(__name__)

add_view_groovy = """\
view = Jenkins.instance.getView("{view_name}")
if(view){{
  if(view.getClass().getName().equals("hudson.model.ListView")){{
    include_regex="{include_regex}"
    if(include_regex != "" && !view.getIncludeRegex().equals(include_regex)){{
        view.setIncludeRegex(include_regex)
        print("ADDED/CHANGED")
    }}else{{
        print("EXISTS")
    }}
  }}else{{
    print("EXISTS")
  }}
}}else{{
  try{{
    {view_def}
    Jenkins.instance.addView(view)
    print("ADDED/CHANGED")
  }}catch(Exception e){{
    print("FAILED")
  }}
}}
""" # noqa

remove_view_groovy = """\
view = Jenkins.instance.getView("{view_name}")
if(view){{
  try{{
    Jenkins.instance.deleteView(view)
    print("REMOVED")
  }}catch(Exception e){{
    print("FAILED")
  }}
}}else{{
  print("NOT PRESENT")
}}
""" # noqa


def present(name, type="ListView", **kwargs):
    """
    Jenkins view present state method

    :param name: view name
    :param type: view type (default ListView)
    :returns: salt-specified state dict
    """
    return _plugin_call(name, type, add_view_groovy, ["ADDED/CHANGED", "EXISTS"], **kwargs)


def absent(name, **kwargs):
    """
    Jenkins view absent state method

    :param name: view name
    :returns: salt-specified state dict
    """
    return _plugin_call(name, None, remove_view_groovy, ["REMOVED", "NOT PRESENT"], **kwargs)


def _plugin_call(name, type, template, success_msgs, **kwargs):
    test = __opts__['test']  # noqa
    ret = {
        'name': name,
        'changes': {},
        'result': False,
        'comment': '',
    }
    result = False
    if test:
        status = success_msgs[0]
        ret['changes'][name] = status
        ret['comment'] = 'Jenkins view %s %s' % (name, status.lower())
    else:
        view_def = "view = new {}(\"{}\")".format(type, name)
        # handle view specific params
        include_regex = kwargs.get('include_regex')
        if type == "ListView":
            if include_regex:
                view_def += "\nview.setIncludeRegex(\"{}\")".format(include_regex)

        call_result = __salt__['jenkins_common.call_groovy_script'](
            template, {"view_def": view_def, "view_name": name, "type": type if type else "", "include_regex": include_regex if include_regex else ""})
        if call_result["code"] == 200 and call_result["msg"] in success_msgs:
            status = call_result["msg"]
            if status == success_msgs[0]:
                ret['changes'][name] = status
            ret['comment'] = 'Jenkins view %s %s' % (name, status.lower())
            result = True
        else:
            status = 'FAILED'
            logger.error(
                "Jenkins view API call failure: %s", call_result["msg"])
            ret['comment'] = 'Jenkins view API call failure: %s' % (call_result[
                                                                           "msg"])
    ret['result'] = None if test else result
    return ret
