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

class IMPORT_EXPORT_PT_PANEL(bpy.types.Panel):
    bl_label = 'import-export'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='PACKAGE')

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        elem = row.split(factor=0.8)
        elem.prop(context.scene, 'res_file')
        elem.operator('object.choose_resfile', text='...')
        #layout.label(text='Models and Figures')
        layout.prop(context.scene, 'figmodel_name')
        layout.operator('object.model_import', text='Import')
        layout.operator('object.model_export', text='Export')


class OPERATOR_PT_PANEL(bpy.types.Panel):
    bl_label = 'operations'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='MOD_SCREW')

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        split = row.split(factor=0.35)
        left = split.column()
        #morphing
        row = layout.row()
        split = row.split(factor=0.4)
        left = split.column()
        left.operator('object.addmorphcomp', text='Copy as')
        right = split.column()
        comp = right.split()
        comp.prop(context.scene, 'morph_comp')
        #automorph (in progress now)
        # row = layout.row()
        # row.operator('object.automorph', text="Auto Morph")

class ANIMATION_PT_PANEL(bpy.types.Panel):
    bl_label = 'animations'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EI_Tools'

    def draw_header(self, context):
        layout = self.layout
        layout.label(text='', icon='POSE_HLT')

    def draw(self, context):
        layout = self.layout
        #layout.label(text='Animations')
        layout.prop(context.scene, 'animation_name')
        layout.operator('object.animation_import', text='Import')
        layout.operator('object.animation_export', text='Export')

