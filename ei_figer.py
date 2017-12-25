# Copyright (c) 2017 konstvest

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

bl_info = {
    "name": "EI figer",
    "author": "konstvest",
    "version": (2, 6),
    "blender": (2, 79, 0),
    "location": "",
    "description": "Addon for import-export model Evil Islands <-> Blender (without animations)",
    "wiki_url": "",
    "tracker_url": "https://github.com/konstvest/ei_figer",
    "category": "Import-Export"}

import copy
import os
from math import sqrt
from struct import pack, unpack
import time
import re

import bmesh
import bpy


FIG_TABLE = dict()
BON_TABLE = dict()
MESH_LIST = list()
POS_LIST = list()
MORPH_COMP = {
    0: '',
    1: 's~',
    2: 'd~',
    3: 'u~',
    4: 'b~',
    5: 'p~',
    6: 'g~',
    7: 'c~',
    8: 'T~'
    }

QUEST = re.compile("initqu[0-9]+item")              # initqu%ditem
QUICK = re.compile("initqi[0-9]+item")              # initqi%ditem
WEAPON = re.compile("initwe[a-zA-Z]+[0-9]+weapon")  # initwe%s%dweapon
ARMOR = re.compile("initar[a-zA-Z]+[0-9]+armor")    # initar%s%darmor
LOOT = re.compile("initlitr[0-9]+item")             # initlitr%ditem
MATERIAL = re.compile("initlimt[0-9]+item")         # initlimt%ditem


class ImportExportPanel(bpy.types.Panel):
    bl_label = "import-export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="PACKAGE")

    def draw(self, context):
        layout = self.layout
        #import
        layout.operator("object.eimodelimport", text="Import")
        #export
        layout.label(text="~~~~~~~export~~~~~~~")
        row = layout.row()
        row = row.split(percentage=0.8)
        row.prop(context.scene, "DestinationDir")
        row.operator("object.choose_dir", text="...")
        row = layout.row()
        row = row.split(percentage=0.75)
        row.prop(context.scene, "LnkName")
        row.operator("object.export_only_lnk", text="*.lnk")
        row = layout.row()
        row = row.split()
        row.operator("object.export_only_fig", text="*.fig's")
        row.operator("object.export_only_bon", text="*.bon's")
        #layout.operator("object.knopo4ka", text="start button   :)")


class OperatorPanel(bpy.types.Panel):
    bl_label = "Operations & options"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="MOD_SCREW")

    def draw(self, context):
        layout = self.layout
        layout.label(text="~~~~~~~options~~~~~~~")
        row = layout.row()
        split = row.split(percentage=0.35)
        left = split.column()
        #morphing
        left.label(text="Morphing")
        right = split.column()
        right.prop(context.scene, "MorphType")
        if context.scene.MorphType != 'non':
            row = layout.row()
            split = row.split(percentage=0.6)
            left = split.column()
            right = split.column()
            left.prop(context.scene, "MorphComp")
            right.operator("object.addmorphcomp", text="Add morph comp")
            #scaling
            if context.scene.MorphType == 'smpl':
                layout.prop(context.scene, "scalefig")
        #object parameters
        if len(context.selected_objects) >= 1:
            row = layout.row()
            split = row.split(percentage=0.5)
            left = split.column()
            left.prop(context.object, "ei_group")
            right = split.column()
            right.prop(context.object, "t_number")
        layout.label(text="~~~~~~~test unit~~~~~~~")
        #test unit
        layout.operator("object.refresh_test_unit", text="test unit",)
        layout.prop(context.scene, "MeshStr")
        layout.prop(context.scene, "MeshDex")
        layout.prop(context.scene, "MeshHeight")
        layout.label(text="~~~~~~operations~~~~~~")
        #scene delete
        layout.operator("object.clearscene", text="clear scene")
        #<<uv>>
        row = layout.row()
        split = row.split(percentage=0.7)
        left = split.column()
        lsplit = left.split(percentage=0.5)
        lleft = lsplit.column()
        lleft.operator("object.packuvcoords", text="<<")
        rleft = lsplit.column()
        rleft.label(text="uv_coords")
        right = split.column()
        right.operator("object.unpackuvcoords", text=">>")
        #type of select
        row = layout.row()
        split = row.split(percentage=0.3)
        left = split.column()
        left.label(text="select")
        right = split.column()
        right.prop(context.scene, "selectType")
        if context.scene.selectType == "mrph":
            row = layout.row()
            split = row.split(percentage=0.8)
            left = split.column()
            left.label(text="click ok ;)")
            right = split.column()
            right.operator("object.applyselect", text="ok")
        if context.scene.selectType == "grp" or context.scene.selectType == "txtrnmbr":
            row = layout.row()
            split = row.split(percentage=0.85)
            left = split.column()
            right = split.column()  #ok
            right.operator("object.applyselect", text="ok")

            split1 = left.split(percentage=0.72)
            left1 = split1.column()
            right1 = split1.column() #max
            right1.prop(context.scene, "selectMax")
            split2 = left1.split(percentage=0.49)
            left2 = split2.column() #min
            left2.prop(context.scene, "selectMin")
            right2 = split2.column()
            if context.scene.selectType == "grp":
                right2.label(text="group")
            else:
                right2.label(text="t_number")
        #uv layers
        row = layout.row()
        split = row.split(percentage=0.7)
        left = split.column()
        right = split.column()
        left.prop(context.scene, "sameUV")
        right.operator("object.setsameuvlayername", text="apply")


#>>>>>TODO animation import for human and export animation (will be able in next versions)
# class animation_panel(bpy.types.Panel):
#     bl_label = "animations"
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'TOOLS'
#     bl_category = 'EI_Tools'

#     def draw_header(self, context):
#         layout = self.layout
#         layout.label(text="", icon="POSE_DATA")

#     def draw(self, context):
#         layout = self.layout
#         layout.label(text="/~~animation zone~~/")
#         layout.operator("object.eimanimationimport", text="Import animation")
#         layout.label(text="\.O./")


def scene_clear():
    """
    deletes objects and meshes data from scene
    """
    bpy.context.scene.layers = [i == 1 for i in range(20)]
    for obj in bpy.data.objects:
        obj.layers = [i == 1 for i in range(20)]
        obj.select = True
    bpy.ops.object.delete()

def clean():
    """
    cleans trash from objects and meshes data from scene without reloading scene
    """
    for rem_mesh in bpy.data.meshes:
        if rem_mesh.users == 0:
            bpy.data.meshes.remove(rem_mesh)
    for rem_obj in bpy.data.objects:
        if rem_obj.users == 0:
            bpy.data.objects.remove(rem_obj)


