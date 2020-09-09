# Blender 2.8 addon:
## View_Layers to EXR Fileouts

This add on is a tool to take all the view_layers in the scene and connect each to a fileout node in the Compositor - adding each pass to an input (to be saved as a layer in the EXR output file).

If the view_layer is not enabled, the Render Layer and Filout nodes are connected but mutted.

If there are any 'beauty' passes for the view_layer, AND the Denoise passes are enabled, a Denoise node is included for each beauty pass.

The filepath for the EXR Fileouts is derived from the scene filepath, and is output to the scene directory parent, where a 'render_layers' directory is created. The EXR files have the scene file stem followed by the view_layer name and frame-number.


