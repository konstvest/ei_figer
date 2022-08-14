# Copyright (c) 2022 konstvest

# This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
import bpy
import bmesh
import copy
from math import sqrt
from mathutils import Quaternion
import copy as cp
import collections

from . utils import subVector, sumVector, CItemGroupContainer, mulVector, sumVector
from . bone import CBone
from . figure import CFigure
from . resfile import ResFile
from . scene_management import CModel
from . animation import CAnimation
from . links import CLink

def model() -> CModel:
    return bpy.context.scene.model

def read_links(lnk_res : ResFile, lnk_name : str):
    active_model : CModel = bpy.types.Scene.model
    err = 0
    with lnk_res.open(lnk_name) as lnk_res:
        data = lnk_res.read()
        lnk = CLink()
        err += lnk.read_lnk(data)
        active_model.links = lnk
    return err

def read_figure(fig_res : ResFile, fig_name : str):
    active_model : CModel = bpy.types.Scene.model
    err = 0
    with fig_res.open(fig_name) as fig_res:
        data = fig_res.read()
        fig = CFigure()
        err += fig.read_fig(fig_name, data)
        active_model.mesh_list.append(fig)
    return err

def read_bone(bon_res : ResFile, bon_name : str):
    active_model : CModel = bpy.types.Scene.model
    err = 0
    with bon_res.open(bon_name) as bon_res:
        data = bon_res.read()
        bon = CBone()
        err += bon.read_bon(bon_name, data)
        active_model.pos_list.append(bon)
    return err

def read_model(resFile : ResFile, model_name):
    err = 0
    with resFile.open(model_name + '.mod') as meshes_container:
        mesh_list_res = ResFile(meshes_container)
        for mesh_name in mesh_list_res.get_filename_list():
            if mesh_name == model_name:
                err += read_links(mesh_list_res, mesh_name)
            else:
                err == read_figure(mesh_list_res, mesh_name)
    return err

def read_bones(resFile : ResFile, model_name):
    err = 0
    #bones container
    with resFile.open(model_name + '.bon') as bone_container:
        bone_list_res = ResFile(bone_container)
        for bone_name in bone_list_res.get_filename_list():
            err += read_bone(bone_list_res, bone_name)
    return err

def read_animations(resFile : ResFile, model_name : str, animation_name : str):
    active_model : CModel = bpy.types.Scene.model
    err = 0
    #animations container
    with resFile.open(model_name + '.anm') as animation_container:
        anm_res_file = ResFile(animation_container)
        with anm_res_file.open(animation_name) as animation_file:
            animation_res = ResFile(animation_file)
            for part_name in animation_res.get_filename_list(): #set of parts
                with animation_res.open(part_name) as part_res:
                    part = part_res.read()
                    anm = CAnimation()
                    anm.read_anm(part_name, part)
                    active_model.anm_list.append(anm)
    return err

def ei2abs_rorations():
    """
    Calculates absolute rotations based on EI values
    """
    active_model : CModel = bpy.types.Scene.model
    lnk = active_model.links.links
    #TODO: check if links correctly (None parent has only 1 obj and other)
    if not active_model.links:
        return 1

    def calc_frames(part : CAnimation):
        nonlocal lnk
        
        if lnk[part.name] is None: #root object
            part.abs_rotation = cp.deepcopy(part.rotations)
        else:
            parent_anm = active_model.animation(lnk[part.name])
            if len(parent_anm.abs_rotation) == 0:
                calc_frames(parent_anm)
            part.abs_rotation = cp.deepcopy(parent_anm.abs_rotation)
            for i in range(len(part.rotations)):
                part.abs_rotation[i].rotate(part.rotations[i])
    
    for part in lnk.keys():
        anm = active_model.animation(part)
        if anm is None:
            print('animation for ' + part + ' not found')
        else:
            calc_frames(anm)

    return 0