#todo lock object after format
def format_obj(cur_obj):
    """
    checks transformation of current object and triangulate it
    """
    quat_rot = cur_obj.rotation_quaternion
    sca = cur_obj.scale
    bpy.ops.object.rotation_clear()
    bpy.ops.object.scale_clear()
    if quat_rot != cur_obj.rotation_quaternion:
        print ("WARNING: return operation and apply rotation to " + cur_obj.name)
    if sca != cur_obj.scale:
        print ("WARNING: return operation and apply scale to " + cur_obj.name)

    # trianfulate obj
    mesh = cur_obj.data
    blender_mesh = bmesh.new()
    blender_mesh.from_mesh(mesh)
    bmesh.ops.triangulate(blender_mesh, faces=blender_mesh.faces[:], quad_method=0, ngon_method=0)
    blender_mesh.to_mesh(mesh)
    blender_mesh.free()

def to_object_mode():
    """
    sets all meshes to 'OBJECT MODE'
    """
    scene = bpy.context.scene
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            scene.objects.active = obj
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

def detect_morph(m_name, obj_type, morph_id):
    """
    finds any morphing components in scene
    """
    try:
        if obj_type == 'OBJECT':
            morph = bpy.data.objects[MORPH_COMP[morph_id] + m_name]
        else:
            morph = bpy.data.meshes[MORPH_COMP[morph_id] + m_name]
    except KeyError:
        if morph_id == 1:
            morph = detect_morph(m_name, obj_type, 0)
        if morph_id == 2:
            morph = detect_morph(m_name, obj_type, 0)
        if morph_id == 3:
            morph = detect_morph(m_name, obj_type, 1)
        if morph_id == 4:
            morph = detect_morph(m_name, obj_type, 0)
        if morph_id == 5:
            morph = detect_morph(m_name, obj_type, 1)
        if morph_id == 6:
            morph = detect_morph(m_name, obj_type, 2)
        if morph_id == 7:
            morph = detect_morph(m_name, obj_type, 3)
    return morph


def get_hierarchy(parent, hierarchy):
    """
    gets hierarchy from parent to children
    """
    for child in parent.children:
        hierarchy[child.name] = parent.name
        #print(child.name + ' <= '+parent.name)
        if child.children:
            get_hierarchy(child, hierarchy)


def export_lnk(lnkpath):
    """
    writes hierarchy in file as *.lnk.
    """
    if not lnkpath.lower().endswith(".lnk"):
        lnkpath += ".lnk"
    export_links = dict()
    root_mesh = ''
    for obj in bpy.data.objects:
        if obj.parent is None and obj.name[0:2] not in MORPH_COMP.values():
            root_mesh = obj.name
            get_hierarchy(obj, export_links)
            break
    links_count = len(export_links) + 1
    if len(root_mesh) > 0:
        lnk_file = open(lnkpath, 'wb')
        flr = lnk_file.write
        # write root mesh
        flr(pack('i', links_count))
        frmt = str(len(root_mesh + 'a')) + 's'
        flr(pack('i', len(root_mesh) + 1))
        flr(pack(frmt, root_mesh.encode()))
        flr(pack('i', 0))

        def do_upora(start):  # write lnk
            """
            writes recursively lnk file
            """
            for cur_link in export_links:
                if export_links[cur_link] == start:
                    flr(pack('i', len(cur_link) + 1))
                    flr(pack(str(len(cur_link) + 1) + 's', cur_link.encode()))
                    flr(pack('i', len(export_links[cur_link]) + 1))
                    flr(pack(
                        str(len(export_links[cur_link]) + 1) + 's', export_links[cur_link].encode()))
                    do_upora(cur_link)
        do_upora(root_mesh)
        lnk_file.close()
    else:
        print("root mesh of hierarchy is not correct")
        return False
    return True

def get_uv_convert_count(filename):
    """
    gets count of convert uv coordinates depending on filename
    """
    #match with begin of string
    if QUEST.match(filename) is not None or QUICK.match(filename) is not None or LOOT.match(filename) is not None:
        return 2
    if WEAPON.match(filename) is not None:
        return 1
    return 0

def unpack_uv(uv_, count):
    """
    increases x,y value 2 times per side and offset by y(vertically)
    """
    for _ in range(count):
        for uv_convert in uv_:
            uv_convert[0] *= 2
            uv_convert[1] = uv_convert[1] * 2 - 1

def pack_uv(uv_, count):
    """
    decreases x,y value 2 times per side and offset by y(vertically)
    """
    for _ in range(count):
        for uv_convert in uv_:
            uv_convert[0] /= 2
            uv_convert[1] = 0.5 + uv_convert[1] / 2

