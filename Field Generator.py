import bpy
from math import *
import numpy as np
import mathutils as mathutils
from bpy.props import (IntProperty, StringProperty, BoolProperty,IntProperty,FloatProperty,FloatVectorProperty,EnumProperty,PointerProperty)
from bpy.types import (Panel,Operator,AddonPreferences,PropertyGroup)
from scipy.integrate import odeint
from colour import Color


def sigmoid(x):
  return 1 / (1 + exp(-x))

						#DEFINE THE FIELD HERE
def vectorfield(w, t):
		x,y,z = w
		#f = [bpy.context.scene.my_props.P, bpy.context.scene.my_props.Q, bpy.context.scene.my_props.R]
		f=[x,y,z]
		return f

obj = bpy.context.selected_objects[0]
startFrame=bpy.context.scene.my_props.startFrame #this throws error please check
"""
bpy.context.scene.frame_set(startFrame)     #switch to the startFrame (you get it from the IntProperty)
initpos = obj.location      
x0 = initpos[0]
y0 = initpos[1]
z0 = initpos[2]
"""
x0=1
y0=1
z0=1

abserr = 1.0e-8
relerr = 1.0e-6
stoptime = bpy.context.scene.my_props.endFrame
numpoints = 250
time = [stoptime * float(i) / (numpoints - 1) for i in range(numpoints)]
w0 = [x0, y0, z0]

wsol = odeint(vectorfield, w0, time, 
			  atol=abserr, rtol=relerr)


def fieldFunction(pos):
	fps = bpy.context.scene.render.fps
	frame = bpy.context.scene.frame_current
	startFrame = bpy.context.scene.my_props.startFrame
	x = [w[0] for w in wsol] #wsol is a list of lists, with each index containing a coordinate
	y = [w[1] for w in wsol] #hence I've supposedly seperated out the x, y and z components
	z = [w[2] for w in wsol]     
	return np.array([x,y,z])

#-----------------------------------------------------------

def generateGrid():
	dim = bpy.context.scene.my_props.CountProp
	
	spacing = bpy.context.scene.my_props.SpacingProp
	maxScale = bpy.context.scene.my_props.maxScale

	obj = bpy.context.selected_objects[0]

	parent_coll = bpy.context.selected_objects[0].users_collection[0]
	coll = bpy.data.collections.new("Grid")
	parent_coll.children.link(coll)
	samples=np.arange(-(dim-1)*spacing/2,(dim)*spacing/2, spacing, int)
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


	#bpy.app.driver_namespace['getRotation'] = getRotation
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

"""

#--------COLOR_LOGIC---------------
#absolute agony XDXDXD
def hex_to_RGB(hex):
  return [int(hex[i:i+2], 16) for i in range(1,6,2)]

def RGB_to_hex(RGB):
  RGB = [int(x) for x in RGB]
  return "#"+"".join(["0{0:x}".format(v) if v < 16 else
            "{0:x}".format(v) for v in RGB])

def color_dict(gradient):
  return [[RGB[0], RGB[1], RGB[2]] for RGB in gradient]

def linear_gradient(start_hex="#1C758A", finish_hex="#F7A1A3", n=100):
  s = hex_to_RGB(start_hex)
  f = hex_to_RGB(finish_hex)

  RGB_list = [s]

  for t in range(1, n):
    curr_vector = [
      int(s[j] + (float(t)/(n-1))*(f[j]-s[j]))
      for j in range(3)
    ]

    RGB_list.append(curr_vector)

  return color_dict(RGB_list)

colors=linear_gradient()
#print(colors)

def rgb_to_cmyk(r, g, b):
    if (r, g, b) == (0, 0, 0):
        # black
        return 0, 0, 0, 100

    # rgb [0,255] -> cmy [0,1]
    c = 1 - r / 255
    m = 1 - g / 255
    y = 1 - b / 255

    # extract out k [0, 1]
    min_cmy = min(c, m, y)
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    return [c * 100, m * 100, y * 100, k * 100]
#----------------ignore till this(nevermind ignore the color BS)-----------

CMYK_colors= [list(rgb_to_cmyk(*w)) for w in colors ] #a list of cmyk lists
#print(CMYK_colors)

def getColor(norm):
	colornorm=int(norm)
	return CMYK_colors[1000*colornorm] #assuming maxScale is 0.5 for now. 100 samples in color, and hence 200

"""

def simulate(obj):
	startFrame = bpy.context.scene.my_props.startFrame
	endFrame = bpy.context.scene.my_props.endFrame
	x = [w[0] for w in wsol]
	y = [w[1] for w in wsol]
	z = [w[2] for w in wsol]    
	for i in range(endFrame-startFrame+1):
		frame = i+startFrame
		bpy.context.scene.frame_set(frame)
		pos = (x[i], y[i], z[i])    #the position is taken from wsol, please improvise this code, I've unnecessarily, unpacked wsol again 

		obj.keyframe_insert("location", frame=frame)
		if i == 0:
			fc = [0,0,0]
			for j in range(3):
				fc[j] = obj.animation_data.action.fcurves.find("location", index=j)
			k = len(fc[0].keyframe_points)-1

		for j in range(3):
			fc[j].keyframe_points[k+i].co[1] = pos[j]
			print(fc[j].keyframe_points[k+i].co[1])

#-------------------------CLASSES--------------------------

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

class FIELD_OT_update_field_equation(bpy.types.Operator):
	bl_idname = "myops.field_update_field_equation"
	bl_label = "use this to update drivers"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self,context):
		#bpy.app.driver_namespace['getScale'] = getScale
		#bpy.app.driver_namespace['getRotation'] = getRotation
		bpy.app.driver_namespace['getObjID'] = getObjID
		frame = bpy.context.scene.frame_current
		bpy.context.scene.frame_set(frame+1)
		bpy.context.scene.frame_set(frame)
		return {'FINISHED'}

#---------------------------------------UI

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
		default = 0.5,
		min=0.0,
		max=100.0,
		soft_min=0.0,
		soft_max=100.0,
		unit='NONE'
		)
	minScale  : FloatProperty(
		name = "minScale",
		description = "Scale for which the arrow is green",
		default = 0.05,
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
		layout.prop(rd, "scaleMultiplier", text = "Scale Multiplier")
		layout.prop(rd, "maxScale", text = "Max scale")
		layout.prop(rd, "minScale", text = "Min scale")
		layout.prop(rd, "P", text = "P")
		layout.prop(rd, "Q", text = "Q")
		layout.prop(rd, "R", text = "R")
		layout.operator("myops.field_generate_grid", text = "Create Grid")

		col = layout.column()
		col.prop(rd, "startFrame", text = "start")
		col.prop(rd, "endFrame", text = "end")
		layout.operator("myops.field_simulate", text = "Bake")
		layout.operator("myops.field_update_field_equation", text = "Update Drivers")


# ----------------------- REGISTER ---------------------

classes = (
	MySettings,
	UI_PT_class,
	FIELD_OT_generate_grid,
	FIELD_OT_simulate,
	FIELD_OT_update_field_equation,
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
