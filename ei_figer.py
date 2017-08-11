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
    "version": (2, 4),
    "blender": (2, 78, 0),
    "location": "",
    "description": "Addon for import-export model Evil Islands <-> Blender (without morphing and animations)",
    "wiki_url": "",
    "tracker_url": "konstvest@gmail.com",
    "category": "Import-Export"}

import copy
import os
from math import sqrt
from struct import pack, unpack
import time

import bmesh
import bpy


class EImodelPanel(bpy.types.Panel):
    bl_label = "import-export"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="PACKAGE")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Morphing")
        layout.prop(context.scene, "MorphType")
        if context.scene.MorphType == 'smpl':
            row = layout.row()
            split = row.split(percentage=0.6)
            left = split.column()
            right = split.column()
            left.prop(context.scene, "MorphComp")
            right.operator("object.addmorphcomp", text="Add morph comp")
            layout.prop(context.scene, "scalefig")
        if context.scene.MorphType == 'hrd':
            row = layout.row()
            split = row.split(percentage=0.6)
            left = split.column()
            right = split.column()
            left.prop(context.scene, "MorphComp")
            right.operator("object.addmorphcomp", text="Add morph comp")

        layout.label(text="~")
        layout.prop(context.scene, "UvType")
        layout.operator("object.eimodelimport", text="Import")
        layout.label(text="~")
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
        #pack layers
        #unpack layers
        #layout.operator("object.knopo4ka", text="start button   :)")
        layout.label(text="~")
        layout.operator("object.refresh_test_unit", text="refresh",)
        layout.prop(context.scene, "MeshStr")
        layout.prop(context.scene, "MeshDex")
        layout.prop(context.scene, "MeshHeight")


class animation_panel(bpy.types.Panel):
    bl_label = "animations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon="POSE_DATA")

    def draw(self, context):
        layout = self.layout
        layout.label(text="/~~animation zone~~/")
        layout.operator("object.eimanimationimport", text="Import animation")
        layout.label(text="\.O./")


#time_start = time.time()
fig_table = dict()
bon_table = dict()
mesh_list = list()
pos_list = list()
morph_comp = {0: '', 1: 's~', 2: 'd~', 3: 'u~', 4: 'b~', 5: 'p~', 6: 'g~', 7: 'c~', 8: 'T~'}

def clean():
    for rem_mesh in bpy.data.meshes:
        if rem_mesh.users == 0:
            bpy.data.meshes.remove(rem_mesh)
    for rem_obj in bpy.data.objects:
        if rem_obj.users == 0:
            bpy.data.objects.remove(rem_obj)


def format_obj(cur_obj):
    #for curObj in bpy.data.objects:
    #    if curObj.type == 'MESH':
    bpy.ops.object.transform_apply(rotation=True, scale=True)
    # trianfulate obj
    me = cur_obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method=0, ngon_method=0)
    bm.to_mesh(me)
    bm.free()


def detect_morph(obj, objtype, morph_ind):
    if objtype == 'OBJECT':
        if morph_ind == 1 or morph_ind == 2:
            try:
                obj = bpy.data.objects[morph_comp[morph_ind]+obj.name]
                return obj
            except KeyError:
                obj = bpy.data.objects[obj.name]
                return obj
        if morph_ind == 3:
            try:
                obj = bpy.data.objects[morph_comp[morph_ind]+obj.name]
                return obj
            except KeyError:
                try:
                    obj = bpy.data.objects[morph_comp[1] + obj.name]
                    return obj
                except KeyError:
                    obj = bpy.data.objects[obj.name]
                    return obj
        return obj
    if objtype == 'MESH':
        if morph_ind == 1 or morph_comp == 2 or morph_comp == 4:
            try:
                obj = bpy.data.meshes[morph_comp[morph_ind]+obj.name]
                return obj
            except KeyError:
                obj = bpy.data.meshes[obj.name]
                return obj
        if morph_ind == 3:  #podymat', mb ybrat' etot pynkt, ved' tol'ko pervie 3 nado dlya simple morfa
            try:
                obj = bpy.data.meshes[morph_comp[morph_ind]+obj.name]
                return obj
            except KeyError:
                try:
                    obj = bpy.data.meshes[morph_comp[1] + obj.name]
                    return obj
                except KeyError:
                    obj = bpy.data.meshes[obj.name]
                    return obj
        return obj


def get_hierarchy(parent, hierarchy):
    for child in parent.children:
        hierarchy[child.name] = parent.name
        #print (child.name + ' <= '+parent.name)
        if child.children:
            get_hierarchy(child, hierarchy)


def export_lnk(lnkpath):
    """
    export hierarchy in file as *.lnk.
    """
    #print('lnk: start export ===>')
    time_lnk_start = time.time()
    if not lnkpath.lower().endswith(".lnk"):
        lnkpath += ".lnk"
    export_links = dict()
    root_mesh = ''
    for obj in bpy.data.objects:
        if obj.parent == None and obj.name[0:2] not in morph_comp.values():
            root_mesh = obj.name
            get_hierarchy(obj, export_links)
            break
    links_count = len(export_links)+1
    if len(root_mesh) > 0:
        fl = open(lnkpath, 'wb')
        flr = fl.write
        # write root mesh
        flr(pack('i', links_count))
        frmt = str(len(root_mesh + 'a')) + 's'
        flr(pack('i', len(root_mesh) + 1))
        flr(pack(frmt, root_mesh.encode()))
        flr(pack('i', 0))
        def do_upora(start):  # write lnk
            for d in export_links:
                if export_links[d] == start:
                    flr(pack('i', len(d) + 1))
                    flr(pack(str(len(d) + 1) + 's', d.encode()))
                    flr(pack('i', len(export_links[d]) + 1))
                    flr(pack(str(len(export_links[d]) + 1) + 's', export_links[d].encode()))
                    do_upora(d)
        do_upora(root_mesh)
        fl.close()
        time_lnk_end = time.time() - time_lnk_start
        print ("Lnk export time: %.4f seconds" %time_lnk_end)
    else:
        print ('root mesh of hierarchy is not correct')
    #print('lnk: exported <===')