def abs2ei_rotations():
    active_model : CModel = bpy.types.Scene.model
    lnk = active_model.links.links

    def calc_frames(part : CAnimation):
        nonlocal lnk
        
        if lnk[part.name] is None:
            return
        
        for i in range(len(part.rotations)):
            parent_rot = cp.deepcopy(active_model.animation(lnk[part.name]).abs_rotation[i])
            parent_rot_invert = parent_rot.inverted().copy()
            parent_rot_invert.rotate(part.abs_rotation[i])
            part.rotations[i] = parent_rot_invert.copy()
    
    for part in lnk.keys():
        anm = active_model.animation(part)
        if anm is None:
            print('animation for ' + part + ' not found')
        else:
            calc_frames(anm)

def abs2Blender_rotations():
    """
    Calculates rotation from absolute to Blender
    """
    active_model : CModel = bpy.types.Scene.model
    lnk = active_model.links.links

    def calc_frames(part : CAnimation):
        nonlocal lnk
        
        if lnk[part.name] is None:
            return
        
        for i in range(len(part.rotations)):
            parent_rot = cp.deepcopy(active_model.animation(lnk[part.name]).abs_rotation[i])
            parent_rot_invert = parent_rot.inverted().copy()
            child_rot : Quaternion = parent_rot.copy()
            child_rot.rotate(part.rotations[i])
            part.rotations[i] = child_rot.copy()
            part.rotations[i].rotate(parent_rot_invert)
    
    for part in lnk.keys():
        anm = active_model.animation(part)
        if anm is None:
            print('animation for ' + part + ' not found')
        else:
            calc_frames(anm)

def blender2abs_rotations():
    active_model : CModel = bpy.types.Scene.model
    lnk = active_model.links.links
    #TODO: check if links correctly (None parent has only 1 obj and other)
    if not active_model.links:
        return 1

    def calc_frames(part : CAnimation):
        nonlocal lnk
        
        if lnk[part.name] is None: #root object
            part.abs_rotation = cp.deepcopy(part.rotations)
        else:
            parent_anm = active_model.animation(lnk[part.name])
            if len(parent_anm.abs_rotation) == 0:
                calc_frames(parent_anm)
            part.abs_rotation = cp.deepcopy(part.rotations)
            for i in range(len(part.rotations)):
                part.abs_rotation[i].rotate(parent_anm.abs_rotation[i])
    
    for part in lnk.keys():
        anm = active_model.animation(part)
        if anm is None:
            print('animation for ' + part + ' not found')
        else:
            calc_frames(anm)

    return 0

def create_mesh_2(figure:CFigure):
    active_model : CModel = bpy.context.scene.model
    faces = []
    ftemp = [0, 0, 0]
    face_indices_count = figure.header[3] - 2
    for i in range(0, face_indices_count, 3):
        for ind in range(3):
            ftemp[ind] = figure.v_c[figure.indicies[i + ind]][0]
        faces.append([ftemp[0], ftemp[1], ftemp[2]])
    
    container = CItemGroupContainer()
    item_group = container.get_item_group(active_model.name)
    mesh_count = item_group.morph_component_count
    for mesh_num in range(mesh_count):
        name = active_model.morph_comp[mesh_num] + figure.name
        base_mesh = bpy.data.meshes.new(name=name)
        base_obj = bpy.data.objects.new(name, base_mesh)
        collection_name = active_model.morph_collection[mesh_num]
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
        else:
            collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(collection)
        bpy.data.collections[collection_name].objects.link(base_obj)
        base_obj.location = (0, 0, 0)
        base_mesh.from_pydata(figure.verts[mesh_num], [], faces)
        
        
        #TODO: create material
        base_mesh.uv_layers.new(name=bpy.context.scene.model.name)
        for uv_ind in range(figure.header[3]):
            for xy in range(2):
                base_mesh.uv_layers[0].data[uv_ind].uv[xy] = \
                        figure.t_coords[figure.v_c[figure.indicies[uv_ind]][1]][xy]
        base_mesh.update()