class EiMesh(object):
    """
    container of EI figure, can read and write file *.fig
    """
    def __init__(self):
        self.name = ''
        self.path = 'c:\\'
        self.header = [0 for _ in range(9)]
        self.center = [(0.0, 0.0, 0.0) for _ in range(8)]
        self.fmin = [(0.0, 0.0, 0.0) for _ in range(8)]
        self.fmax = [(0.0, 0.0, 0.0) for _ in range(8)]
        self.radius = [0.0 for _ in range(8)]
        # [main], [strength], [dexterity], [unique] and scaled once
        self.verts = [[], [], [], [], [], [], [], []]
        self.normals = []
        self.t_coords = []
        self.indicies = []
        self.v_c = []

    def read_mesh(self):
        """
        reads data from *.fig file
        """
        fig_file = open(self.path, 'rb')
        ffr = fig_file.read
        while 1 == 1:
            # SIGNATURE
            if ffr(4) == b'FIG8':
                # HEADER
                for ind in range(9):
                    tmp = unpack('i', ffr(4))
                    self.header[ind] = tmp[0]
                # Center
                tmp = [0, 0, 0]
                for mrph_cmp in range(8):
                    for xyz in range(3):
                        tmp[xyz] = unpack('f', ffr(4))[0]
                    self.center[mrph_cmp] = tuple(tmp)
                # MIN
                for mrph_cmp in range(8):
                    for xyz in range(3):
                        tmp[xyz] = unpack('f', ffr(4))[0]
                    self.fmin[mrph_cmp] = tuple(tmp)
                # MAX
                for mrph_cmp in range(8):
                    for xyz in range(3):
                        tmp[xyz] = unpack('f', ffr(4))[0]
                    self.fmax[mrph_cmp] = tuple(tmp)
                # Radius
                ffr(32)  # xD
                # VERTICES
                block = [[[0 for _ in range(3)] for _ in range(8)] for _ in range(4)]
                for ver in range(self.header[0]):
                    for xyz in range(3):
                        for mc in range(8):  #morphing component
                            for b in range(4):  #block
                                block[b][mc][xyz] = unpack('f', ffr(4))[0]
                    for b in range(4):
                        for mc in range(8):
                            self.verts[mc].append(tuple(block[b][mc][0:3]))
                del block
                # NORMALS
                ffr(self.header[1] * 64)  # =)
                # TEXTURE COORDS
                for _ in range(self.header[2]):
                    self.t_coords.append([unpack('f', ffr(4))[0], unpack('f', ffr(4))[0]])
                unpack_uv(self.t_coords, get_uv_convert_count(self.name))
                # INDICES
                for _ in range(self.header[3]):
                    tmp = unpack('h', ffr(2))
                    self.indicies.append(tmp[0])
                # VERTICES COMPONENTS
                tmp = [0, 0]
                for _ in range(self.header[4]):
                    ffr(2)
                    for vc_i in range(2):
                        tmp[vc_i] = unpack('h', ffr(2))[0]
                    self.v_c.append(tuple(tmp))
                fig_file.close()
                break
            else:
                print('mesh header is not correct')

    def create_mesh(self, morph_type):
        """
        creates mesh (count depending on morph type) in scene using data from class
        """
        # FACES
        faces = []
        ftemp = [0, 0, 0]
        face_indices_count = self.header[3] - 2
        cur_face_indices = 0
        while cur_face_indices < face_indices_count:
            for vvv in range(3):
                ftemp[vvv] = self.v_c[self.indicies[cur_face_indices + vvv]][0]
            faces.append([ftemp[0], ftemp[1], ftemp[2]])
            cur_face_indices += 3
        # =====>MESH IN SCENE<======
        if morph_type == 'smpl':
            #>>>>>TODO try to find out file scale
            # try:
            #    scn.scalefig = self.verts[4][0][0] / self.verts[0][0][0]
            # except ZeroDivisionError:
            #    print('ny ebana')
            models_count = 3
        if morph_type == 'hrd':
            models_count = 8
        if morph_type == 'non':
            models_count = 1
        for i in range(models_count):
            morph_mesh = bpy.data.meshes.new(name=MORPH_COMP[i] + self.name)
            morph_obj = bpy.data.objects.new(MORPH_COMP[i] + self.name, morph_mesh)
            morph_obj.location = (0, 0, 0)
            morph_obj["ei_group"] = self.header[7]
            morph_obj["t_number"] = self.header[8]
            bpy.context.scene.objects.link(morph_obj)
            morph_mesh.from_pydata(self.verts[i], [], faces)
            morph_mesh.update()
            if i != 0:
                #bug here: if you import model again figures on layers !=0 will be
                #in (0,0,0) location. move it and press ctrl+z to fix it
                morph_obj.layers[i] = True
                morph_obj.layers[0] = False

        # UV COORDINATES
        mesh = bpy.data.meshes[self.name]
        mesh.uv_textures.new(self.name)
        for uv_ind in range(self.header[3]):
            for xy_ in range(2):
                mesh.uv_layers[0].data[uv_ind].uv[xy_] = self.t_coords[self.v_c[self.indicies[uv_ind]][1]][xy_]
        mesh.update()

    def get_data_from_mesh(self, m_name):
        """
        gets data from current mesh by mesh name
        """
        scn = bpy.context.scene
        for mesh_morph_component in range(8):
            mesh = detect_morph(m_name, 'MESH', mesh_morph_component)
            count_vert = 0
            count_norm = 0
            v_restore = 0
            ind_count = 0
            tmp3 = [0, 0, 0]
            duplicate_vert = 0
            duplicate_ind = [[], []]
            min_m = [0, 0, 0]
            max_m = [0, 0, 0]
            if (scn.MorphType == 'smpl') and (mesh_morph_component > 3):
                simple_morph_scale = scn.scalefig
            else:
                simple_morph_scale = 1

            # VERTICES & NORMALS
            for mvert in mesh.vertices:
                same_flag = False
                for same_vert in range(count_vert):
                    if mvert.co == self.verts[mesh_morph_component][same_vert]:
                        same_flag = True
                        if mesh_morph_component == 0:
                            duplicate_ind[0].append(same_vert)
                            duplicate_ind[1].append(duplicate_vert)
                if not same_flag:
                    # vertices
                    self.verts[mesh_morph_component].append(tuple(mvert.co*simple_morph_scale))
                    count_vert += 1
                    # normals
                    if mesh_morph_component == 0:
                        tmp4 = [mvert.normal[0], mvert.normal[1],
                                mvert.normal[2], 1.0]
                        self.normals.append(tuple(tmp4))
                        count_norm += 1
                        # MIN & MAX PREPARE
                    if mvert.index == 0:
                        min_m = copy.copy(mvert.co)
                        max_m = copy.copy(mvert.co)
                    m_index = 0
                    while m_index < 3:
                        if max_m[m_index] < mvert.co[m_index]:
                            max_m[m_index] = mvert.co[m_index]
                        if min_m[m_index] > mvert.co[m_index]:
                            min_m[m_index] = mvert.co[m_index]
                        m_index += 1
                if mesh_morph_component == 0:
                    duplicate_vert += 1
            self.fmin[mesh_morph_component] = copy.copy(min_m)
            self.fmax[mesh_morph_component] = copy.copy(max_m)
            # RADIUS
            self.radius[mesh_morph_component] = sqrt(
                (self.fmax[mesh_morph_component][0] - self.fmin[mesh_morph_component][0]) ** 2 +
                (self.fmax[mesh_morph_component][1] - self.fmin[mesh_morph_component][1]) ** 2 +
                (self.fmax[mesh_morph_component][2] - self.fmin[mesh_morph_component][2]) ** 2) / 2
            # REAL CENTER
            for i in range(3):
                tmp3[i] = (self.fmin[mesh_morph_component][i] + self.fmax[mesh_morph_component][i]) / 2
            self.center[mesh_morph_component] = tuple(tmp3)
            # MIN & MAX
            for i in range(3):
                self.fmin[mesh_morph_component][i] -= self.center[mesh_morph_component][i]
                self.fmax[mesh_morph_component][i] -= self.center[mesh_morph_component][i]
            if count_vert != 0 and mesh_morph_component == 0:
                self.header[5] = count_vert
            # align vertices
            if count_vert % 4 != 0:
                v_restore = 4 - count_vert % 4
            for _ in range(v_restore):
                self.verts[mesh_morph_component].append((0.0, 0.0, 0.0))
                count_vert += 1
            # if count_vert % 4 == 0 and mesh_morph_component == 0:
                #print('verts now: ' + str(count_vert) + ' added: ' + str(v_restore))
            if mesh_morph_component == 0:
                self.header[0] = int(count_vert / 4)
                if len(self.normals) % 4 != 0:
                    for _ in range(4 - len(self.normals) % 4):
                        self.normals.append(
                            copy.copy(self.normals[count_norm - 1]))
                        count_norm += 1
                self.header[1] = int(len(self.normals) / 4)
                ind_ar = []
                for mpoly in mesh.polygons:
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
                if mesh.uv_layers.active_index >= 0:
                    for uv_act in mesh.uv_layers.active.data:  # get only active layer with uv_cords
                        uv_ = [uv_act.uv[0], uv_act.uv[1]]
                        uv_ar.append(copy.copy(uv_))
                        if uv_ not in self.t_coords:
                            self.t_coords.append(uv_)
                else:
                    print ("mesh " + mesh.name + "has no active uv layer")
                self.header[2] = len(self.t_coords)
                self.header[3] = ind_count
                for uv_ind1 in uv_ar:  # get indicies of new t_coords array
                    for uv_ind2 in self.t_coords:
                        if uv_ind1 == uv_ind2:
                            new_uv_ind.append(self.t_coords.index(uv_ind2))

                # VERTEX COMPONENTS
                for n_i in range(len(ind_ar)):
                    uv_ind = [ind_ar[n_i], new_uv_ind[n_i]]
                    if uv_ind not in self.v_c:
                        self.v_c.append(copy.copy(uv_ind))
                #>>>>>TODO use other sort instead bubble sort
                for _ in range(len(self.v_c)):
                    for buble in range(len(self.v_c) - 1):
                        if self.v_c[buble][0] > self.v_c[buble + 1][0]:
                            swap_pts = copy.copy(self.v_c[buble + 1])
                            self.v_c[buble + 1] = copy.copy(self.v_c[buble])
                            self.v_c[buble] = copy.copy(swap_pts)
                        elif self.v_c[buble][0] == self.v_c[buble + 1][0]:
                            if self.v_c[buble][1] > self.v_c[buble + 1][1]:
                                swap_pts = copy.copy(self.v_c[buble + 1])
                                self.v_c[buble + 1] = copy.copy(self.v_c[buble])
                                self.v_c[buble] = copy.copy(swap_pts)
                self.header[4] = len(self.v_c)
                # INDICIES
                #>>>>>TODO refactore?!
                for mix in range(len(ind_ar)):
                    for mix1 in range(len(self.v_c)):
                        if (ind_ar[mix] == self.v_c[mix1][0]) & (new_uv_ind[mix] == self.v_c[mix1][1]):
                            self.indicies.append(mix1)
                            break
                #GROUP AND TEXTURE NUMBER
                try:
                    obj = bpy.data.objects[mesh.name]
                    self.header[7] = obj["ei_group"]
                    self.header[8] = obj["t_number"]
                except KeyError:
                    print ('key error blead/t' + mesh.name + " use the same name for object and its mesh")
                    self.header[7] = 18
                    self.header[8] = 8

    def write_in_file(self):
        """
        writes mesh in file as *.fig
        """
        fig_file = open(self.path, 'wb')
        ffw = fig_file.write
        ffw(b'FIG8')
        # print('\theader')
        for header_ind in range(9):
            ffw(pack('i', self.header[header_ind]))
        # print('\tcenter')
        for mrph_cmp in range(8):
            for xyz in range(3):
                ffw(pack('f', self.center[mrph_cmp][xyz]))
        # print('\tmin')
        for mrph_cmp in range(8):
            for xyz in range(3):
                ffw(pack('f', self.fmin[mrph_cmp][xyz]))
        # print('\tmax')
        for mrph_cmp in range(8):
            for xyz in range(3):
                ffw(pack('f', self.fmax[mrph_cmp][xyz]))
        # print('\tradius')
        for mrph_cmp in range(8):
            ffw(pack('f', self.radius[mrph_cmp]))
        # print('\tverts')
        block_index = 0
        for _ in range(self.header[0]):
            for xyz in range(3):
                for morph_c in range(8):
                    for cur_block_ind in range(4):
                        ffw(pack('f', self.verts[morph_c][block_index + cur_block_ind][xyz]))
            block_index += 4
        # print('\tnormals')
        block_index = 0
        for _ in range(self.header[1]):
            for xyzw in range(4):
                for cur_block_ind in range(4):
                    ffw(pack('f', self.normals[block_index + cur_block_ind][xyzw]))
            block_index += 4
        # print('\ttexture coordinates')
        pack_uv(self.t_coords, get_uv_convert_count(self.name))
        for tex_ind in range(self.header[2]):
            for xy_ in range(2):
                ffw(pack('f', self.t_coords[tex_ind][xy_]))
        # print('\tindicies')
        for i_i in range(self.header[3]):
            ffw(pack('h', self.indicies[i_i]))
        # print('\tv_c')
        for v_c_i in range(self.header[4]):
            for _ in range(2):
                ffw(pack('h', self.v_c[v_c_i][0]))
            ffw(pack('h', self.v_c[v_c_i][1]))
        # print('\tm_c')
        for m_c_i in range(self.header[5]):
            ffw(pack('h', m_c_i))
            ffw(pack('h', m_c_i))
        fig_file.close()