# FIG EXPORT==============================================================>
class ei_mesh:
    def __init__(self):
        self.name = ''
        self.path = 'c:\\'
        self.header = [0 for i in range(9)]
        self.center = [(0.0, 0.0, 0.0) for i in range(8)]
        self.fmin = [(0.0, 0.0, 0.0) for i in range(8)]
        self.fmax = [(0.0, 0.0, 0.0) for i in range(8)]
        self.radius = [0.0 for i in range(8)]
        self.verts = [[], [], [], [], [], [], [], []]  # [main], [strength], [dexterity], [unique] and scaled
        self.normals = []
        self.t_coords = []
        self.indicies = []
        self.v_c = []

    def read_mesh(self, scn):
        ff = open(self.path, 'rb')
        while 1 == 1:
            # SIGNATURE
            if ff.read(4) == b'FIG8':
                #print ('YES, it is a FIG8-mesh')
                # HEADER
                for c in range(9):
                    tmp = unpack('i', ff.read(4))
                    self.header[c] = tmp[0]
                # Center
                tmp=[0,0,0]
                for c in range (8):
                    for c1 in range (3):
                        tmp[c1] = unpack ('f', ff.read(4))[0]
                    self.center[c]=tuple(tmp)
                # MIN
                for i in range(8):
                    for j in range(3):
                        tmp[j] = unpack('f', ff.read(4))[0]
                    self.fmin[i]=tuple(tmp)
                # MAX
                for i in range(8):
                    for j in range(3):
                        tmp[j] = unpack('f', ff.read(4))[0]
                    self.fmax[i]=tuple(tmp)
                # Radius
                ff.read(32) # xD
                # VERTICES
                block=[[[0 for j1 in range (3)] for j2 in range (8)] for j3 in range (4)]
                m_verts_count = 0
                for ver in range(self.header[0]):
                    for xyz in range(3):
                        for m in range(8):
                            for b in range (4):
                                block[b][m][xyz] = unpack('f', ff.read(4))[0]
                    for v in range (4):
                        for mo in range (8):
                            self.verts[mo].append(tuple(block[v][mo][0:3]))
                    m_verts_count += 1
                del block
                # NORMALS
                ff.read(self.header[1]*64)  #=)
                # TEXTURE COORDS
                # convert uv_type
                if scn.UvType == 'shop_w':
                    uvt = 1
                elif scn.UvType == 'quest' or scn.UvType == 'quick' or scn.UvType == 'loot':
                    uvt = 2
                else:
                    uvt = 0
                for t_c in range(self.header[2]):
                    tmpx = unpack('f', ff.read(4))[0]
                    tmpy = unpack('f', ff.read(4))[0]
                    for uvt_i in range(uvt):
                        tmpx *= 2
                        tmpy = tmpy*2-1
                    self.t_coords.append([copy.copy(tmpx), copy.copy(tmpy)])
                # INDICES
                for i_c in range(self.header[3]):
                    tmp = unpack('h', ff.read(2))
                    self.indicies.append(tmp[0])
                # VERTICES COMPONENTS
                tmp=[0,0]
                for vc in range(self.header[4]):
                    ff.read(2)
                    for vc_i in range(2):
                        tmp[vc_i] = unpack('h', ff.read(2))[0]
                    self.v_c.append(tuple(tmp))
                del tmp
                ff.close()
                break
            else:
                print ('mesh header is not correct')


    def create_mesh(self, MorphT):
        # FACES
        faces = []
        ftemp = [0, 0, 0]
        fi = self.header[3] - 2
        f = 0
        while f < fi:
            for vvv in range(3):
                ftemp[vvv] = self.v_c[self.indicies[f + vvv]][0]
            faces.append([ftemp[0], ftemp[1], ftemp[2]])
            f += 3
        # =====>MESH IN SCENE<======
        if MorphT == 'smpl':
            #try:
            #    scn.scalefig = self.verts[4][0][0] / self.verts[0][0][0]
            #except ZeroDivisionError:
            #    print ('ny ebana')
            models_count = 3
        if MorphT == 'hrd':
            models_count = 8
        if MorphT == 'non':
            models_count = 1
        for i in range (models_count):
            me = bpy.data.meshes.new(name=morph_comp[i]+self.name)
            obj = bpy.data.objects.new(morph_comp[i]+self.name, me)
            obj.location = (0, 0, 0)
            bpy.context.scene.objects.link(obj)
            me.from_pydata(self.verts[i], [], faces)
            me.update()
            if i!=0:
                #pri povtornom importe odnogo i togo je unita na slo9h !=0 objecti
                #zalipaut v nylevom sosto9nii, poka ih ne dernyt
                obj.layers[i] = True
                obj.layers[0] = False

        # UV COORDINATES
        #me.uv_textures.new(name=os.path.splitext(os.path.basename(self.path))[0])  # mogyt bit' zagvozdki pri importe only fig
        mesh=bpy.data.meshes[self.name]
        mesh.uv_textures.new(self.name)
        for t in range(self.header[3]):
            for xy in range (2):
                mesh.uv_layers[0].data[t].uv[xy] = self.t_coords[self.v_c[self.indicies[t]][1]][xy]
        mesh.update()


    def get_from_mesh (self, mesh, sc, m_c):
        """ function for export with full morphing"""
        count_vert = 0
        count_norm = 0
        v_restore = 0
        ind_count = 0
        tmp3 = [0, 0, 0]
        duplicate_vert = 0
        duplicate_ind = [[], []]
        minM = [0, 0, 0]
        maxM = [0, 0, 0]

        # VERTICES & NORMALS
        for mvert in mesh.vertices:
            same_flag = False
            for same_vert in range(count_vert):
                if mvert.co == mesh.vertices[same_vert].co:
                    same_flag = True
                    if m_c == 0:
                        # print ('same_vert: '+str(same_vert)+' duplicate_vert: '+str(duplicate_vert))
                        duplicate_ind[0].append(same_vert)
                        duplicate_ind[1].append(duplicate_vert)
            if not same_flag:
                # vertices
                self.verts[m_c].append(tuple(mvert.co))
                count_vert += 1
                # normals
                if m_c == 0:
                    tmp4 = [mvert.normal[0], mvert.normal[1], mvert.normal[2], 1.0]
                    self.normals.append(tuple(tmp4))
                    count_norm += 1
                    # MIN & MAX PREPARE
                if mvert.index == 0:
                    minM = copy.copy(mvert.co)
                    maxM = copy.copy(mvert.co)
                mi = 0
                while mi < 3:
                    if maxM[mi] < mvert.co[mi]:
                        maxM[mi] = mvert.co[mi]
                    if minM[mi] > mvert.co[mi]:
                        minM[mi] = mvert.co[mi]
                    mi += 1
            if m_c == 0:
                duplicate_vert += 1
        self.fmin[m_c] = copy.copy(minM)
        self.fmax[m_c] = copy.copy(maxM)
        # RADIUS
        self.radius[m_c] = sqrt((self.fmax[m_c][0] - self.fmin[m_c][0]) ** 2 + (self.fmax[m_c][1] - self.fmin[m_c][1]) ** 2 + (self.fmax[m_c][2] - self.fmin[m_c][2]) ** 2) / 2
        # REAL CENTER
        for mcntr in range(3):
            tmp3[mcntr] = (self.fmin[m_c][mcntr] + self.fmax[m_c][mcntr]) / 2
        self.center[m_c] = tuple(tmp3)
        # MIN & MAX
        for i in range(3):
            self.fmin[m_c][i] -= self.center[m_c][i]
            self.fmax[m_c][i] -= self.center[m_c][i]
        if count_vert != 0 and m_c == 0:
            self.header[5] = count_vert
        # align vertices
        if count_vert % 4 != 0:
            v_restore = 4 - count_vert % 4
        for mvert_restore in range(v_restore):
            self.verts[m_c].append((0.0, 0.0, 0.0))
            count_vert += 1
        #if count_vert % 4 == 0 and m_c == 0:
            #print('verts now: ' + str(count_vert) + ' added: ' + str(v_restore))
        if m_c == 0:
            self.header[0] = int(count_vert / 4)
            #for i in range(len(duplicate_ind[0])):
                #print('duplicate vertex: ' + str(duplicate_ind[0][i]) + '<=>' + str(duplicate_ind[1][i]))
            if len(self.normals) % 4 != 0:
                for v_norn_restore in range(4 - len(self.normals) % 4):
                    # print ('len: '+str(len(self.normals))+'\tcount: '+str(count_norm))
                    self.normals.append(copy.copy(self.normals[count_norm - 1]))
                    count_norm += 1
            self.header[1] = int(len(self.normals) / 4)
            #print('normals: ' + str(len(self.normals)))
            ind_ar = []
            for mpoly in mesh.polygons:
                # INDICES PREPARE
                for poly_vrt in mpoly.vertices:
                    same_flag = False
                    for dp_vrt in range(len(duplicate_ind[1])):  # remove duplicate indices
                        if poly_vrt == duplicate_ind[1][dp_vrt]:
                            same_flag = True
                            ind_ar.append(duplicate_ind[0][dp_vrt])
                            # print ('pl_vrt: '+str(poly_vrt)+' ->'+str(duplicate_ind[0][dp_vrt]))
                    if not same_flag:
                        ind_ar.append(poly_vrt)
                    ind_count += 1
            # UV COORDS PREPARE
            uv_ar = []  # array with all t_coords
            new_uv_ind = []
            uv_counter = 0
            for uv_act in mesh.uv_layers.active.data:  # get only active layer with uv_cords
                uv_temp = [uv_act.uv[0], uv_act.uv[1]]
                uv_ar.append(copy.copy(uv_temp))
                if uv_temp not in self.t_coords:
                    self.t_coords.append(copy.copy(uv_temp))
                uv_counter += 1
            self.header[2] = len(self.t_coords)
            self.header[3] = ind_count
            for uv_ind1 in range(len(uv_ar)):  # get indicies of new t_coords array
                for uv_ind2 in range(len(self.t_coords)):
                    if uv_ar[uv_ind1] == self.t_coords[uv_ind2]:
                        new_uv_ind.append(uv_ind2)
            # VERTEX COMPONENTS
            for n_i in range(len(ind_ar)):
                uv_temp = [ind_ar[n_i], new_uv_ind[n_i]]
                if uv_temp not in self.v_c:
                    # print ('uv_temp: '+str(uv_temp))
                    self.v_c.append(copy.copy(uv_temp))  # try to change on tuple (tuple provide error)
            # swap_pts = 0
            for bub in range(len(self.v_c)):
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
            for mix in range(len(ind_ar)):
                for mix1 in range(len(self.v_c)):
                    if (ind_ar[mix] == self.v_c[mix1][0]) & (new_uv_ind[mix] == self.v_c[mix1][1]):
                        self.indicies.append(mix1)
                        break
            # group of object & texture number
            gt_object = {'world': [22, 7], 'weapon': [19, 2], 'shop_w': [18, 2], 'quest': [17, 8], 'quick': [17, 8], 'loot': [18, 8]}
            self.header[7] = gt_object[sc.UvType][0]
            self.header[8] = gt_object[sc.UvType][1]
            #print('group:' + str(self.header[7]) + ' t_number:' + str(self.header[8]))
            # convert uv_type
            #print('UvType: ' + str(sc.UvType))
            if sc.UvType == 'shop_w':
                uvt = 1
            elif sc.UvType == 'quest' or sc.UvType == 'quick' or sc.UvType == 'loot':
                uvt = 2
            else:
                uvt = 0
            for uvt_i in range(uvt):
                for uvt_j in range(len(self.t_coords)):
                    self.t_coords[uvt_j][0] /= 2
                    self.t_coords[uvt_j][1] = 0.5 + self.t_coords[uvt_j][1] / 2

    def get_from_mesh_simple(self, start_mesh, sc):
        for m_c in range (4):
            mesh = detect_morph(start_mesh, 'MESH', m_c)
            scale = sc.scalefig
            count_vert = 0
            count_norm = 0
            v_restore = 0
            ind_count = 0
            tmp3 = [0, 0, 0]
            duplicate_vert = 0
            duplicate_ind = [[], []]
            minM=[0,0,0]
            maxM=[0,0,0]

            # VERTICES & NORMALS
            for mvert in mesh.vertices:
                same_flag = False
                for same_vert in range(count_vert):
                    if mvert.co == mesh.vertices[same_vert].co:
                        same_flag = True
                        if m_c == 0:
                            # print ('same_vert: '+str(same_vert)+' duplicate_vert: '+str(duplicate_vert))
                            duplicate_ind[0].append(same_vert)
                            duplicate_ind[1].append(duplicate_vert)
                if not same_flag:
                    # vertices
                    self.verts[m_c].append(tuple(mvert.co))
                    for i in range(3):
                        tmp3[i] = mvert.co[i] * scale
                    self.verts[m_c + 4].append(copy.copy(tuple(tmp3)))
                    count_vert += 1
                    # normals
                    if m_c == 0:
                        tmp4 = [mvert.normal[0], mvert.normal[1], mvert.normal[2], 1.0]
                        self.normals.append(tuple(tmp4))
                        count_norm += 1
            # MIN & MAX PREPARE
                    if mvert.index == 0:
                        minM = copy.copy(mvert.co)
                        maxM = copy.copy(mvert.co)
                    mi = 0
                    while mi < 3:
                        if maxM[mi] < mvert.co[mi]:
                            maxM[mi] = mvert.co[mi]
                        if minM[mi] > mvert.co[mi]:
                            minM[mi] = mvert.co[mi]
                        mi += 1
                if m_c == 0:
                    duplicate_vert += 1
            self.fmin[m_c] = copy.copy(minM)
            self.fmax[m_c] = copy.copy(maxM)
            for i in range(3):
                tmp3[i] = minM[i] * scale
            self.fmin[m_c + 4] = copy.copy(tmp3)
            for i in range(3):
                tmp3[i] = maxM[i] * scale
            self.fmax[m_c + 4] = copy.copy(tmp3)
            # RADIUS
            self.radius[m_c] = sqrt((self.fmax[m_c][0] - self.fmin[m_c][0]) ** 2
                                    + (self.fmax[m_c][1] - self.fmin[m_c][1]) ** 2
                                    + (self.fmax[m_c][2] - self.fmin[m_c][2]) ** 2) / 2
            self.radius[m_c + 4] = copy.copy(self.radius[m_c] * scale)
            # REAL CENTER
            for mcntr in range(3):
                tmp3[mcntr] = (self.fmin[m_c][mcntr] + self.fmax[m_c][mcntr]) / 2
            self.center[m_c] = tuple(tmp3)
            self.center[m_c + 4] = tuple([tmp3[0] * scale, tmp3[1] * scale, tmp3[2] * scale])
            #MIN & MAX
            for i in range(3):
                self.fmin[m_c][i] -= self.center[m_c][i]
                self.fmin[m_c+4][i] -= self.center[m_c+4][i]
                self.fmax[m_c][i] -= self.center[m_c][i]
                self.fmax[m_c+4][i] -= self.center[m_c+4][i]
            if count_vert != 0 and m_c == 0:
                self.header[5] = count_vert
            # align vertices
            if count_vert % 4 != 0:
                v_restore = 4 - count_vert % 4
            for mvert_restore in range(v_restore):
                self.verts[m_c].append((0.0, 0.0, 0.0))
                self.verts[m_c + 4].append((0.0, 0.0, 0.0))
                count_vert += 1
            #if count_vert % 4 == 0 and m_c == 0:
                #print('verts now: ' + str(count_vert) + ' added: ' + str(v_restore))
            if m_c == 0:
                self.header[0] = int(count_vert / 4)
                #for i in range(len(duplicate_ind[0])):
                    #print('duplicate vertex: ' + str(duplicate_ind[0][i]) + '<=>' + str(duplicate_ind[1][i]))
                if len(self.normals) % 4 != 0:
                    for v_norn_restore in range(4 - len(self.normals) % 4):
                        # print ('len: '+str(len(self.normals))+'\tcount: '+str(count_norm))
                        self.normals.append(copy.copy(self.normals[count_norm - 1]))
                        count_norm += 1
                self.header[1] = int(len(self.normals) / 4)
                #print('normals: ' + str(len(self.normals)))
                ind_ar = []
                for mpoly in mesh.polygons:
                    # INDICES PREPARE
                    for poly_vrt in mpoly.vertices:
                        same_flag = False
                        for dp_vrt in range(len(duplicate_ind[1])):  # remove duplicate indices
                            if poly_vrt == duplicate_ind[1][dp_vrt]:
                                same_flag = True
                                ind_ar.append(duplicate_ind[0][dp_vrt])
                                # print ('pl_vrt: '+str(poly_vrt)+' ->'+str(duplicate_ind[0][dp_vrt]))
                        if not same_flag:
                            ind_ar.append(poly_vrt)
                        ind_count += 1
                # UV COORDS PREPARE
                uv_ar = []
                new_uv_ind = []
                uv_counter = 0
                for uv_act in mesh.uv_layers.active.data:  # get only active layer with uv_cords
                    uv_temp = [uv_act.uv[0], uv_act.uv[1]]
                    uv_ar.append(copy.copy(uv_temp))
                    if uv_temp not in self.t_coords:
                        self.t_coords.append(copy.copy(uv_temp))
                    uv_counter += 1
                self.header[2] = len(self.t_coords)
                self.header[3] = ind_count
                for uv_ind1 in range(len(uv_ar)):  # get indicies of new t_coords array
                    for uv_ind2 in range(len(self.t_coords)):
                        if uv_ar[uv_ind1] == self.t_coords[uv_ind2]:
                            new_uv_ind.append(uv_ind2)
                # VERTEX COMPONENTS
                for n_i in range(len(ind_ar)):
                    uv_temp = [ind_ar[n_i], new_uv_ind[n_i]]
                    if uv_temp not in self.v_c:
                        self.v_c.append(copy.copy(uv_temp)) #try to change on tuple (tuple provide error)
                for bub in range(len(self.v_c)):
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
                for mix in range(len(ind_ar)):
                    for mix1 in range(len(self.v_c)):
                        if (ind_ar[mix] == self.v_c[mix1][0]) & (new_uv_ind[mix] == self.v_c[mix1][1]):
                            self.indicies.append(mix1)
                            break
                # group of object & texture number
                gt_object = {'world': [22, 7],
                             'weapon': [19, 2],
                             'shop_w': [18, 2],
                             'quest': [17, 8],
                             'quick': [17, 8],
                             'loot': [18, 8]}
                self.header[7] = gt_object[sc.UvType][0]
                self.header[8] = gt_object[sc.UvType][1]
                #print('group:' + str(self.header[7]) + ' t_number:' + str(self.header[8]))
                # convert uv_type
                #print('UvType: ' + str(sc.UvType))
                if sc.UvType == 'shop_w':
                    uvt = 1
                elif sc.UvType == 'quest' or sc.UvType == 'quick' or sc.UvType == 'loot':
                    uvt = 2
                else:
                    uvt = 0
                for uvt_i in range(uvt):
                    for uvt_j in range(len(self.t_coords)):
                        self.t_coords[uvt_j][0] /= 2
                        self.t_coords[uvt_j][1] = 0.5 + self.t_coords[uvt_j][1] / 2

    def write_in_file(self):
        fg = open(self.path, 'wb')
        fgr = fg.write
        fgr(b'FIG8')
        # print ('\theader')
        for h in range(9):
            fgr(pack('i', self.header[h]))
        # print ('\tcenter')
        for tmp in range(8):
            for xyz in range(3):
                fgr(pack('f', self.center[tmp][xyz]))
        # print ('\tmin')
        for tmp in range(8):
            for xyz in range(3):
                fgr(pack('f', self.fmin[tmp][xyz]))
        # print ('\tmax')
        for tmp in range(8):
            for xyz in range(3):
                fgr(pack('f', self.fmax[tmp][xyz]))
        # print ('\tradius')
        for tmp in range(8):
            fgr(pack('f', self.radius[tmp]))
        # print ('\tverts')
        ib = 0
        for v_c in range(self.header[0]):
            for xyz in range(3):
                for morph_c in range(8):
                    for block_ind in range(4):
                        fgr(pack('f', self.verts[morph_c][ib + block_ind][xyz]))
            ib += 4
        # print ('\tnormals')
        nb = 0
        for n_c in range(self.header[1]):
            for xyzw in range(4):
                for tmp in range(4):
                    fgr(pack('f', self.normals[nb + tmp][xyzw]))
            nb += 4
        # print ('\ttexture coordinates')
        for t_c in range(self.header[2]):
            for tmp in range(2):
                fgr(pack('f', self.t_coords[t_c][tmp]))
        # print ('\tindicies')
        for ii in range(self.header[3]):
            fgr(pack('h', self.indicies[ii]))
        # print ('\tv_c')
        for v_c_i in range(self.header[4]):
            for tmp in range(2):
                fgr(pack('h', self.v_c[v_c_i][0]))
            fgr(pack('h', self.v_c[v_c_i][1]))
        # print ('\tm_c')
        for m_c_i in range(self.header[5]):
            for tmp in range(2):
                fgr(pack('h', m_c_i))
        fg.close()


