import bpy
import math
from bpy.props import (IntProperty, StringProperty, BoolProperty,IntProperty,FloatProperty,FloatVectorProperty,EnumProperty,PointerProperty)
from bpy.types import (Panel,Operator,AddonPreferences,PropertyGroup)

def generateGrid():
    dim = bpy.context.scene.my_props.CountProp
    spacing = 1
    ctrl = bpy.data.objects["CTRL"]     #the control object
    maxScale = 0.2

    obj = bpy.context.selected_objects[0]

    parent_coll = bpy.context.selected_objects[0].users_collection[0]
    coll = bpy.data.collections.new("Grid")
    parent_coll.children.link(coll)
    for i in range(dim):
        for j in range(dim):
            for k in range(dim):
                new_obj = obj.copy()
                #new_obj.data = obj.data.copy()
                new_obj.animation_data_clear()
                coll.objects.link(new_obj)
                new_obj.location = ((i-dim/2)*spacing, (j-dim/2)*spacing, (k-dim/2)*spacing)  #define arrows positions (here they are centered on the world origin)

                #add drivers on the scale
                for t in range(3):
                    driv = new_obj.driver_add("scale", t).driver
                    driv.type = 'SCRIPTED'
                    driv.use_self = True

                    driv.expression = "getScale(self)"
    bpy.app.driver_namespace['getScale'] = getScale

def getScale(obj):
    scaleMultiplier = bpy.context.scene.my_props.scaleMultiplier
    versors = fieldFunction(obj.location)
    scale = 0
    for i in range(3):
        scale += versors[i]**2
    return (scale**0.5)*scaleMultiplier

def getDistance(ctrl, obj):
    sum = 0
    for i in range(3):
        sum += (ctrl.location[i] - obj.location[i])**2
    return sum**0.5

                        #DEFINE THE FIELD HERE
def fieldFunction(pos):
    x = 0
    y = 1
    z = 0
    return [x,y,z]

def solveDifferential(frame):    #returns the position for each frame
    fps = bpy.context.scene.render.fps
    startFrame = bpy.context.scene.my_props.startFrame
    t = (frame-startFrame)/fps
    print("time = "+str(t))
    x = 0
    y = (t**2)/2        #if initial condition --> y(0) = 0
    z = 0
    print(str([x,y,z]))
    return [x,y,z]

def simulate(obj):
    startFrame = bpy.context.scene.my_props.startFrame
    endFrame = bpy.context.scene.my_props.endFrame
    for i in range(endFrame-startFrame+1):
        frame = i+startFrame
        bpy.context.scene.frame_set(frame)
        pos = solveDifferential(frame)

        obj.keyframe_insert("location", frame=frame)
        if i == 0:
            fc = [0,0,0]
            for j in range(3):
                fc[j] = obj.animation_data.action.fcurves.find("location", index=j)
            k = len(fc[0].keyframe_points)-1

        for j in range(3):
            fc[j].keyframe_points[k+i].co[1] = pos[j]
            print(fc[j].keyframe_points[k+i].co[1])

#-------------------------CLASSES

class FIELD_OT_generate_grid(bpy.types.Operator):
    bl_idname = "myops.field_generate_grid"
    bl_label = "Add Field Grid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        generateGrid()
        return {'FINISHED'}

class FIELD_OT_simulate(bpy.types.Operator):
    bl_idname = "myops.field_simulate"
    bl_label = "simulate Field Dynamics"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self,context):
        for obj in bpy.context.selected_objects:
            simulate(obj)
        return {'FINISHED'}

#---------------------------------------UI

class MySettings(PropertyGroup):
    CountProp : IntProperty(
        name = "Count",
        description = "number of arrows on an edge",
        default = 10,
        min=0,
        max=100
        )
    SpacingProp  : IntProperty(
        name = "Spacing",
        description = "",
        default = 1,
        min=0,
        max=10000
        )
    startFrame  : IntProperty(
        name = "start Frame",
        description = "",
        default = 0,
        min=0,
        max=10000
        )
    endFrame  : IntProperty(
        name = "end Frame",
        description = "",
        default = 10,
        min=0,
        max=10000
        )
    scaleMultiplier  : FloatProperty(
        name = "scale Multiplier",
        description = "",
        default = 1,
        min=0.0,
        max=10000.0,
        soft_min=0.0,
        soft_max=10000.0,
        step=1,
        precision=0,
        unit='NONE'
        )


class UI_PT_class(bpy.types.Panel):
    """Creates a Panel"""
    bl_label = "Field"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Field"
    bl_context = "objectmode"

    @classmethod
    def poll(self,context):
        return True

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        rd = scene.my_props

        layout.prop(rd, "CountProp", text = "Count")
        layout.prop(rd, "SpacingProp", text = "Spacing")
        layout.operator("myops.field_generate_grid", text = "Create Grid")

        col = layout.column()
        col.prop(rd, "startFrame", text = "start")
        col.prop(rd, "endFrame", text = "end")
        col.prop(rd, "scaleMultiplier", text = "Scale Multiplier")
        layout.operator("myops.field_simulate", text = "Bake")


# ----------------------- REGISTER ---------------------

classes = (
    MySettings,
    UI_PT_class,
    FIELD_OT_generate_grid,
    FIELD_OT_simulate,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.my_props = PointerProperty(type=MySettings)



def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_props


if __name__ == "__main__":
    register()