class EiBon(object):
    """
    container of EI bone position, can read and write file *.bon
    """
    def __init__(self):
        self.name = ''
        self.path = 'c:\\'
        self.pos = [(0.0, 0.0, 0.0) for _ in range(8)]

    def read_pos(self):
        """
        reads position of figure from *.bon file
        """
        bon_file = open(self.path, 'rb')
        btmp = [0, 0, 0]
        for mrph_cmp in range(8):
            for orig in range(3):
                btmp[orig] = unpack('f', bon_file.read(4))[0]
            self.pos[mrph_cmp] = tuple(btmp)
        bon_file.close()

    def set_pos(self, morph_type):
        """
        sets position to mesh and this morph components
        """
        if morph_type == 'smpl':
            pos_counter = 3
        if morph_type == 'hrd':
            pos_counter = 8
        if morph_type == 'non':
            pos_counter = 1
        for cur_morph in range(pos_counter):
            try:
                bpy.data.objects[MORPH_COMP[cur_morph] + self.name].location = self.pos[cur_morph]
            except KeyError:
                print(MORPH_COMP[cur_morph] + self.name + " : object not found in scene")

    def get_object_position(self, name):
        """
        gets position from object by name and his morph friends
        """
        scn = bpy.context.scene
        for morph_component_id in range(8):
            obj = detect_morph(name, 'OBJECT', morph_component_id)
            if (scn.MorphType == "smpl") and (morph_component_id > 3):
                scale = scn.scalefig
            else:
                scale = 1
            self.pos[morph_component_id] = tuple(obj.location * scale)

    def write_pos(self):
        """
        writes position in file
        """
        bon_file = open(self.path, 'wb')
        for mrph_cmp in range(8):
            for xyz in range(3):
                bon_file.write(pack('f', self.pos[mrph_cmp][xyz]))
        bon_file.close()