def check_hard_morphing (name):
    for i in range (8):
        if (morph_comp[i]+name) not in bpy.data.meshes:
            print ('mesh '+name + 'does not contain all morphing components for HARD morphing\nexport aborted')
            return False
        if (morph_comp[i]+name) not in bpy.data.objects:
            print('object ' + name + 'does not contain all morphing components for HARD morphing\nexport aborted')
            return False
    return True

class ei_bon:
    def __init__ (self):
        self.name = ''
        self.path = 'c:\\'
        self.pos = [(0.0, 0.0, 0.0) for i in range (8)]
    def read_pos(self):
        """read position of figure from bon-file"""
        fb = open(self.path, 'rb')
        btmp = [0, 0, 0]
        for mo in range (8):
            for orig in range(3):
                btmp[orig] = unpack('f', fb.read(4))[0]
            self.pos[mo] = tuple(btmp)
        fb.close()

    def set_pos(self, mt):  #popravit' na otdel'nyu funkciu
        """set position to mesh and this morph components"""
        if mt == 'smpl':
            pos_counter = 3
        if mt == 'hrd':
            pos_counter = 8
        if mt == 'non':
            pos_counter = 1
        for m in range (pos_counter):
            try:
                bpy.data.objects[morph_comp[m]+self.name].location = self.pos[m]
            except KeyError:
                print(morph_comp[m] + self.name + ': object not found in scene')

    def get_pos(self, obj, mo):
        """get position from mesh and his morph friends"""
        self.pos[mo] = tuple(obj.location)

    def get_pos_simple (self, obj, mo, scale):
        """get position from mesh and his morph friends for simple morphing"""
        #print ('obj '+str(obj.name)+' mo: '+str(mo))
        self.pos[mo] = tuple(obj.location)
        print (self.pos[mo])
        tmp = [0.0, 0.0, 0.0]
        for i in range (3):
            tmp[i] = obj.location[i]*scale
        self.pos[mo+4] = tuple(tmp)
        del tmp

    def write_pos(self):
        """write position in file"""
        fb = open (self.path, 'wb')
        for m in range (8):
            for xyz in range (3):
                fb.write (pack('f', self.pos[m][xyz]))
        fb.close()

