
function gid(pid) {
  return document.getElementById(pid);
}

let parameters = document.getElementById('parameters');
var iris = { 
  p:{}, 
  send: function(pid, data) {
    var msg = `${pid},${data}`;
    console.log(msg);
    this.websocket.send(msg);
  },
  send_json: function(pid, data) {
    const json = JSON.stringify(data);
    var msg = `${pid},${json}`;
    console.log(msg);
    this.websocket.send(msg);    
  },
  compose_page: function(data) {
    const json = JSON.parse(data);
    build_params(json);
  }
}

var Zorg = {
call: function (_pid) {
  let load = {
    adr: gid(`${_pid}_adr`).value, 
    pid: gid(`${_pid}_pid`).value,
    msg: gid(`${_pid}_msg`).value,
    write: gid(`${_pid}_read`).checked
  }
  iris.send_json(_pid, load)
},
getHTML: function(param) {
  return `
<div style="width: 32%;" class="parameter">
<h3>Send message</h3>
<table>
<td>write: </td><td><input type="checkbox" id="${param.pid}_read"></td><td>unchecked is event</td>
<table>
adr: <input style="width: 50%;" id="${param.pid}_adr"><br>
pid: <input style="width: 50%;" id="${param.pid}_pid"><br>
msg: <input style="width: 50%;" id="${param.pid}_msg"><br>
<button id="${param.pid}_send" class="sm_button green" onclick="Zorg.call(${param.pid})">send</button>
</div>`
  }
}

var Terminal = {
  write : function (terminal, line) {
    var lineElm = document.createElement('div');
      if (line) {
          var time = new Date().toLocaleTimeString();
          lineElm.innerText = "[" + time + "] " + line;
      }
      else
          lineElm.innerHTML = '&nbsp;';
      terminal.appendChild(lineElm);
      terminal.scrollTop = terminal.scrollHeight;
  },
  clear_input: function (e) {
    key = (e.key || e.keyCode);
    // console.log(key);
    if ((key === 13 || key.toUpperCase() === "ENTER") && !e.shiftKey) {
      this.innerHTML = "";
    }
  },
  on_input: function (e) {
    key = (e.key || e.keyCode);
    // console.log(key);
    var index = 0;

    if ((key === 13 || key.toUpperCase() === "ENTER") && !e.shiftKey) {
      // input = getElmById("input-chat");
      line = this.innerHTML.trim();
      line = line.replaceAll('<br>', '\n');
      cleanText = line.replace(/<\/?[^>]+(>|$)/g, "");
      // console.log(cleanText)
      Terminal.write(this.terminal, ">>> " + cleanText);
      index = 0
      // input.innerHTML = "";
      
      iris.send('test', cleanText);
      // console.log(json);
    }
  },
  init: function(param) {
    var term_input = gid(`${param.pid}_input`);
      term_input.terminal = gid(`${param.pid}_terminal`);
      term_input.addEventListener('keydown', Terminal.on_input);
      term_input.addEventListener('keyup', Terminal.clear_input);
    return term_input.terminal
  }
}

var GuiRotatableCamera = {
  getHTML: function(param){
    return `
<div class="parameter" style="width:500px; height:675px">
  <h3>${param.name}</h3>
  <button class="xsm_button green" onclick="GuiRotatableCamera.show_crosshair(${param.pid}, 'visible')">show crosshair</button>
  <button class="xsm_button red" onclick="GuiRotatableCamera.show_crosshair(${param.pid}, 'hidden')">hide crosshair</button>
  <button class="xsm_button pink" onclick="reload_cam('${param.pid}')">reload camera</button>
  <table><tr><td>current rotation: </td><td id="${param.pid}_deg" style="width:40px">0</td><td>camera location</td><td id="cam_loc">${param.url}</td></tr></table>
  <div style="width: 95%;" class="slide_container parameter">deg offset<input type="range" min="0" max="359" value="0" class="slider" oninput="GuiRotatableCamera.rotate_cam(${param.pid}, this)" id="${param.pid}_slider"></div>
  <img id="${param.pid}" src="${param.url}" height="480" width="480" title="Iframe Example" style="transform:rotate(0deg); object-fit:none; border-radius:50%;">
  <img id="${param.pid}_crosshair" src="crosshair.png" style="position:relative; left: 140px; bottom: 347px; height:200px; width:200px">
</div>
`
  },
  rotate_cam: function (pid, slider){
    // iris.send(pid, slider.value)
    document.getElementById(`${pid}_deg`).innerText = slider.value;
    document.getElementById(`${pid}`).style.transform = `rotate(${slider.value}deg)`;
  },
  reload_cam: function (cam){
    console.log('reloading cam');
    document.getElementById(`${pid}`).src = "http://10.203.136.47/video";
  },
  show_crosshair: function (pid, show){
    document.getElementById(`${pid}_crosshair`).style.visibility = show  
    
  }
  
}