def set_pos_2(bone : CBone):
    active_model : CModel = bpy.context.scene.model
    container = CItemGroupContainer()
    item_group = container.get_item_group(bone.name)
    obj_count = item_group.morph_component_count
    
    for obj_num in range(obj_count):
        name = active_model.morph_comp[obj_num] + bone.name
        if name in bpy.data.objects:
            obj = bpy.data.objects[name]
            obj.location = bone.pos[obj_num]
    
    return 0

def create_links_2(link : CLink):
    active_model : CModel = bpy.context.scene.model
    container = CItemGroupContainer()
    for part, parent in link.links.items():
        if parent is None:
            continue
        
        obj_count = container.get_item_group(active_model.name).morph_component_count
        for obj_num in range(obj_count):
            part_name = active_model.morph_comp[obj_num] + part
            parent_name = active_model.morph_comp[obj_num] + parent
            if part_name in bpy.data.objects and parent_name in bpy.data.objects:
                bpy.data.objects[part_name].parent = bpy.data.objects[parent_name]
    
    return 0

def clear_animation_data():
    base_rotation = Quaternion((1, 0, 0, 0))
    bpy.context.scene.frame_set(0)
    model : CModel = bpy.types.Scene.model
    for obj in bpy.data.objects:
        if model.is_morph_name(obj.name):
            continue
        obj.rotation_mode = 'QUATERNION'
        obj.animation_data_clear()
        obj.rotation_quaternion = base_rotation
        if obj.parent is None:
            obj.location = (0, 0, 0)
        obj.shape_key_clear()

    bpy.context.scene.frame_end = 1
    bpy.context.scene.frame_end = 250

def insert_keyframe(sk, f):
    sk.keyframe_insert("value", frame=f-1)
    sk.keyframe_insert("value", frame=f+1)
    sk.value = 1.0
    sk.keyframe_insert("value", frame=f)   

def insert_animation(anm_list : list[CAnimation]):
    err = 0
    clear_animation_data()

    for part in anm_list:
        if part.name not in bpy.data.objects:
            print('object ' + part.name + ' not found in animation list')
            continue

        obj = bpy.data.objects[part.name]
        obj.rotation_mode = 'QUATERNION'
        bpy.context.scene.frame_end = 0
        bpy.context.scene.frame_end = len(part.rotations)-1 #for example, 43 frames from 0 to 42
        for frame in range(len(part.rotations)):
            #rotations
            bpy.context.scene.frame_set(frame) #choose frame
            obj.rotation_quaternion = part.rotations[frame]
            obj.keyframe_insert(data_path='rotation_quaternion', index=-1)
            #positions
            if obj.parent is None: #root
                obj.location = part.translations[frame]
                obj.keyframe_insert(data_path='location', index=-1)
            #morphations
        if len(part.morphations) > 0:
            obj.shape_key_add(name='basis', from_mix=False)
            for frame in range(len(part.morphations)):
                key = obj.shape_key_add(name=str(frame), from_mix=False)
                for i in range(len(part.morphations[frame])):
                    key.data[i].co = sumVector(obj.data.vertices[i].co, part.morphations[frame][i])
                insert_keyframe(key, frame)

    return err

def collect_animations():
    active_model : CModel = bpy.types.Scene.model
    for obj in bpy.data.objects:
        if obj.name[0:2] in bpy.types.Scene.model.morph_comp.values():
            continue #skip morphed objects

        anm = CAnimation()
        anm.name = obj.name
        obj.rotation_mode = 'QUATERNION'
        
        for frame in range(bpy.context.scene.frame_start, bpy.context.scene.frame_end + 1):
            #rotations
            bpy.context.scene.frame_set(frame) #choose frame
            anm.rotations.append(Quaternion(obj.rotation_quaternion))
            #positions
            if obj.parent is None: #root
                anm.translations.append(obj.location.copy())
            
            #morphations
            if not obj.data.shape_keys:
                continue

            if not len(anm.morphations):
                anm.morphations = [[] for _ in range(bpy.context.scene.frame_end - bpy.context.scene.frame_start + 1)]

            #check if 'basis' morph exists
            basis_block = obj.data.shape_keys.key_blocks['basis']
            block = obj.data.shape_keys.key_blocks[str(frame)]
            if block.value != 1.0:
                print(f'{obj.name} incorrect moorph value')
            
            for i in range(len(block.data)):
                #dif = subVector(block.data[i].co, basis_block.data[i].co)
                anm.morphations[frame].append(subVector(block.data[i].co, basis_block.data[i].co))


        active_model.anm_list.append(anm)