class EIExport(bpy.types.Operator):
    bl_label = "EI figure export Operator"
    bl_idname = "object.eifigexport"
    bl_description = "Exporting figure file for Evil Islands"
    filepath = bpy.props.StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        self.report({'INFO'}, 'executing export')
        path_file = self.filepath
        scn = bpy.context.scene

        clean()  # delete objects & meshes without users
        for obj in bpy.data.objects:  # set all object to 'OBJECT MODE'
            if obj.type == 'MESH':
                scn.objects.active = obj
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)    #may be unhide all objects

        time_start = time.time()
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                format_obj(obj)  # triangulate and apply RotScale
        time_format = time.time() - time_start

        export_lnk(path_file)

        bpy.ops.object.select_all(action='DESELECT')
        fdir = os.path.dirname(path_file)
        for mesh in bpy.data.meshes:
            if mesh.name[0:2] not in morph_comp.values():
                #print(str(mesh.name) + ': start fig export ===>')
                if scn.MorphType == 'hrd' and check_hard_morphing(mesh.name):
                    cur_m = ei_mesh()
                    cur_m.name = mesh.name
                    cur_m.path = fdir + '\\' + mesh.name + '.fig'
                    for i in range (8):
                        cur_m.get_from_mesh(bpy.data.meshes[morph_comp[i]+mesh.name], scn, i)
                    cur_m.write_in_file()
                if scn.MorphType == 'smpl':
                    cur_m = ei_mesh()
                    cur_m.name = mesh.name
                    cur_m.path = fdir + '\\' + mesh.name + '.fig'
                    cur_m.get_from_mesh_simple(mesh, scn)
                    cur_m.write_in_file()
                if scn.MorphType == 'non':
                    cur_m = ei_mesh()
                    cur_m.name = mesh.name
                    cur_m.path = fdir + '\\' + mesh.name + '.fig'
                    for i in range (8):
                        cur_m.get_from_mesh(mesh, scn, i)
                    cur_m.write_in_file()
                #print(str(mesh.name) + ' <=== finished fig export')
        for obj in bpy.data.objects:
            if obj.name[0:2] not in morph_comp.values():
                print(str(obj.name) + ': start bon export ===>')
                if scn.MorphType == 'hrd' and check_hard_morphing(obj.name):
                    cur_b = ei_bon()
                    cur_b.name = obj.name
                    cur_b.path = fdir + '\\' + obj.name + '.bon'
                    for morph in range(8):  #mb change this function to nonclass function
                        cur_b.get_pos(bpy.data.objects[morph_comp[morph]+obj.name], morph)
                    cur_b.write_pos()
                if scn.MorphType == 'smpl':
                    cur_b = ei_bon()
                    cur_b.name = obj.name
                    cur_b.path = fdir + '\\' + obj.name + '.bon'
                    for morph in range(4):
                        ob = detect_morph(obj, 'OBJECT', morph)
                        cur_b.get_pos_simple(ob, morph, scn.scalefig)
                    cur_b.write_pos()
                if scn.MorphType == 'non':
                    cur_b = ei_bon()
                    cur_b.name = obj.name
                    cur_b.path = fdir + '\\' + obj.name + '.bon'
                    for morph in range(8):
                        cur_b.get_pos(obj, morph)
                    cur_b.write_pos()
                #print (str(obj.name) + ' <=== finished bon export')
        self.report({'INFO'}, "finished export")
        print("time format: %.4f seconds" % time_format)
        return {"FINISHED"}

    def invoke(self, context, event):
        WindowManager = context.window_manager
        WindowManager.fileselect_add(self)
        return {"RUNNING_MODAL"}