##########################################################################
##########################################################################
############################ EXPORT ZONE #################################
##########################################################################
##########################################################################

class ChooseDir(bpy.types.Operator):
    """
    operator to choose project dir for export
    """
    bl_label = "Choose dir"
    bl_idname = "object.choose_dir"
    directory = bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        bpy.context.scene.DestinationDir = self.directory
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}


class EiExportOnlyLnk(bpy.types.Operator):
    """
    writes all objects links in one file as *.lnk
    """
    bl_label = "export lnk"
    bl_idname = "object.export_only_lnk"
    bl_description = "export link file"

    def execute(self, context):
        clean()
        scn = context.scene
        if export_lnk(scn.DestinationDir + scn.LnkName):
            self.report({'INFO'}, scn.LnkName + ".lnk exported")
        return {"FINISHED"}


class EiExportOnlyFigs(bpy.types.Operator):
    """
    writes selected objects data in file as *.lnk
    """
    bl_label = "export fig"
    bl_idname = "object.export_only_fig"
    def execute(self, context):
        clean()
        scn = context.scene
        info = len(bpy.context.selected_objects)
        for obj in bpy.context.selected_objects:
            if obj.data.name[0:2] not in MORPH_COMP.values():
                format_obj(obj)
                mesh = bpy.data.meshes[obj.data.name]
                cur_m = EiMesh()
                cur_m.name = mesh.name
                cur_m.path = os.path.join(scn.DestinationDir, mesh.name + '.fig')
                cur_m.get_data_from_mesh(mesh.name)
                cur_m.write_in_file()
                if info == 1:
                    self.report({'INFO'}, mesh.name + ".fig exported")
        if info > 1:
            self.report({'INFO'}, "*.fig(s) exported")
        return {"FINISHED"}


class EiExportOnlyBons(bpy.types.Operator):
    """
    writes selected objects positions in file as *.fig
    """
    bl_label = "export bon"
    bl_idname = "object.export_only_bon"

    def execute(self, context):
        clean()
        scn = bpy.context.scene
        info = len(bpy.context.selected_objects)
        for obj in bpy.context.selected_objects:
            if obj.name[0:2] not in MORPH_COMP.values():
                cur_b = EiBon()
                cur_b.name = obj.name
                cur_b.path = os.path.join(scn.DestinationDir, obj.name + ".bon")
                cur_b.get_object_position(obj.name)
                cur_b.write_pos()
                if info == 1:
                    self.report({'INFO'}, obj.name + ".bon exported")
        if info > 1:
            self.report({'INFO'}, "*.bon(s) exported")
        return {"FINISHED"}

##########################################################################
##########################################################################
############################## OPERATOR ZONE #############################
##########################################################################
##########################################################################

def add_morph_comp(act_obj, mrph_cmp):
    """
    copys base object on new layer according to morphing prefix
    """
    if (mrph_cmp + act_obj.name) not in bpy.data.objects:
        # copy object
        new_obj = act_obj.copy()
        new_obj.data = act_obj.data.copy()
        new_obj.name = (mrph_cmp + act_obj.name)
        new_obj.data.name = (mrph_cmp + act_obj.name)
        bpy.context.scene.objects.link(new_obj)
        # place object in according to layer
        for i in MORPH_COMP:
            if MORPH_COMP[i] == mrph_cmp:
                new_obj.layers[i] = True
                new_obj.layers[0] = False
    else:
        print(act_obj.name + ' it is a bad object to add morph component, try another object')


def morphing_list(self, context):
    """
    returns list of morphing components for UI
    """
    hard_morph_list = [
        ('s~', 'Strength (s~)', 'Strength component', 1),
        ('d~', 'Dexterity (d~)', 'Dexterity component', 2),
        ('u~', 'Unique (u~)', 'Mean between Strength & Dexterity components in one object', 3),
        ('b~', 'Scaled (b~)', 'Scaled base figure', 4),
        ('p~', 'Power (p~)', 'Scaled strength component', 5),
        ('g~', 'Grace (g~)', 'Scaled dexterity component', 6),
        ('c~', 'Common (c~)', 'Common scaled strength & scaled dexterity components in one object', 7)
        ]
    simple_morph_list = [
        ('s~', 'Strength (s~)', 'Strength component', 1),
        ('d~', 'Dexterity (d~)', 'Dexterity component', 2),
        ('u~', 'Unique (u~)', 'Mean between Strength & Dexterity components in one object', 3)
        ]
    if context.scene.MorphType == 'hrd':
        return hard_morph_list
    else:
        return simple_morph_list


def calculate_mesh(self, context):
    """
    calculates test unit using data (str, dex, height) from scene
    """
    q_str = context.scene.MeshStr
    q_dex = context.scene.MeshDex
    q_height = context.scene.MeshHeight
    global FIG_TABLE
    global BON_TABLE
    global MESH_LIST
    global POS_LIST
    for t_mesh in MESH_LIST:
        m_verts = FIG_TABLE[t_mesh].verts
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
    for t_pos in POS_LIST:
        m_pos = BON_TABLE[t_pos].pos
        for i in range(3):
            temp1 = m_pos[0][i] + (m_pos[1][i] - m_pos[0][i]) * q_str
            temp2 = m_pos[2][i] + (m_pos[3][i] - m_pos[2][i]) * q_str
            value1 = temp1 + (temp2 - temp1) * q_dex
            temp1 = m_pos[4][i] + (m_pos[5][i] - m_pos[4][i]) * q_str
            temp2 = m_pos[6][i] + (m_pos[7][i] - m_pos[6][i]) * q_str
            value2 = temp1 + (temp2 - temp1) * q_dex
            final = value1 + (value2 - value1) * q_height
            bpy.data.objects[t_pos].location[i] = final