def create_hierarchy(links : dict[str, str]):
    '''
    sets parent for objects in lnks
    '''
    for key, value in links.items():
        if value is None:
            continue
        
        if key in bpy.data.objects and value in bpy.data.objects:
            bpy.data.objects[key].parent = bpy.data.objects[value]
        else:
            print(str(key) + ': object not found in scene, but found in links of hierarchy')

def is_model_correct():

    obj_count = CItemGroupContainer().get_item_group(model().name).morph_component_count
    collections = bpy.context.scene.collection.children
    if len(collections) < 0:
        print('scene empty')
        return False

    if collections[0].name != model().morph_collection[0]:
        print('invalid scene name, must be \"' + model().morph_collection[0] + '\"')

    if len(collections) != obj_count:
        print('collection number must correspond Model type count (now: '+ str(obj_count) +')')
        return False

    root_list = []

    for obj in collections[0].objects:
        if obj.type != 'MESH':
            continue
        
        if obj.parent is None:
            root_list.append(obj.name)

        mesh : bpy.types.Mesh = obj.data
        if mesh.uv_layers.active_index < 0:
            print('mesh ' + mesh.name + ' has no active uv layer (UV map)')
            return False
        
        for i in range(obj_count):
            if (model().morph_comp[i] + obj.name) not in collections[i].objects:
                print('cannot find object: ' + model().morph_comp[i] + obj.name)
                return False

    if len(root_list) != 1:
        print('incorrect root objects, must be only one, exist: ' + str(root_list))

    return True

def parts_ordered(links : dict[str, str], links_out : dict[str, str], root):
    '''
    converts hierarchy to ordered list
    '''
    candidates=dict()
    if links[root] is None:
        links_out[root] = None

    for child, parent in links.items():
        if parent is None:
            continue

        if parent == root:
            candidates[child] = parent

    #alphabetical dict sort
    od = collections.OrderedDict(sorted(candidates.items()))
    #len(key) dict sort
    new_d = {}
    for k in sorted(od, key=len):
        new_d[k] = od[k]

    for child, parent in new_d.items():
        links_out[child] = parent
        parts_ordered(links, links_out, child)
    

def collect_links():
    lnk = CLink()
    collections = bpy.context.scene.collection.children

    for obj in collections[0].objects:
        if obj.type != 'MESH':
            continue
        lnk.add(obj.name, obj.parent.name if obj.parent is not None else None)

    lnk_ordered : dict[str, str] = dict()
    parts_ordered(lnk.links, lnk_ordered, lnk.root)
    lnk.links = lnk_ordered
    model().links = lnk

def collect_pos():
    err = 0
    obj_count = CItemGroupContainer().get_item_group(model().name).morph_component_count
    collections = bpy.context.scene.collection.children

    for obj in collections[0].objects:
        if obj.type != 'MESH':
            continue
        bone = CBone()
        for i in range(obj_count):
            #TODO: if object has no this morph comp, use previous components (end-point: base)
            morph_obj = collections[i].objects[model().morph_comp[i] + obj.name]
            bone.pos.append(morph_obj.location[:])
        
        bone.name = obj.name
        if obj_count == 1:
            bone.fillPositions()

        model().pos_list.append(bone)
    return err

