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
from . scene_utils import calculate_mesh
from . scene_management import CModel

def register_props():
    scene = bpy.types.Scene
    scene.res_file = bpy.props.StringProperty(
        name='ResFile',
        default='',
        description='*.res file containing models, figures, animations. Usually Figures.res'
    )

    scene.figmodel_name = bpy.props.StringProperty(
        name='Name',
        default='',
        description='Write Model/Figure name to Import/Export'
    )

    scene.animation_name = bpy.props.StringProperty(
        name='Name',
        default='',
        description='Write Animation Name for Import/Export Model/Figure animation'
    )

    scene.morph_comp = bpy.props.EnumProperty(
        items=[
            ('s~', 'str (s~)', 'Strength component', 1),
            ('d~', 'dex (d~)', 'Dexterity component', 2),
            ('u~', 'unique (u~)',
             'Mean combination of Strength & Dexterity components in one object', 3),
            ('b~', 'base(scaled) (b~)', 'Scaled base figure', 4),
            ('p~', 'str(scaled) (p~)', 'Scaled strength component', 5),
            ('g~', 'dex(scaled) (g~)', 'Scaled dexterity component', 6),
            ('c~', 'unique(scaled) (c~)', 'Scaled Unique component', 7)
        ], 
        name='', 
        description='Select morphing component to copy', 
        default='s~'
    )

    scene.mesh_str = bpy.props.FloatProperty(
        name='str',
        default=0.5,
        step=2,
        update=calculate_mesh
    )

    scene.mesh_dex = bpy.props.FloatProperty(
        name='dex',
        default=0.5,
        step=2,
        update=calculate_mesh
    )

    scene.mesh_height = bpy.props.FloatProperty(
        name='height',
        default=0.5,
        step=2,
        update=calculate_mesh
    )

    scene.model = CModel()

def unregister_props():
    scene = bpy.types.Scene
    del scene.res_file
    del scene.figmodel_name
    del scene.animation_name
    del scene.morph_comp

    del scene.mesh_str
    del scene.mesh_dex
    del scene.mesh_height

    del scene.model