class RefreshTestTable(bpy.types.Operator):
    bl_label = "EI refresh test unit"
    bl_idname = "object.refresh_test_unit"
    bl_description = "delete current test unit and create new one"

    def execute(self, context):
        bpy.ops.object.select_all(action='DESELECT')
        tu_dict = dict()
        global FIG_TABLE
        global BON_TABLE
        global MESH_LIST
        global POS_LIST
        for obj in bpy.data.objects:
            if obj.name[0:2] == MORPH_COMP[8]:
                obj.select = True
                bpy.ops.view3d.layers(nr=9, extend=False)
                bpy.ops.object.delete()
        clean()
        if MESH_LIST:
            MESH_LIST = []
        if POS_LIST:
            POS_LIST = []
        if FIG_TABLE:
            FIG_TABLE.clear()
        if BON_TABLE:
            BON_TABLE.clear()
        to_object_mode()

        #find base objects
        for obj in bpy.data.objects:
            if obj.layers[0] and not obj.hide and obj.name[0:2] not in MORPH_COMP.values():
                MESH_LIST.append(MORPH_COMP[8] + obj.data.name)
                POS_LIST.append(MORPH_COMP[8] + obj.name)
                if obj.parent is None:
                    tu_dict[MORPH_COMP[8] + obj.name] = None
                else:
                    tu_dict[MORPH_COMP[8] + obj.name] = MORPH_COMP[8] + obj.parent.name

        for test_mesh in MESH_LIST:
            cur_m = EiMesh()
            cur_m.name = test_mesh
            cur_m.get_data_from_mesh(test_mesh[2:])
            FIG_TABLE[test_mesh] = cur_m
        for test_obj in POS_LIST:
            cur_b = EiBon()
            cur_b.name = test_obj
            cur_b.get_object_position(test_obj[2:])
            BON_TABLE[test_obj] = cur_b

        for t_ind in MESH_LIST:
            FIG_TABLE[t_ind].create_mesh('non')
            bpy.data.objects[t_ind].layers[8] = True
            bpy.data.objects[t_ind].layers[0] = False
        create_hierarchy(tu_dict)
        for p_ind in POS_LIST:
            BON_TABLE[p_ind].set_pos('non')
        calculate_mesh(self, context)
        return {'FINISHED'}


class MorphOperators(bpy.types.Operator):
    bl_label = "EI Add Morphing Components"
    bl_idname = "object.addmorphcomp"
    bl_description = "Add morphing component of selected objects"

    def execute(self, context):
        prefix = bpy.context.scene.MorphComp
        new_links = dict()
        clean()
        for obj in bpy.data.objects:
            if obj.name[0:2] not in MORPH_COMP.values():
                if obj.parent is None:
                    get_hierarchy(obj, new_links)
        for obj in bpy.data.objects:
            if obj.select and obj.name[0:2] not in MORPH_COMP.values():
                add_morph_comp(obj, prefix)
        # create new links of morphing components and make hierarchy
        morph_lnk = dict()
        for node in new_links:
            morph_lnk[prefix + node] = prefix + new_links[node]
        create_hierarchy(morph_lnk)
        morph_lnk.clear()
        return {'FINISHED'}

class ClearScene(bpy.types.Operator):
    bl_label = "Del all"
    bl_idname = "object.clearscene"
    bl_description = "Delete all objects and meshes from scene"

    def execute(self, context):
        scene_clear()
        return {'FINISHED'}

def ei_set_group(self, context):
    """
    Set EI group for selected objects
    """
    for obj in bpy.context.selected_objects:
        obj["ei_group"] = bpy.context.object.ei_group

def ei_set_texture_number(self, context):
    """
    Set EI texture number for selected objects
    """
    for obj in bpy.context.selected_objects:
        obj["t_number"] = bpy.context.object.t_number

class PackUv(bpy.types.Operator):
    bl_label = "Pack uv coords"
    bl_idname = "object.packuvcoords"
    bl_description = "Pack UV coords same EI for selected objects"

    def execute(self, context):
        to_object_mode()
        for obj in bpy.context.selected_objects:
            if obj.data.uv_layers.active_index >= 0:
                for pt_ in obj.data.uv_layers.active.data:
                    pt_.uv[0] /= 2
                    pt_.uv[1] = 0.5 + pt_.uv[1]/2
        return {'FINISHED'}

class UnpackUv(bpy.types.Operator):
    bl_label = "Unpack uv coords"
    bl_idname = "object.unpackuvcoords"
    bl_description = "Unpack UV coords same EI for selected objects"

    def execute(self, context):
        to_object_mode()
        for obj in bpy.context.selected_objects:
            if obj.data.uv_layers.active_index >= 0:
                for pt_ in obj.data.uv_layers.active.data:
                    pt_.uv[0] *= 2
                    pt_.uv[1] = pt_.uv[1] * 2 - 1
        return {'FINISHED'}

class ApplySelect(bpy.types.Operator):
    bl_label = "Select objects by type of select"
    bl_idname = "object.applyselect"
    bl_description = "Select objects depending on choose type"

    def execute(self, context):
        if context.scene.selectType == "mrph":
            for obj in context.selected_objects:
                if obj.name[0:2] in MORPH_COMP.values():
                    find_name = obj.name[2:]
                else:
                    find_name = obj.name
                    for morph_id in range(8):
                        detect_morph(find_name, "OBJECT", morph_id).select = True
        if context.scene.selectType == "grp" or context.scene.selectType == "txtrnmbr":
            minRange = context.scene.selectMin
            maxRange = context.scene.selectMax
            for obj in context.selected_objects:
                obj.select = False
        if context.scene.selectType == "grp":
            for obj in bpy.data.objects:
                if obj["ei_group"] >= minRange and obj["ei_group"] <= maxRange:
                    obj.select = True
        if context.scene.selectType == "txtrnmbr":
            for obj in bpy.data.objects:
                if obj["t_number"] >= minRange and obj["t_number"] <= maxRange:
                    obj.select = True

        return {'FINISHED'}

def update_range_min(self, context):
    if context.scene.selectMax < context.scene.selectMin:
        context.scene.selectMax = context.scene.selectMin

def update_range_max(self, context):
    if context.scene.selectMax < context.scene.selectMin:
        context.scene.selectMin = context.scene.selectMax

