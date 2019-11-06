import bpy
from math import *
import numpy as np
import mathutils as mathutils
import ast

from sympy.abc import x, y, z
from bpy.props import (IntProperty, StringProperty, BoolProperty,IntProperty,FloatProperty,FloatVectorProperty,EnumProperty,PointerProperty)
from bpy.types import (Panel,Operator,AddonPreferences,PropertyGroup)
from scipy.integrate import odeint
from colour import Color
from sympy.physics.vector import ReferenceFrame
from sympy.physics.vector import curl

x0=0
y0=0
z0=0

def sigmoid(x):
  return 1 / (1 + exp(-x))


                        #DEFINE THE FIELD HERE


def vectorfield(w, t):
        x,y,z = w
        P=bpy.context.scene.my_props.P
        Q= bpy.context.scene.my_props.Q
        R= bpy.context.scene.my_props.R
		#(isinstance(P, str))
        #f = [bpy.context.scene.my_props.P, bpy.context.scene.my_props.Q, bpy.context.scene.my_props.R]
        f=[eval(P), eval(Q), eval(R)]
		#f=[x,y,z]
        return f


obj = bpy.context.selected_objects[0]


def fieldFunction(pos):
    fps = bpy.context.scene.render.fps
    frame = bpy.context.scene.frame_current
    startFrame = bpy.context.scene.my_props.startFrame
    x = [w[0] for w in wsol] #wsol is a list of lists, with each index containing a coordinate
    y = [w[1] for w in wsol] #hence I've supposedly seperated out the x, y and z components
    z = [w[2] for w in wsol]     
    return np.array([x,y,z])

#-----------------------------------------------------------

scale_list=[]

MaxScale=0
MinScale=0

def generateGrid():
	dim = bpy.context.scene.my_props.CountProp
	spacing = bpy.context.scene.my_props.SpacingProp
	samples=np.arange(-(dim-1)*spacing/2,(dim)*spacing/2, spacing, int)
    maxScale = bpy.context.scene.my_props.maxScale

    obj = bpy.context.selected_objects[0]

    parent_coll = bpy.context.selected_objects[0].users_collection[0]
    coll = bpy.data.collections.new("Grid")
    parent_coll.children.link(coll)
    
    global location
    location=[]
    for i in samples:
        for j in samples:
            for k in samples:
                new_obj = obj.copy()
                new_obj.animation_data_clear()
                coll.objects.link(new_obj)
                new_obj.location = (i,j,k)  #define arrows positions (here they are centered on the world origin)
                norm = getScale(new_obj.location)
				scale_list.append(norm)
                new_obj.scale = [norm,norm,norm]
                getRotation(new_obj.location)
                new_obj.rotation_mode = 'QUATERNION'
                DirVec=getRotation(new_obj.location)
                new_obj.rotation_quaternion = DirVec.to_track_quat('Z','Y')

                #add drivers on the Object ID (for the color)
                driv = new_obj.driver_add("pass_index").driver
                driv.type = 'SCRIPTED'
                driv.use_self = True
				driv.expression = "getObjID(self)"


	global MaxScale,MinScale
	MaxScale = max(scale_list, default=0)
	MinScale = min(filter(lambda i: i > 0.00, scale_list)) 
    #bpy.app.driver_namespace['getCurlMag'] = getCurlMag
    bpy.app.driver_namespace['getObjID'] = getObjID


def getScale(pos):
    RHSP = bpy.context.scene.my_props.P 
    RHSQ = bpy.context.scene.my_props.Q 
    RHSR = bpy.context.scene.my_props.R
    scaleMultiplier = bpy.context.scene.my_props.scaleMultiplier
    x = pos[0]
    y = pos[1]                 
    z = pos[2]
    P= (eval(RHSP, {'x': x, 'y': y, 'z': z }))
    Q= (eval(RHSQ, {'x': x, 'y': y, 'z': z }))
    R= (eval(RHSR, {'x': x, 'y': y, 'z': z }))
    vector=np.array([P,Q,R])
	
    actual_norm=(np.dot(vector, vector))**.5
    display_norm =sigmoid(actual_norm)*scaleMultiplier
	#scale_list.append(display_norm)
    if actual_norm==0:
        return 0
    else:
        return display_norm
    #return actual_norm*scaleMultiplier #for now


def getRotation(pos):
    RHSP = bpy.context.scene.my_props.P 
    RHSQ = bpy.context.scene.my_props.Q 
    RHSR = bpy.context.scene.my_props.R

    x = pos[0]
    y = pos[1]                 
    z = pos[2]

    P= (eval(RHSP, {'x': x, 'y': y, 'z': z }))
    Q= (eval(RHSQ, {'x': x, 'y': y, 'z': z }))
    R= (eval(RHSR, {'x': x, 'y': y, 'z': z }))

    vector=(P,Q,R)
    DirectionVector = mathutils.Vector(vector) 
    return DirectionVector


def getObjID(obj):
    minScale = bpy.context.scene.my_props.minScale
    maxScale = bpy.context.scene.my_props.maxScale

    scale = getScale(obj.location)

    ID = (scale-minScale)/(maxScale-minScale)*100+100
    return ID