def collect_mesh():
    err = 0
    item = CItemGroupContainer().get_item_group(model().name)
    obj_count = item.morph_component_count
    collections = bpy.context.scene.collection.children

    individual_group=['helms', 'second layer', 'arrows', 'weapons', 'armor']

    for obj in collections[0].objects:
        if obj.type != 'MESH':
            continue
        figure = CFigure()
        obj_group = CItemGroupContainer().get_item_group(obj.name)
        if obj_group.type in individual_group:
            figure.header[7] = obj_group.ei_group
            figure.header[8] = obj_group.t_number
        else:
            figure.header[7] = item.ei_group
            figure.header[8] = item.t_number
        for i in range(obj_count):
            #TODO: if object has no this morph comp, use previous components (end-point: base)
            morph_mesh : bpy.types.Mesh = collections[i].objects[model().morph_comp[i] + obj.name].data

            count_vert = 0
            count_norm = 0
            v_restore = 0
            ind_count = 0
            duplicate_vert = 0
            duplicate_ind = [[], []]
            min_m = [0, 0, 0]
            max_m = [0, 0, 0]

            # VERTICES & NORMALS
            for mvert in morph_mesh.vertices:
                same_flag = False
                #collect duplicate vertices
                for same_vert in range(count_vert):
                    if mvert.co == figure.verts[i][same_vert]:
                        same_flag = True
                        if i == 0:
                            duplicate_ind[0].append(same_vert)
                            duplicate_ind[1].append(duplicate_vert)
                if not same_flag:
                    # vertices
                    figure.verts[i].append(tuple(mvert.co))
                    count_vert += 1
                    # normals
                    if i == 0:
                        figure.normals.append(tuple([mvert.normal[0], mvert.normal[1],
                                mvert.normal[2], 1.0]))
                        count_norm += 1
                    # MIN & MAX PREPARE
                    if mvert.index == 0:
                        min_m = copy.copy(mvert.co)
                        max_m = copy.copy(mvert.co)
                    for xyz in range(3):
                        if max_m[xyz] < mvert.co[xyz]: max_m[xyz] = mvert.co[xyz]
                        if min_m[xyz] > mvert.co[xyz]: min_m[xyz] = mvert.co[xyz]
                if i == 0:
                    duplicate_vert += 1
 
            figure.fmin.append(tuple(min_m))
            figure.fmax.append(tuple(max_m))
            # RADIUS
            figure.radius.append(sqrt(
                (max_m[0] - min_m[0]) ** 2 +\
                    (max_m[1] - min_m[1]) ** 2 +\
                    (max_m[2] - min_m[2]) ** 2) / 2)
            # CENTER
            figure.center.append(mulVector(sumVector(min_m, max_m), 0.5))
            if count_vert != 0 and i == 0:
                figure.header[5] = count_vert
                figure.generate_m_c()
            # align vertices
            v_restore = (4 - (count_vert % 4)) % 4 # fill count until %4 will be 0
            for _ in range(v_restore):
                figure.verts[i].append((0.0, 0.0, 0.0))
                count_vert += 1
            
            if i == 0: # ONLY FOR BASE OBJECT
                figure.header[0] = int(count_vert / 4)
                if len(figure.normals) % 4 != 0:
                    for _ in range(4 - len(figure.normals) % 4):
                        figure.normals.append(
                            copy.copy(figure.normals[count_norm - 1]))
                        count_norm += 1
                figure.header[1] = int(len(figure.normals) / 4)
                ind_ar = []
                for mpoly in morph_mesh.polygons:
                    # INDICES PREPARE
                    for poly_vrt in mpoly.vertices:
                        same_flag = False
                        # remove duplicate indices
                        for dp_vrt in range(len(duplicate_ind[1])):
                            if poly_vrt == duplicate_ind[1][dp_vrt]:
                                same_flag = True
                                ind_ar.append(duplicate_ind[0][dp_vrt])
                        if not same_flag:
                            ind_ar.append(poly_vrt)
                        ind_count += 1
                # UV COORDS PREPARE
                uv_ar = []  # array with all t_coords
                new_uv_ind = []
                # get only active layer with uv_cords
                for uv_act in morph_mesh.uv_layers.active.data:
                    uv_ = [uv_act.uv[0], uv_act.uv[1]]
                    uv_ar.append(copy.copy(uv_))
                    if uv_ not in figure.t_coords:
                        figure.t_coords.append(uv_)
                # get indicies of new t_coords array
                for uv_ind1 in uv_ar:
                    for uv_ind2 in figure.t_coords:
                        if uv_ind1 == uv_ind2:
                            new_uv_ind.append(figure.t_coords.index(uv_ind2))
                # VERTEX COMPONENTS
                for n_i in range(len(ind_ar)):
                    uv_ind = [ind_ar[n_i], new_uv_ind[n_i]]
                    if uv_ind not in figure.v_c:
                        figure.v_c.append(copy.copy(uv_ind))
                #>>>>>TODO use other sort instead bubble sort
                for _ in range(len(figure.v_c)):
                    for buble in range(len(figure.v_c) - 1):
                        if figure.v_c[buble][0] > figure.v_c[buble + 1][0]:
                            swap_pts = copy.copy(figure.v_c[buble + 1])
                            figure.v_c[buble + 1] = copy.copy(figure.v_c[buble])
                            figure.v_c[buble] = copy.copy(swap_pts)
                        elif figure.v_c[buble][0] == figure.v_c[buble + 1][0]:
                            if figure.v_c[buble][1] > figure.v_c[buble + 1][1]:
                                swap_pts = copy.copy(figure.v_c[buble + 1])
                                figure.v_c[buble + 1] = copy.copy(figure.v_c[buble])
                                figure.v_c[buble] = copy.copy(swap_pts)
                figure.header[4] = len(figure.v_c)
                # INDICIES
                #>>>>>TODO refactore?!
                for mix in range(len(ind_ar)):
                    for mix1 in range(len(figure.v_c)):
                        if (ind_ar[mix] == figure.v_c[mix1][0]) and\
                                (new_uv_ind[mix] == figure.v_c[mix1][1]):
                            figure.indicies.append(mix1)
                            break

                figure.header[2] = len(figure.t_coords)
                figure.header[3] = ind_count
        
        figure.name = obj.name
        if obj_count == 1:
            figure.fillVertices()
            figure.fillAux()
            
            
        model().mesh_list.append(figure)

    return err