class SetSameUvLayerName(bpy.types.Operator):
    bl_label = "set active uv layer name"
    bl_idname = "object.setsameuvlayername"
    bl_description = "Sets the name to active uv layer of selected objects"

    def execute(self, context):
        to_object_mode()
        for obj in bpy.context.selected_objects:
            if obj.data.uv_layers.active_index >= 0:
                obj.data.uv_layers.active.name = context.scene.sameUV
        return {'FINISHED'}

##########################################################################
##########################################################################
############################ IMPORT ZONE #################################
##########################################################################
##########################################################################


# LNK IMPORT <==============================================================
def import_lnk(lnkpath):
    lnks = dict()
    file = open(lnkpath, 'rb')
    link_number = unpack('i', file.read(4))[0]
    for l in range(link_number):
        tmp1 = unpack('i', file.read(4))[0]
        child = unpack(str(tmp1 - 1) + 's', file.read(tmp1 - 1))[0].decode()
        file.read(1)
        tmp1 = unpack('i', file.read(4))[0]
        if tmp1 == 0:
            lnks[child] = None
            root = child
        else:
            parent = unpack(str(tmp1 - 1) + 's', file.read(tmp1 - 1))[0].decode()
            file.read(1)
            lnks[child] = parent
    file.close()
    return lnks, root


def create_hierarchy(lnks):
    for key in lnks:
        #print(key, lnks[k])
        if lnks[key] is not None:
            try:
                bpy.data.objects[key].parent = bpy.data.objects[lnks[key]]
            except KeyError:
                print(str(key) + ': object not found in scene, but found in links of hierarchy')


class EIImport(bpy.types.Operator):
    bl_label = "EI model import Operator"
    bl_idname = "object.eimodelimport"
    bl_description = "Import model from Evil Islands file"
    filepath = bpy.props.StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        self.report({'INFO'}, "executing import")
        path_file = self.filepath
        scene = context.scene
        clean()

        if path_file.lower().endswith('.lnk'):
            links, root_mesh = import_lnk(path_file)
            for node in links:
                figfile = os.path.join(os.path.dirname(path_file), node + ".fig")
                if os.path.exists(figfile):
                    cur_m = EiMesh()
                    cur_m.path = figfile
                    cur_m.name = node
                    cur_m.read_mesh()
                    cur_m.create_mesh(scene.MorphType)

            create_hierarchy(links)
            if scene.MorphType == 'smpl':
                morph_links = 3
            elif scene.MorphType == 'hrd':
                morph_links = 7
            else:
                morph_links = 0
            for i in range(morph_links):
                morphed_links = dict()
                for base_node in links:
                    if links[base_node] is None:
                        morphed_links[str(MORPH_COMP[i + 1]) + str(base_node)] = None
                    else:
                        morphed_links[str(MORPH_COMP[i + 1]) + str(base_node)] = str(MORPH_COMP[i + 1]) + str(links[base_node])
                create_hierarchy(morphed_links)
            for node in links:
                bonfile = os.path.join(os.path.dirname(path_file), node + ".bon")
                if os.path.exists(bonfile):
                    cur_b = EiBon()
                    cur_b.path = bonfile
                    cur_b.name = node
                    cur_b.read_pos()
                    cur_b.set_pos(scene.MorphType)

        if path_file.lower().endswith('.fig'):
            cur_m = EiMesh()
            cur_m.path = path_file
            cur_m.name = os.path.basename(os.path.splitext(path_file)[0])
            cur_m.read_mesh()
            cur_m.create_mesh(scene.MorphType)

        if path_file.lower().endswith('.bon'):
            cur_b = EiBon()
            cur_b.name = os.path.basename(os.path.splitext(path_file)[0])
            cur_b.path = path_file
            cur_b.read_pos()
            cur_b.set_pos(scene.MorphType)
        self.report({'INFO'}, "finished import")
        return {'FINISHED'}

    def invoke(self, context, event):
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}


##########################################################################
##########################################################################
############################# ANIMATION ZONE #############################
##########################################################################
##########################################################################
def import_anm(anmpath, selected):
    base_loc = dict()
    base_rot = dict()
    #count_rot = 0
    count_trans = 0
    #count_morph = 0
    for cur in range(len(selected)):
        try:
            fa = open(os.path.dirname(anmpath) + '\\' +
                      selected[cur] + '.anm', 'rb')
            rot = []
            trans = []
            morph = []
            # rotation frames in quaternions
            count_rot = unpack('i', fa.read(4))[0]
            tmp = [0, 0, 0, 0]
            for cr in range(count_rot):
                for i in range(4):
                    tmp[i] = unpack('f', fa.read(4))[0]
                rot.append([tmp[0], tmp[1], tmp[2], tmp[3]])
            base_rot[selected[cur]] = copy.copy(rot)
            # morph_positions and translations frames
            count_trans = unpack('i', fa.read(4))[0]
            tmp1 = [0, 0, 0]
            for ct in range(count_trans):
                for i in range(3):
                    tmp1[i] = unpack('f', fa.read(4))[0]
                trans.append([tmp1[0], tmp1[1], tmp1[2]])
            base_loc[selected[cur]] = copy.copy(trans)
            # morphing translations to be continued
            count_morph = unpack('i', fa.read(4))[0]
            count_morph_vert = unpack('i', fa.read(4))[0]
            for cm in range(count_morph):
                # print(str(cm)+' frame')
                for cmv in range(count_morph_vert):
                    for tr in range(3):
                        tmp[tr] = round(unpack('f', fa.read(4))[0], 4)
            fa.close()
            del trans
            del rot
            del morph
        except FileNotFoundError:
            print(selected[cur] + '.anm - file not found: ')
    return base_loc, base_rot, count_trans


def order(linked, root):
    lnk_order = []

    def do_upora(start):
        for d in linked:
            if linked[d] == start:  # and d is not None:
                lnk_order.append(d)
                do_upora(d)

    do_upora(root)
    # print(lnk_order)
    return lnk_order


