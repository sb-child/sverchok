import traceback

import bpy
from bpy.app.handlers import persistent

from sverchok import old_nodes
from sverchok import data_structure
from sverchok.core import upgrade_nodes, upgrade_group

from sverchok.ui import color_def, bgl_callback_nodeview, bgl_callback_3dview


_state = {'frame': None}

def sverchok_trees():
    for ng in bpy.data.node_groups:
        if ng.bl_idname == 'SverchCustomTreeType':
            yield ng


def has_frame_changed(scene):
    last_frame = _state['frame']
    _state['frame'] = scene.frame_current
    return not last_frame == scene.frame_current


@persistent
def sv_update_handler(scene):
    """
    Update sverchok node groups on frame change events.
    """
    if not has_frame_changed(scene):
        return
    
    for ng in sverchok_trees():
        try:
            # print('sv_update_handler')
            ng.process_ani()
        except Exception as e:
            print('Failed to update:', str(e)) #name,

    scene.update()


@persistent
def sv_scene_handler(scene):
    """
    Avoid using this.
    Update sverchok node groups on scene update events.
    Not used yet.
    """
    # print('sv_scene_handler')
    for ng in sverchok_trees():
        try:
            ng.process_ani()
        except Exception as e:
            print('Failed to update:', ng, str(e))


@persistent
def sv_main_handler(scene):
    """
    Main Sverchok handler for updating node tree upon editor changes
    """
    for ng in sverchok_trees():
        # print("Scene handler looking at tree {}".format(ng.name))
        if ng.has_changed:
            print('depsgraph_update_pre called - ng.has_changed -> ')
            # print('sv_main_handler')
            # print("Edit detected in {}".format(ng.name))
            ng.process()


@persistent
def sv_clean(scene):
    """
    Cleanup callbacks, clean dicts.
    """
    bgl_callback_nodeview.callback_disable_all()
    bgl_callback_3dview.callback_disable_all()

    data_structure.sv_Vars = {}
    data_structure.temp_handle = {}

@persistent
def sv_undo(scene):
    """
    this is to handle any number of undo related events. 
    """

    # undo doesn't appear granular to the point of being able
    # to query the undo event that triggered this handler.
    # doing this is about the simplest approach. 
    sv_clean(scene)
    sv_scene_handler(scene)


@persistent
def sv_post_load(scene):
    """
    Upgrade nodes, apply preferences and do an update.
    """

    for monad in (ng for ng in bpy.data.node_groups if ng.bl_idname == 'SverchGroupTreeType'):
        if monad.input_node and monad.output_node:
            monad.update_cls()
        else:
            upgrade_group.upgrade_group(monad)

    sv_types = {'SverchCustomTreeType', 'SverchGroupTreeType'}
    sv_trees = list(ng for ng in bpy.data.node_groups if ng.bl_idname in sv_types and ng.nodes)
    for ng in sv_trees:
        ng.freeze(True)
        try:
            old_nodes.load_old(ng)
        except:
            traceback.print_exc()
        ng.freeze(True)
        try:
            upgrade_nodes.upgrade_nodes(ng)
        except:
            traceback.print_exc()
        ng.unfreeze(True)

    addon_name = data_structure.SVERCHOK_NAME
    addon = bpy.context.preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        pref = addon.preferences
        if pref.apply_theme_on_open:
            color_def.apply_theme()

    for ng in sv_trees:
        if ng.bl_idname == 'SverchCustomTreeType' and ng.nodes:
            ng.update()


def set_frame_change(mode):
    post = bpy.app.handlers.frame_change_post
    pre = bpy.app.handlers.frame_change_pre

    # scene = bpy.app.handlers.scene_update_post
    # remove all
    if sv_update_handler in post:
        post.remove(sv_update_handler)
    if sv_update_handler in pre:
        pre.remove(sv_update_handler)
    #if sv_scene_handler in scene:
    #    scene.remove(sv_scene_handler)

    # apply the right one
    if mode == "POST":
        post.append(sv_update_handler)
    elif mode == "PRE":
        pre.append(sv_update_handler)


def register():
    bpy.app.handlers.undo_pre.append(sv_undo)
    bpy.app.handlers.load_pre.append(sv_clean)
    bpy.app.handlers.load_post.append(sv_post_load)
    bpy.app.handlers.depsgraph_update_pre.append(sv_main_handler)

    data_structure.setup_init()
    addon_name = data_structure.SVERCHOK_NAME
    addon = bpy.context.preferences.addons.get(addon_name)
    if addon and hasattr(addon, "preferences"):
        set_frame_change(addon.preferences.frame_change_mode)
    else:
        print("Couldn't setup Sverchok frame change handler")


def unregister():
    bpy.app.handlers.load_pre.remove(sv_clean)
    bpy.app.handlers.load_post.remove(sv_post_load)
    bpy.app.handlers.depsgraph_update_pre.remove(sv_main_handler)
    bpy.app.handlers.undo_pre.remove(sv_undo)
    set_frame_change(None)