class ChooseDir(bpy.types.Operator):
    bl_label = "Choose dir"
    bl_idname = "object.choose_dir"
    directory = bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        #print ('dialog run')
        bpy.context.scene.DestinationDir = self.directory
        #bpy.context.scene.DestinationDir = 'hello'
        #print(self.directory)
        return {'FINISHED'}
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add (self)
        return {"RUNNING_MODAL"}
        #return wm.invoke_props_dialog (self)

class ei_export_only_lnk(bpy.types.Operator):
    bl_label = "export lnk"
    bl_idname = "object.export_only_lnk"
    bl_description = "nya"

    def execute(self, context):
        clean()
        export_lnk(bpy.context.scene.DestinationDir+bpy.context.scene.LnkName)
        self.report({'INFO'}, "Lnk exported")
        return {"FINISHED"}

class ei_export_only_figs(bpy.types.Operator):
    bl_label = "export fig"
    bl_idname = "object.export_only_fig"
    def execute(self, context):
        #print ('export fig')
        clean()
        scn = bpy.context.scene
        sel_obj = bpy.context.selected_objects
        if sel_obj:
            for obj in sel_obj:
                if obj.data.name[0:2] not in morph_comp.values():
                    # print(str(mesh.name) + ': start fig export ===>')
                    format_obj(obj)
                    mesh = bpy.data.meshes[obj.data.name]
                    if scn.MorphType == 'hrd' and check_hard_morphing(mesh.name):
                        cur_m = ei_mesh()
                        cur_m.name = mesh.name
                        cur_m.path = scn.DestinationDir + '\\' + mesh.name + '.fig'
                        for i in range(8):
                            cur_m.get_from_mesh(bpy.data.meshes[morph_comp[i] + mesh.name], scn, i)
                        cur_m.write_in_file()
                    if scn.MorphType == 'smpl':
                        cur_m = ei_mesh()
                        cur_m.name = mesh.name
                        cur_m.path = scn.DestinationDir + '\\' + mesh.name + '.fig'
                        cur_m.get_from_mesh_simple(mesh, scn)
                        cur_m.write_in_file()
                    if scn.MorphType == 'non':
                        cur_m = ei_mesh()
                        cur_m.name = mesh.name
                        cur_m.path = scn.DestinationDir + '\\' + mesh.name + '.fig'
                        for i in range(8):
                            cur_m.get_from_mesh(mesh, scn, i)
                        cur_m.write_in_file()
                        # print(str(mesh.name) + ' <=== finished fig export')
                    self.report({'INFO'}, "Fig's exported")
        return {"FINISHED"}

