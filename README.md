# slic3r2aerotech
 Slice an STL with Slic3r and then make it work on an Aerotech

## Slic3r configuration details

- Slic3r must be set to produce verbose GCode.
- Turn off heat bed, fans, and other things not meaningful to the AeroTech
- Also recommended to remove the skirt and brim

For an example config file for 1 extruder see:
(slic3r2aerotech/src/main/resources/single_solid_config_bundle.ini)
For an example config file for 2 extruders see:
(slic3r2aerotech/src/main/resources/multi_solid_config_bundle.ini)

### Multimaterial considerations
You'll still need to measure offsets

## Dependencies
- conda install pip
- pip install fbs
- conda install -c anaconda pyqt    