def clear_unlinked_data():
    for mesh in bpy.data.meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for obj in bpy.data.objects:
        if obj.users == 0:
            bpy.data.objects.remove(obj)
    for col in bpy.data.collections:
        if col.users == 0:
            bpy.data.collections.remove(col)

def scene_clear():
    '''
    deletes objects, meshes and collections from scene
    '''
    for collection in bpy.context.scene.collection.children:
        for obj in collection.objects:
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
    for rem_mesh in bpy.data.meshes:
        if rem_mesh.users == 0:
            bpy.data.meshes.remove(rem_mesh)
    #the blender does not have a single solution for cleaning the scene. this method was invented to try to clean up the scene in any way =\
    if len(bpy.data.objects) > 0:
        for obj in bpy.data.objects:
            bpy.data.objects.remove(obj)
        scene_clear()
    
    #restore animation data to default
    bpy.context.scene.frame_end = 250
    bpy.context.scene.frame_set(1)

#todo lock object after format?
def format_obj(cur_obj):
    '''
    checks transformation of current object and triangulate it
    '''
    quat_rot = cur_obj.rotation_quaternion
    sca = cur_obj.scale
    bpy.ops.object.rotation_clear()
    bpy.ops.object.scale_clear()
    if quat_rot != cur_obj.rotation_quaternion:
        print('WARNING: return operation and apply rotation to ' + cur_obj.name)
    if sca != cur_obj.scale:
        print('WARNING: return operation and apply scale to ' + cur_obj.name)

    # trianfulate obj
    mesh = cur_obj.data
    blender_mesh = bmesh.new()
    blender_mesh.from_mesh(mesh)
    bmesh.ops.triangulate(blender_mesh, faces=blender_mesh.faces[:], quad_method='BEAUTY', ngon_method='BEAUTY')
    blender_mesh.to_mesh(mesh)
    blender_mesh.free()