class ei_export_only_bons(bpy.types.Operator):
    bl_label = "export bon"
    bl_idname = "object.export_only_bon"

    def execute(self, context):
        clean()
        scn = bpy.context.scene
        sel_obj = bpy.context.selected_objects
        for obj in sel_obj:
            if obj.name[0:2] not in morph_comp.values():
                #print(str(obj.name) + ': start bon export ===>')
                if scn.MorphType == 'hrd' and check_hard_morphing(obj.name):
                    cur_b = ei_bon()
                    cur_b.name = obj.name
                    cur_b.path = scn.DestinationDir + '\\' + obj.name + '.bon'
                    for morph in range(8):  #mb change this function to nonclass function
                        cur_b.get_pos(bpy.data.objects[morph_comp[morph]+obj.name], morph)
                    cur_b.write_pos()
                if scn.MorphType == 'smpl':
                    cur_b = ei_bon()
                    cur_b.name = obj.name
                    cur_b.path = scn.DestinationDir + '\\' + obj.name + '.bon'
                    for morph in range(4):
                        ob = detect_morph(obj, 'OBJECT', morph)
                        cur_b.get_pos_simple(ob, morph, scn.scalefig)
                    cur_b.write_pos()
                if scn.MorphType == 'non':
                    cur_b = ei_bon()
                    cur_b.name = obj.name
                    cur_b.path = scn.DestinationDir + '\\' + obj.name + '.bon'
                    for morph in range(8):
                        cur_b.get_pos(obj, morph)
                    cur_b.write_pos()
                #print (str(obj.name) + ' <=== finished bon export')
                self.report({'INFO'}, "Bon's exported")
        return {"FINISHED"}

##########################################################################
########################### OPERATOR ZONE ################################
##########################################################################
def add_morph_comp(act_obj, mc):
    if (mc + act_obj.name) not in bpy.data.objects:
        # copy object
        new_obj = act_obj.copy()
        new_obj.data = act_obj.data.copy()
        new_obj.name = (mc + act_obj.name)
        new_obj.data.name = (mc + act_obj.name)
        bpy.context.scene.objects.link(new_obj)
        # place object in according layer
        for m in morph_comp:
            if morph_comp[m] == mc:
                new_obj.layers[m] = True
                new_obj.layers[0] = False
    else:
        print(act_obj.name + ' it is a bad object to add morph component, try another object')

def morphing_list(self, context):
    list1=[('s~', 'Strength', 'Strength component', 1),
           ('d~', 'Dexterity', 'Dexterity component', 2),
           ('u~', 'Unique', 'Mean between Strength & Dexterity components in one object', 3),
           ('b~', 'Scaled', 'Scaled base figure', 4),
           ('p~', 'Power', 'Scaled strength component', 5),
           ('g~', 'Grace', 'Scaled dexterity component', 6),
           ('c~', 'Common', 'Common scaled strength & scaled dexterity components in one object', 7)]
    list2=[('s~', 'Strength', 'Strength component', 1),
           ('d~', 'Dexterity', 'Dexterity component', 2),
           ('u~', 'Unique', 'Mean between Strength & Dexterity components in one object', 3)]
    if context.scene.MorphType == 'hrd':
        return list1
    else:
        return list2

def calculate_mesh (self, context):
    q_str = bpy.context.scene.MeshStr
    q_dex = bpy.context.scene.MeshDex
    q_height = bpy.context.scene.MeshHeight
    for t_mesh in mesh_list:
        m_verts = fig_table[t_mesh].verts
        for vert in bpy.data.meshes[t_mesh].vertices:
            ind = vert.index
            for i in range (3):
                temp1 = m_verts[0][ind][i]+(m_verts[1][ind][i]-m_verts[0][ind][i])*q_str
                temp2 = m_verts[2][ind][i]+(m_verts[3][ind][i]-m_verts[2][ind][i])*q_str
                value1 = temp1+(temp2-temp1)*q_dex
                temp1 = m_verts[4][ind][i] + (m_verts[5][ind][i] - m_verts[4][ind][i]) * q_str
                temp2 = m_verts[6][ind][i] + (m_verts[7][ind][i] - m_verts[6][ind][i]) * q_str
                value2 = temp1+(temp2-temp1)*q_dex
                final = value1+(value2-value1)*q_height
                vert.co[i] = final
    for t_pos in pos_list:
        m_pos = bon_table[t_pos].pos
        for i in range (3):
            temp1 = m_pos[0][i]+(m_pos[1][i]-m_pos[0][i])*q_str
            temp2 = m_pos[2][i] + (m_pos[3][i] - m_pos[2][i]) * q_str
            value1 = temp1+(temp2-temp1)*q_dex
            temp1 = m_pos[4][i] + (m_pos[5][i] - m_pos[4][i]) * q_str
            temp2 = m_pos[6][i] + (m_pos[7][i] - m_pos[6][i]) * q_str
            value2 = temp1+(temp2-temp1)*q_dex
            final = value1+(value2-value1)*q_height
            bpy.data.objects[t_pos].location[i] = final

