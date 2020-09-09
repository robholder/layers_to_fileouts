# Blender 2.8 addon:
## View_Layers to EXR Fileouts

This Blender addon is a tool to take all the View_layers in the scene and connect its 'Render Layers' node to a 'Fileout' node in the Compositor - adding each active pass to an input in the 'Fileout' node (to be saved as a layer in the EXR output file).

If a View_layer is not enabled, the corresponding 'Render Layers' and 'Fileout' nodes are connected, but are muted.

If there are any beauty passes for the View_layer AND the Denoise passes are enabled for the View_layer, a Denoise node is included for each beauty pass.

The filepath for the EXR Fileouts is derived from the blend-file filepath, and is output to the scene directory's parent, where a 'render_layers' directory is created. The EXR files have the scene file stem followed by the View_layer name and frame-number.