var GRBLScara = {
  getHTML: function(param) {
    return `
  <div style="width: 55%;" class="parameter">
  <h3>${param.name}</h3>
  <div><label class="checkbox_container">show status messages<input id="${param.pid}_show_status" type="checkbox"><span class="checkmark"></span></label></div>
  <div id="${param.pid}_terminal" class="terminal"></div>
  <div id="${param.pid}_input" class="term_input" contenteditable="true"></div>
<span style="font-size: 12px; color: grey;">please note this terminal is a direct line to GRBL. It is NOT for python code input. please use regular terminal for that. </span><br><br>

<div style="display: flex">
  <div style="width: 95%;">
    <table style="width: 100%;">
    <tr><td colspan="2">Move Machine:</td><td>Position</td><td>Offset</td><td>Absolute Pos</td><td colspan="2">Encoders</td></tr>
    <tr>
      <td style="width: 5px;"><strong>x: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_x"></td>
      <td><div id="${param.pid}_xpos">None</div></td>
      <td><div id="${param.pid}_xoffset">None</div></td>
      <td><div id="${param.pid}_xabs">None</div></td>
      <td style="width: 5px;">Theta:</td>
      <td><div id="${param.pid}_theta_enc">None</div></td>
    </tr>
    <tr>
      <td><strong>y: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_y"></td>
      <td><div id="${param.pid}_ypos">None</div></td>
      <td><div id="${param.pid}_yoffset">None</div></td>
      <td><div id="${param.pid}_yabs">None</div></td>
      <td>Phi:</td>
      <td><div id="${param.pid}_phi_enc">None</div></td>
    </tr>
    <tr>
      <td><strong>z: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_z"></td>
      <td><div id="${param.pid}_zpos">None</div></td>
      <td><div id="${param.pid}_zoffset">None</div></td>
      <td><div id="${param.pid}_zabs">None</div></td>
    </tr>
    <tr>
      <td style="width: 5px;"><strong>a: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_a"></td>
      <td><div id="${param.pid}_apos">None</div></td>
      <td><div id="${param.pid}_aoffset">None</div></td>
      <td><div id="${param.pid}_aabs">None</div></td>
    </tr>
    <tr>
      <td><strong>b: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_b"></td>
      <td><div id="${param.pid}_bpos">None</div></td>
      <td><div id="${param.pid}_boffset">None</div></td>
      <td><div id="${param.pid}_babs">None</div></td>
    </tr>
    <tr>
      <td><strong>c: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_c"></td>
      <td><div id="${param.pid}_cpos">None</div></td>
      <td><div id="${param.pid}_coffset">None</div></td>
      <td><div id="${param.pid}_cabs">None</div></td>
    </tr>
    <tr>
      <td><strong>feed: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_f" value="500"></td>
      <td><div id="${param.pid}_state">Status: None</div></td>
      <td><div id="${param.pid}_offset_name">Name: None</div></td>
      <td><div id="${param.pid}_blinker" style="height:15px; width:15px; background-color: rgb(11, 111, 93); border: 1px solid black; border-radius: 8px;">&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsphbt</div></td>
    </tr>
    </table>
  </div>

  </div>

    <button id="${param.pid}move_submit" onclick="iris.send_json(${param.pid}, {'cmd': 'move.linear', 'x': gid('${param.pid}move_x').value, 'y': gid('${param.pid}move_y').value, 'z': gid('${param.pid}move_z').value, 'feed':gid('${param.pid}move_f').value})" class="sm_button green">Move</button>
  <hr>
  
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'disable_motors'})" class="sm_button red">disable_motors</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'enable_motors'})" class="sm_button green">enable_motors</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'unlock'})" class="sm_button blue">unlock</button>
  <hr>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_x'})" class="sm_button blue">home_theta</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_y'})" class="sm_button blue">home_phi</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_z'})" class="sm_button blue">home_z</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_a'})" class="sm_button blue">home_a</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_b'})" class="sm_button blue">home_b</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_c'})" class="sm_button blue">home_c</button><br>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'reset_x'})" class="sm_button coral">reset_theta</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'reset_y'})" class="sm_button coral">reset_phi</button>

  <hr>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'listdir'})" class="sm_button coral">listdir</button>
  run script: <input style="width: 50%;" id="${param.pid}_script">
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'run', 'script': gid('${param.pid}_script').value})" class="sm_button blue">open file</button>
  </div>`
  },
  init: function(param) {
    iris.p[param.pid] = function (pid, data) {  // register functions with iris
      const msg = JSON.parse(data);
      if (msg.cmd == 'post') {
        Terminal.write(gid(`${pid}_terminal`), msg.data);
      }
      else if (msg.cmd == 'status') {
        gid(`${param.pid}_xpos`).innerHTML = msg.x;
        gid(`${param.pid}_ypos`).innerHTML = msg.y;
        gid(`${param.pid}_zpos`).innerHTML = msg.z;
        gid(`${param.pid}_theta_enc`).innerHTML = msg.theta_enc;
        gid(`${param.pid}_phi_enc`).innerHTML = msg.phi_enc;
        gid(`${param.pid}_state`).innerHTML = `Status: ${msg.state}`;
        if (gid(`${param.pid}_blinker`).style.backgroundColor != "rgb(12, 19, 17)") {
          gid(`${param.pid}_blinker`).style.backgroundColor = "rgb(12, 19, 17)";
        }
        else {gid(`${param.pid}_blinker`).style.backgroundColor = "rgb(18, 48, 43)";}
        if (gid(`${param.pid}_show_status`).checked == true) {
          Terminal.write(gid(`${pid}_terminal`), JSON.stringify(msg));
        }
      }
      else if (msg.cmd == 'set_offset') {
        gid(`${param.pid}_xoffset`).innerHTML = msg.x;
        gid(`${param.pid}_yoffset`).innerHTML = msg.y;
        gid(`${param.pid}_zoffset`).innerHTML = msg.z;
        gid(`${param.pid}_name`).innerHTML = `Name: ${msg.name}`;
      }
    };
    Terminal.init(param, true);  // initialize the terminal
  }
}

  
var GRBL = {
  getHTML: function(param) {
    return `
  <div style="width: 55%;" class="parameter">
  <h3>${param.name}</h3>
  <div id="${param.pid}_terminal" class="terminal"></div>
  <div id="${param.pid}_input" class="term_input" contenteditable="true"></div>

  <div style="display: flex">
  <div style="width: 95%;">
    <table style="width: 100%;">
    <tr><td colspan="2">Move Machine:</td><td>Position</td><td>Offset</td><td>Absolute Pos</td></tr>
    <tr>
      <td style="width: 5px;"><strong>x: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_x"></td>
      <td><div id="${param.pid}_xpos">None</div></td>
      <td><div id="${param.pid}_xoffset">None</div></td>
      <td><div id="${param.pid}_xabs">None</div></td>
    </tr>
    <tr>
      <td><strong>y: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_y"></td>
      <td><div id="${param.pid}_ypos">None</div></td>
      <td><div id="${param.pid}_yoffset">None</div></td>
      <td><div id="${param.pid}_yabs">None</div></td>
    </tr>
    <tr>
      <td><strong>z: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_z"></td>
      <td><div id="${param.pid}_zpos">None</div></td>
      <td><div id="${param.pid}_zoffset">None</div></td>
      <td><div id="${param.pid}_zabs">None</div></td>
    </tr>
    <tr>
      <td style="width: 5px;"><strong>a: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_a"></td>
      <td><div id="${param.pid}_apos">None</div></td>
      <td><div id="${param.pid}_aoffset">None</div></td>
      <td><div id="${param.pid}_aabs">None</div></td>
    </tr>
    <tr>
      <td><strong>b: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_b"></td>
      <td><div id="${param.pid}_bpos">None</div></td>
      <td><div id="${param.pid}_boffset">None</div></td>
      <td><div id="${param.pid}_babs">None</div></td>
    </tr>
    <tr>
      <td><strong>c: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_c"></td>
      <td><div id="${param.pid}_cpos">None</div></td>
      <td><div id="${param.pid}_coffset">None</div></td>
      <td><div id="${param.pid}_cabs">None</div></td>
    </tr>
    <tr>
      <td><strong>feed: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_f" value="500"></td>
      <td><div id="${param.pid}_state">Status: None</div></td>
      <td><div id="${param.pid}_offset_name">Name: None</div></td>
      <td><div id="${param.pid}_blinker" style="height:15px; width:15px; background-color: rgb(11, 111, 93); border: 1px solid black; border-radius: 8px;">&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsphbt</div></td>
    </tr>
    </table>
  </div>

  </div>

    <button id="${param.pid}move_submit" onclick="iris.send_json(${param.pid}, {'cmd': 'move.linear', 'x': gid('${param.pid}move_x').value, 'y': gid('${param.pid}move_y').value, 'z': gid('${param.pid}move_z').value, 'feed':gid('${param.pid}move_f').value})" class="sm_button green">Move</button>
  <hr>
  
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'disable_motors'})" class="sm_button red">disable_motors</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'enable_motors'})" class="sm_button green">enable_motors</button><br>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'unlock'})" class="sm_button blue">unlock</button>
  <hr>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_x'})" class="sm_button blue">home_x</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_y'})" class="sm_button blue">home_y</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_z'})" class="sm_button blue">home_z</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_a'})" class="sm_button blue">home_a</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_b'})" class="sm_button blue">home_b</button>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'home_c'})" class="sm_button blue">home_c</button>
  <hr>
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'listdir'})" class="sm_button coral">listdir</button>
  run script: <input style="width: 50%;" id="${param.pid}_script">
  <button onclick="iris.send_json(${param.pid}, {'cmd': 'run', 'script': gid('${param.pid}_script').value})" class="sm_button blue">open file</button>
  </div>`
  },
  init: function(param) {
    // on init we hand a function off to iris, when our pid is found she will route the message to that function
    iris.p[param.pid] = function (pid, data) {
      const msg = JSON.parse(data);
      if (msg.cmd == 'post') {
        Terminal.write(gid(`${pid}_terminal`), msg.data);
      }
      else if (msg.cmd == 'status') {
        gid(`${param.pid}_xpos`).innerHTML = msg.x;
        gid(`${param.pid}_ypos`).innerHTML = msg.y;
        gid(`${param.pid}_zpos`).innerHTML = msg.z;
        gid(`${param.pid}_state`).innerHTML = `Status: ${msg.state}`;
        if (gid(`${param.pid}_blinker`).style.backgroundColor != "rgb(12, 19, 17)") {
          gid(`${param.pid}_blinker`).style.backgroundColor = "rgb(12, 19, 17)";
        }
        else {gid(`${param.pid}_blinker`).style.backgroundColor = "rgb(18, 48, 43)";}
      }
      else if (msg.cmd == 'set_offset') {
        gid(`${param.pid}_xoffset`).innerHTML = msg.x;
        gid(`${param.pid}_yoffset`).innerHTML = msg.y;
        gid(`${param.pid}_zoffset`).innerHTML = msg.z;
        gid(`${param.pid}_name`).innerHTML = `Name: ${msg.name}`;
      }
    }
  }
}