class refresh_test_table(bpy.types.Operator):
    bl_label = "EI refresh test unit"
    bl_idname = "object.refresh_test_unit"
    bl_description = "delete current test unit and create new one"

    def execute(self, context):
        scn = bpy.context.scene
        bpy.ops.object.select_all(action='DESELECT')
        T_dict = dict()
        for obj in bpy.data.objects:
            if obj.name[0:2]==morph_comp[8]:
                obj.select = True
                bpy.ops.view3d.layers(nr=9, extend=False)
                bpy.ops.object.delete()
        clean()  # delete objects & meshes without users
        if mesh_list:
            mesh_list.clear()
        if pos_list:
            pos_list.clear()
        if fig_table:
            fig_table.clear()
        if bon_table:
            bon_table.clear()
        for obj in bpy.data.objects:  # set all object to 'OBJECT MODE'
            if obj.type == 'MESH':
                scn.objects.active = obj
                bpy.ops.object.mode_set(mode='OBJECT', toggle=False)  # may be unhide all objects
        for obj in bpy.data.objects:
            if obj.layers[0] and not obj.hide and obj.name[0:2] not in morph_comp.values():
                mesh_list.append(morph_comp[8]+obj.data.name)
                pos_list.append(morph_comp[8]+obj.name)
                if obj.parent == None:
                    T_dict[morph_comp[8]+obj.name] = None
                else:
                    T_dict[morph_comp[8] + obj.name] = morph_comp[8] + obj.parent.name
        for test_mesh in mesh_list:
            cur_m = ei_mesh()
            cur_m.name = test_mesh
            mesh = bpy.data.meshes[test_mesh[2:]]
            if scn.MorphType == 'hrd' and check_hard_morphing(mesh.name):
                for i in range(8):
                    cur_m.get_from_mesh(bpy.data.meshes[morph_comp[i] + mesh.name], scn, i)

            if scn.MorphType == 'smpl':
                cur_m.get_from_mesh_simple(mesh, scn)
            if scn.MorphType == 'non':
                for i in range(8):
                    cur_m.get_from_mesh(mesh, scn, i)
            fig_table[test_mesh] = cur_m

        for test_obj in pos_list:
            cur_b = ei_bon()
            #print ('test obj: '+test_obj)
            cur_b.name = test_obj
            obj = bpy.data.objects[test_obj[2:]]
            if scn.MorphType == 'hrd' and check_hard_morphing(obj.name):
                for morph in range(8):
                    cur_b.get_pos(bpy.data.objects[morph_comp[morph] + obj.name], morph)
            if scn.MorphType == 'smpl':
                for morph in range(4):
                    ob = detect_morph(obj, 'OBJECT', morph)
                    #print ('name: '+str(cur_b.name)+' '+str(cur_b.pos[0]))
                    cur_b.get_pos_simple(ob, morph, scn.scalefig)
            if scn.MorphType == 'non':
                for morph in range(8):
                    cur_b.get_pos(obj, morph)
            bon_table[test_obj] = cur_b
        print ('mesh list: '+str(mesh_list))
        for t in mesh_list:
            fig_table[t].create_mesh('non')
            bpy.data.objects[t].layers[8] = True
            bpy.data.objects[t].layers[0] = False
        create_hierarchy(T_dict)
        for p in pos_list:
            #print (str(p))
            bon_table[p].set_pos('non')

        return {'FINISHED'}



class morph_operators(bpy.types.Operator):
    bl_label = "EI Add Morphing Components"
    bl_idname = "object.addmorphcomp"
    bl_description = "Add morphing component of selected objects"

    def execute(self, context):
        prefix = bpy.context.scene.MorphComp
        new_links = dict()
        clean()
        for obj in bpy.data.objects:
            if obj.name[0:2] not in morph_comp.values():
                if obj.parent == None:
                    get_hierarchy(obj, new_links)
        for obj in bpy.data.objects:
            if obj.select and obj.name[0:2] not in morph_comp.values():
                add_morph_comp(obj, prefix)
        #create new links of morphing components and make hierarchy
        ml = dict()
        for nl in new_links:
            ml[prefix+nl] = prefix + new_links[nl]
        create_hierarchy(ml)
        ml.clear()
        return {'FINISHED'}

##########################################################################
##########################################################################
############################ IMPORT ZONE #################################
##########################################################################
##########################################################################


# LNK IMPORT <==============================================================
def import_lnk(lnkpath):
    lnks = dict()
    f = open(lnkpath, 'rb')
    s = unpack('i', f.read(4))
    for l in range(s[0]):
        tmp1 = unpack('i', f.read(4))[0]
        child = unpack(str(tmp1 - 1) + 's', f.read(tmp1 - 1))[0].decode()
        f.read(1)
        tmp1 = unpack('i', f.read(4))[0]
        if tmp1 == 0:
            lnks[child] = None
            root = child
        else:
            parent = unpack(str(tmp1 - 1) + 's', f.read(tmp1 - 1))[0].decode()
            f.read(1)
            lnks[child] = parent
    f.close()
    return lnks, root


def create_hierarchy(lnks):
    for k in lnks:
        #print(k, lnks[k])
        if lnks[k] != None:
            try:
                bpy.data.objects[k].parent = bpy.data.objects[lnks[k]]
            except KeyError:
                print(str(k) + ': object not found in scene, but found in links of hierarchy')