def to_object_mode():
    '''
    sets all meshes to 'OBJECT MODE'
    '''
    scene = bpy.context.scene
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)


def add_morph_comp(act_obj, morph_component):
    '''
    copys base object on new layer according to morphing prefix
    '''
    if (morph_component + act_obj.name) not in bpy.data.objects:
        # create copy of object
        new_obj = act_obj.copy()
        new_obj.data = act_obj.data.copy()
        new_obj.name = (morph_component + act_obj.name)
        new_obj.data.name = (morph_component + act_obj.name)
        scene = bpy.context.scene
        scene.objects.link(new_obj)
        for i in bpy.types.Scene.model.morph_comp:
            if bpy.types.Scene.model.morph_comp[i] == morph_component:
                if morph_component not in scene.collection.children:
                    # make new collection for this morph component
                    bpy.data.collections.new(bpy.types.Scene.model.morph_collection[i])
                    scene.collection.children.link(bpy.types.Scene.model.morph_collection[i])
                col = scene.collection.children[bpy.types.Scene.model.morph_collection[i]]
                col.objects.link(new_obj)
    else:
        print(act_obj.name + ' it is a bad object to add morph component, try another object')

def calculate_mesh(self, context):
    '''
    calculates test unit using data (str, dex, height) from scene
    '''
    q_str = context.scene.MeshStr
    q_dex = context.scene.MeshDex
    q_height = context.scene.MeshHeight
    for t_mesh in bpy.types.Scene.model.mesh_list:
        if t_mesh in bpy.data.meshes:
            m_verts = bpy.types.Scene.model.fig_table[t_mesh].verts
            for vert in bpy.data.meshes[t_mesh].vertices:
                for i in range(3):
                    temp1 = m_verts[0][vert.index][i] + \
                        (m_verts[1][vert.index][i] - m_verts[0][vert.index][i]) * q_str
                    temp2 = m_verts[2][vert.index][i] + \
                        (m_verts[3][vert.index][i] - m_verts[2][vert.index][i]) * q_str
                    value1 = temp1 + (temp2 - temp1) * q_dex
                    temp1 = m_verts[4][vert.index][i] + \
                        (m_verts[5][vert.index][i] - m_verts[4][vert.index][i]) * q_str
                    temp2 = m_verts[6][vert.index][i] + \
                        (m_verts[7][vert.index][i] - m_verts[6][vert.index][i]) * q_str
                    value2 = temp1 + (temp2 - temp1) * q_dex
                    final = value1 + (value2 - value1) * q_height
                    vert.co[i] = final
    for t_pos in bpy.types.Scene.model.pos_lost:
        if t_pos in bpy.data.objects:
            m_pos = bpy.types.Scene.model.bon_table[t_pos].pos
            for i in range(3):
                temp1 = m_pos[0][i] + (m_pos[1][i] - m_pos[0][i]) * q_str
                temp2 = m_pos[2][i] + (m_pos[3][i] - m_pos[2][i]) * q_str
                value1 = temp1 + (temp2 - temp1) * q_dex
                temp1 = m_pos[4][i] + (m_pos[5][i] - m_pos[4][i]) * q_str
                temp2 = m_pos[6][i] + (m_pos[7][i] - m_pos[6][i]) * q_str
                value2 = temp1 + (temp2 - temp1) * q_dex
                final = value1 + (value2 - value1) * q_height
                bpy.data.objects[t_pos].location[i] = final