def getCurlAxis(obj, pos):
    L = bpy.context.scene.my_props.P 
    M = bpy.context.scene.my_props.Q 
    N = bpy.context.scene.my_props.R


    R = ReferenceFrame('R')
    H =L* R.x + M * R.y + N * R.z
    #print(H)
    F=H.subs([(x, R[0]), (y, R[1]), (z, R[2])])
    G = curl(F, R)  
    a = pos[0]
    b = pos[1]                 
    c = pos[2]
	if G==0:
		pass
	else:
    	lis = list(G.args[0][0].subs([(R[0], a), (R[1], b), (R[2], c)]))
		u,v,w=lis[:]
    	vector=(u,v,w)
    	DirectionVector = mathutils.Vector(vector)
    	obj.rotation_mode = 'QUATERNION'
    	obj.rotation_quaternion = DirectionVector.to_track_quat('Z','Y')


def getCurlMag(pos):
    L = bpy.context.scene.my_props.P 
    M = bpy.context.scene.my_props.Q 
    N = bpy.context.scene.my_props.R
    #pos=obj.location
    R = ReferenceFrame('R')
    H = L* R.x +M * R.y + N * R.z
    F=H.subs([(x, R[0]), (y, R[1]), (z, R[2])])
    G = curl(F, R)  
    p=pos[0]
    q=pos[1]
    r=pos[2]
	if G==0:
		return 0
	else:
    	lis=list(G.args[0][0].subs([(R[0], p), (R[1], q), (R[2], r)]))

    	u,v,w=lis[:]
    	curl_vec=np.array([u,v,w])
    	mag=(np.dot(curl_vec,curl_vec))**.5
    	frame = bpy.context.scene.frame_current
    	fps = bpy.context.scene.render.fps
    	startFrame = bpy.context.scene.my_props.startFrame
    	t = (frame-startFrame)/fps 
    	theta= mag*(t**2)

    	return theta


def simulate(obj,solution):
    wsol=solution
    startFrame = bpy.context.scene.my_props.startFrame
    endFrame = bpy.context.scene.my_props.endFrame
    frame = bpy.context.scene.frame_current

    x = [w[0] for w in wsol]
    y = [w[1] for w in wsol]
    z = [w[2] for w in wsol]    
    for i in range(endFrame-startFrame+1):
        frame = i+startFrame
        bpy.context.scene.frame_set(frame)
        pos = (x[i], y[i], z[i])    #the position is taken from wsol, please improvise this code, I've unnecessarily, unpacked wsol again 

        
        if frame==startFrame:
            bpy.ops.object.empty_add(type="PLAIN_AXES", location=obj.location)
            parobj = bpy.context.object
            #parobj.location=obj.location
            obj.parent= parobj
            #print(parobj.name)
            
        getCurlAxis(parobj,parobj.location)
        parobj.keyframe_insert("location", frame=frame)
        parobj.keyframe_insert("rotation_quaternion", frame=frame)
        if i == 0:
            fc = [0,0,0]
            for j in range(3):
                fc[j] = parobj.animation_data.action.fcurves.find("location", index=j)
            k = len(fc[0].keyframe_points)-1
        for j in range(3):
            fc[j].keyframe_points[k+i].co[1] = pos[j]
            #print(fc[j].keyframe_points[k+i].co[1])
        #------------HERE-------------
        theta=getCurlMag(obj.location)
        obj.rotation_euler=(0,0,theta)
        #print("------ROOKS LIVES HERE------------")
        #print(theta)
        obj.keyframe_insert("rotation_euler",2, frame=frame)


#-------------------------CLASSES--------------------------

class FIELD_OT_generate_grid(bpy.types.Operator):
    bl_idname = "myops.field_generate_grid"
    bl_label = "Add Field Grid"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description= "Create the vector field"
    def execute(self,context):
        generateGrid()
        return {'FINISHED'}

class FIELD_OT_simulate(bpy.types.Operator):
    bl_idname = "myops.field_simulate"
    bl_label = "simulate Field Dynamics"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description= "Simulate object's motion"
    def execute(self,context):
        #add driver on the rotation of the object in field.
        for obj in bpy.context.selected_objects:
            startFrame = bpy.context.scene.my_props.startFrame
            endFrame = bpy.context.scene.my_props.endFrame
            frame = bpy.context.scene.frame_current

            bpy.context.scene.frame_set(startFrame)     #switch to the startFrame (you get it from the IntProperty)
            initpos = obj.location      
            abserr = 1.0e-8
            relerr = 1.0e-6
            stoptime=endFrame
            numpoints = 250
            time = [stoptime * float(i) / (numpoints - 1) for i in range(numpoints)]
            w0 = [x0, y0, z0]
            wsol = odeint(vectorfield, w0, time, 
                            atol=abserr, rtol=relerr)

            simulate(obj,wsol)
        return {'FINISHED'}