class EIImport(bpy.types.Operator):
    bl_label = "EI model import Operator"
    bl_idname = "object.eimodelimport"
    bl_description = "Importing model file from Evil Islands"
    filepath = bpy.props.StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        self.report({'INFO'}, "executing import")
        path_file = self.filepath
        scene = bpy.context.scene
        clean()


        if path_file.lower().endswith('.lnk'):
            links, root_mesh = import_lnk(path_file)
            for l in links:
                figfile = os.path.dirname(path_file)+'\\'+l+'.fig'
                if os.path.exists(figfile):
                    cur_m = ei_mesh()
                    cur_m.path = figfile
                    cur_m.name = l
                    cur_m.read_mesh(scene)
                    cur_m.create_mesh(scene.MorphType)

            create_hierarchy(links)
            if scene.MorphType == 'smpl':
                    morph_links = 3
            if scene.MorphType == 'hrd':
                morph_links = 7
            if scene.MorphType == 'non':
                morph_links = 0
            for i in range (morph_links):
                ml = dict()
                for ln in links:
                    if links[ln] == None:
                        ml[str(morph_comp[i + 1]) + str(ln)] = None
                    else:
                        ml[str(morph_comp[i+1])+str(ln)]=str(morph_comp[i+1])+str(links[ln])
                create_hierarchy(ml)
            for l in links:
                bonfile = os.path.dirname(path_file) + '\\' + l + '.bon'
                if os.path.exists(bonfile):
                    cur_b = ei_bon()
                    cur_b.path = bonfile
                    cur_b.name = l
                    cur_b.read_pos()
                    cur_b.set_pos(scene.MorphType)

        if path_file.lower().endswith('.fig'):
            cur_m=ei_mesh()
            cur_m.path=path_file
            cur_m.name=os.path.basename(os.path.splitext(path_file)[0])
            cur_m.read_mesh(scene)
            cur_m.create_mesh(scene.MorphType)

        if path_file.lower().endswith('.bon'):
            cur_b = ei_bon()
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
########################## ANIMATION ZONE ################################
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
            fa = open(os.path.dirname(anmpath) + '\\' + selected[cur] + '.anm', 'rb')
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
                # print (str(cm)+' frame')
                for cmv in range(count_morph_vert):
                    for tr in range(3):
                        tmp[tr] = round(unpack('f', fa.read(4))[0], 4)
            fa.close()
            del trans
            del rot
            del morph
        except FileNotFoundError:
            print(selected[cur] + '.anm -file not found: ')
    return base_loc, base_rot, count_trans


def order(linked, root):
    lnk_order = []

    def do_upora(start):
        for d in linked:
            if linked[d] == start:  # and d!=None:
                lnk_order.append(d)
                do_upora(d)

    do_upora(root)
    #print(lnk_order)
    return lnk_order

class EIanimationImport(bpy.types.Operator):
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
            morph_position, rotations, count_frames = import_anm(path_file, list(links.keys()))
            anmlnk = order(links, root_of_links)
            scene.frame_start = 0
            scene.frame_end = count_frames
            # WARNING 'If there is an animation with a lot of frames, then the new animation will not overwrite the old one, but only will be inserted on the frames earlier'
            #tmp = [0, 0, 0]
            for fr in range(count_frames):
                scene.frame_set(fr)
                for num in range(len(anmlnk)):
                    # for obj in bpy.data.objects:
                    # for i in range (3):
                    # bpy.data.objects[anmlnk[num]].location[i]=(loc_loc[anmlnk[num]][fr][i])
                    # obj.location[i]=assoc_loc[obj.name][fr][i]-base_bon[obj.name][i]
                    bpy.data.objects[anmlnk[num]].rotation_mode = 'QUATERNION'
                    # for i in range (4):
                    try:
                        bpy.data.objects[anmlnk[num]].rotation_quaternion = rotations[anmlnk[num]][fr]
                    except KeyError:
                        print(str(anmlnk[num]) + ': bodypart is absent but found in animation links')
                    # bpy.data.objects[anmlnk[num]].keyframe_insert(data_path='location', index=-1)
                    bpy.data.objects[anmlnk[num]].keyframe_insert(data_path='rotation_quaternion', index=-1)

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


def register():
    bpy.utils.register_module(__name__)
    bpy.types.Scene.scalefig = bpy.props.FloatProperty(name="scale", default=2, min=0, max=3)
    bpy.types.Scene.UvType = bpy.props.EnumProperty(
        items=[('world', 'world_object', 'Any objects in any locations\nTexture: BIGxBIG\ndds: DXT1 or DXT3', 1),
               ('weapon', 'weapon',
                'For weapon in arms\nTexture: 128x128, alpha-channel is necessary\ndds: 8.8.8.8 ARGB', 2),
               ('shop_w', 'shop_weapon',
                'Weapons in arms and weapons in shop have different position of uv coordinates\nTexture: 128x128, alpha-channel is necessary\ndds: 8.8.8.8 ARGB',
                3),
               # ('armors', 'armors', 'Armors? Are you sure?',4),
               ('quest', 'quest_item',
                'For quest items, ofc\nTexture: 64x64, alpha-channel is necessary\ndds: 8.8.8.8 ARGB', 5),
               ('quick', 'quick_item',
                'Items such as potions, scrolls, wands, etc...\nTexture: 64x64, alpha-channel is necessary\ndds: 8.8.8.8 ARGB',
                6),
               ('loot', 'loot_item',
                'Items such as rocks, metalls, animal skin, other materials and items only for sale\nTexture: 64x64, alpha-channel is necessary\ndds: 8.8.8.8 ARGB',
                7)],
        name="type",
        description="Choose UV Mapping type of object do you want to import/export",
        default='world')
    #bpy.types.Scene.morphing = bpy.props.BoolProperty(name="include morphing?", default=True)
    bpy.types.Scene.MorphComp = bpy.props.EnumProperty(
        items=morphing_list,
        name="",
        description="Select morphing component to add")
    bpy.types.Scene.MorphType = bpy.props.EnumProperty(
        items=[('non', 'None', 'it contains only base objects', 1),
               ('smpl', 'simple', 'it contains only base (+str/dex) components', 2),
               ('hrd', '^^>H.A.R.D<^^', 'It is required to contain 8 different figures for EVERY ONE object', 3)],
        name="",
        description="Select type of morphing",
        default='non')
    bpy.types.Scene.DestinationDir = bpy.props.StringProperty (
        name = "dir",
        default = "c:\\",
        description = "destination dir for export selected objects as you wish"
    )
    bpy.types.Scene.LnkName = bpy.props.StringProperty (
        name = "name",
        default = "lnk"
    )
    bpy.types.Scene.MeshStr = bpy.props.FloatProperty(name="str", default=1, step=2, update=calculate_mesh)
    bpy.types.Scene.MeshDex = bpy.props.FloatProperty(name="dex", default=1, step=2, update=calculate_mesh)
    bpy.types.Scene.MeshHeight = bpy.props.FloatProperty(name="height", default=1, step=2, update=calculate_mesh)
def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.Scene.scalefig
    bpy.types.Scene.t_number
    bpy.types.Scene.group
    bpy.types.Scene.scale
    bpy.types.Scene.UvType
    bpy.types.Scene.MorphType
    bpy.types.Scene.MorphComp
    bpy.types.Scene.DestinationDir
    bpy.types.Scene.LnkName
    bpy.types.Scene.MeshStr
    bpy.types.Scene.MeshDex
    bpy.types.Scene.MeshHeight

if __name__ == "__main__":
    register()
