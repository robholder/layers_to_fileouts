# Layers To Fileouts - View_Layers to EXR Fileouts
## Blender 2.8 addon:

## THIS ADDON IS IN BETA - DO NOT USE ON CRITICAL PROJECTS!!

This is a Blender Addon to create Fileout nodes for each View_layer's 'Render Layers' node - and link each active pass from the Render Layers node to an input on the 'Fileout' node's inputs (ready to be saved as a multilayer EXR output file).

If a View_layer is not enabled, the corresponding 'Render Layers' and 'Fileout' nodes are linked, but are muted.

If there are any beauty passes for the View_layer (AND the Denoise passes are enabled for the View_layer), a Denoise node is included for each of those beauty passes.

The filepath for the EXR Fileouts is derived from the blend-file filepath, and is output to the scene directory's parent, where a 'render_layers' directory is created. The EXR files have the scene file stem followed by the View_layer name and the frame-number.


