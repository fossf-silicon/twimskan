This is a pyQT6 application which runs GDS Factory to generate a technical demonstration of taking content, generating a GDS file and displaying it in KLayout, then generating an SVG file of it and burning it to silicon wafer using a fiber laser.

Key applications used for this demo:

- [GDS Factory](https://github.com/gdsfactory/gdsfactory) for generating GDS components dynamically in Python
- [KLayout](https://www.klayout.de/build.html) to visually view the resulting GDS file
- [KLive](https://gdsfactory.github.io/klive/) (A plugin for KLayout) to dynamically load the GDS file
- [Meerk40t](https://github.com/meerk40t/meerk40t) for Fiber Laser control on Linux.


There are several components needed, and here’s a basic breakdown:

- GDS Factory installation, from github, not from pip3. See below
- Klayout installation, with klive plugin installed, this needs to be running during script execution.
- Meerk40t, this is also running from main github repo, not a binary, see below
- Python3, pip3, typical version used in testing is 3.13.2
- System dependencies and python dependencies, noted below

Note! Make sure all dependencies are running at the same level, aka living in the same folder root, with each project a leaf:

├── open-fab
│   ├── gdsfactory
│   ├── meerk40t
│   └── klayout

### GDS Factory:
Make a folder open-fab, and change to it. Then install gdsfactory:
```bash
python3 -m venv venv/
. ./venv/bin/activate
pip3 install git+https://github.com/gdsfactory/gdsfactory --force-reinstall
Pip3 install pyqt6
```

Follow the instructions below for Meerk40t, and ensure KLayout is installed with KLive.

**Copy the files** from this repo from the laser_workflow folder into the `gdsfactory` folder.  
  
Run `startDemo.sh`  
  
# Setup notes for automatic laser control of the ezCad 2 board.

## Installing 
## Setup Meerk40t on Fedora
Steps are basically:
1. Clone repo
2. Install system dependencies
3. Install python dependencies
4. Copy over udev rule and restart udev

Please not that we use python's venv environment, so you will need to ensure the venv is *active* whenever you run meerk40t.
### Setup application
I set this up on Fedora which uses `dnf`, not `apt` or `apt-get`. For installing system dependencies, I assume packages should be similar on Ubuntu or other debian systems, but in the case of gtk libraries Fedora uses meta packages. The names of the meta packages may be different on Ubuntu.
```bash
git clone https://github.com/meerk40t/meerk40t.git
cd ./meerk40t/
# Create the virtual environment for a local install
python3 -m venv venv/
source venv/bin/activate
# Ensure the system dependencies are met
sudo dnf install pkg-config gtk+-2.0
sudo dnf install gtk2 gtk2-devel gtk3 gtk3-devel 
sudo dnf install libpng libpng-devel
pkg-config gtk+-2.0 --libs
sudo dnf install gtk4 gtk4-devel
# set up python dependencies.
pip3 install setuptools
pip install --upgrade pip
# Amusingly setup doesn't actually pull in all dependencies.
python3 setup.py install
pip3 install pillow
pip3 install image
pip3 install ezdxf opencv-python-headless
pip3 install wxPython 
```

Meerk40t should run now, however you will have permission problems with the usb permissions. Let's fix that:

## Udev rules
We need to add a udev rule to get permissions to talk to the laser driver. Udev rules to the rescue!
Create the file `/etc/udev/rules.d/99-ezCad.rule`, and copy the following into it.

```udev
# We simply say that all devices from BJJCZ which are in the "usb" domain are enumerated with normal user == R/W
SUBSYSTEM=="usb", ATTR{idVendor}=="9588", ATTR{idProduct}=="9899", MODE="0660", GROUP="dialout", TAG+="uaccess", TAG+="udev-acl"
```

Save the file then restart udev:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### Running Meerk40t
Now you should be able to start meerk40t!
```bash
source venv/bin/activate
python3 meerk40t.py
```

You will need to set up the hardware driver at this point:
![[meerk40t-device-setup.png]]

And for actual burning connect to the device:
![[meerk40t-burning-setup.png]]

The following will run load the SVG file listed last and burn it. It also adds a script file to allow changing of operations including power, pulswidth and type for instance.
```bash
python3 meerk40t.py -zab script_filename <svgfile.svg> 
```

Meerk40t allows a lot of scripting on the system, some key aspects are:
```bash
# Load a file with a script to dynamically create
python3 meerk40t.py -b script_filename
```

This file can combine a combination of device commands and geometry commands. See full list at the end. In addition there is a console for quickly running commands inside the app itself.

You can also run commands on the command line, using the `-e` making sure to double quote the string you want to run:
```bash
# Run meerk40t without any user interface (-Z) and no plugins (-p), executing
# the commands for creating a circle and then quiting.
meerk40t -Zpe "circle 5,5,5 quit"
```

## List of commands

```
     Window opened: Console
 help
     --- Base Commands ---
     ??              find <substr>
     alias           alias <alias> <console commands[;console command]*>
     align           align selected elements
     ants            Marching ants of the given element path.
     arc             arc <cx> <cy> <rx> <ry> <start> <end>
     area            provides information about/changes the area of a selected element
     axis_pos        Checks the Axis Position.
     background      use the image as bed background
     batch           Base command to manipulate batch commands.
     beep
     bind            bind <key> <console command>
     box             outline the current selected elements
     bug
     call_url        call_url <url>
     Opens a webpage or REST-Interface page
     camdetect       camdetect: Tries to detect cameras on the system
     camera\d*       camera commands and modifiers.
     camwin          camwin <index>: Open camera window at index
     cd              change directory
     channel         channel (open|close|save|list|print) <channel_name>
     check_for_updates Check whether a newer version of Meerk40t is available
     circ_copy       circ_copy <copies> <radius> <startangle> <endangle> <rotate>
     circle          circle <x> <y> <r>
     circle_arc_path Convert paths to use circular arcs.
     circle_r        circle_r <r>
     classify        classify elements into operations
     clear           Clear console screen
     clear_lock_input_port clear the input_port
     clear_project
     clipboard       clipboard
     clone_init      Initializes a galvo clone board from specified file.
     cls             Clear console screen
     console_font    Sets the console font
     consoleop       <consoleop> - Create new utility operation
     consoleserver   starts a console_server on port 23 (telnet)
     context
     coolant_off     Turns off the coolant for the active device
     coolant_off_by_id Turns the coolant off using the given method
     coolant_on      Turns on the coolant for the active device
     coolant_on_by_id Turns the coolant on using the given method
     coolants        displays registered coolant methods
     correction      set the correction file
     current_position Adds a relative job start position (at the current laser position)
     cut             <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     cycloid         cycloid sx sy r_major r_minor iterations
     cylinder        Cylinder base command
     declassify      declassify selected elements
     device          show device providers
     devinfo         Show current device info.
     dir             list directory
     disable_lock_input_port clear the input_port
     dots            <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     down            cmd <amount>
     echo            Echo text to console
     effect-hatch    adds hatch-effect to scene
     effect-remove   remove effects from element
     effect-wobble   adds wobble-effect to selected elements
     element         element, selected elements
     element([0-9]+,?)+ element0,3,4,5: chain a list of specific elements
     element*        element*, all elements
     elements        Show information about elements
     element~        element~, all non-selected elements
     ellipse         ellipse <cx> <cy> <rx> <ry>
     enable_lock_input_port clear the input_port
     engrave         <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     estop           stops the current job, deletes the spooler
     execute         Loads a given file and executes all lines as commmands (as long as they don't start with a #)
     exit            shuts down the gui and exits
     feature_request
     fiber_config_extend Checks the fiber config extend
     fiber_st_mo_ap  Checks the fiber st mo ap
     file_startup    Execute file startup command list
     fill            fill <svg color>
     fillrule        fillrule <rule>
     find            find <substr>
     flush           flush current settings to disk
     fly_speed       Checks the Fly Speed.
     fly_wait_count  Checks the fiber config extend
     force_correction Resets the galvo laser
     fractal_tree    fractal_tree sx, sy, branch, iterations
     frame           Draws a frame the current selected elements
     full-light      Execute full light idle job
     geometry        Convert any element nodes to paths
     goto            send laser a goto command
     gotoop          <gotoop> <x> <y> - Create new utility operation
     grblmock        starts a grblmock server on port 23 (telnet)
     grid            grid <columns> <rows> <x_distance> <y_distance> <origin>
     growingshape    growingshape sx sy sides iterations
     gui             Provides a GUI wrapper around a console command
     hatch           <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     home            home the laser
     hull            convex hull of the current selected elements
     hull-light      Execute convex hull light idle job
     identify_contour identify contours in image
     image           image <operation>*
     imageop         <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     inkscape        invoke inkscape to convert elements
     input_port      Checks the input_port
     inputop         <outputop, inputop> - Create new utility operation
     keyhole         Set a path-like element as keyhole frame for selected images
     left            cmd <amount>
     lens            set the lens size
     line            adds line to scene
     linecap         linecap <cap>
     linefill        Create a linefill representation of the provided images
     linejoin        linejoin <join>
     linetext        linetext <font> <font_size> <text>
     load            load <file>
     load_types      load_types
     lock            lock the rail
     ls              list directory
     lstatus         Checks the list status.
     mark_count      Checks the Mark Count.
     mark_time       Checks the Mark Time.
     material        material base operation
     matrix          matrix <sx> <kx> <ky> <sy> <tx> <ty>
     module          module [(open|close) <module_name>]
     move            move <x> <y>: move to position.
     move_absolute   move <x> <y>: move to position.
     move_relative   move_relative <dx> <dy>
     move_to_laser   translates the selected element to the laser head
     note            note <note>
     offset          create an offset path for any of the given elements, old algorithm
     offset2         create an offset path for any of the given elements, old algorithm
     op-property-set set operation property to new value
     operation       operation: selected operations.
     operation([0-9]+,?)+ operation0,2: operation #0 and #2
     operation*      operation*: all operations
     operation.*     operation.*: selected operations
     operations      Show information about operations
     operation~      operation~: non selected operations.
     outline         Create an outline path at the inner and outer side of a path
     outputop        <outputop, inputop> - Create new utility operation
     page            Switches to a particular page in the ribbonbar
     pane            control various panes for main window
     path            path <svg path>
     pause           Pauses the currently running job
     penbox          Penbox base operation
     pgrid           pgrid sx, sy, cols, rows, id
     physical_home   home the laser (goto endstops)
     placement       Adds a placement = a fixed job start position
     plan            plan<?> <command>
     plugin
     polycut
     polygon         poly(gon|line) (Length Length)*
     polyline        poly(gon|line) (Length Length)*
     port            Turns port on or off, eg. port off 8
     position        position <tx> <ty>
     position        position <tx> <ty>
     position_xy     Checks the Position XY
     property-set    set property to new value
     pulse           pulse <time>: Pulse the laser in place.
     quit            shuts down the gui and exits
     radial          radial <repeats> <radius> <startangle> <endangle> <rotate>
     raster          <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     raw             sends raw galvo list command exactly as composed
     read_port       Checks the read_port
     recalc
     rect            adds rectangle to scene
     red             Turns redlight on/off
     redo
     reference
     refresh         Refresh the main wxMeerK40 window
     register
     regmark         regmark cmd
     reify           reify affine transformations
     remove_keyhole  Removes keyhole frame for selected images
     render          Create a raster image from the given elements
     render_keyhole  render_keyhole <columns> <rows> <dpi>
     Render selected elements and split the image into multiple parts
     render_split    render_split <columns> <rows> <dpi>
     Render selected elements and split the image into multiple parts
     reset           reset affine transformations
     resize          resize <x-pos> <y-pos> <width> <height>
     restart         shuts down all processes, exits and restarts meerk40t
     resume          Resume the currently running job
     right           cmd <amount>
     rotary          Rotary base command
     rotary_pos      Check the rotary position
     rotary_relative Advance the rotary by the given amount
     rotary_to       Send laser rotary command info.
     rotaryscale     Rotary Scale selected elements
     rotaryview      Rotary View of Scene
     rotate          rotate <angle>
     ruidacontrol    activate the ruidaserver.
     save            save <file>
     save_restore_point
     save_types      save_types
     scale           scale <scale> [<scale-y>]?
     scene
     schedule        show scheduled events
     select-light    Execute selection light idle job
     serial_exchange Talk to a serial port in a blocking manner.
     serial_number   Checks the serial number.
     service         Base command to manipulate services
     set             set [<key> <value>]
     setting_export  Save a copy of the current configuration
     setting_import  Restore a previously saved configuration file
     shape           shape <corners> <x> <y> <r> <startangle> <inscribed> or shape <corners> <r>
     shutdown        shuts down the gui and exits
     signal          sends a signal
     simplify
     softreboot      Resets the galvo laser
     spool           spool <command>
     status          Sends status check
     stop            stops the idle running job
     stroke          stroke <svg color>
     stroke-width    stroke-width <length>
     test
     text            text <text>
     text-anchor     set text object text-anchor; start, middle, end
     text-edit       set text object text to new text
     thread          show threads
     timer.*         run the command a given number of times with a given duration between.
     tool            sets a particular tool for the scene
     trace           trace the given elements
     tracegen        create the trace around the given elements
     translate       translate <tx> <ty>
     tree            access and alter tree elements
     undo
     undolist
     unlock          unlock the rail
     up              cmd <amount>
     usb_abort       Stops USB retries
     usb_connect     connect usb
     usb_disconnect  connect usb
     user_data       Checks the User Data.
     vectorize       Convert given elements to a path
     vent_off        Turns off the coolant for the active device
     vent_off_by_id  Turns the coolant off using the given method
     vent_on         Turns on the coolant for the active device
     vent_on_by_id   Turns the coolant on using the given method
     vents           displays registered coolant methods
     version
     wait
     waitop          <waitop> - Create new utility operation
     webhelp         Launch a registered webhelp page
     webserver       starts a web-serverconsole_server on port 2080 (http)
     window          Base window command
     wordlist        Wordlist base operation
     xload           xload <filename> <x> <y> <width> <height>
     Gets a file and puts it on the screen
     --- align Commands ---
     bed             Set the requested alignment to within the bed
     bottom          align elements at bottom
     center          align elements at center
     centerh         align elements at center horizontally
     centerv         align elements at center vertically
     default         align within selection - all equal
     first           Set the requested alignment to first element selected
     group           Set the requested alignment to treat selection as group
     individual      Set the requested alignment to treat selection as individuals
     last            Set the requested alignment to last element selected
     left            align elements at left
     pop             pushes the current align mode to the stack
     push            pushes the current align mode to the stack
     ref             Set the requested alignment to the reference object
     right           align elements at right
     spaceh          distribute elements across horizontal space
     spaceh2         distribute elements across horizontal space
     spacev          distribute elements across vertical space
     spacev2         distribute elements across vertical space
     top             align elements at top
     view            align elements within viewbox
     xy              align elements in x and y
     --- batch Commands ---
     add             add a batch command 'batch add <line>'
     disable         disable/enable the command at the particular index
     enable          disable/enable the command at the particular index
     remove          delete line located at specific index
     run             execute line located at specific index
     --- camera Commands ---
     background      set background image
     contrast        Turn on AutoContrast
     export          export camera image
     fisheye         fisheye subcommand
     focus
     info            list camera info
     list            list camera settings
     nocontrast      Turn off AutoContrast
     perspective     perspective (set <#> <value>|reset)
     resolution      list available resolutions for the camera
     server
     set             set a particular setting in the camera
     size            force set camera size
     start           Start Camera.
     stop            Stop Camera
     uri             Set camera uri
     --- channel Commands ---
     close           stop watching this channel in the console
     list            list the channels open in the kernel
     open            watch this channel in the console
     print           print this channel to the standard out
     save            save this channel to disk
     --- clipboard Commands ---
     clear           clipboard clear
     contents        clipboard contents
     copy            clipboard copy
     cut             clipboard cut
     list            clipboard list
     paste           clipboard paste
     --- cylinder Commands ---
     axis            Sets the to be used axis (X or Y)
     distance        Sets mirror cylinder distance
     off             Turn cylinder correction off
     on              Turn cylinder correction on
     --- device Commands ---
     activate        Activate a particular device entry
     add             Add a new device and start it
     delete          Delete a particular device entry
     duplicate       Duplicate a particular device entry
     --- elements Commands ---
     align           align selected elements
     ants            Marching ants of the given element path.
     arc             arc <cx> <cy> <rx> <ry> <start> <end>
     area            provides information about/changes the area of a selected element
     circ_copy       circ_copy <copies> <radius> <startangle> <endangle> <rotate>
[1 e4:23:50]     circle          circle <x> <y> <r>
     circle_arc_path Convert paths to use circular arcs.
     circle_r        circle_r <r>
     classify        classify elements into operations
     clear_all       Clear all content
     clipboard       clipboard
     copy            Duplicate elements
     cut             <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     declassify      declassify selected elements
     delete          Delete elements
     difference      Constructive Additive Geometry: Add
     dots            <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     effect-hatch    adds hatch-effect to scene
     effect-remove   remove effects from element
     effect-wobble   adds wobble-effect to selected elements
     ellipse         ellipse <cx> <cy> <rx> <ry>
     engrave         <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     fill            fill <svg color>
     fillrule        fillrule <rule>
     filter          Filter data by given value
     frame           Draws a frame the current selected elements
     geometry        Convert any element nodes to paths
     grid            grid <columns> <rows> <x_distance> <y_distance> <origin>
     hatch           <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     hull            convex hull of the current selected elements
     id              id <id>
     imageop         <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     intersection    Constructive Additive Geometry: Add
     keyhole         Set a path-like element as keyhole frame for selected images
     label           label <label>
     line            adds line to scene
     linecap         linecap <cap>
     linefill        Create a linefill representation of the provided images
     linejoin        linejoin <join>
     list            Show information about the chained data
     lock            Lock element (protect from manipulation)
     matrix          matrix <sx> <kx> <ky> <sy> <tx> <ty>
     merge           merge elements
     move_to_laser   translates the selected element to the laser head
     offset          create an offset path for any of the given elements, old algorithm
     offset2         create an offset path for any of the given elements, old algorithm
     outline         Create an outline path at the inner and outer side of a path
     path_d_info     List the path_d of any recognized paths
     polycut
     polygon         poly(gon|line) (Length Length)*
     polyline        poly(gon|line) (Length Length)*
     position        position <tx> <ty>
     property-set    set property to new value
     radial          radial <repeats> <radius> <startangle> <endangle> <rotate>
     range           Subset existing selection by begin and end indices and step
     raster          <cut/engrave/raster/imageop/dots/hatch> - group the elements into this operation
     recalc
     rect            adds rectangle to scene
     regmark         regmark cmd
     reify           reify affine transformations
     remove_keyhole  Removes keyhole frame for selected images
     render          Create a raster image from the given elements
     render_keyhole  render_keyhole <columns> <rows> <dpi>
     Render selected elements and split the image into multiple parts
     render_split    render_split <columns> <rows> <dpi>
     Render selected elements and split the image into multiple parts
     reset           reset affine transformations
     resize          resize <x-pos> <y-pos> <width> <height>
     rotate          rotate <angle>
     scale           scale <scale> [<scale-y>]?
     select          Set these values as the selection.
     select+         Add the input to the selection
     select-         Remove the input data from the selection
     select^         Toggle the input data in the selection
     shape           shape <corners> <x> <y> <r> <startangle> <inscribed> or shape <corners> <r>
     simplify
     stroke          stroke <svg color>
     stroke-width    stroke-width <length>
     subpath         break elements
     text            text <text>
     text-anchor     set text object text-anchor; start, middle, end
     text-edit       set text object text to new text
     trace           trace the given elements
     tracegen        create the trace around the given elements
     translate       translate <tx> <ty>
     union           Constructive Additive Geometry: Add
     unlock          Unlock element (allow manipulation)
     vectorize       Convert given elements to a path
     xor             Constructive Additive Geometry: Add
     --- geometry Commands ---
     circle          circle <x> <y> <r>
     combine         Constructive Area Geometry, Combine
     copies          Convert any element nodes to paths
     difference      Constructive Area Geometry, difference
     greedy          Perform greedy optimization on the current geometry
     hatch           Add hatch geometry
     hull            convex hull of the current selected elements
     intersection    Constructive Area Geometry, intersection
     light           runs light on events.
     light-simulate  runs light on events.
     node            Convert any shapes to pathnodes
     quad_corners
     rect            adds rectangle to geometry
     rotate          scale <scale-factor>
     round_corners
     scale           scale <scale-factor>
     translate       translate <tx> <ty>
     two-opt         Perform two-opt on the current geometry
     union           Constructive Area Geometry, Union
     uscale          scale <scale-factor>
     validate
     xor             Constructive Area Geometry, xor
     --- image-array Commands ---
     image           image <operation>*
     --- image Commands ---
     add             
     autocontrast    autocontrast image
     background      use the image as bed background
     blur            blur image
     brightness      brighten image
     ccw             rotate image ccw
     color           color enhance
     contour         contour image
     contrast        increase image contrast
     crop            Crop image
     cw              rotate image cw
     detail          detail image
     dewhite         
     dither          Dither to 1-bit
     edge_enhance    enhance edges
     emboss          emboss image
     equalize        equalize image
     find_edges      find edges
     flatrotary      apply flatrotary bilinear mesh
     flip            flip image
     grayscale       convert image to grayscale
     greyscale       convert image to grayscale
     halftone        halftone the provided image
     identify_contour identify contours in image
     innerwhite      identify inner white areas in image
     invert          invert the image
     linefill        Create a linefill representation of the provided images
     lock            lock manipulations
     mirror          mirror image
     path            return paths around image
     pop             Pop pixels for more efficient rastering
     quantize        image quantize <colors>
     remove          Remove color from image
     rgba            
     save            save image to disk
     sharpen         sharpen image
     sharpness       shapen image
     slash           Slash image cutting it horizontally into two images
     slice           Slice image cutting it vertically into two images.
     smooth          smooth image
     solarize        
     threshold       
     unlock          unlock manipulations
     vectrace        return paths around image
     wizard          apply image wizard
     --- inkscape Commands ---
     image           image <operation>*
     input           input filename fn ... - provide the filename to process
     load            inkscape ... load  - load the previous conversion
     locate          inkscape locate    - set the path to inkscape on your computer
     makepng         inkscape makepng   - make a png of all elements
     simplify        inkscape simplify  - convert to plain svg
     text2path       inkscape text2path - convert text objects to paths
     version         inkscape version   - get the inkscape version
     --- materials Commands ---
     delete          Delete materials from persistent settings
     list            Show information about materials
     load            Load materials from persistent settings
     save            Save current materials to persistent settings
     --- ops Commands ---
     clear_all       Clear all content
     copy            Duplicate elements
     delete          Delete elements
     disable         Disable the given operations
     dpi             dpi <raster-dpi>
     empty           Remove all elements from provided operations
     enable          Enable the given operations
     filter          Filter data by given value
     frequency       frequency <kHz>
     hatch-angle     hatch-angle <angle>
     hatch-distance  hatch-distance <distance>
     id              id <id>
     label           label <label>
     list            Show information about the chained data
     material        material base operation
     op-property-set set operation property to new value
     passes          passes <passes>
     penbox_pass     Set the penbox_pass for the given operation
     penbox_value    Set the penbox_value for the given operation
     plan            plan<?> <command>
     power           power <ppi>
     range           Subset existing selection by begin and end indices and step
     select          Set these values as the selection.
     select+         Add the input to the selection
     select-         Remove the input data from the selection
     select^         Toggle the input data in the selection
     speed           speed <speed>
     --- panes Commands ---
     create          create a floating about pane
     dock            Dock the pane
     float           Float the pane
     hide            show the pane
     load            load pane configuration
     lock            lock the panes
     reset           reset all panes restoring the default perspective
     save            load pane configuration
     show            show the pane
     toggleui        Hides/Restores all the visible panes (except scene)
     unlock          unlock the panes
     --- penbox Commands ---
     add             add pens to the chosen penbox
     del             delete pens to the chosen penbox
     set             set value in penbox
     --- plan Commands ---
     blob            plan<?> blob
     clear           plan<?> clear
     console         plan<?> command
     copy            plan(-selected)<?> copy
     copy-selected   plan(-selected)<?> copy
     geometry        plan<?> geometry
     optimize        plan<?> optimize
     preopt          plan<?> preopt
     preprocess      plan<?> preprocess
     return          plan<?> return
     save_job        save job export
     spool           spool <command>
     sublist         plan<?> sublist
     validate        plan<?> validate
     --- scene Commands ---
     aspect
     color
     focus
     grid            grid <target> <rows> <x_distance> <y_distance> <origin>
     pan
     reset
     rotate
     zoom
     --- service Commands ---
     activate        Activate the service at the given index
     destroy         Destroy the service at the given index
     start           Initialize a provider
     --- spooler Commands ---
     clear           spooler<?> clear
     down            cmd <amount>
     home            home the laser
     left            cmd <amount>
     list            spool<?> list
     lock            lock the rail
     move            move <x> <y>: move to position.
     move_absolute   move <x> <y>: move to position.
     move_relative   move_relative <dx> <dy>
     physical_home   home the laser (goto endstops)
     right           cmd <amount>
     send            send a plan-command to the spooler
     unlock          unlock the rail
     up              cmd <amount>
     --- tree Commands ---
     bounds          view tree bounds
     delegate        delegate commands to focused value
     delete          delete the given nodes
     dnd             Drag and Drop Node
     emphasized      delegate commands to focused value
     highlighted     delegate commands to sub-focused value
     list            view tree
     menu            Load menu for given node
     remove          forcefully deletes all given nodes
     selected        delegate commands to focused value
     targeted        delegate commands to sub-focused value
     --- window Commands ---
     close           close the supplied window
     displays        Give display info for the current opened windows
     list            List available windows.
     open            open/toggle the supplied window
     reset           reset the supplied window, or '*' for all windows
     toggle          open/toggle the supplied window
     --- wordlist Commands ---
     add             add value to wordlist
     addcounter      add numeric counter to wordlist
     advance         advances all indices in wordlist (if wordlist was used)
     backup          Saves the current wordlist
     get             get current value from wordlist
     index           sets index in wordlist
     list            list wordlist values
     load            Attach a csv-file to the wordlist
     restore         Loads a previously saved wordlist
     set             set value to wordlist
 planz copy preprocess validate blob preopt optimize
     Copied Operations.
 window toggle Simulation z
     Window opened: Simulation
 planz clear


```