// Delete this once textbox has been formally incorporated
function send_textbox(e) {
  // console.log(e);
  // console.log(e.originalTarget);
  var pid = parseInt(e.originalTarget.id); 
  iris.send(pid, e.originalTarget.value)
}


function build_params(params) {
  parameters.innerHTML = "";
  // var these_params = none;
  for (var i = 0; i < params.length; i++) {
      console.log(params[i])
      build_param(params[i]);
  }
}

function build_param(param) {
  var new_param = document.createElement('div');
  var add_listener = false;
  if (param.type == 'checkbox') {
      var checked = "";
      if (param.initial_value) {
          checked = "checked";
      }
      new_param.innerHTML = `<div class="parameter"><label class="checkbox_container">${param.name}<input id="${param.pid}" type="checkbox" onclick="iris.send(${param.pid}, this.checked)"${checked}><span class="checkmark"></span></label></div>`
      iris.p[param.pid] = function (pid, val) {
        let bool;
        console.log(val)
        if (val == 'True'){bool = true;}
        else {bool = false;}  
        
        document.getElementById(pid).checked = bool;
      }
  }

  else if (param.type == 'slider') {

      new_param.innerHTML = `<div style="width: 98%;" class="slide_container parameter">${param.name}<input type="range" min="${param.min}" max="${param.max}" value="${param.initial_value}" class="slider" oninput="iris.send(${param.pid}, parseInt(this.value))" id="${param.pid}"></div>`

      iris.p[param.pid] = function (pid, val) {
          var slider = document.getElementById(pid);
          if (slider.value != val) {
              slider.value = val;
              // console.log('slider  ' + slider.value)
          }
      }
  }

  else if (param.type == 'button') {


      new_param.innerHTML = `<button class="sm_button ${param.color}" onclick="iris.send(${param.pid}, true)" id="${param.pid}">${param.name}</button>`

  }

  else if (param.type == 'text_input') {

      new_param.innerHTML = `<div class="text_input parameter">${param.name}<input type="text" id="${param.pid}" value="${param.initial_value}"></div>`;

      iris.p[param.pid] = function (pid, val) {
          document.getElementById(pid).value = val;
      }
  }

  else if (param.type == 'GRBL') {
    new_param.innerHTML = GRBL.getHTML(param)
  }

  else if (param.type == 'GRBLScara') {
    new_param.innerHTML = GRBLScara.getHTML(param)
  }


  else if (param.type == 'Zorg') {
      new_param.innerHTML = Zorg.getHTML(param)
  }

  else if (param.type == 'GuiRotatableCamera') {
    new_param.innerHTML = GuiRotatableCamera.getHTML(param)
}

  parameters.appendChild(new_param);



  if (param.type == 'text_input') {
      var _param = document.getElementById(param.pid);
      new_param.addEventListener('keyup', send_textbox);
  }
  else if (param.type == 'GRBL') {
    GRBL.init(param)
    // TODO: add open file thing...
  }
  else if (param.type == 'GRBLScara') {
    GRBLScara.init(param)
    // TODO: add open file thing...
  }

}


