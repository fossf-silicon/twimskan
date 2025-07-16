


class Move:
    def __init__(self, machine):
        self.machine = machine

    def linear(self, cmd: dict) -> dict:
        """
        Executes a move in a straight line from the current position
        kwargs: [any available axis] and feed  eg. 'x', 'y', 'theta', 'feed'
        """
        # example: {'cmd': 'move.linear', 'x': 5, 'y': None}
        # print(cmd)
        
        for axis, val in cmd.items():
            cmd[axis] = val + self.machine.offset[axis]

        # print(cmd)
        # post the thing
        post = {'cmd': 'move.linear'}
        for key in self.machine.current_position:
            if self.machine.current_position[key] != self.machine.previous_position[key]:
                post[key] = round(self.machine.current_position[key], 3)
        if 'comment' in cmd:
            post['comment'] = cmd['comment']
        # to_post_or_not_to_post(post)

        # set the previous location to machine for next run
        for key in self.machine.current_position:
            self.machine.previous_position[key] = self.machine.current_position[key]

        yield post

    def rapid(self, **cmd):
        """
        Executes a rapid move
        **Warning** Move may be non-linear, be sure to have proper clearance
        kwargs: [any available axis] and feed  eg. 'x', 'y', 'theta', 'feed'
        """
        for axis in self.machine.axes:
            if axis in cmd:
                if axis in self.machine.work_offset:
                    cmd[axis] += self.machine.work_offset[axis]
                if axis in self.machine.tool_offset:
                    cmd[axis] += self.machine.tool_offset[axis]
                self.machine.current_position[axis] = cmd[axis]

        # post the thing
        post = {'cmd': 'move.rapid'}
        for key in self.machine.current_position:
            if not self.machine.current_position[key] == self.machine.previous_position[key]:
                post[key] = self.machine.current_position[key]
        if 'comment' in cmd:
            post['comment'] = cmd['comment']
        # to_post_or_not_to_post(post)

        for key in self.machine.current_position:
            self.machine.previous_position[key] = self.machine.current_position[key]

        yield post

    def home(self, **cmd):
        """
        Moves machine to endstops or executes applicable find home routine
        kwargs: [any available axis] and will only execute on said axes
        Homing feedrate and other settings found in config
        """
        cmd['cmd'] = 'move.home'
        yield cmd