class FIELD_OT_update_field_equation(bpy.types.Operator):
    bl_idname = "myops.field_update_field_equation"
    bl_label = "use this to update drivers"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description= "Update the desired colour range"

    def execute(self,context):
        #bpy.app.driver_namespace['getScale'] = getScale
        #bpy.app.driver_namespace['getRotation'] = getRotation
        bpy.app.driver_namespace['getObjID'] = getObjID
        frame = bpy.context.scene.frame_current
        bpy.context.scene.frame_set(frame+1)
        bpy.context.scene.frame_set(frame)
        return {'FINISHED'}

class FIELD_OT_reset_settings(bpy.types.Operator):
    bl_idname = "myops.reset_settings"
    bl_label = "use this reset settings"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description= "Reset settings to default"
    def execute(self,context):
		bpy.context.scene.my_props.CountProp=5
		bpy.context.scene.my_props.SpacingProp=2
		bpy.context.scene.my_props.startFrame=0
		bpy.context.scene.my_props.endFrame=20
		bpy.context.scene.my_props.scaleMultiplier=0.1
		bpy.context.scene.my_props.maxScale=MaxScale
		bpy.context.scene.my_props.minScale=MinScale
		return {'FINISHED'}

class FIELD_OT_set_initial_conditions(bpy.types.Operator):
    bl_idname = "myops.set_initial_conditions"
    bl_label = "use this to set initial conditions"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description= "Set Initial Conditions, before baking"
    def execute(self,context):
		global x0,y0,z0
		x0 = bpy.context.scene.my_props.x0
		y0 = bpy.context.scene.my_props.y0
		z0 = bpy.context.scene.my_props.z0
		return {'FINISHED'}

class FIELD_OT_auto_scale(bpy.types.Operator):
    bl_idname = "myops.auto_scale"
    bl_label = "use this to auto scale"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description= "Set recommended scale range"

    def execute(self,context):
		bpy.context.scene.my_props.maxScale=MaxScale
		bpy.context.scene.my_props.minScale=MinScale
		return {'FINISHED'}

#---------------------------UI---------------------------------

class MySettings(PropertyGroup):
    CountProp : IntProperty(
        name = "Count",
        description = "number of arrows on an edge",
        default = 5,
        min=0,
        max=100
        )
    SpacingProp  : IntProperty(
        name = "Spacing",
        description = "",
        default = 2,
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
        default = 0.1,
        min=0.0,
        max=10000.0,
        soft_min=0.0,
        soft_max=10000.0,
        unit='NONE'
        )
    maxScale  : FloatProperty(
        name = "maxScale",
        description = "Scale for which the arrow is red",
        default = MaxScale,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=100.0,
        unit='NONE'
        )

    minScale  : FloatProperty(
        name = "minScale",
        description = "Scale for which the arrow is green",
        default = MinScale,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=100.0,
        unit='NONE'
        )
    P : StringProperty(
        name = "P",
        description = "x component of the vector field",
        default = 'x',

        )
    Q  : StringProperty(
        name = "Q",
        description = "y component of the vector field",
        default = 'y',

        )
    R  : StringProperty(
        name = "R",
        description = "z component of the vector field",
        default = 'z',
        )
    x0  : FloatProperty(
        name = "x0",
        description = "x coordinate of initial position",
        default = 0,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=100.0,
        unit='NONE'
        )
    y0  : FloatProperty(
        name = "y0",
        description = "y coordinate of initial position",
        default = 0,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=100.0,
        unit='NONE'
        )
    z0  : FloatProperty(
        name = "z0",
        description = "z coordinate of initial position",
        default = 0,
        min=0.0,
        max=100.0,
        soft_min=0.0,
        soft_max=100.0,
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

		layout.label(text="Time:")
		col = layout.column()
        col.prop(rd, "startFrame", text = "start")
        col.prop(rd, "endFrame", text = "end")

		layout.label(text="Scale:")
        layout.prop(rd, "scaleMultiplier", text = "Scale Multiplier")

		layout.label(text="Vector Field:")
        layout.prop(rd, "P", text = "P")
        layout.prop(rd, "Q", text = "Q")
        layout.prop(rd, "R", text = "R")
        layout.operator("myops.field_generate_grid", text = "Create Grid")
        
		layout.label(text="Color Scale Range:")
        layout.prop(rd, "maxScale", text = "Max scale")
        layout.prop(rd, "minScale", text = "Min scale")
        layout.operator("myops.auto_scale", text = "Auto Scale")
        layout.operator("myops.field_update_field_equation", text = "Update Color Scale")


		layout.label(text="Initial Conditions:")
        layout.prop(rd, "x0", text = "x0")
        layout.prop(rd, "y0", text = "y0")
        layout.prop(rd, "z0", text = "z0")
		layout.operator("myops.set_initial_conditions", text = "Set Initial Conditions")



		layout.label(text="General:")
        layout.operator("myops.field_simulate", text = "Bake")
		layout.operator("myops.reset_settings", text = "Reset")



# ----------------------- REGISTER ---------------------

classes = (
    MySettings,
    UI_PT_class,
    FIELD_OT_generate_grid,
    FIELD_OT_simulate,
    FIELD_OT_update_field_equation,
	FIELD_OT_reset_settings,
	FIELD_OT_set_initial_conditions,
    FIELD_OT_auto_scale,
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


