#########################################################################
# Copyright (C) 2020 Robert Holder
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#########################################################################


bl_info = {
    "name": "Layers to Fileouts",
    "author": "Robert Holder",
    "version": (1, 1, 1), # last update: fixed mute sticking on render layers nodes
    "blender": (2, 80, 0),
    "location": "Compositor > Node",
    "description": "Manages EXR Fileouts for Render Layers based on View_Layers",
    "warning": "", # used for warning icon and text in addons panel
    "doc_url": "https://github.com/robholder/layers_to_fileouts",
    "category": "Compositing",
}

 
import bpy
import os
import sys


class RPASSES_MT_render_passes_fileouts(bpy.types.Operator):
    bl_idname = "node.render_passes_fileouts"
    bl_label = "Layers to Fileouts"
    bl_description = "Manages EXR Fileouts for Render Layers"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_options = {'REGISTER', 'UNDO'}           


    def execute(self, context):
        
        # -------------------- Functions for the script ----------------------- #

        def get_nodes():
            '''Returns list of nodes'''
            nodes = bpy.context.scene.node_tree.nodes
            return nodes


        def get_layers():
            '''Returns a list of the view_layers in the scene'''
            layers = list(set(bpy.context.scene.view_layers.keys()))
            return layers


        def is_renderlayer_node(node):
            '''Return true if node is a Render Layers node'''
            if node.type == 'R_LAYERS':
                return True


        def renderlayer_nodes_view_layer(node):
            '''Return the view_layer for Render Layers node'''
            return node.layer


        def set_layer(node, layer):
            '''Set node's layer to view_layer'''
            node.layer = layer


        def create_node(node_type):
            '''Creates a specified node'''

            if node_type == "RenderLayers":
                type = "CompositorNodeRLayers"

            elif node_type == "Denoising":
                type = "CompositorNodeDenoise"

            elif node_type == "Fileout":
                type = "CompositorNodeOutputFile"

            else:
                type = "CompositorNodeDenoise"

            return bpy.context.scene.node_tree.nodes.new(type)


        def formal_node_name(node, layer):
            '''Produce a formal node name from the node and the layer name'''
            stem = node_stem_from_type(node)

            return "{} - {}".format(stem, layer)


        def rename_and_relabel_node(node, layer_name):
            '''Rename and Re-label a node appended with the view_layer name'''

            node.name = formal_node_name(node, layer_name)
            node.label = node.name


        def formal_denoise_node_name(node, layer, output):
            '''Produce a formal node name from the node and the layer name'''
            stem = node_stem_from_type(node)

            return "{}-{} - {}".format(stem, output, layer)


        def rename_and_relabel_denoise_node(node, layer_name, output):
            '''Rename and Re-label a node appended with the view_layer name'''

            node.name = formal_denoise_node_name(node, layer_name, output)
            node.label = node.name

            
        def node_stem_from_type(node):
            '''Get formal name stem from node type'''
            if node.type == 'R_LAYERS':
                stem = "Render_Layers"

            elif node.type == 'DENOISE':
                stem = "Denoise"

            elif node.type == 'OUTPUT_FILE':
                stem = "EXR_File_Output"

            return stem


        def reposition_node(node, x, y):
            '''Reposition node to given x and y coordinates'''
            node.location = (x, y)


        def link_nodes(start_node, output, end_node, input):
            '''Link output to input between two nodes'''
            tree = bpy.context.scene.node_tree

            tree.links.new(start_node.outputs[output], end_node.inputs[input])


        def layer_enabled(node, layer):
            '''Test if view_layer is enabled'''
            # Get view_layers path from layer name
            layer_node = bpy.context.scene.view_layers[layer]
            if not layer_node.use:
                node.mute = True
            else:
                node.mute = False


        # List of potential beauty passes suitable for denoise treatment:
        beauty_passes = [
            "Image",
            "Shadow",
            "AO",
            "DiffDir",
            "DiffInd",
            "DiffCol",
            "GlossDir",
            "GlossInd",
            "GlossCol",
            "TransDir",
            "TransInd",
            "TransCol",
            "Emit",
            "Env",
            ]

        # List of denoising passes:
        denoise_passes = [
            "Denoising Normal",
            "Denoising Albedo",
            ]

        
        # --------------- Switch on use_nodes to activate the compositor ---------------- #

        bpy.context.scene.use_nodes = True
        

        # --------------- Get the blendfile name and location path info ----------------- #

        # If the blend file hasn't been saved, set the paths to default
        curr_dir = "//"
        parent_dir = "//"

        # get filename (if saved)
        filename = bpy.path.basename(bpy.data.filepath)
        filename = os.path.splitext(filename)[0]

        # If saved, set the render output paths relative to saved file directory:
        if filename:
            # Furnish file path variables including the parent directory
            curr_dir = os.path.split(bpy.data.filepath)[0]
            parent_dir = os.path.split(curr_dir)[0]


        # ---------------- Set up vars, empty lists and dicts ----------------- #

        # Keep track of view_layers that have a Render Layer node assigned:
        processed_layers = list()

        # Dictionary to store the Render Layer nodes with the view_layer as a value
        render_layer_nodes = dict()
        
        # Specify y value and left-most and rightmost placement for nodes
        x1, x2, y = (0, 1400, 0)


        # --------------------- Get all layers and nodes ---------------------- #

        # List the view_layers in the scene:
        layers = get_layers()

        # List all nodes:
        all_nodes = get_nodes()
        
        
        # --------------- Process existing Render Layers nodes ---------------- #

        # Process the Render Layer nodes if any exist:
        # rename with view layers and add to processed layers list:
        # (Ignore if view_layer already has a processed Render Layers node.)

        # Stop if there are no nodes in the editor:
        if len(all_nodes) > 1:
            
            for node in all_nodes:

                # Process node if it's a Render Layers node:
                if is_renderlayer_node(node):

                    # Get the Render Layer node's view_layer:
                    layer = renderlayer_nodes_view_layer(node)

                    # Only proceed if view_layer hasn't been in any Render Layers node yet:
                    if layer not in processed_layers:
                        # If the node isn't already named correctly, rename to the correct name
                        if node.name != formal_node_name(node, layer):
                            # Rename and Re-label nodes with view_layer name appended:
                            rename_and_relabel_node(node, layer)

                        # Add Render Layers node and corresponding view_layer to dictionary
                        # for later retreval
                        render_layer_nodes[node] = layer

                        # Add view_layer to processed list:
                        processed_layers.append(layer)


        # -------- Create new Render Layers nodes for remaining view_layers -------- #

        # List remaining view_layers that don't have Render Layers nodes):
        remaining = list(i for i in layers if i not in processed_layers)
        
        # Create a new Render Layers node for each remaining view_layer:
        for layer in remaining:

            node = create_node("RenderLayers")
            rename_and_relabel_node(node, layer)
            set_layer(node, layer)

            # Add Render Layers node and corresponding view_layer to dictionary
            render_layer_nodes[node] = layer

            # Add view_layer to processed list:
            processed_layers.append(layer)


        # ------- Create new File Output nodes and arrange in the node graph -------- #

        # Process all Render Layers nodes (position, and add fileout and denoise nodes)
        # Get Render Layers and view_layers from dict

        # un-sorted version
        # for count, (node, layer) in enumerate(render_layer_nodes.items()):
        # sorted version
        
        # shorten variable to shorten for loop line!
        rla = render_layer_nodes
        for count, (node, layer) in enumerate(sorted(rla.items(), key=lambda x: x[1])):


            # Get list of active passes by looking at Render Layers' outputs
            # using a list comprehension (false is a safety net if it fails)
            output_list = [
                key for key, output in node.outputs.items()
                if getattr(output, 'enabled', False)
                ]

            # Prepare y offset for location of nodes:
            
            # base arbitrary vertical offset for each new row of nodes:
            y_offset = 400
            
            # update y location with offset (multiplied by count of new node)
            y_loc = y-(y_offset * count)

            # Position Render Layers node on the lower left of the existing node graph
            reposition_node(node, x1, y_loc)
            
            # Delete existing File Output nodes (that have the view_layer in the name):
            for existing_node in all_nodes:
                if existing_node.type == 'OUTPUT_FILE' and layer in existing_node.name:
                    bpy.context.scene.node_tree.nodes.remove(existing_node)
                elif existing_node.type == 'DENOISE' and layer in existing_node.name:
                    bpy.context.scene.node_tree.nodes.remove(existing_node)

            # Create File Output nodes for each Render Layers node:
            fileout_node = create_node('Fileout')
            # Rename and re-label the fileout node with view_layer suffix:
            rename_and_relabel_node(fileout_node, layer)

            # Set EXR, RGBA and Bit-depth format
            fileout_node.format.file_format = 'OPEN_EXR_MULTILAYER'
            fileout_node.format.color_mode = 'RGBA'
            fileout_node.format.color_depth = '16'
            
            # If view_layer is disabled, mute Render Layers and Filout node:
            layer_enabled(node, layer)
            layer_enabled(fileout_node, layer)

            # Remove original 'Image' slot (to automate replacements later)
            fileout_node.file_slots.remove(fileout_node.inputs["Image"])

            # Create and set File output path: scene filename_view-layer
            file= "{}.".format(layer)

            # Add out Base Path (output)
            out_path = os.path.join(parent_dir, "render_layers", filename, layer, file)
            fileout_node.base_path = out_path

            # Position new node on the lower-right of the existing node graph
            reposition_node(fileout_node, x2, y_loc + 50)

            # Up the color-depth to 32 if there are cryptomatte passes:
            for output in output_list:
                if "Crypto" in output:
                    fileout_node.format.color_depth = '32'
                    # If a cryptomatte is found, stop looking for more:
                    break
                
            # Check if denoise nodes are activated for the render
            denoise_on = set(denoise_passes).issubset(set(output_list))
            # Reset number of denoise nodes (for vertical graph offset calc later):
            denoise_num = 0

            # Connect Render Layers, Fileouts and Denoise nodes:
            for output in output_list:

                # Add output list to Fileout inputs
                fileout_node.file_slots.new(output)

                # Check if a denoise node is needed for the Render Layers output:
                if output in beauty_passes and denoise_on:

                    # keep count of denoise nodes:
                    denoise_num += 1

                    # Create a denoise node
                    denoise_node = create_node("Denoising")
                    # Rename and re-label the new node with layer suffix
                    rename_and_relabel_denoise_node(denoise_node, layer, output)
                    # Position the denoise node between Render Layers and File Out
                    reposition_node(denoise_node, (x1+x2)/2, y_loc)
                    # If view_layer is disabled, mute denoise node:
                    layer_enabled(denoise_node, layer)

                    # Lower the position coordinates for next denoise node
                    y_loc = y_loc - 150

                    # Link up the Render Layers to the Denoise node
                    link_nodes(node, output, denoise_node, "Image")
                    link_nodes(node, "Denoising Normal", denoise_node, "Normal")
                    link_nodes(node, "Denoising Albedo", denoise_node, "Albedo")
                    # Link up the Denoise node to the Fileout node:
                    link_nodes(denoise_node, "Image", fileout_node, output)

                else:
                    # link output of Render Layers directly to the Fileout node:
                    link_nodes(node, output, fileout_node, output)
        
            # ------------- Update y offset for next node in list  --------------- #

            # regular Render Layers offset:
            rl_offset = len(output_list) * 22 - 12
            # Measure height of denoise stack to offset if taller than Render Layers node:
            denoise_stack_height = denoise_num * 150 - 350

            if denoise_stack_height > rl_offset:
                rl_offset = denoise_stack_height

            y = y - rl_offset


        return {'FINISHED'}


classes = [
    RPASSES_MT_render_passes_fileouts,
]


def menu_func(self, context):
    self.layout.operator(RPASSES_MT_render_passes_fileouts.bl_idname)
    
    
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_node.append(menu_func)
    

def unregister():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.NODE_MT_node.remove(menu_func)


if __name__ == "__main__":
    register()
