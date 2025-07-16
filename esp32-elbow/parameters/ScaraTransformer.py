import math, json
import GcodeTools.inkscape as ink
from pprint import pprint
CartesianPosition = dict # this is a dict of a position
ScaraPosition = dict

class ScaraTransformer:
    def __init__(self, theta_length:float, phi_length:float, max_segment_size: float, work_offset:dict):
        self.theta_len = theta_length
        self.phi_len = phi_length
        
        self.theta_2 = theta_length**2
        self.phi_2 = phi_length**2
        
        self.work_offset = dict(x=0, y=0, z=0, a=0, b=0, c=0, rot=0)
        self.work_offset.update(work_offset)
        work_offset['rot'] = math.radians(work_offset['rot'])
        print(self.work_offset)

        self.max_seg = max_segment_size

        self.prev_scara: ScaraPosition = dict(x=45, y=45, z=0, a=0, b=0, c=0)   # needed for time constant stuff 
        self.prev_cart: CartesianPosition = dict(x=0, y=0, z=0, a=0, b=0, c=0) 

    
    
    def segmentize(self, end: CartesianPosition, feed: int) -> CartesianPosition:
        """ 
        """
        if not self.prev_cart:
            # we are starting fresh and have no previous position
            # TODO: we must calculate this position manually
            start = dict(x=5, y=7, z=0, a=0, b=0, c=0) 
            
        else:
            start = self.prev_cart
        
        # calculate the length of this line
        line_len = self.calc_dist(start, end)

        
        
        if line_len < self.max_seg:
            new_scara = self.translate(end.copy())
            new_scara['z'] = 0
            # new_scara['feed'] = self.calc_dist(self.prev_scara, new_scara)/line_len * feed   # feed is now a ratio of cart_dist/scara_dist
            yield new_scara
            # print(new_scara)
            self.prev_scara = new_scara
            
        
        else:
            num_segs = int(math.ceil(line_len / self.max_seg))
            seg_len = line_len/num_segs
            for i in range(1, num_segs):
                # interpolate
                new_scara = self.translate({axis: (i*end[axis]+(num_segs-i)*start[axis])/num_segs for axis in end.keys()})
                # new_scara['feed'] = self.calc_dist(self.prev_scara, new_scara)/seg_len * feed # feed is now a ratio of cart_dist/scara_dist
                new_scara['z'] = 0
                yield new_scara
                # print(new_scara) 
                self.prev_scara = new_scara
    
    @staticmethod
    def calc_dist(start: dict, end: dict):
        if 'z' in end:
            return math.sqrt((end['x'] - start['x'])**2 + (end['y'] - start['y'])**2 + (end['z'] - start['z'])**2)
        return math.sqrt((end['x'] - start['x'])**2 + (end['y'] - start['y'])**2)
        
    def translate(self, pos: CartesianPosition):
        # rotate
        # print(f'f{pos = }')
        hyp = math.hypot(pos['x'], pos['y'])
        hyp_angle = math.atan2(pos['y'], pos['x'])
        new_hyp_angle = hyp_angle + self.work_offset['rot']
        
        pos['x'] = math.cos(new_hyp_angle) * hyp
        pos['y'] = math.sin(new_hyp_angle) * hyp

        # translate
        for axis, position in pos.items():
            pos[axis] = position + self.work_offset[axis]
            # print(f'{pos = }')
        return pos
    
    def transform(self, point: CartesianPosition, right_handed: bool = True) -> ScaraPosition:
        R = math.hypot(point['x'], point['y'])
        gamma = math.atan2(point['y'], point['x'])
        beta = math.acos((R**2 - self.theta_2 - self.phi_2) / (-2 * self.theta_len * self.phi_2)) 
        psi = math.pi - beta
        alpha = math.asin((self.phi_len * math.sin(psi)) / R)
        
        if right_handed:
            point['x'] = math.degrees(gamma - alpha)
            point['y'] = math.degrees(psi)
        else:
            point['x'] = math.degrees(gamma + alpha)
            point['y'] = math.degrees(beta - math.pi)
    
        return point    

if __name__ == '__main__':
    compiled = ink.inkscape_compiler('nami.gcode')
    # pprint(compiled)
    st = ScaraTransformer(200, 219, .5, dict(x=0, y=0, z=0, a=0, b=0, c=0, rot=180))
    for line in compiled:
        if line['cmd'] != 'move.linear':
            continue
        line.pop('cmd')
        if 'feed' in line:
            line.pop('feed')
        output = [seg for seg in st.segmentize(line, 500)]
    with open('pts2.js', 'w') as f:
        f.write('var pts = ')
        json.dump(output, f)
    print('complete')
        