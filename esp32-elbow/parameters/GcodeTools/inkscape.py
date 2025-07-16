def inkscape_compiler(ngc_filename) -> list[dict]:
    with open(ngc_filename, 'r') as ngc_file: 
        output = []
        
        converts = {
        'G21 (All units in mm)\n': {'cmd': 'set_units', 'data': 'mm'},
        'G00 Z5.000000\n': {'cmd': 'tool.off'},
        'G01 Z-0.125000 F100.0(Penetrate)\n': {'cmd': 'tool.on'}   
        }
        
        def parse_segment(segment) -> dict | None:
            axis = segment[0].lower()
            if axis =='z':
                return None
            if axis == 'f':
                axis = 'feed'
            value = round(float(segment[1:]), 3)
            return {axis: value}
        
        def parse_move(line) -> dict:
            line = line.strip()
            line = line.split(' ')
            if line[0] == 'G00':
                cmd = {'cmd': 'move.rapid'}
            else:
                cmd = {'cmd': 'move.linear'}
            
            for segment in line[1:]:
                seg = parse_segment(segment)
                if seg is not None:
                    cmd.update(seg)
            return cmd

        # parse the file
        for line in ngc_file:
            if line in converts:
                output.append(converts[line])
            elif line[:3] == 'G01' or line[:3] == 'G00':
                output.append(parse_move(line))           
                
        return output


if __name__ == "__main__":
    # print("starting")
    import json
    output = []
    current_pos = {'x':0, 'y':0, 'z':0}
    
    for line in inkscape_compiler('GcodeTools/evezor.gcode'):
        cmd = line['cmd']
        if cmd == 'tool.on':
            current_pos['z'] = 0
        elif cmd == 'tool.off':
            current_pos['z'] = 5
        elif cmd == 'move.linear' or cmd == 'move.rapid':
            current_pos['x'] = line['x']
            current_pos['y'] = line['y']
        else:
            pass
        output.append(current_pos.copy())
    
    with open('pts.js', 'w') as f:
        f.write('var pts = ')
        json.dump(output, f)
            

        
            
    
    