class EiAnimationImport(bpy.types.Operator):
    bl_label = "EI animation import Operator"
    bl_idname = "object.eimanimationimport"
    bl_description = "Importing animation file from Evil Islands"
    filepath = bpy.props.StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        self.report({'INFO'}, "executing import")
        path_file = self.filepath
        scene = bpy.context.scene

        if path_file.lower().endswith('.lnk'):
            links, root_of_links = import_lnk(path_file)
            morph_position, rotations, count_frames = import_anm(
                path_file, list(links.keys()))
            anmlnk = order(links, root_of_links)
            scene.frame_start = 0
            scene.frame_end = count_frames
            # WARNING 'If there is an animation with a lot of frames, then the new animation will not overwrite the old one, but only will be inserted on the frames earlier'
            #tmp = [0, 0, 0]
            for fr in range(count_frames):
                scene.frame_set(fr)
                for num in range(len(anmlnk)):
                    # for obj in bpy.data.objects:
                    # for i in range(3):
                    # bpy.data.objects[anmlnk[num]].location[i]=(loc_loc[anmlnk[num]][fr][i])
                    # obj.location[i]=assoc_loc[obj.name][fr][i]-base_bon[obj.name][i]
                    bpy.data.objects[anmlnk[num]].rotation_mode = 'QUATERNION'
                    # for i in range(4):
                    try:
                        bpy.data.objects[anmlnk[num]].rotation_quaternion = rotations[anmlnk[num]][fr]
                    except KeyError:
                        print(
                            str(anmlnk[num]) + ': bodypart is absent but found in animation links')
                    # bpy.data.objects[anmlnk[num]].keyframe_insert(data_path='location', index=-1)
                    bpy.data.objects[anmlnk[num]].keyframe_insert(
                        data_path='rotation_quaternion', index=-1)

        self.report({'INFO'}, "finished import")
        return {'FINISHED'}

    def invoke(self, context, event):
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class testButton(bpy.types.Operator):
    bl_label = "knopo4ka"
    bl_idname = "object.knopo4ka"
    bl_description = "none"

    def execute(self, context):
        self.report({'INFO'}, "Hello friend! Have a nice day :)")
        return {'FINISHED'}

##########################################################################
##########################################################################
############################## BLENDER ZONE ##############################
##########################################################################
##########################################################################

def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.scalefig = bpy.props.FloatProperty(
        name="scale",
        default=2,
        min=0,
        max=3)
    bpy.types.Scene.MorphComp = bpy.props.EnumProperty(
        items=morphing_list,
        name="",
        description="Select morphing component to add")
    bpy.types.Scene.MorphType = bpy.props.EnumProperty(
        items=[
            ('non', 'None', 'Contains only base objects', 1),
            ('smpl', 'Simple', 'Contains base (str & dex optionally) component(s) and scale', 2),
            ('hrd', '^^>H.A.R.D<^^', 'Contains 8 morphed components for EVERY object', 3)
            ],
        name="",
        description="Select type of morphing",
        default='non')
    bpy.types.Scene.selectType = bpy.props.EnumProperty(
        items=[
            ('mrph', 'morph components', 'desc', 1),
            ('grp', 'group range', 'desc', 2),
            ('txtrnmbr', 't_number range', 'desc', 3)
            ],
        name="",
        description="Type of selecting",
        default='mrph')
    bpy.types.Scene.sameUV = bpy.props.StringProperty(
        name="",
        default="ei_unwrap",
    )
    bpy.types.Scene.DestinationDir = bpy.props.StringProperty(
        name="dir",
        default="c:\\",
        description="destination dir for export selected objects as you wish"
    )
    bpy.types.Scene.LnkName = bpy.props.StringProperty(
        name="name",
        default="model"
    )
    bpy.types.Scene.MeshStr = bpy.props.FloatProperty(
        name="str",
        default=0.5,
        step=2,
        update=calculate_mesh)
    bpy.types.Scene.MeshDex = bpy.props.FloatProperty(
        name="dex",
        default=0.5,
        step=2,
        update=calculate_mesh)
    bpy.types.Scene.MeshHeight = bpy.props.FloatProperty(
        name="height",
        default=0.5,
        step=2,
        update=calculate_mesh)
    # bpy.types.Object.uvType = bpy.props.EnumProperty(
    #     items=[
    #         ('wrld', 'World', 'Suitable for static objects and animals in the map\n' +
    #          'Texture: BIGxBIG\n' +
    #          'dds: DXT1 or DXT3', 1),
    #         ('wpn', 'Weapon',
    #          'For weapon in arms\n' +
    #          'Texture: 128x128, alpha-channel is necessary\n' +
    #          'dds: 8.8.8.8 ARGB', 2),
    #         ('shpwpn', 'Shop weapon',
    #          'Weapons for shop\n' +
    #          'Texture: 128x128, alpha-channel is necessary\n' +
    #          'dds: 8.8.8.8 ARGB', 3),
    #         #>>>>>TODO add description to armors
    #         ('armr', 'Armor',
    #          'Armor? Are you sure?', 4),
    #         ('itm', 'Item',
    #          'Items are potions, scrolls, wands and also quest items\n' +
    #          'Texture: 64x64, alpha-channel is necessary\n' +
    #          'dds: 8.8.8.8 ARGB', 5),
    #         ('lt', 'Loot item',
    #          'Materials such as rocks, metalls, animal skin and items only for sale\n' +
    #          'Texture: 64x64, alpha-channel is necessary\n' +
    #          'dds: 8.8.8.8 ARGB', 6)],
    #     name="uv type",
    #     description="uv coordinates type of EI object",
    #     default='wrld',
    #     update=set_uv_type)
    bpy.types.Scene.selectMin = bpy.props.IntProperty(
        name="",
        default=0,
        min=0,
        update=update_range_min
        )
    bpy.types.Scene.selectMax = bpy.props.IntProperty(
        name="",
        default=0,
        min=0,
        update=update_range_max
        )
    bpy.types.Object.ei_group = bpy.props.IntProperty(
        name="group",
        description="I don't know why it needs but EI figures contain different groups",
        default=0,
        step=1,
        min=0,
        update=ei_set_group)
    bpy.types.Object.t_number = bpy.props.IntProperty(
        name="texture number",
        description="Affects on draw in EI.\n" +
        "For example, quick/quest/loot items, world objects use 8 number\n" +
        "Try another number for more information",
        default=0,
        step=1,
        min=0,
        update=ei_set_texture_number)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.Scene.scalefig
    bpy.types.Scene.scale
    bpy.types.Scene.selectType
    bpy.types.Scene.MorphType
    bpy.types.Scene.MorphComp
    bpy.types.Scene.DestinationDir
    bpy.types.Scene.LnkName
    bpy.types.Scene.MeshStr
    bpy.types.Scene.MeshDex
    bpy.types.Scene.MeshHeight
    bpy.types.Object.t_number
    bpy.types.Object.ei_group


if __name__ == "__main__":
    register()
