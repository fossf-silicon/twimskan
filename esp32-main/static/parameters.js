function toggle_all(direction) {
  buttons = document.getElementsByClassName('toggler')
  for (const button of buttons) {
    toggleCollapsible(button, direction);
  }
}
function expand_all() {
  buttons = document.getElementsByClassName('toggler')
  for (const button of buttons) {
    toggleCollapsible(button);
  }
}

function gid(pid) {
  return document.getElementById(pid);
}

// async function send_cmd(pid, url, payload, callback) {
//   const response = await fetch('/iamhere', {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json'
//     },
//     body: JSON.stringify({ data: payload })
//   });


//   if (!response.ok) {
//     console.log('some problem in send_cmd');
//   }

//   const resp = await response.text();
//   callback(pid, resp)

// }

/**
 * MessageQueue manages messages by pid, ensuring that:
 * - The first message of a given ID is sent immediately.
 * - If a new message with the same ID arrives before the timeout, it replaces the previous message.
 * - If no new message arrives within the timeout, the last stored message is sent.
 * - After the timeout expires, the ID is cleared from the queue, allowing new messages with that ID to be sent.
 *
 * @class MessageQueue
 * @param {number} duration - The delay duration in milliseconds before allowing a new message for the same ID.
 */
class MessageQueue {
  constructor(duration = 50) {
    this.queue = new Map();
    this.duration = duration;
  }

  /**
   * Sends a message with a given ID.
   * If the ID is not in the queue, the message is sent immediately.
   * If the ID is already in the queue, the message replaces the previous one and resets the timeout.
   *
   * @param {number} id - The unique identifier for the message.
   * @param {string} message - The message content.
   * @param {function} callback - The function to call with the message.
   */
  sendMessage(id, message, callback) {
    if (!this.queue.has(id)) {
      callback(id, message);
      const timeout = setTimeout(() => {
        this.queue.delete(id);
      }, this.duration);
      this.queue.set(id, { message, callback, timeout });
    } else {
      clearTimeout(this.queue.get(id).timeout);
      const timeout = setTimeout(() => {
        this.queue.get(id).callback(id, this.queue.get(id).message);
        this.queue.delete(id);
      }, this.duration);
      this.queue.set(id, { message, callback, timeout });
    }
  }
}

class Hermes {
  constructor() {
    this.p = {};
    this.files = [];
    this.websocket = null;
    this.file_sender = {
      filename: "",
      chunks: [],
      index: 0,
      closed: true,
    }
  }
  send(pid, data) {
    var msg = `${pid},${data}`;
    this.websocket.send(msg);
  }
  send_json(pid, data) {
    const json = JSON.stringify(data);
    var msg = `${pid},${json}`;
    this.websocket.send(msg);
  }
  compose_page(data) {
    const json = JSON.parse(data);
    build_params(json);
  }
  listdir(data) {
    const files = JSON.parse(data);
    this.files = files.data;
    let buttons = document.getElementById('file_buttons');
    buttons.innerHTML = "";
    for (const file of files.data) {
      let button = document.createElement('button');
      button.innerText = file;
      button.onclick = function () {
        hermes.send('get_file', this.innerText)
      };
      buttons.appendChild(button);
    }
  }
  to_file_editor(data) {
    const comma_index = data.indexOf(',');
    const filename = data.substring(0, comma_index);
    const file = data.substring(comma_index + 1);
    document.getElementById('file_editor_filename').innerHTML = filename;
    const editor = document.getElementById('file_editor');
    editor.value = file;
    editor.style.height = (editor.scrollHeight + 80) + 'px';
  }
  create_new_file() {
    const filename_display = document.getElementById('file_editor_filename');
    const new_filename = gid('filecreator_new').value;
    if (new_filename == "") { console.log('no filename'); return; }
    filename_display.innerHTML = new_filename;
    this.file_sender.filename = new_filename;
    this.save_file();
  }
  save_file() {
    // sends file chunks over websocket
    this.file_sender.filename = document.getElementById('file_editor_filename').innerHTML;
    if (this.file_sender.filename == 'filename') {
      return
    }
    this.file_sender.chunks = [];
    const chunkSize = 700;
    const file = document.getElementById('file_editor').value;
    let startIndex = 0;

    while (startIndex < file.length) {
      const chunk = file.substring(startIndex, startIndex + chunkSize);
      this.file_sender.chunks.push(chunk);
      startIndex += chunkSize;
    }
    this.file_sender.closed = false;
    this.file_sender.index = 0;
    this.send_chunk();
  }
  send_chunk() {
    let type = 'chunk,'
    if (this.file_sender.index == 0) {
      if (this.file_sender.chunks.length == 1) {
        type = `newsingle,${this.file_sender.filename},`
      }
      else {
        type = `new,${this.file_sender.filename},`
      }
    }
    else if (this.file_sender.index >= this.file_sender.chunks.length - 1) {
      type = 'end,'
      this.file_sender.closed = true
    }
    const chunk = this.file_sender.chunks[this.file_sender.index];
    // console.log(chunk);
    const type_chunk = `${type}${chunk}`;
    this.send('save_file', type_chunk);
    this.file_sender.index += 1;
  }
}

let parameters = document.getElementById('parameters');
var constructors = {}
var hermes = new Hermes()

class GuiParameter {
  constructor(param, div) {
    this.pid = param.pid;
    this.param = param;
    this.div = div;
    this.div.innerHTML = this.getHTML(param);
  }
  getHTML(param) {
    return `{{ html }}`
  }
  call(val) {
    console.log(val);
  }
}

var Terminal = {
  write: function (terminal, line) {
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
      // This is a HACK and should probably do something else, like call a function owned by the terminal owner and they can send to hermes however they see fit
      json = { "cmd": "term", "msg": cleanText }
      hermes.send_json(this.terminal.pid, json);
      console.log(json);
    }
  },
  init: function (param) {
    var term_input = gid(`${param.pid}_input`);
    term_input.terminal = gid(`${param.pid}_terminal`);
    term_input.terminal.pid = param.pid;
    term_input.addEventListener('keydown', Terminal.on_input);
    term_input.addEventListener('keyup', Terminal.clear_input);
    return term_input.terminal
  }
}
















class FileSender extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    print('FileSender constructor');
    this.progress_bar = document.getElementById(`${param.pid}_file`);
    this.send_button = document.getElementById(`${param.pid}_send`);
    this.send_button.onclick = () => {this.send()};
  }

  getHTML(param) {
    return `<div class="parameter" style="max-width: 500px">
    <span style="font-size: large;">${param.name}</span>
    <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)"
        style="float:right;">-</button>
    <div>
        <label for="${param.pid}_file">progress:</label>
        <progress id="${param.pid}_file" value="0" max="100"></progress><br>
        <label>local filename<label>
        <input type="text" style="width: 100%;" id="${param.pid}_local_filename" value="test.py">
        <label>remote adr<label>
        <input type="number" style="width: 100%;" id="${param.pid}_adr" value="10">
        <label>remote pid<label>
        <input type="number" style="width: 100%;" id="${param.pid}_pid" value="65000">
        <label>remote filename<label>
        <input type="text" style="width: 100%;" id="${param.pid}_remote_filename" value="testing.py">
        <button class="xsm_button green" id="${param.pid}_send">Send</button>
    </div>
</div>`
  }

  call(val) {
    this.progress_bar.value = val;
  }

  send() {
    let remote_adr = gid(`${this.pid}_adr`).value;
    let remote_pid = gid(`${this.pid}_pid`).value;
    let remote_filename = gid(`${this.pid}_remote_filename`).value;
    let local_filename = gid(`${this.pid}_local_filename`).value;
    hermes.send_json(this.pid, {'remote_adr': remote_adr, 'remote_pid': remote_pid, 'remote_filename': remote_filename, 'local_filename': local_filename});
  }
}
constructors['FileSender'] = FileSender;




class GRBL extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    const self = this;

    this.tabs = {
      machine: {button: gid(`${param.pid}_machine_button`), tab: gid(`${param.pid}_machine_tab`)},
      work_offsets: {button: gid(`${param.pid}_work_offsets_button`), tab: gid(`${param.pid}_work_offsets_tab`)},
      tool_offsets: {button: gid(`${param.pid}_tool_offsets_button`), tab: gid(`${param.pid}_tool_offsets_tab`)},
      term: {button: gid(`${param.pid}_term_button`), tab: gid(`${param.pid}_term_tab`)}
    }

    for (const [key, value] of Object.entries(this.tabs)) {
      value.button.addEventListener('click', function () { self.set_tabs(key) });
    }
    
    this.create_machine_table();
    this.create_grbl_coms_table();
    Terminal.init(param, true);  // initialize the terminal
  }

  create_machine_table() {
    const machine_table = gid(`${this.pid}_machine_table`);
    console.log(machine_table);
    // First row: Move Machine headers
    const headerRow = document.createElement('tr');
    const headers = [
        { text: 'Move Machine:', colspan: 2 },
        'Position',
        'Offset',
        'Absolute Pos',
        { text: 'Encoders', colspan: 2 }
    ];

    headers.forEach(header => {
        const th = document.createElement('td');
        if (typeof header === 'object') {
            th.textContent = header.text;
            th.colSpan = header.colspan;
        } else {
            th.textContent = header;
        }
        headerRow.appendChild(th);
    });
    machine_table.appendChild(headerRow);

    // Axes rows: t, p, z, a, b, c
    const axes = ['x', 'y', 'z', 'a', 'b', 'c'];
    axes.forEach(axis => {
        const row = document.createElement('tr');

        // Label cell
        const labelCell = document.createElement('td');
        labelCell.innerHTML = `<strong>${axis}: </strong>`;
        labelCell.style.width = '5px';
        row.appendChild(labelCell);

        // Input cell
        const inputCell = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'number';
        input.style.width = '100%';
        input.id = `${this.pid}move_${axis}`;
        inputCell.appendChild(input);
        row.appendChild(inputCell);

        // Position, Offset, Absolute Pos cells
        ['pos', 'offset', 'abs', 'enc'].forEach(suffix => {
            const cell = document.createElement('td');
            const div = document.createElement('div');
            div.id = `${this.pid}_${axis}${suffix}`;
            div.textContent = 'None';
            cell.appendChild(div);
            row.appendChild(cell);
        });

        machine_table.appendChild(row);
    });

    // Feed row
    const feedRow = document.createElement('tr');

    // Feed label and input
    const feedLabelCell = document.createElement('td');
    feedLabelCell.innerHTML = '<strong>feed: </strong>';
    feedRow.appendChild(feedLabelCell);

    const feedInputCell = document.createElement('td');
    const feedInput = document.createElement('input');
    feedInput.type = 'number';
    feedInput.style.width = '100%';
    feedInput.id = `${this.pid}move_f`;
    feedInput.value = '500';
    feedInputCell.appendChild(feedInput);
    feedRow.appendChild(feedInputCell);

    // Status and Offset Name cells
    const statusCell = document.createElement('td');
    const statusDiv = document.createElement('div');
    statusDiv.id = `${this.pid}_state`;
    statusDiv.textContent = 'Status: None';
    statusCell.appendChild(statusDiv);
    feedRow.appendChild(statusCell);

    const offsetNameCell = document.createElement('td');
    const offsetNameDiv = document.createElement('div');
    offsetNameDiv.id = `${this.pid}_offset_name`;
    // offsetNameDiv.textContent = 'Name: None';
    offsetNameCell.appendChild(offsetNameDiv);
    feedRow.appendChild(offsetNameCell);

    // Blinker cell
    const blinkerCell = document.createElement('td');
    blinkerCell.colSpan = 2;
    const blinkerDiv = document.createElement('div');
    blinkerDiv.id = `${this.pid}_blinker`;
    blinkerDiv.style.cssText = 'height:15px; width:15px; background-color: rgb(11, 111, 93); border: 1px solid black; border-radius: 8px;';
    blinkerCell.appendChild(blinkerDiv);
    feedRow.appendChild(blinkerCell);

    machine_table.appendChild(feedRow);

  }

  getHTML(param) {
    return `<div style="max-width: 750px;" class="parameter">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <div id="${param.pid}_tabs">
      <button class="xsm_button green" id="${param.pid}_machine_button">Machine</button>
      <button class="xsm_button blue" id="${param.pid}_work_offsets_button">Work Offsets</button>
      <button class="xsm_button blue" id="${param.pid}_tool_offsets_button">Tool Offsets</button>
      <button class="xsm_button blue" id="${param.pid}_term_button">Terminal</button>
    </div>
    <div id="${param.pid}_term_tab" style="display: none">
      <div><label class="checkbox_container">show status messages<input id="${param.pid}_show_status" type="checkbox"><span
                                                                                                                            class="checkmark"></span></label></div>
      <div id="${param.pid}_terminal" class="terminal"></div>
      <div id="${param.pid}_input" class="term_input" contenteditable="true"></div>
      <span style="font-size: 12px; color: grey;">please note this terminal is a direct line to GRBL. It is NOT for python
        code input. please use regular terminal for that. </span><br><br>
      <table id="${param.pid}_grbl_coms_table">
      </table>


    </div>
    <div id="${param.pid}_machine_tab" style="display: block">
      <div style="width: 95%;">
        <table id="${param.pid}_machine_table" style="width: 100%;">
          
          </tr>
        </table>
      </div>
      <button id="${param.pid}move_submit"
              onclick="hermes.send_json(${param.pid}, {'cmd': 'move.linear', 'x': gid('${param.pid}move_x').value, 'y': gid('${param.pid}move_y').value, 'z': gid('${param.pid}move_z').value, 'a': gid('${param.pid}move_a').value, 'b': gid('${param.pid}move_b').value, 'c': gid('${param.pid}move_c').value, 'feed':gid('${param.pid}move_f').value})"
              class="sm_button green">Move</button><br>

    </div>
    <div id="${param.pid}_work_offsets_tab" style="display: none">
      <div style="width: 95%;">

        <table id="${param.pid}_work_offsets_table" style="width: 100%;">
          <tr>
            <td>offset:</td>
            <td>Name</td>
            <td>X</td>
            <td>Y</td>
            <td>Z</td>
            <td>A</td>
          </tr>
          <tr>
            <td><input type="radio" id="${param.pid}_radio_offset_0" name="${param.pid}_radio_offset" onchange="GRBLScara.change_work_offset(${param.pid} ,0)">0</td>
            <td><input type="text" value="machine"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 0)">set</button></td>
          </tr>
          <tr>
            <td><input type="radio" id="${param.pid}_radio_offset_1" name="${param.pid}_radio_offset" onchange="GRBLScara.change_work_offset(${param.pid} ,1)">1</td>
            <td><input type="text" value="G54"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 1)">set</button></td>
          </tr>
          <tr>
            <td><input type="radio" id="${param.pid}_radio_offset_2" name="${param.pid}_radio_offset" onchange="GRBLScara.change_work_offset(${param.pid} ,2)">2</td>
            <td><input type="text" value="G55"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 2)">set</button></td>
          </tr>
          <tr>
            <td><input type="radio" id="${param.pid}_radio_offset_3" name="${param.pid}_radio_offset" onchange="GRBLScara.change_work_offset(${param.pid} ,3)">3</td>
            <td><input type="text" value="G56"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 3)">set</button></td>
          </tr>
          <tr>
            <td><input type="radio" id="${param.pid}_radio_offset_4" name="${param.pid}_radio_offset" onchange="GRBLScara.change_work_offset(${param.pid} ,4)">4</td>
            <td><input type="text" value="G57"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 4)">set</button></td>
          </tr>
          <tr>
            <td><input type="radio" id="${param.pid}_radio_offset_5" name="${param.pid}_radio_offset" onchange="GRBLScara.change_work_offset(${param.pid} ,5)">5</td>
            <td><input type="text" value="G58"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><input type="number" style="min-width:55px;" value="0"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 5)">set</button></td>
          </tr>
        </table>
      </div>
    </div>
    <div id="${param.pid}_tool_offsets_tab" style="display: none">
      <div style="width: 95%;">
        <h3>Coming Soon</h3>
      </div>
    </div>
    
    <hr>

    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'disable_motors'})" class="sm_button red">disable_motors</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'enable_motors'})" class="sm_button green">enable_motors</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'unlock'})" class="sm_button blue">unlock</button>
    <hr>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_x'})" class="sm_button blue">home_theta</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_y'})" class="sm_button blue">home_phi</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_z'})" class="sm_button blue">home_z</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_a'})" class="sm_button blue">home_a</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_b'})" class="sm_button blue">home_b</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_c'})" class="sm_button blue">home_c</button><br>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'reset_x'})" class="sm_button coral">reset_theta</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'reset_y'})" class="sm_button coral">reset_phi</button>
    <hr>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'listdir'})" class="sm_button coral">listdir</button>
    run script: <input style="width: 50%;" id="${param.pid}_script">
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'run', 'script': gid('${param.pid}_script').value})" class="sm_button blue">open file</button>
  </div>
</div>`
  }

  call(data) {
    const msg = JSON.parse(data);
    if (msg.cmd == 'post') {
      Terminal.write(gid(`${pid}_terminal`), msg.data);
      let command = msg.data;
      if (command[0] === '$') {
        // we have a command frame
        if (command.includes('=')) {
          pieces = command.split('=')
          let table = document.getElementById('machine_table');
          for (const row of table.rows) {
            if (row.cells[0].innerHTML.includes(pieces[0])) {
              row.cells[1].querySelector('input').value = pieces[1]
            }
          }
        }
      }
    }
    else if (msg.cmd == 'status') {
      gid(`${pid}_xpos`).innerHTML = msg.x;
      gid(`${pid}_ypos`).innerHTML = msg.y;
      gid(`${pid}_zpos`).innerHTML = msg.z;
      gid(`${pid}_apos`).innerHTML = msg.a;
      gid(`${pid}_bpos`).innerHTML = msg.b;
      gid(`${pid}_cpos`).innerHTML = msg.c;
      gid(`${pid}_theta_enc`).innerHTML = msg.theta_enc;
      gid(`${pid}_phi_enc`).innerHTML = msg.phi_enc;
      gid(`${pid}_state`).innerHTML = `Status: ${msg.state}`;
      if (gid(`${pid}_blinker`).style.backgroundColor != "rgb(12, 19, 17)") {
        gid(`${pid}_blinker`).style.backgroundColor = "rgb(12, 19, 17)";
      }
      else { gid(`${pid}_blinker`).style.backgroundColor = "rgb(18, 48, 43)"; }
      if (gid(`${pid}_show_status`).checked == true) {
        Terminal.write(gid(`${pid}_terminal`), JSON.stringify(msg));
      }
      // const pos = GRBLScara.fk(param.pid, msg.x, msg.y);
      const pos = GRBLScara.fk(pid, msg.theta_enc, msg.phi_enc);
      gid(`${pid}_cart_x`).innerHTML = pos[0];
      gid(`${pid}_cart_y`).innerHTML = pos[1];
      gid(`${pid}_cart_z`).innerHTML = msg.z;

    }
    // else if (msg.cmd == 'set_offset') {
    //   gid(`${param.pid}_xoffset`).innerHTML = msg.x;
    //   gid(`${param.pid}_yoffset`).innerHTML = msg.y;
    //   gid(`${param.pid}_zoffset`).innerHTML = msg.z;
    //   gid(`${param.pid}_name`).innerHTML = `Name: ${msg.name}`;
    // }
    else if (msg.cmd == 'set_work_offset') {
      let table = gid(`${pid}_machine_table`);
      axes = ['x', 'y', 'z', 'a', 'b', 'c'];
      for (let i = 1; i < 7; i++) {
        table.rows[i].cells[3].innerHTML = msg.data[axes[i - 1]];
      }
      table.rows[7].cells[3].innerHTML = "Name: " + msg.data.name;
    }
  }
  
  send(cmd, payload) {
    if (cmd == 'req_w_offset') {
      // this function will send a request to main to get machine position 
      // and return another value to actually 
      let table = gid(`${pid}_work_offsets_table`)
      let name = table.rows[payload + 1].cells[1].querySelector('input').value
      let data = {
        cmd: 'req_w_offset',
        off_id: payload,
        name: name
      }
      hermes.send_json(pid, data);
    }
  }

  change_work_offset(id, from_machine) {
    function get_val(cell) {
      return cell.querySelector('input').value
    }
    function set_val(cell, val) {
      cell.querySelector('input').value = val
    }
    cells = gid(`${this.pid}_work_offsets_table`).rows[id + 1].cells
    if (from_machine === true) { // we're putting the submition and reply in the same function
      console.log('apply')
      return
    }
    console.log('submit');
    let offset = {
      cmd: 'set_work_offset',
      name: get_val(cells[1]),
      x: parseFloat(get_val(cells[2])),
      y: parseFloat(get_val(cells[3])),
      z: parseFloat(get_val(cells[4])),
      a: parseFloat(get_val(cells[5])),
    }
    hermes.send_json(pid, offset)
    console.log(offset)
  }

  set_tabs(tab) {
    for (const [key, value] of Object.entries(this.tabs)) {
      const button = value.button;
      if (key == tab) {
        value.tab.style.display = "block";
        if (button.classList.contains('green')) {
          console.log(button)
          button.classList.remove('green');
          button.classList.add('blue');
        }
      }
      else {
        value.tab.style.display = "none";
        if (button.classList.contains('blue')) {
          console.log(button)
          button.classList.remove('blue');
          button.classList.add('green');
        }
      }
    }
  }

  fk(theta_deg, phi_deg, a_deg = null) {
    // forward kinematics
    const theta = theta_deg * Math.PI / 180;
    const phi = phi_deg * Math.PI / 180;
    const c2 = (this.theta_2 + this.phi_2) - (2 * this.theta_len * this.phi_len * Math.cos(Math.PI - phi));
    const c = Math.sqrt(c2);
    const B = Math.acos((c2 + this.theta_2 - this.phi_2) / (2 * c * this.theta_len));
    const new_theta = theta + B;
    // we implicitly to the coordinate tranform here
    let y = -Math.cos(new_theta) * c;
    let x = Math.sin(new_theta) * c;
    return [x.toFixed(3), y.toFixed(3)];
  }

  create_grbl_coms_table() {
    const self = this;
    const coms_table = gid(`${this.pid}_grbl_coms_table`);
    const axes = ['x', 'y', 'z', 'a', 'b', 'c'];
    const properties = [
        'steps_per_mm',
        'max_rate_mm_per_min',
        'acceleration_mm_per_sec2',
        'max_travel_mm'
    ];

    axes.forEach(axis => {
        properties.forEach(property => {
            const row = document.createElement('tr');

            // Create and append the first cell (label)
            const labelCell = document.createElement('td');
            labelCell.textContent = `$/axes/${axis}/${property}`;
            row.appendChild(labelCell);

            // Create and append the second cell (input)
            const inputCell = document.createElement('td');
            const input = document.createElement('input');
            input.type = 'number';
            inputCell.appendChild(input);
            row.appendChild(inputCell);

            // Create and append the third cell (buttons)
            const buttonCell = document.createElement('td');
            const setButton = document.createElement('button');
            setButton.textContent = 'set';
            // setButton.onclick = () => self.grbl_coms(self.pid, labelCell.textContent, 'set');
            setButton.onclick = () => self.grbl_coms(labelCell.textContent, input, 'set');

            const getButton = document.createElement('button');
            getButton.textContent = 'get';
            getButton.onclick = () => self.grbl_coms(labelCell.textContent, input, 'get');

            buttonCell.appendChild(setButton);
            buttonCell.appendChild(getButton);
            row.appendChild(buttonCell);

            // Append the row to the table
            coms_table.appendChild(row);
        });
    });
  }

  grbl_coms(command, input_cell, action) {
    // this is stuff that should be sent directly to the grbl machine itself
    let data = {
      cmd: 'machine',
      action: action,
      command: command,
    }
    if (action == 'set') {
      let value = parseFloat(input_cell.value)
      data.value = value
      console.log(value)
      if (isNaN(value)) {
        console.log('sdkfjsdolkfjsolidjfoiwneopifnwopenfopiwenofinweofnoweinfoienoiwenfion')
        Terminal.write(gid(`${this.pid}_terminal`), `invalid data: ${value}`);
        return
      }
    }
    console.log(data)
    hermes.send_json(this.pid, data);
  }
}
constructors['GRBL'] = GRBL;


class GRBLScara extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    const self = this;

    this.tabs = {
      machine: { button: gid(`${param.pid}_machine_button`), tab: gid(`${param.pid}_machine_tab`) },
      work_offsets: { button: gid(`${param.pid}_work_offsets_button`), tab: gid(`${param.pid}_work_offsets_tab`) },
      tool_offsets: { button: gid(`${param.pid}_tool_offsets_button`), tab: gid(`${param.pid}_tool_offsets_tab`) },
      term: { button: gid(`${param.pid}_term_button`), tab: gid(`${param.pid}_term_tab`) },
      files: { button: gid(`${param.pid}_files_button`), tab: gid(`${param.pid}_files_tab`) },
    }

    for (const [key, value] of Object.entries(this.tabs)) {
      value.button.addEventListener('click', function () { self.set_tabs(key) });
    }

    this.work_offsets = param.work_offsets;
    this.work_offset = param.work_offset;

    this.tool_offsets = param.tool_offsets;
    this.tool_offset = param.tool_offset;

    this.theta_len = param.theta_len;
    this.theta_2 = this.theta_len ** 2;

    this.phi_len = param.tool_offsets[this.tool_offset]['l']
    this.phi_2 = this.phi_len ** 2;
    this.axes = param.axes;
    this.axes_map = param.axes_map;

    this.create_machine_table();
    this.create_grbl_coms_table();
    this.create_work_offsets_table();
    this.create_tool_offset_table();
    Terminal.init(param, true);  // initialize the terminal
  }

  create_tool_offset_table() {
    const table = document.getElementById(`${this.pid}_tool_offsets_table`);
    table.innerHTML = '';
    table.style.width = '100%';

    // Create header row
    const headerRow = document.createElement('tr');
    const headers = ['Offset:', 'Name', 'p', 'l', 'z', ''];
    headers.forEach(text => {
      const th = document.createElement('td');
      th.textContent = text;
      headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Create offset rows
    Object.entries(this.tool_offsets).forEach(([name, values], index) => {
      const row = document.createElement('tr');

      // Offset radio button
      const radioTd = document.createElement('td');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.id = `${this.pid}_radio_tool_offset_${index}`;
      radio.name = `${this.pid}_radio_tool_offset`;
      if (this.tool_offset === name) {
        radio.checked = true;
      }

      radio.onchange = () => this.send('change_tool_offset', name);
      radioTd.appendChild(radio);
      radioTd.appendChild(document.createTextNode(index));
      row.appendChild(radioTd);

      // Offset name
      const nameTd = document.createElement('td');
      const nameInput = document.createElement('input');
      nameInput.type = 'text';
      nameInput.value = name;
      nameTd.appendChild(nameInput);
      row.appendChild(nameTd);

      // X, Y, Z, A input fields
      ['p', 'l', 'z'].forEach(axis => {
        const td = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'number';
        input.style.minWidth = '55px';
        input.value = values[axis] || 0;
        td.appendChild(input);
        row.appendChild(td);
      });

      // Set button
      const buttonTd = document.createElement('td');
      const button = document.createElement('button');
      button.className = 'xsm_button blue';
      button.textContent = 'set';
      button.onclick = () => this.send('set_tool_offset', name);
      buttonTd.appendChild(button);
      row.appendChild(buttonTd);

      table.appendChild(row);
    });

    this.phi_len = this.tool_offsets[this.tool_offset]['l']
    console.log(this.phi_len);
    this.phi_2 = this.phi_len ** 2;
  }

  create_machine_table() {
    // main tab for machine movement
    const self = this;

    // add function to move button
    const move_button = gid(`${this.pid}move_submit`);
    move_button.onclick = function () {

      let move = { cmd: 'move.linear' };

      for (const axis of Object.values(self.axes_map)) {
        let pos = gid(`${self.pid}move_${axis}`).value;
        if (pos != "") {
          pos = parseFloat(pos);
        }
        move[axis] = pos;
      }
      console.log(move);
      move['feed'] = gid(`${self.pid}move_f`).value;

      hermes.send_json(self.pid, move);
    }

    // create the table
    const machine_table = gid(`${this.pid}_machine_table`);
    console.log(machine_table);
    // First row: Move Machine headers
    const headerRow = document.createElement('tr');
    const headers = [
      { text: 'Move Machine:', colspan: 2 },
      'Position',
      'Offset',
      'MPos',
      'Encoders',
      'Jog',
    ];

    headers.forEach(header => {
      const th = document.createElement('td');
      if (typeof header === 'object') {
        th.textContent = header.text;
        th.colSpan = header.colspan;
      } else {
        th.textContent = header;
      }
      headerRow.appendChild(th);
    });
    machine_table.appendChild(headerRow);


    this.axes.forEach(axis => {
      const _axis = this.axes_map[axis]
      const row = document.createElement('tr');

      // Label cell
      const labelCell = document.createElement('td');
      labelCell.innerHTML = `<strong>${_axis}: </strong>`;
      labelCell.style.width = '5px';
      row.appendChild(labelCell);

      // Input cell
      const inputCell = document.createElement('td');
      const input = document.createElement('input');
      input.type = 'number';
      input.style.width = '100%';
      input.id = `${this.pid}move_${_axis}`;
      inputCell.appendChild(input);
      row.appendChild(inputCell);

      // Position, Offset, Absolute Pos cells
      ['pos', 'offset', 'mpos', 'enc'].forEach(suffix => {
        const cell = document.createElement('td');
        const div = document.createElement('div');
        div.id = `${this.pid}_${_axis}${suffix}`;
        div.textContent = 'None';
        cell.appendChild(div);
        row.appendChild(cell);
      });

      // create jog elements
      const cell = document.createElement('td');
      const div = document.createElement('div');
      div.id = `${this.pid}_${_axis}${'jog'}`;

      const jog_minus = document.createElement('button');
      jog_minus.textContent = '←';
      jog_minus.onclick = function () { 
        let val = parseFloat(gid(`${self.pid}_${_axis}pos`).innerHTML) - .1;
        let order = { cmd: 'move', 
          feed: 500,
        }
        order[_axis] = val
        hermes.send_json(self.pid, order);
      };


      const jog_plus = document.createElement('button');
      jog_plus.textContent = '→';
      jog_plus.onclick = function () { 
        let val = parseFloat(gid(`${self.pid}_${_axis}pos`).innerHTML) + .1;
        let order = { cmd: 'move', 
          feed: 500,
        }
        order[_axis] = val
        hermes.send_json(self.pid, order);
      };
      div.appendChild(jog_minus);
      div.appendChild(jog_plus);
      cell.appendChild(div);
      row.appendChild(cell);
      // /create jog elements

      machine_table.appendChild(row);
    });

    // Feed row
    const feedRow = document.createElement('tr');

    // Feed label and input
    const feedLabelCell = document.createElement('td');
    feedLabelCell.innerHTML = '<strong>feed: </strong>';
    feedRow.appendChild(feedLabelCell);

    const feedInputCell = document.createElement('td');
    const feedInput = document.createElement('input');
    feedInput.type = 'number';
    feedInput.style.width = '100%';
    feedInput.id = `${this.pid}move_f`;
    feedInput.value = '500';
    feedInputCell.appendChild(feedInput);
    feedRow.appendChild(feedInputCell);

    // Status and Offset Name cells
    const statusCell = document.createElement('td');
    const statusDiv = document.createElement('div');
    statusDiv.id = `${this.pid}_state`;
    statusDiv.textContent = 'Status: None';
    statusCell.appendChild(statusDiv);
    feedRow.appendChild(statusCell);

    const offsetNameCell = document.createElement('td');
    const offsetNameDiv = document.createElement('div');
    offsetNameDiv.id = `${this.pid}_offset_name`;
    // offsetNameDiv.textContent = 'Name: None';
    offsetNameCell.appendChild(offsetNameDiv);
    feedRow.appendChild(offsetNameCell);

    // Blinker cell
    const blinkerCell = document.createElement('td');
    blinkerCell.colSpan = 2;
    const blinkerDiv = document.createElement('div');
    blinkerDiv.id = `${this.pid}_blinker`;
    blinkerDiv.style.cssText = 'height:15px; width:15px; background-color: rgb(11, 111, 93); border: 1px solid black; border-radius: 8px;';
    blinkerCell.appendChild(blinkerDiv);
    feedRow.appendChild(blinkerCell);

    machine_table.appendChild(feedRow);

  }

  getHTML(param) {
    return `<div style="max-width: 750px;" class="parameter">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <div id="${param.pid}_tabs">
      <button class="xsm_button green" id="${param.pid}_machine_button">Machine</button>
      <button class="xsm_button grey" id="${param.pid}_work_offsets_button">Work Offsets</button>
      <button class="xsm_button grey" id="${param.pid}_tool_offsets_button">Tool Offsets</button>
      <button class="xsm_button grey" id="${param.pid}_term_button">Terminal</button>
      <button class="xsm_button grey" id="${param.pid}_files_button">Files</button>
    </div>
    <div id="${param.pid}_term_tab" style="display: none">
      <div><label class="checkbox_container">show status messages<input id="${param.pid}_show_status" type="checkbox"><span
                                                                                                                            class="checkmark"></span></label></div>
      <div id="${param.pid}_terminal" class="terminal"></div>
      <div id="${param.pid}_input" class="term_input" contenteditable="true"></div>
      <span>GRBL COMS</span><button class="toggler" onclick="toggleCollapsible(this)">+</button>
      <div style="display: none;">
        <span style="font-size: 12px; color: grey;">please note this terminal is a direct line to GRBL. It is NOT for python
          code input. please use regular terminal for that. </span><br><br>
        <table id="${param.pid}_grbl_coms_table">
        </table>  
      </div>
      
    </div>
    <div id="${param.pid}_machine_tab" style="display: block">
      <div style="width: 95%;">
        <table id="${param.pid}_machine_table" style="width: 100%;">
          
          </tr>
        </table>
      </div>
      <button id="${param.pid}move_submit"
              class="sm_button green">Move</button>
      work_offset: <span id="${param.pid}_work_offset">error</span> | 
      tool_offset: <span id="${param.pid}_tool_offset">error</span>        
      <br>
      cartesian position encoders: 
      <span style="font-size: large;"> X: </span>
      <span id="${param.pid}_cart_x">000.00</span>
      <span style="font-size: large;"> Y: </span>
      <span id="${param.pid}_cart_y">000.00</span>
      <span style="font-size: large;"> Z: </span>
      <span id="${param.pid}_cart_z">000.00</span>
      <span style="font-size: large;"> A: </span>
      <span id="${param.pid}_cart_a">000.00</span>  
      <br>
      cartesian position grbl: 
      <span style="font-size: large;"> X: </span>
      <span id="${param.pid}_cart_x_grbl">000.00</span>
      <span style="font-size: large;"> Y: </span>
      <span id="${param.pid}_cart_y_grbl">000.00</span>
      <span style="font-size: large;"> Z: </span>
      <span id="${param.pid}_cart_z_grbl">000.00</span>
      <span style="font-size: large;"> A: </span>
      <span id="${param.pid}_cart_a_grbl">000.00</span>  
      <br>
      <span id="${param.pid}_cart_dict">{}</span>
      <br>
    </div>
    <div id="${param.pid}_work_offsets_tab" style="display: none">
      <div style="width: 95%;">

        <table id="${param.pid}_work_offsets_table" style="width: 100%;">
        </table>
      </div>
    </div>
    <div id="${param.pid}_tool_offsets_tab" style="display: none">
      <div style="width: 95%;">
        <table id="${param.pid}_tool_offsets_table" style="width: 100%;">
        </table>
      </div>
    </div>
    <div id="${param.pid}_files_tab" style="display: none">
      <div style="width: 95%;">
        <table style="width: 100%;" id="${param.pid}_files_table">
          <tr>
            <td>File</td>
            <td>Size</td>
            <td>Actions</td>
          </tr>
        </table>
      </div>
    </div>
    <hr>

    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'disable_motors'})" class="sm_button red">disable_motors</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'enable_motors'})" class="sm_button green">enable_motors</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'unlock'})" class="sm_button blue">unlock</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'feed_hold'})" class="sm_button red">feed_hold</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'resume'})" class="sm_button green">resume</button>
    <hr>
    <span style="font-size:large">Home</span>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_x'})" class="sm_button blue">theta</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_y'})" class="sm_button blue">phi</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_z'})" class="sm_button blue">z</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_a'})" class="sm_button blue">a</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_b'})" class="sm_button blue">b</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_c'})" class="sm_button blue">c</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'reset_x'})" class="sm_button coral">reset_theta</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'reset_y'})" class="sm_button coral">reset_phi</button>
    <hr>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'listdir'})" class="sm_button coral">listdir</button>
    run script: <input style="width: 50%;" id="${param.pid}_script">
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'run', 'script': gid('${param.pid}_script').value})" class="sm_button blue">open file</button>
  </div>
</div>`
  }

  call(data) {
    const self = this;
    const msg = JSON.parse(data);
    if (msg.cmd != 'status') {
      console.log(msg);
    }
    if (msg.cmd == 'post') {
      Terminal.write(gid(`${self.pid}_terminal`), msg.data);
      let command = msg.data;
      if (command[0] === '$') {
        // we have a command frame
        if (command.includes('=')) {
          const pieces = command.split('=');
          let table = gid(`${self.pid}_grbl_coms_table`);
          for (const row of table.rows) {
            if (row.cells[0].innerHTML.includes(pieces[0])) {
              row.cells[1].querySelector('input').value = pieces[1]
            }
          }
        }
      }
    }
    else if (msg.cmd == 'status') {
      this._status(msg);
    }
    else if (msg.cmd == 'set_work_offset') {
      console.log('set_work_offset', msg.data);
      this.work_offsets = msg.data;
      this.create_work_offsets_table();
    }
    else if (msg.cmd == 'change_work_offset') {
      this.work_offset = msg.data;
      this.create_work_offsets_table();
    }
    else if (msg.cmd == 'change_tool_offset') {
      this.tool_offset = msg.data;
      this.create_tool_offset_table();
    }
    else if (msg.cmd == 'set_tool_offset') {
      console.log('set_tool_offset', msg.data);
      this.tool_offsets = msg.data;
      this.create_tool_offset_table();
    }
    else if (msg.cmd == 'populate_files') {
      let table = gid(`${this.pid}_files_table`);
      console.log(table);
      table.innerHTML = '';
      for (let i = 0; i < msg.data.length; i++) {
        let row = table.insertRow();
        let cell = row.insertCell();
        cell.innerHTML = msg.data[i];
        let cell2 = row.insertCell();
        let button = document.createElement('button');
        button.innerHTML = 'load';
        button.onclick = function () {
          hermes.send_json(self.pid, { cmd: 'run', script: msg.data[i] });
        }
        cell2.appendChild(button);
      }
    }
    else {
      console.log('unknown message', msg)
    }
  }

  _status(msg) {

    if (this.axes.includes('x')) {
      gid(`${this.pid}_tpos`).innerHTML = msg.x;
      gid(`${this.pid}_tmpos`).innerHTML = msg.x;
    }
    if (this.axes.includes('y')) {
      const p = msg.y - this.tool_offsets[this.tool_offset]['p'];
      gid(`${this.pid}_ppos`).innerHTML = p.toFixed(3);
      gid(`${this.pid}_pmpos`).innerHTML = msg.y;
    }
    if (this.axes.includes('z')) {
      const z = msg.z - this.work_offsets[this.work_offset]['z'] - - this.tool_offsets[this.tool_offset]['z'];
      gid(`${this.pid}_zmpos`).innerHTML = msg.z;
      gid(`${this.pid}_zpos`).innerHTML = z.toFixed(3);
    }
    if (this.axes.includes('a')) {
      gid(`${this.pid}_apos`).innerHTML = msg.a;
      gid(`${this.pid}_ampos`).innerHTML = msg.a;
    }
    if (this.axes.includes('b')) {
      gid(`${this.pid}_bpos`).innerHTML = msg.b;
      gid(`${this.pid}_bmpos`).innerHTML = msg.b;
    }
    if (this.axes.includes('c')) {
      gid(`${this.pid}_cpos`).innerHTML = msg.c;
      gid(`${this.pid}_cmpos`).innerHTML = msg.c;
    }
    
    // TODO: create error state if no encoders
    if (msg.theta_enc == null) {msg.theta_enc = 0;}
    if (msg.phi_enc == null) {msg.phi_enc = 0;}
    gid(`${this.pid}_tenc`).innerHTML = msg.theta_enc.toFixed(3);
    gid(`${this.pid}_penc`).innerHTML = msg.phi_enc.toFixed(3);
    
    gid(`${this.pid}_state`).innerHTML = `Status: ${msg.state}`;
    if (gid(`${this.pid}_blinker`).style.backgroundColor != "rgb(12, 19, 17)") {
      gid(`${this.pid}_blinker`).style.backgroundColor = "rgb(12, 19, 17)";
    }
    else { gid(`${this.pid}_blinker`).style.backgroundColor = "rgb(18, 48, 43)"; }
    if (gid(`${this.pid}_show_status`).checked == true) {
      Terminal.write(gid(`${this.pid}_terminal`), JSON.stringify(msg));
    }

    gid(`${this.pid}_work_offset`).innerHTML = this.work_offset;
    gid(`${this.pid}_tool_offset`).innerHTML = this.tool_offset;

    // const pos = GRBLScara.fk(param.pid, msg.x, msg.y);
    let pos = this.translatexy(this.fk(msg.theta_enc, msg.phi_enc));
    gid(`${this.pid}_cart_x`).innerHTML = pos[0].toFixed(3);
    gid(`${this.pid}_cart_y`).innerHTML = pos[1].toFixed(3);
    gid(`${this.pid}_cart_z`).innerHTML = gid(`${this.pid}_zpos`).innerHTML;

    let grbl_pos = this.translatexy(this.fk(msg.x, msg.y - this.tool_offsets[this.tool_offset]['p']));
    let pos_dict = {x: grbl_pos[0].toFixed(3), y:grbl_pos[1].toFixed(3), z:gid(`${this.pid}_zpos`).innerHTML}
    gid(`${this.pid}_cart_x_grbl`).innerHTML = grbl_pos[0].toFixed(3);
    gid(`${this.pid}_cart_y_grbl`).innerHTML = grbl_pos[1].toFixed(3);
    gid(`${this.pid}_cart_z_grbl`).innerHTML = gid(`${this.pid}_zpos`).innerHTML;
    gid(`${this.pid}_cart_dict`).innerHTML = `{"x": ${pos_dict.x}, "y": ${pos_dict.y}, "z": ${pos_dict.z}}`
  }

  send(cmd, payload) {
    let msg = {};
    console.log(cmd, payload);
    if (cmd == 'change_work_offset' || cmd == 'change_tool_offset') {
      msg = { cmd: cmd, data: payload }
    }

    else if (cmd == 'set_work_offset') {
      const table = document.getElementById(`${this.pid}_work_offsets_table`);
      let row;
      
      for (let i = 1; i < table.rows.length; i++) {
        if (table.rows[i].cells[1].querySelector('input').value == payload) {
          row = table.rows[i];
        }
      }
      msg.cmd = cmd;
      msg.name = row.cells[1].querySelector('input').value;

      for (let i = 0; i < this.axes.length; i++) {
        msg[this.axes[i]] = parseFloat(row.cells[i + 2].querySelector('input').value);
      }
      console.log(msg);
    }

    else if (cmd == 'set_tool_offset') {
      const table = document.getElementById(`${this.pid}_tool_offsets_table`);
      let row;
      for (let i = 1; i < table.rows.length; i++) {
        // console.log(table.rows[i].cells[1].querySelector('input').value);
        if (table.rows[i].cells[1].querySelector('input').value == payload) {
          row = table.rows[i];
        }
      }
      msg.cmd = cmd;
      msg.name = row.cells[1].querySelector('input').value;
      msg.p = parseFloat(row.cells[2].querySelector('input').value);
      msg.l = parseFloat(row.cells[3].querySelector('input').value);
      msg.z = parseFloat(row.cells[4].querySelector('input').value);

      console.log(msg);
    }
    else {
      console.log('error')
      return
    }
    hermes.send_json(this.pid, msg)
  }

  create_work_offsets_table() {
    const table = document.getElementById(`${this.pid}_work_offsets_table`);
    table.innerHTML = '';
    table.style.width = '100%';

    // Create header row
    const headerRow = document.createElement('tr');
    const headers = ['Offset:', 'Name', 'X', 'Y', 'Z', 'A', ''];
    headers.forEach(text => {
      const th = document.createElement('td');
      th.textContent = text;
      headerRow.appendChild(th);
    });
    table.appendChild(headerRow);

    // Create offset rows
    Object.entries(this.work_offsets).forEach(([name, values], index) => {
      const row = document.createElement('tr');

      // Offset radio button
      const radioTd = document.createElement('td');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.id = `${this.pid}_radio_work_offset_${index}`;
      radio.name = `${this.pid}_radio_work_offset`;
      if (this.work_offset === name) {
        radio.checked = true;
      }

      radio.onchange = () => this.send('change_work_offset', name);
      radioTd.appendChild(radio);
      radioTd.appendChild(document.createTextNode(index));
      row.appendChild(radioTd);

      // Offset name
      const nameTd = document.createElement('td');
      const nameInput = document.createElement('input');
      nameInput.type = 'text';
      nameInput.value = name;
      nameTd.appendChild(nameInput);
      row.appendChild(nameTd);

      // X, Y, Z, A input fields
      ['x', 'y', 'z', 'a'].forEach(axis => {
        const td = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'number';
        input.style.minWidth = '55px';
        input.value = values[axis] || 0;
        td.appendChild(input);
        row.appendChild(td);
      });

      // Set button
      const buttonTd = document.createElement('td');
      const button = document.createElement('button');
      button.className = 'xsm_button blue';
      button.textContent = 'set';
      button.onclick = () => this.send('set_work_offset', name);
      buttonTd.appendChild(button);
      row.appendChild(buttonTd);

      table.appendChild(row);
    });
  }

  set_tabs(tab) {
    for (const [key, value] of Object.entries(this.tabs)) {
      const button = value.button;
      if (key == tab) {
        value.tab.style.display = "block";
        if (button.classList.contains('grey')) {
          // console.log(button)
          button.classList.remove('grey');
          button.classList.add('green');
        }
      }
      else {
        value.tab.style.display = "none";
        if (button.classList.contains('green')) {
          console.log(button)
          button.classList.remove('green');
          button.classList.add('grey');
        }
      }
    }
  }

  fk(theta_deg, phi_deg) {
    // forward kinematics
    const theta = theta_deg * Math.PI / 180;
    const phi = phi_deg * Math.PI / 180;
    const c2 = (this.theta_2 + this.phi_2) - (2 * this.theta_len * this.phi_len * Math.cos(Math.PI - phi));
    const c = Math.sqrt(c2);
    const B = Math.acos((c2 + this.theta_2 - this.phi_2) / (2 * c * this.theta_len));
    const new_theta = theta + B;
    // we implicitly do the coordinate tranform here
    let y = -Math.cos(new_theta) * c;
    let x = Math.sin(new_theta) * c;
    return [x, y];
  }

  translatexy(pos) {
    const work_offset = this.work_offsets[this.work_offset]
    // Rotate
    let hyp = Math.hypot(pos[0], pos[1]);
    let hypAngle = Math.atan2(pos[1], pos[0]);
    let newHypAngle = hypAngle + work_offset.a;

    pos[0] = Math.cos(newHypAngle) * hyp;
    pos[1] = Math.sin(newHypAngle) * hyp;

    // Translate
    pos[0] -= work_offset['x']
    pos[1] -= work_offset['y']

    return pos;
  }

  create_grbl_coms_table() {
    const self = this;
    const coms_table = gid(`${this.pid}_grbl_coms_table`);
    const axes = ['x', 'y', 'z', 'a', 'b', 'c'];
    const properties = [
      'steps_per_mm',
      'max_rate_mm_per_min',
      'acceleration_mm_per_sec2',
      'max_travel_mm'
    ];

    axes.forEach(axis => {
      properties.forEach(property => {
        const row = document.createElement('tr');

        // Create and append the first cell (label)
        const labelCell = document.createElement('td');
        labelCell.textContent = `$/axes/${axis}/${property}`;
        row.appendChild(labelCell);

        // Create and append the second cell (input)
        const inputCell = document.createElement('td');
        const input = document.createElement('input');
        input.type = 'number';
        inputCell.appendChild(input);
        row.appendChild(inputCell);

        // Create and append the third cell (buttons)
        const buttonCell = document.createElement('td');
        const setButton = document.createElement('button');
        setButton.textContent = 'set';
        // setButton.onclick = () => self.grbl_coms(self.pid, labelCell.textContent, 'set');
        setButton.onclick = () => self.grbl_coms(labelCell.textContent, input, 'set');

        const getButton = document.createElement('button');
        getButton.textContent = 'get';
        getButton.onclick = () => self.grbl_coms(labelCell.textContent, input, 'get');

        buttonCell.appendChild(setButton);
        buttonCell.appendChild(getButton);
        row.appendChild(buttonCell);

        // Append the row to the table
        coms_table.appendChild(row);
      });
    });
  }

  grbl_coms(command, input_cell, action) {
    // this is stuff that should be sent directly to the grbl machine itself
    let data = {
      cmd: 'machine',
      action: action,
      command: command,
    }
    if (action == 'set') {
      let value = parseFloat(input_cell.value)
      data.value = value
      console.log(value)
      if (isNaN(value)) {
        Terminal.write(gid(`${this.pid}_terminal`), `invalid data: ${value}`);
        return
      }
    }
    console.log(data)
    hermes.send_json(this.pid, data);
  }
}
constructors['GRBLScara'] = GRBLScara;
class Gui3dViewer extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;
    this.editor = CodeMirror.fromTextArea(document.getElementById(`${param.pid}_code`), {
      lineNumbers: true, // Display line numbers
      mode: "python", // Set mode to Python
      theme: "dracula" // Set theme (you can change it)
    });

    this.save_button = gid(`${param.pid}_save_button`);
    this.submit_button = gid(`${param.pid}_submit_button`);
    this.recalculate_button = gid(`${param.pid}_recalculate_button`); 
    this.color = gid(`${param.pid}_color`);
    
    this.save_button.addEventListener('click', function () { self.save_file() });
    this.submit_button.addEventListener('click', function () { self.send() });
    this.recalculate_button.addEventListener('click', function () { self.recalculate() });
    this.color.addEventListener('change', function () { self.recalculate() });
    // Set initial and maximum height
    let initialHeight = 50; // Initial height in pixels
    let maxHeight = 800; // Maximum height in pixels

    // Set initial height
    gid(`${param.pid}_editor`).style.height = initialHeight + 'px';

    // Make editor resizable
    this.editor.setSize(null, initialHeight);

    // Get the resize bar element
    this.resizeBar = gid(`${param.pid}_resize-bar`);
    // Function to handle mouse down on the resize bar
    this.resizeBar.addEventListener('mousedown', function (event) {
      event.preventDefault(); // Prevent text selection
      var startY = event.clientY;
      var startHeight = self.editor.getWrapperElement().clientHeight;

      // Function to handle mouse move while dragging
      function onMouseMove(event) {
        var delta = event.clientY - startY;
        var newHeight = startHeight + delta;
        newHeight = Math.min(Math.max(newHeight, initialHeight), maxHeight);
        gid(`${param.pid}_editor`).style.height = newHeight + 'px';
        self.editor.setSize(null, newHeight);
      }

      // Function to handle mouse up after dragging
      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      }

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });
    gid(`${param.pid}_file_input`).addEventListener('change', function (event) {
      const fileInput = event.target;

      if (fileInput.files.length > 0) {
        const selectedFile = fileInput.files[0];
        // Read the file content
        const reader = new FileReader();
        reader.onload = function (e) {
          const fileContent = e.target.result;
          self.editor.setValue(fileContent);
        };
        reader.readAsText(selectedFile);
      }
    });
  }

  getHTML(param) {
    return `<div class="parameter">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <div id="${param.pid}_editor" style="border: 2px solid black;">
      <!-- Create a textarea for the CodeMirror editor -->
      <textarea id="${param.pid}_code" name="${param.pid}_code">${param.state}</textarea>
      <!-- Create a draggable bar for resizing -->
      <div id="${param.pid}_resize-bar"
           style="cursor: row-resize; height: 6px; background-color: #ccc; position: relative; bottom: -6px; width: 100%;">
      </div>
    </div>
    <div style="height: 7px;"></div>
    <button class="xsm_button green" id="${param.pid}_submit_button">submit</button>
    <button class="xsm_button coral" id="${param.pid}_save_button">save file</button>
    <input type="file" id="${param.pid}_file_input" style="width:50%">
    <button class="xsm_button coral" id="${param.pid}_recalculate_button">recalculate</button>
    <input type="color" id="${param.pid}_color" style="width: 50px;" value="#00ff99">
  </div>
</div>`
  }

  call(data) {
    this.editor.setValue(data);
    this.recalculate();
  }

  send() {
    const text = this.editor.getValue();
    hermes.send(this.pid, text);
  }

  save_file() {
    // Prompt for a filename
    const fileName = prompt('Enter a filename: ', "filename.evzr");

    if (fileName) {
      const fileContent = this.editor.getValue();

      const blob = new Blob([fileContent], { type: 'text/plain' });
      const blobUrl = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = blobUrl;

      a.download = fileName;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      URL.revokeObjectURL(blobUrl);
    }
  }

  recalculate() {
    DDD_viewer.recalculate_toolpath(
      this.pid,
      this.editor.getValue(),
      this.color.value
    );
  }
}
constructors['Gui3dViewer'] = Gui3dViewer;

class GuiButton extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.button = document.getElementById(`${param.pid}_button`);
    this.button.onclick = () => {hermes.send(this.pid, true)};
  }
  getHTML(param) {
    return `<button class="sm_button ${param.color}" id="${param.pid}_button">${param.name}</button>`
  }

  call(val) {
    console.log(`button ${this.pid} clicked`, val);
  }
}
constructors['GuiButton'] = GuiButton;
class GuiCheckbox extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.checkbox = document.getElementById(`${param.pid}_checkbox`);
    this.checkbox.onclick = () => {hermes.send(this.pid,this.checkbox.checked)};
    
    if (param.initial_value) {
      this.checkbox.checked = true;
    }
  }

  getHTML(param) {
    return `<div class="parameter" style="width:fit-content">
  <label class="checkbox_container">${param.name}<input id="${param.pid}_checkbox" type="checkbox">
    <span class="checkmark"></span>
  </label>
</div>`
  }

  call(val) {
    let bool;
    // console.log(val)
    if (val == 'True') { bool = true; }
    else { bool = false; }
    this.checkbox.checked = bool;
  }
}

constructors['GuiCheckbox'] = GuiCheckbox;
class GuiCmdAggregator extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;

    this.create_event_button = document.getElementById(`${param.pid}_create_event_button`);
    this.verify_button = document.getElementById(`${param.pid}_verify_button`);
    this.copy_button = document.getElementById(`${param.pid}_copy_button`);

    this.create_event_button.addEventListener('click', function () { self.send() });
    this.verify_button.addEventListener('click', function () { self.verify(false) });
    this.copy_button.addEventListener('click', function () { self.copy2clip() });


    this.editor = CodeMirror.fromTextArea(document.getElementById(`${param.pid}_code`), {
      lineNumbers: true, // Display line numbers
      mode: "python", // Set mode to Python
      theme: "dracula", // Set theme (you can change it)
      autoCloseBrackets: true, // Enable auto close brackets
    });

    // Set initial and maximum height
    let initialHeight = 100; // Initial height in pixels
    let maxHeight = 800; // Maximum height in pixels

    // Set initial height
    document.getElementById(`${param.pid}_editor`).style.height = initialHeight + 'px';

    // Make editor resizable
    this.editor.setSize(null, initialHeight);

    this.resizeBar = document.getElementById(`${param.pid}_resize-bar`);
    this.resizeBar.addEventListener('mousedown', (event) => {
      event.preventDefault(); // Prevent text selection
      var startY = event.clientY;
      var startHeight = self.editor.getWrapperElement().clientHeight;

      // Function to handle mouse move while dragging
      function onMouseMove(event) {
        var delta = event.clientY - startY;
        var newHeight = startHeight + delta;
        newHeight = Math.min(Math.max(newHeight, initialHeight), maxHeight);
        document.getElementById(`${param.pid}_editor`).style.height = newHeight + 'px';
        self.editor.setSize(null, newHeight);
      }

      // Function to handle mouse up after dragging
      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      }

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });
  }

  getHTML(param) {
    return `<div class="parameter">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <div id="${param.pid}_editor"  style="border: 2px solid black;">
      <!-- Create a textarea for the CodeMirror editor -->
      <textarea id="${param.pid}_code" name="${param.pid}_code"></textarea>
      <!-- Create a draggable bar for resizing -->
      <div id="${param.pid}_resize-bar" style="cursor: row-resize; height: 6px; background-color: #ccc; position: relative; bottom: -6px; width: 100%;"></div>
    </div>
    <div style="height: 7px;"></div>
    <span style="color: red; padding-top:50px; font-size:10px;" id="${param.pid}_editor_error" ></span><br>
    <button id="${param.pid}_create_event_button">create event</button>
    <button id="${param.pid}_verify_button">verify</button>
    <button id="${param.pid}_copy_button">copy as json list</button>
  </div>
</div>	`
  }

  call(val) {
    this.editor.setValue(val)
  }

  send() {
    let list = this.verify(this.pid, false);
    if (list !== null) {
      hermes.send(this.pid, list)
    }
  }

  verify(json) {
    let raw = this.editor.getValue().split('\n')
    console.log(raw);
    for (const e in raw) {
      try {
        if (raw[e] == "") {
          continue
        }
        JSON.parse(raw[e])
      }
      catch {
        document.getElementById(`${this.pid}_editor_error`).innerHTML = `error on line ${parseInt(e) + 1} - no action was taken`
        return null
      }
    }
    document.getElementById(`${this.pid}_editor_error`).innerHTML = ""
    if (json == true) {
      return `[${raw}]`;
    }
    return this.editor.getValue()
  }

  copy2clip() {
    let clip = this.verify(true)
    if (clip != null) {
      navigator.clipboard.writeText(clip);
    }
  }
}
constructors['GuiCmdAggregator'] = GuiCmdAggregator;
class GuiCodeEditor extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;
    this.editor = CodeMirror.fromTextArea(gid(`${param.pid}_code`), {
      lineNumbers: true, // Display line numbers
      mode: "python", // Set mode to Python
      theme: "dracula" // Set theme (you can change it)
    });
    
    this.save_button = gid(`${param.pid}_save_button`);
    this.submit_button = gid(`${param.pid}_submit_button`);

    this.save_button.addEventListener('click', function () { self.save_file() });
    this.submit_button.addEventListener('click', function () { self.send() });

    // Set initial and maximum height
    let initialHeight = 50; // Initial height in pixels
    let maxHeight = 800; // Maximum height in pixels

    // Set initial height
    gid(`${param.pid}_editor`).style.height = initialHeight + 'px';

    // Make editor resizable
    this.editor.setSize(null, initialHeight);
    
    // Get the resize bar element
    this.resizeBar = gid(`${param.pid}_resize-bar`);
    // Function to handle mouse down on the resize bar
    this.resizeBar.addEventListener('mousedown', function (event) {
      event.preventDefault(); // Prevent text selection
      var startY = event.clientY;
      var startHeight = self.editor.getWrapperElement().clientHeight;

      // Function to handle mouse move while dragging
      function onMouseMove(event) {
        var delta = event.clientY - startY;
        var newHeight = startHeight + delta;
        newHeight = Math.min(Math.max(newHeight, initialHeight), maxHeight);
        gid(`${param.pid}_editor`).style.height = newHeight + 'px';
        self.editor.setSize(null, newHeight);
      }

      // Function to handle mouse up after dragging
      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      }

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });
    gid(`${param.pid}_file_input`).addEventListener('change', function (event) {
      const fileInput = event.target;

      if (fileInput.files.length > 0) {
        const selectedFile = fileInput.files[0];
        // Read the file content
        const reader = new FileReader();
        reader.onload = function (e) {
          const fileContent = e.target.result;
          self.editor.setValue(fileContent);
        };
        reader.readAsText(selectedFile);
      }
    });
  }

  getHTML(param) {
    return `<div class="parameter">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <div id="${param.pid}_editor"  style="border: 2px solid black;">
      <!-- Create a textarea for the CodeMirror editor -->
      <textarea id="${param.pid}_code" name="${param.pid}_code">${param.state}</textarea>
      <!-- Create a draggable bar for resizing -->
      <div id="${param.pid}_resize-bar" style="cursor: row-resize; height: 6px; background-color: #ccc; position: relative; bottom: -6px; width: 100%;"></div>
    </div>
    <div style="height: 7px;"></div>
    <button class="xsm_button green" id="${param.pid}_submit_button">submit</button>
    <button class="xsm_button coral" id="${param.pid}_save_button">save file</button>
    <input type="file" id="${param.pid}_file_input" style="width:50%">
  </div>
</div>`
  }

  call(data) {
    this.editor.setValue(data);
  }

  send() {
    const text = this.editor.getValue();
    hermes.send(this.pid, text);
  }

  save_file() {
    // Prompt for a filename
    const fileName = prompt('Enter a filename: ', "filename.evzr");

    if (fileName) {
      const fileContent = this.editor.getValue();

      const blob = new Blob([fileContent], { type: 'text/plain' });
      const blobUrl = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = blobUrl;

      a.download = fileName;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      URL.revokeObjectURL(blobUrl);
    }
  }
}
constructors['GuiCodeEditor'] = GuiCodeEditor;

class GuiCodeTester extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;
    // Initialize CodeMirror
    this.editor = CodeMirror.fromTextArea(gid(`${param.pid}_code`), {
      lineNumbers: true, // Display line numbers
      mode: "python", // Set mode to Python
      theme: "dracula" // Set theme
    });

    gid(`${param.pid}_description`).innerHTML = marked.parse(param.description)

    // Set initial and maximum height
    let initialHeight = 50; // Initial height in pixels
    let maxHeight = 800; // Maximum height in pixels

    // Set initial height
    gid(`${param.pid}_editor`).style.height = initialHeight + 'px';

    // Make editor resizable
    this.editor.setSize(null, initialHeight);

    this.editor.setValue(param.code);

    // Get the resize bar element
    this.resizeBar = gid(`${param.pid}_resize-bar`);

    // Function to handle mouse down on the resize bar
    this.resizeBar.addEventListener('mousedown', function (event) {
      event.preventDefault(); // Prevent text selection
      var startY = event.clientY;
      var startHeight = self.editor.getWrapperElement().clientHeight;

      // Function to handle mouse move while dragging
      function onMouseMove(event) {
        var delta = event.clientY - startY;
        var newHeight = startHeight + delta;
        newHeight = Math.min(Math.max(newHeight, initialHeight), maxHeight);
        gid(`${param.pid}_editor`).style.height = newHeight + 'px';
        self.editor.setSize(null, newHeight);
      }

      // Function to handle mouse up after dragging
      function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
      }

      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', onMouseUp);
    });
  
    this.terminal = Terminal.init(param, true)
    gid(`${param.pid}_toggler`).click();
  
  }

  getHTML(param) {
    return `<div class="parameter">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button id="${param.pid}_toggler" class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <div>
      <span>description</span><button class="toggler" onclick="toggleCollapsible(this)">-</button>
      <div id="${param.pid}_description" style="border: #ccc solid 1px; border-radius:5px; height: fit-content; padding:5px; resize:both; overflow:auto">
        ${param.description}
      </div>
      <br>
    </div>

    <div>
      <span>code</span><button class="toggler" onclick="toggleCollapsible(this)">-</button>
      <div>
        <div id="${param.pid}_editor"  style="border: 2px solid black;">
          <!-- Create a textarea for the CodeMirror editor -->
          <textarea id="${param.pid}_code" name="${param.pid}_code">${param.state}</textarea>
          <!-- Create a draggable bar for resizing -->
          <div id="${param.pid}_resize-bar" style="cursor: row-resize; height: 6px; background-color: #ccc; position: relative; bottom: -6px; width: 100%;">
          </div>
        </div>
      </div>
    </div>
    <div style="height: 7px;"></div>
    <br>
    <div id="${param.pid}_buttons">
      ${this.make_buttons(param)}
    </div>
    <div>
      <span>repl</span><button class="toggler" onclick="toggleCollapsible(this)">-</button>
      <div>
        <br>
        <div id="${param.pid}_terminal" class="terminal" style="height: 130px;"></div>
        <div id="${param.pid}_input" class="term_input" contenteditable="true"></div>
      </div>
    </div>
  </div>
</div>`
  }

  call(data) {
    let msg = JSON.parse(data);
    console.log(msg.cmd);
    if (msg.cmd == 'term') {
      Terminal.write(gid(`${this.pid}_terminal`), msg.msg)
    }
  }

  button(button) {
    // console.log(button.innerText);
    const pid = button.dataset.pid
    const msg = `{"cmd": "button", "msg": "${button.innerText}"}`;
    hermes.send(pid, msg);
  }

  make_buttons(param) {
    let buttons_html = ""
    for (const button in param.buttons) {
      const but = `<button data-pid=${param.pid} onclick="hermes.p[${param.pid}].button(this)">${button}</button>`;
      buttons_html = buttons_html + but;
    }
    return buttons_html
  }
  
  send() {
    const text = this.editor.getValue();
    hermes.send(this.pid, text);
  }
}
constructors['GuiCodeTester'] = GuiCodeTester;

class GuiFloat extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.input = document.getElementById(`${param.pid}_input`);
    this.input.value = param.initial_value;
    this.input.onchange = () => {this.send(this.pid)};
  }

  send() {
    const val = this.input.value
    hermes.send(this.pid, val)
  }

  getHTML(param) {
    return `<div class="parameter" style="max-width: 500px">
  ${param.name}
  <input type="number" id="${param.pid}_input" style="width: 75%;">
</div>`
  }

  call(val) {
    this.input.value = val;
  }
}
constructors['GuiFloat'] = GuiFloat;

class GuiLockerPicker extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.websocket = param.websocket;  // pid: Websocket
    this.current_user = null;
    this.state = param.pod
    this.name = param.name
    if (param.websocket != "") {
      let gl_ws = new WebSocket(param.websocket);
      this.websocket = gl_ws;
      let self = this;
      gl_ws.onmessage = function (event) {
        let order = JSON.parse(event.data)
        self.process(order);
      }
    }
    else {
      // We must just be running locally and have a pod
      this.renderTable(param.pod)
    }
    setInterval(this.updateTimeRemaining, 1000, this);
  }

  process(order) {
    console.log('order', order);
    const cmd = order.cmd;
    if (cmd === 'connected') {
      // { cmd: "connected", name: "pallet_racks" }
      console.log('connected', cmd);
      let resp = JSON.stringify({ cmd: 'get', 'name': order.name })
      this.websocket.send(resp)
      console.log('sent', resp)
    }
    if (cmd === 'update_locker') {
      this.updateLockerInfo(order.name, order.address, order.status, order.days)
    }
    if (cmd === 'choose_locker') {
      console.log(this);
      this.current_user = order.user
      this.setClaimButtons('show');
      setTimeout(() => this.setClaimButtons('hide'), 30000);
    }
    if (cmd === 'render_table') {
      // {cmd: renderTable, name: name, pod: dict}: websocket
      // {cmd: renderTable, pod: dict}: hermes
      // console.log(order);
      this.renderTable(order.pod)
    }
  }
  
  call(order) {
    order = JSON.parse(order);
    // console.log(order)
    this.process(order);
  }

  getHTML(param) {
    return `<style>
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    box-shadow: 0 2px 3px rgba(0, 0, 0, 0.1);
  }
  th, td {
    border: 1px solid #dee2e6;
    padding: 15px;
    text-align: left;
  }
  th {
    background-color: #343a40;
    color: #fff;
  }
  tr:nth-child(even) {
    background-color: #f2f2f2;
  }
  .large-text {
    font-size: 24px;
    font-weight: bold;
  }
  .empty {
    background-color: #a00234;
    color: #fff;
  }
  .full {
    background-color: #26d00b;
    color: #fff;
  }
  .full-warning {
    background-color: #ff9800;
    color: #fff;
  }
  .owned {
    background-color: #8928a7;
    color: #fff;
  }
  .time-remaining {
    font-weight: bold;
    color: #ebf5fe;
  }
  .claim_button {
    margin-top: 10px;
    padding: 5px 10px;
    background-color: #007bff;
    color: white;
    border: none;
    cursor: pointer;
    display: none;
  }
</style>
<div class="parameter"  id="${param.pid}">
  <h1>${param.name}</h1>
  <table id="${param.pid}_lockersTable">
  </table>
</div>`
  }

  renderTable(pod) {
    const table = document.getElementById(`${this.pid}_lockersTable`);
    this.state = pod;
    // Clear existing rows
    while (table.rows.length > 0) {
      table.deleteRow(0);
    }
    const columnCount = this.state[0].length;
    const columnWidth = 100 / columnCount;
    this.state.forEach(row => {
      const tr = document.createElement('tr');

      row.forEach(locker => {
        const timeRemaining = Math.round((new Date(locker.date) - new Date()) / 1000);
        locker.timeRemaining = timeRemaining;
        const td = document.createElement('td');
        const timeRemainingText = locker.status === 'full' ? `<br>time remaining: <span class="time-remaining" data-address="${locker.address}">${this.formatTime(timeRemaining)}</span>` : '';
        const dateText = locker.status === 'full' ? `<br>date: ${new Date(locker.date).toLocaleString()}` : '';
        const claimButton = locker.status === 'empty' ? `<br><button class="claim_button" onclick="hermes.p[${this.pid}].claimLocker(${locker.address})">Claim</button>` : '';
        td.innerHTML = `name: ${locker.name || 'N/A'}<br>address: <span class="large-text">${locker.address}</span><br>status: ${locker.status}${dateText}${timeRemainingText}${claimButton}`;
        td.className = this.getLockerClass(locker);
        td.style.width = `${columnWidth}%`;
        tr.appendChild(td);
      });
      table.appendChild(tr);
    });
  }
  
  formatTime(seconds) {
    // helper function
    const days = Math.floor(seconds / (24 * 3600));
    seconds %= 24 * 3600;
    const hours = Math.floor(seconds / 3600);
    seconds %= 3600;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${days}d ${hours}h ${minutes}m ${secs}s`;
  }

  getLockerClass(locker) {
    // helper function
    if (locker.status === 'full') {
      return locker.timeRemaining < 86400 ? 'full-warning' : 'full'; // 86400 seconds = 1 day
    }
    return locker.status;
  }

  updateTimeRemaining(self) {
    // helper function    
    const timeElements = document.querySelectorAll('.time-remaining');
    timeElements.forEach(el => {
      const address = parseInt(el.getAttribute('data-address'));
      for (const lockers of Object.values(self.lockers)) {
        const locker = lockers.flat().find(locker => locker.address === address);
        if (locker && locker.timeRemaining > 0) {
          locker.timeRemaining--;
          el.textContent = self.formatTime(locker.timeRemaining);
          el.closest('td').className = self.getLockerClass(locker);
        }
      }
    });
  }

  updateLockerInfo(name, address, status, days = 0) {
    this.state.forEach(row => {
      row.forEach(locker => {
        if (locker.address === address) {
          locker.name = name;
          locker.status = status;
          if (status === 'full') {
            locker.date = new Date();
            locker.date.setSeconds(locker.date.getSeconds() + days * 24 * 3600);
            locker.timeRemaining = days * 24 * 3600; // Convert days to seconds
          } else {
            delete locker.date;
            delete locker.timeRemaining;
          }
        }
      });
    });
    this.renderTable(this.state);
  }

  claimLocker(address) {
    this.setClaimButtons('hide');

    if (confirm(`Claim locker ${address} for: ${this.current_user}`)) {
      console.log(`${this.current_user} wants locker ${address}`);
      // this is a hack. Fix once you understand better what should happen
      if (this.websocket) {
        let msg = JSON.stringify({
          cmd: 'claim',
          name: this.current_user,
          address: address,
          pod: this.state,
        });
        console.log(msg);
        this.websocket.send(msg)
      }
      hermes.send_json(this.pid, {
        cmd: 'get_locker',
        user: this.current_user,
        pid: this.pid,
        address: address,
      })
    }
  }

  setClaimButtons(display) {
    const buttons = document.getElementsByClassName('claim_button');
    for (const button of buttons) {
      if (display === 'hide') {
        button.style.display = 'none';
      }
      else {
        button.style.display = 'inline-block';
      }
    }
  }
}
constructors['GuiLockerPicker'] = GuiLockerPicker;
class GuiPnpFeeder extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    const self = this;
    // this.rack = param.rack
    this.table = gid(`${param.pid}_table`)
    this.save_button = gid(`${param.pid}_save_button`)
    this.save_button.addEventListener('click', function () { self.send('save_rack', null); })
    this.copy_button = gid(`${param.pid}_copy_button`)
    this.copy_button.addEventListener('click', function () { self.copy_rack(); })
    this.create_feeder_table(param);
    this.set_all(param.rack);
  }

  getHTML(param) {
    return `<div style="max-width: 750px;" class="parameter"  id="${param.pid}">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <table style="width: 100%;" id="${param.pid}_table">
      <tr>
        <td>feeder_num</td>
        <td>Component Name</td>
        <td>x pos</td>
        <td>y pos</td>
        <td>z pos</td>
        <td>a pos</td>
        <td>set pos</td>
      </tr>
    </table>
    <button class="xsm_button grey" id="${param.pid}_save_button">save</button>
    <button class="xsm_button pink" id="${param.pid}_copy_button" style="float:right">copy rack</button>
  </div>
</div>`
  }

  call(data) {
    let msg = JSON.parse(data);
    console.log(msg.cmd);
    if (msg.cmd == 'set_feeder') {
      console.log(msg)
      this.set_feeder(msg)
    }
    if (msg.cmd == 'saved') {
      this.saved()
    }
    else {
      console.log('unknown command GuiPnpFeeder', msg)
    }
  }

  saved() {
    this.save_button.style.backgroundColor = "#6c6c6c";
    const color = "#304050"
    let first = true;
    for (const row of this.table.rows) {
      if (!first) {
        row.cells[1].querySelector('input').style.backgroundColor = color
        row.cells[2].querySelector('input').style.backgroundColor = color
        row.cells[3].querySelector('input').style.backgroundColor = color
        row.cells[4].querySelector('input').style.backgroundColor = color
        row.cells[5].querySelector('input').style.backgroundColor = color
      }
      first = false
    }
  }

  set_all(data) {
    console.log('set all', data);
    for (const component in data) {
      const comp = data[component]
      const row = this.table.rows[comp.id + 1]
      row.cells[1].querySelector('input').value = component
      row.cells[2].querySelector('input').value = comp.x
      row.cells[3].querySelector('input').value = comp.y
      row.cells[4].querySelector('input').value = comp.z
      row.cells[5].querySelector('input').value = comp.a
    }
  }

  set_feeder(data) {
    // return from when the set button was hit
    const color = "#ff8b8b" // lit color
    for (const component in data) {
      const row = this.table.rows[data.feeder + 1]
      row.cells[1].querySelector('input').style.backgroundColor = color
      row.cells[2].querySelector('input').value = data.x
      row.cells[2].querySelector('input').style.backgroundColor = color
      row.cells[3].querySelector('input').value = data.y
      row.cells[3].querySelector('input').style.backgroundColor = color
      row.cells[4].querySelector('input').value = data.z
      row.cells[4].querySelector('input').style.backgroundColor = color
      row.cells[5].querySelector('input').value = data.a
      row.cells[5].querySelector('input').style.backgroundColor = color
    }
    this.save_button.style.backgroundColor = color;
  }

  get_data() {
    let data = {};
    for (let i = 0; i < this.table.rows.length; i++) {
      if (i == 0) { continue };
      const row = this.table.rows[i];
      const val = row.cells[1].querySelector('input').value;
      data[val] = {
        "id": i - 1,
        "x": parseFloat(row.cells[2].querySelector('input').value),
        "y": parseFloat(row.cells[3].querySelector('input').value),
        "z": parseFloat(row.cells[4].querySelector('input').value),
        "a": parseFloat(row.cells[5].querySelector('input').value),
      }
    }
    console.log(data);
    return data
  }

  change(element) {
    // will make background red to note changes that have not been saved
    element.style.backgroundColor = "#ff8b8b";
    this.save_button.style.backgroundColor = "#068770"
  }

  send(action, payload) {
    let data = {};
    if (action == 'feed') {
      data['feed'] = payload;
    }
    else if (action == 'save_rack') {
      data['save_rack'] = this.get_data();
    }
    else if (action == 'set') {
      data['set'] = payload;
    }
    else if (action == 'set_pos') {
      data['set_pos'] = payload;
    }
    else if (action == 'move_to') {
      data['move_to'] = payload;
    }
    else {
      alert(`unknown action from GuiPnpFeeder: ${action}, ${payload}`);
    }
    hermes.send_json(this.pid, data);
  }

  create_feeder_table(param) {
    let self = this;
    console.log('create_feeder_table', this.table);
    for (let i = 0; i < param.num_feeders; i++) {
      let row = document.createElement('tr'); // Create a new row

      // Create the first cell for feeder label
      let feederCell = document.createElement('td');
      feederCell.textContent = `feeder: ${i}`;
      row.appendChild(feederCell);

      // Create the input cells
      let inputs = ['val', 'xpos', 'ypos', 'zpos', 'apos'];
      inputs.forEach(inputType => {
        let cell = document.createElement('td');
        let input = document.createElement('input');

        input.type = inputType === 'val' ? 'text' : 'number';
        input.style.width = '100%';
        input.id = `${param.pid}_${inputType}_${i}`;
        input.value = inputType === 'val' ? `${i}_bbb` : '';
        input.onchange = () => self.change(input);

        cell.appendChild(input);
        row.appendChild(cell);
      });

      // Create the button cells
      let actions = [
        { class: 'xsm_button blue', text: 'set', action: 'set' },
        { class: 'xsm_button green', text: 'feed', action: 'feed' },
        { class: 'xsm_button grey', text: 'move_to', action: 'move_to' },
      ];

      actions.forEach(action => {
        let cell = document.createElement('td');
        let button = document.createElement('button');

        button.className = action.class;
        button.textContent = action.text;
        button.onclick = () => self.send(action.action, i);

        cell.appendChild(button);
        row.appendChild(cell);
      });

      this.table.appendChild(row); // Append the row to the table
    }
  }

  copy_rack() {
    // copy rack to the clipboard
    const prettyString = JSON.stringify(this.get_data(), null, 2);
    navigator.clipboard.writeText(prettyString)

    return prettyString;
  }
}
constructors['GuiPnpFeeder'] = GuiPnpFeeder;
class GuiRotatableCamera extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this;
    this.src = param.src;

    this.show_crosshair_button = gid(`${param.pid}_show_crosshair_button`);
    this.hide_crosshair_button = gid(`${param.pid}_hide_crosshair_button`);
    this.reloadButton = gid(`${param.pid}_reload_button`);
    this.crosshair = gid(`${param.pid}_crosshair`);
    this.deg_label = gid(`${param.pid}_deg`);
    this.slider = gid(`${param.pid}_slider`);
    this.view = gid(`${param.pid}_view`);

    this.slider.addEventListener('input', function () { self.rotate_cam() });
    this.reloadButton.addEventListener('click', function () { self.view.src = self.src; });
    this.show_crosshair_button.addEventListener('click', function () { self.show_crosshair('visible') });
    this.hide_crosshair_button.addEventListener('click', function () { self.show_crosshair('hidden') });
    
    this.rotate_cam();
  }
  call(data) {
    console.log('guicamera not impemented', data)
  }

  getHTML(param) {
    return `<div class="parameter" style="width:500px;">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler">-</button>
  <div>
    <button class="xsm_button green" id="${param.pid}_show_crosshair_button">
      show crosshair
    </button>
    <button class="xsm_button red" id="${param.pid}_hide_crosshair_button">
      hide crosshair
    </button>
    <button class="xsm_button pink" id="${param.pid}_reload_button">
      reload camera
    </button>
    <table>
      <tr>
        <td>current rotation: </td>
        <td id="${param.pid}_deg" style="width:40px">180</td>
        <td>camera location</td>
        <td id="cam_loc">${param.url}</td>
      </tr>
    </table>
    <div style="width: 95%;" class="slide_container parameter">deg offset<input type="range" min="0" max="359"
        value="180" class="slider" id="${param.pid}_slider">
    </div>
    <img id="${param.pid}_view" src="${param.url}" height="480" width="480" title="Iframe Example"
      style="transform:rotate(0deg); object-fit:none; border-radius:50%;">
    <img id="${param.pid}_crosshair" src="../static/crosshair.png"
      style="position:relative; left: 140px; bottom: 347px; height:200px; width:200px">
  </div>
</div>`
  }

  rotate_cam() {
    this.deg_label.innerText = parseInt(this.slider.value) - 180;
    this.view.style.transform = `rotate(${this.slider.value}deg)`;
  }

  show_crosshair(show) {
    this.crosshair.style.visibility = show;
  }
}
constructors['GuiRotatableCamera'] = GuiRotatableCamera;
class GuiSlider extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.slider = document.getElementById(`${param.pid}_slider`);
    console.log(this.slider);
    this.slider.value = param.initial_value;
    this.slider.oninput = () => {
      hermes.send(this.param.pid, parseInt(this.slider.value));
    }
  }

  getHTML(param) {
    return `<div class="slide_container parameter">${param.name}
    <input type="range" min="${param.min}" max="${param.max}" class="slider" id="${param.pid}_slider">
</div>`
  }

  call(val) {
    if (this.slider.value != val) {
      this.slider.value = val;
    }
  }
}
constructors['GuiSlider'] = GuiSlider;
class GuiTeleprompter extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    let self = this
    this.textContainer = document.getElementById("scrollingText");
    console.log('stating', param)
    this.textContainer.innerHTML = param.state;

    // Add mirror checkbox
    this.mirrorCheckbox = document.getElementById('teleprompterMirrorCheckbox');

    this.isMirrored = this.mirrorCheckbox.checked;
    this.mirrorCheckbox.addEventListener('change', function() { self.mirror() });

    this.speed = param.speed; // Default scrolling speed (pixels per frame)
    this.isScrolling = false;
    this.animationFrame = null;
    this.popupWindow = null;
    this.pid = 123;
    this.startButton = document.getElementById('teleprompterStartButton')
    this.stopButton = document.getElementById('teleprompterStopButton')
    this.resetButton = document.getElementById('teleprompterResetButton')
    
    this.startButton.addEventListener('click', function () { self.start() });
    this.stopButton.addEventListener('click', function () { self.stop() });
    this.resetButton.addEventListener('click', function () { self.reset() });

  }

  getHTML(param) {
    return `<div class="parameter" style="resize: both; overflow:auto;">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)"
    style="float:right;">-</button>
  <style>
    #teleprompter {
      position: relative;
      height: 95vh;
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
      background-color: #000;
      border: 1px solid #fff;
      box-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
    }

    #scrollingText {
      font-size: 2rem;
      line-height: 1.5;
      text-align: center;
      white-space: pre-wrap;
      will-change: transform;
    }
  </style>
  <div style="height: auto;">
    <div id="teleprompter">
      <div id="scrollingText">
        Welcome to the teleprompter application!\n\n
        This is a simple demonstration of how text can scroll vertically
        at a consistent pace. Use the provided controls to start, stop,
        and adjust the speed of the scrolling.\n\n
        Write your script here and let it scroll smoothly during your presentation.
      </div>
    </div>
    <div>
      <button id="teleprompterStartButton">Start</button>
      <button id="teleprompterStopButton">Stop</button>
      <button id="teleprompterResetButton">Reset</button>
      <label style="display: inline-flex; align-items: center; margin-left: 10px;">
        <input type="checkbox" id="teleprompterMirrorCheckbox" style="margin-right: 5px;">
        Mirror
      </label>
    </div>
  </div>
</div>`
  }

  call(data) {
    let msg = JSON.parse(data);
    console.log(msg.cmd);
    if (msg.cmd == 'set_state') {
      console.log('stater', msg.state);
      this.textContainer.innerHTML = msg.state;
    }
    else if (msg.cmd == 'set_speed') {
      console.log(msg.state);
      this.setSpeed(msg.state);
    }
    else if (msg.cmd == 'start') {
      this.start();
    }
    else if (msg.cmd == 'stop') {
      this.stop();
    }
    else if (msg.cmd == 'reset') {
      this.reset();
    }
    else {
      console.log('unknown command GuiTeleprompter', msg)
    }
  }

  setSpeed(speed) {
    this.speed = speed; // Set the scrolling speed
  }

  mirror() {
    this.isMirrored = this.mirrorCheckbox.checked;
    if (this.isMirrored) {
      this.textContainer.style.transform = 'scaleX(-1)';
    } else {
      this.textContainer.style.transform = 'scaleX(1)';
    }
  }

  start() {
    if (this.isScrolling) return; // Prevent multiple instances of scrolling

    this.isScrolling = true;
    const step = () => {
      const currentTransform = getComputedStyle(this.textContainer).transform;
      // Extract translateY from the matrix
      let translateY = 0;
      if (currentTransform !== 'none') {
        const matrix = currentTransform.match(/matrix.*\((.+)\)/);
        if (matrix) {
          const values = matrix[1].split(', ');
          translateY = parseFloat(values[5]);
        }
      }
      const newTranslateY = translateY - this.speed;

      // Set transform with mirroring if needed
      if (this.isMirrored) {
        this.textContainer.style.transform = `scaleX(-1) translateY(${newTranslateY}px)`;
      } else {
        this.textContainer.style.transform = `scaleX(1) translateY(${newTranslateY}px)`;
      }

      if (this.isScrolling) {
        this.animationFrame = requestAnimationFrame(step);
      }
    };

    this.animationFrame = requestAnimationFrame(step);
  }

  stop() {
    this.isScrolling = false;
    cancelAnimationFrame(this.animationFrame);
  }

  reset() {
    this.stop();
    this.textContainer.style.transform = 'translateY(0)';
    this.mirror();
  }
}

constructors['GuiTeleprompter'] = GuiTeleprompter;

class GuiTextbox extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.textbox = document.getElementById(`${param.pid}_textbox`);
    this.textbox.value = param.initial_value;
    this.textbox.oninput = () => {
      hermes.send(this.param.pid, this.textbox.value);
    }
  }

  getHTML(param) {
    return `<div class="text_input parameter">${param.name}
    <input type="text" id="${param.pid}_textbox">
</div>`;
  }

  call(val) {
    if (this.textbox.value != val) {
      this.textbox.value = val;
    }
  }
}
constructors['GuiTextbox'] = GuiTextbox;
class GuiUsbCamera extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.recording = false;

    this.videoElement = document.getElementById('webcam');
    this.stopButton = document.getElementById('stopWebcamButton');
    this.startButton = document.getElementById('startWebcamButton');
    this.startRecordingButton = document.getElementById('startRecordingButton');
    this.stopRecordingButton = document.getElementById('stopRecordingButton');
    this.saveRecordingButton = document.getElementById('saveRecordingButton');
    this.videoSourceSelect = document.getElementById('videoSource');
    this.testMicButton = document.getElementById('testMicButton');
    
    this.stopButton.onclick = (event) => { this.stopWebcam() };
    this.startButton.onclick = (event) => { console.log('start_button'); this.startWebcam() };
    this.startRecordingButton.onclick = (event) => { this.startRecording() };
    this.stopRecordingButton.onclick = (event) => { this.stopRecording() };
    this.saveRecordingButton.onclick = (event) => { this.saveRecording() };
    this.videoSourceSelect.onchange = (event) => { this.startWebcam() };
    this.testMicButton.onclick = (event) => { this.testMicrophone() };

    this.mediaRecorder;
    this.recordedChunks = [];
    this.currentStream;
    this.audioStream;

    // TODO: add something to prevent autostart if desired
    this.getVideoSources();
    this.startWebcam();
  }

  getHTML(param) {
    return `<div class="parameter" style="resize: both; overflow:auto;">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <style>
        video {
            margin-top: 20px;
            border: 2px solid #333;
            border-radius: 10px;
            width: 80%;
            max-width: 640px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
        }
    </style>
    <video id="webcam" autoplay playsinline></video>
    <br>
    <button id="startRecordingButton">Start Recording</button>
    <button id="stopRecordingButton" disabled>Stop Recording</button>
    <button id="saveRecordingButton" disabled>Save Recording</button>
    <button id="startWebcamButton" disabled>Start Webcam</button>
    <button id="stopWebcamButton" disabled>Stop Webcam</button>
    
    <br>
    <button id="testMicButton">Test Microphone</button>
    <label for="videoSource">Video Source:</label>
    <select id="videoSource"></select>
  </div>
</div>`
  }

  call(data) {
    let msg = JSON.parse(data);
    console.log('GuiUsbCamera call', msg);
    if (msg.cmd == 'set_record') {
      if (!this.recording && msg.state) {
        this.startRecording();
      }
      else if (this.recording && !msg.state) {
        this.stopRecording();
      }
      else {
        console.log('recorder parameter out of sync somehow');
      }
    }
    else if (msg.cmd == 'save_file') {
      console.log(msg)
      if (this.saveRecordingButton.disabled) {
        return
      }
      if ('filename' in msg) {
        this.saveRecording(msg.filename);
      }
      else {
        this.saveRecording();
      }
    }
    else {
      console.log('unknown command to GuiUsbCamera', msg);
    }
  }

  // Function to start the webcam with selected video source and default to 1080p
  async startWebcam() {
    if (this.currentStream) {
      this.currentStream.getTracks().forEach(track => track.stop());
    }
    this.videoSource = this.videoSourceSelect.value;
    this.constraints = {
      video: {
        deviceId: this.videoSource ? { exact: this.videoSource } : undefined,
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: true
    };
    try {
      const stream = await navigator.mediaDevices.getUserMedia(this.constraints);
      const videoTracks = stream.getVideoTracks();
      const audioTracks = stream.getAudioTracks();
      this.videoElement.srcObject = new MediaStream(videoTracks); // Only attach video to the video element;

      this.currentStream = stream;
      this.audioStream = new MediaStream(stream.getAudioTracks());

      this.startButton.disabled = true;
      this.stopButton.disabled = false;
    } catch (error) {
      console.error('Error accessing webcam:', error);
      alert('Unable to access webcam. Please allow camera access.');
    }
  }

  // Function to test the microphone
  async testMicrophone() {
    const micStream = new MediaStream(this.audioStream.getAudioTracks());
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const micSource = audioContext.createMediaStreamSource(micStream);
    const analyser = audioContext.createAnalyser();

    micSource.connect(analyser);
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    function visualizeMic() {
      analyser.getByteFrequencyData(dataArray);
      const volume = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
      console.log(`Microphone volume: ${volume}`);
      requestAnimationFrame(visualizeMic);
    }

    visualizeMic();
  }

  // Function to stop the webcam
  stopWebcam () {
    if (this.currentStream) {
      this.currentStream.getTracks().forEach(track => track.stop());
      this.videoElement.srcObject = null;
      console.log('Webcam stopped');
    }
    this.startButton.disabled = false;
    this.stopButton.disabled = true;
  }

  // Function to populate video source options
  async getVideoSources() {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');

      this.videoSourceSelect.innerHTML = '';
      videoDevices.forEach(device => {
        const option = document.createElement('option');
        option.value = device.deviceId;
        option.text = device.label || `Camera ${this.videoSourceSelect.length + 1}`;
        this.videoSourceSelect.appendChild(option);
      });
    } catch (error) {
      console.error('Error getting video sources:', error);
    }
  }

  // Function to start recording
  startRecording() {
    if (this.currentStream) {
      this.mediaRecorder = new MediaRecorder(this.currentStream);
      this.recordedChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.recordedChunks.push(event.data);
        }
      };

      this.mediaRecorder.start();
      console.log('Recording started');

      this.recording = true;
      this.startRecordingButton.disabled = true;
      this.stopRecordingButton.disabled = false;
      this.saveRecordingButton.disabled = true;
    }

  }

  // Function to stop recording
  stopRecording() {
    if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
      this.mediaRecorder.stop();
      console.log('Recording stopped');

      this.recording = false;
      this.startRecordingButton.disabled = false;
      this.stopRecordingButton.disabled = true;
      this.saveRecordingButton.disabled = false;
    }
  }

  // Function to save the recording
  saveRecording(_filename) {
    let filename
    if (typeof _filename === 'string') {
      filename = _filename + '.webm'
    }
    else {
      filename = 'recording.webm'
    }
    const blob = new Blob(this.recordedChunks, { type: 'video/webm' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    URL.revokeObjectURL(url);
    console.log('Recording saved');
  }
}







constructors['GuiUsbCamera'] = GuiUsbCamera;




















// var Pcf8563 = {
//   getHTML: function (param) {
//     return `{{ !html }}`
//   },
//   pid: 0,
//   init: function (param) {
//     this.pid = param.pid;

//     // Update current time every second
//     setInterval(this.updateCurrentTime, 1000);

//     Pcf8563.add_all_alarms(param.pid, param.alarms, param.current);

//     hermes.p[param.pid] = function (pid, data) {
//       const msg = JSON.parse(data);
//       if (msg.cmd == 'status') {
//         gid(`${pid}_ts`).innerHTML = msg.ts;
//         if (msg.alarm) {
//           gid(`${pid}_alarm`).innerHTML = 'on';
//         }
//         else {
//           gid(`${pid}_alarm`).innerHTML = 'off';
//         }
//         if (msg.state) {
//           gid(`${pid}_state`).innerHTML = 'on';
//         }
//         else {
//           gid(`${pid}_state`).innerHTML = 'off';
//         }
//       }
//       else if (msg.cmd == 'ts') {
//         gid(`${pid}_ts`).innerHTML = msg.ts;
//       }
//       else if (msg.cmd == 'alarms') {
//         Pcf8563.add_all_alarms(pid, msg.alarms, msg.current);
//       }
//     }
//   },
//   clear_alarms: function (pid) {
//     cmd = { cmd: 'clear_alarms' }
//     hermes.send_json(pid, cmd)
//   },
//   add_all_alarms: function (pid, alarms, current) {
//     console.log('adding alarms');
//     gid(`${pid}_current`).innerHTML = current;
//     gid(`${pid}_alarms`).innerHTML = "";
//     for (let alarm of alarms) {
//       Pcf8563.addAlarm(pid, alarm)
//     }
//   },
//   // Function to format datetime as required by the input
//   formatDatetimeForInput: function (datetime) {
//     var year = datetime.getFullYear();
//     var month = ('0' + (datetime.getMonth() + 1)).slice(-2); // Months are zero-based
//     var day = ('0' + datetime.getDate()).slice(-2);
//     var hours = ('0' + datetime.getHours()).slice(-2);
//     var minutes = ('0' + datetime.getMinutes()).slice(-2);
//     return year + month + day + hours + minutes;
//   },
//   // Function to update the current time continuously
//   updateCurrentTime: function () {
//     var currentTimeDiv = gid(`Pcf8563_currentTime`)
//     var now = new Date();
//     var month = ('0' + (now.getMonth() + 1)).slice(-2); // Months are zero-based
//     var day = ('0' + now.getDate()).slice(-2);
//     var year = now.getFullYear();
//     var hours = ('0' + now.getHours()).slice(-2);
//     var minutes = ('0' + now.getMinutes()).slice(-2);
//     var seconds = ('0' + now.getSeconds()).slice(-2);
//     var currentTimeString = 'Current Time: ' + month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ':' + seconds;
//     currentTimeDiv.textContent = currentTimeString;
//   },
//   please_wait: function (pid) {
//     document.getElementById(`${pid}_alarms`).innerHTML = "Getting alarms<br> please wait";
//   },
//   timestamp2date: function (timestamp) {
//     var year = parseInt(timestamp.slice(0, 4), 10);
//     var month = parseInt(timestamp.slice(4, 6), 10) - 1; // Months are zero-indexed
//     var day = parseInt(timestamp.slice(6, 8), 10);
//     var hour = parseInt(timestamp.slice(8, 10), 10);
//     var minute = parseInt(timestamp.slice(10, 12), 10);
//     return new Date(year, month, day, hour, minute);
//   },
//   date2timestamp: function (date) {
//     var year = date.getFullYear();
//     var month = ('0' + (date.getMonth() + 1)).slice(-2); // Months are zero-indexed
//     var day = ('0' + date.getDate()).slice(-2);
//     var hour = ('0' + date.getHours()).slice(-2);
//     var minute = ('0' + date.getMinutes()).slice(-2);
//     return year + month + day + hour + minute;
//   },
//   add_rel_alarm: function (pid) {
//     var days = parseInt(document.getElementById('days').value, 10);
//     var hours = parseInt(document.getElementById('hours').value, 10);
//     var minutes = parseInt(document.getElementById('minutes').value, 10);
//     var date = document.getElementById(`${pid}_ts`).innerText;
//     let now = this.timestamp2date(date)
//     now.setDate(now.getDate() + days);
//     now.setHours(now.getHours() + hours);
//     now.setMinutes(now.getMinutes() + minutes);
//     let timestamp = this.date2timestamp(now);
//     let callback = document.getElementById(`${pid}_callback`).value;
//     let alarm = timestamp + callback
//     hermes.send_json(pid, { cmd: "add_alarm", alarm: alarm })
//     return false;
//   },

//   add_abs_alarm: function (pid) {
//     var date = document.getElementById(`${pid}_datetimeInput`).value;
//     let callback = document.getElementById(`${pid}_callback`).value;
//     const charactersToRemove = /[-:T]/g;
//     let alarm = date.replace(charactersToRemove, "") + callback;
//     hermes.send_json(pid, { cmd: "add_alarm", alarm: alarm })
//   },
//   delete: function (pid, button) {
//     let alarm = button.previousSibling.data;
//     hermes.send_json(pid, { cmd: 'delete', alarm: alarm })
//     this.please_wait(pid)
//   },

//   eval_change: function (pid, input) {
//     let timestamp = input.previousSibling.previousSibling;
//     hermes.send_json(pid, { cmd: 'eval_change', timestamp: timestamp })
//     this.please_wait(pid)
//   },

//   addAlarm: function (pid, alarm) {
//     var alarmsDiv = document.getElementById(`${pid}_alarms`);
//     console.log(alarm);
//     // var alarmText = this.formatDatetimeForInput(date);


//     var alarmElement = document.createElement('div');
//     alarmElement.textContent = alarm;

//     // Create delete button for the alarm
//     var deleteButton = document.createElement('button');
//     deleteButton.textContent = 'Delete';
//     deleteButton.onclick = function () {
//       Pcf8563.delete(pid, this)
//     };
//     alarmElement.appendChild(deleteButton);

//     // var evalElement = document.createElement('input');
//     // evalElement.style.width = "200px";
//     // evalElement.value = alarm.slice(12);
//     // evalElement.onchange = function() {
//     //   Pcf8563.eval_change(pid, this)
//     // }

//     // alarmElement.appendChild(evalElement);

//     // Add the new alarm to alarms div
//     alarmsDiv.appendChild(alarmElement);


//     // cmd = {cmd: 'set_alarms', alarms: dates}
//     // hermes.send_json(pid, cmd)
//   }
// }


class Pcf8563 extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    // Update current time every second
    setInterval(this.updateCurrentTime, 1000);

    this.add_all_alarms(param.alarms, param.current);
    this.abs_alarm_button = gid(`${this.pid}_abs_alarm_button`);
    this.timeform = gid(`${this.pid}_timeform`);
    this.timeform.onsubmit = function () {
      return this.add_rel_alarm();
    }
  }

  getHTML(param) {
    return `<div class="parameter">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <div id="Pcf8563_currentTime"></div><br>
    <div id="${param.pid}_ts"></div><br>
    alarm: <span id="${param.pid}_alarm"></span><br>
    state: <span id="${param.pid}_state"></span><br>
    current alarm: <span id="${param.pid}_current"></span><br>
    <div id="${param.pid}_error"></div>
    <label for="${param.pid}_callback">callback</label>
    <input style="width:50%" type="text" id="${param.pid}_callback" value="pass"><br>
    <label for="${param.pid}_datetimeInput">Select a date and time:</label>
    <input style="width:50%" type="datetime-local" id="${param.pid}_datetimeInput">

    <button id="${this.pid}_abs_alarm_button">Absolute Alarm</button>
    <br><br>
    Add A Relative Alarm: Alarm Time will be added to Current Time<br>
    <form id="${param.pid}_timeform">
      <label for="days">Days:</label>
      <input style="width:100px" type="number" id="days" min="0" value="0">
      <label for="hours">Hours:</label>
      <input style="width:100px" type="number" id="hours" min="0" value="0">
      <label for="minutes">Minutes:</label>
      <input style="width:100px" type="number" id="minutes" min="0" max="59" value="0">
      <button type="submit">Relative Alarm</button>
    </form>

    <h4>Current Alarms</h4>
    <div style="border: 2px solid black; border-radius:5px; padding: 5px; width:fit-content" id="${param.pid}_alarms"></div>
    <button onclick="Pcf8563.clear_alarms(${param.pid})">Clear All Alarms</button>
  </div>    
</div>`
  }

  call(data) {
    const msg = JSON.parse(data);
    if (msg.cmd == 'status') {
      gid(`${pid}_ts`).innerHTML = msg.ts;
      if (msg.alarm) {
        gid(`${pid}_alarm`).innerHTML = 'on';
      }
      else {
        gid(`${pid}_alarm`).innerHTML = 'off';
      }
      if (msg.state) {
        gid(`${pid}_state`).innerHTML = 'on';
      }
      else {
        gid(`${pid}_state`).innerHTML = 'off';
      }
    }
    else if (msg.cmd == 'ts') {
      gid(`${pid}_ts`).innerHTML = msg.ts;
    }
    else if (msg.cmd == 'alarms') {
      Pcf8563.add_all_alarms(pid, msg.alarms, msg.current);
    }

  }

  clear_alarms() {
    cmd = { cmd: 'clear_alarms' }
    hermes.send_json(this.pid, cmd)
  }

  add_all_alarms(alarms, current) {
    console.log('adding alarms');
    gid(`${this.pid}_current`).innerHTML = current;
    gid(`${this.pid}_alarms`).innerHTML = "";
    for (let alarm of alarms) {
      this.addAlarm(alarm)
    }
  }

  // Function to format datetime as required by the input
  formatDatetimeForInput(datetime) {
    var year = datetime.getFullYear();
    var month = ('0' + (datetime.getMonth() + 1)).slice(-2); // Months are zero-based
    var day = ('0' + datetime.getDate()).slice(-2);
    var hours = ('0' + datetime.getHours()).slice(-2);
    var minutes = ('0' + datetime.getMinutes()).slice(-2);
    return year + month + day + hours + minutes;
  }

  // Function to update the current time continuously
  updateCurrentTime() {
    var currentTimeDiv = gid(`Pcf8563_currentTime`)
    var now = new Date();
    var month = ('0' + (now.getMonth() + 1)).slice(-2); // Months are zero-based
    var day = ('0' + now.getDate()).slice(-2);
    var year = now.getFullYear();
    var hours = ('0' + now.getHours()).slice(-2);
    var minutes = ('0' + now.getMinutes()).slice(-2);
    var seconds = ('0' + now.getSeconds()).slice(-2);
    var currentTimeString = 'Current Time: ' + month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ':' + seconds;
    currentTimeDiv.textContent = currentTimeString;
  }

  please_wait() {
    document.getElementById(`${this.pid}_alarms`).innerHTML = "Getting alarms<br> please wait";
  }

  timestamp2date(timestamp) {
    var year = parseInt(timestamp.slice(0, 4), 10);
    var month = parseInt(timestamp.slice(4, 6), 10) - 1; // Months are zero-indexed
    var day = parseInt(timestamp.slice(6, 8), 10);
    var hour = parseInt(timestamp.slice(8, 10), 10);
    var minute = parseInt(timestamp.slice(10, 12), 10);
    return new Date(year, month, day, hour, minute);
  }

  date2timestamp(date) {
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2); // Months are zero-indexed
    var day = ('0' + date.getDate()).slice(-2);
    var hour = ('0' + date.getHours()).slice(-2);
    var minute = ('0' + date.getMinutes()).slice(-2);
    return year + month + day + hour + minute;
  }

  add_rel_alarm() {
    var days = parseInt(document.getElementById('days').value, 10);
    var hours = parseInt(document.getElementById('hours').value, 10);
    var minutes = parseInt(document.getElementById('minutes').value, 10);
    var date = document.getElementById(`${this.pid}_ts`).innerText;
    let now = this.timestamp2date(date)
    now.setDate(now.getDate() + days);
    now.setHours(now.getHours() + hours);
    now.setMinutes(now.getMinutes() + minutes);
    let timestamp = this.date2timestamp(now);
    let callback = document.getElementById(`${this.pid}_callback`).value;
    let alarm = timestamp + callback
    hermes.send_json(this.pid, { cmd: "add_alarm", alarm: alarm })
    return false;
  }

  add_abs_alarm() {
    var date = document.getElementById(`${this.pid}_datetimeInput`).value;
    let callback = document.getElementById(`${this.pid}_callback`).value;
    const charactersToRemove = /[-:T]/g;
    let alarm = date.replace(charactersToRemove, "") + callback;
    hermes.send_json(this.pid, { cmd: "add_alarm", alarm: alarm })
  }

  delete(button) {
    let alarm = button.previousSibling.data;
    hermes.send_json(this.pid, { cmd: 'delete', alarm: alarm })
    this.please_wait()
  }

  eval_change(input) {
    let timestamp = input.previousSibling.previousSibling;
    hermes.send_json(this.pid, { cmd: 'eval_change', timestamp: timestamp })
    this.please_wait()
  }

  addAlarm(alarm) {
    var alarmsDiv = document.getElementById(`${this.pid}_alarms`);
    console.log(alarm);

    var alarmElement = document.createElement('div');
    alarmElement.textContent = alarm;

    // Create delete button for the alarm
    var deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = function () {
      this.delete(pid, this)
    };
    alarmElement.appendChild(deleteButton);


    alarmsDiv.appendChild(alarmElement);
  }
}
constructors['Pcf8563'] = Pcf8563;


















class WaferSpaceViewer extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    const svg = document.getElementById('wafer');
    const descriptionBox = document.getElementById('description');

    const waferDiameterMM = 300;
    const chipWidthMM = 8;
    const chipHeightMM = 10;
    const pxPerMM = 2;

    const waferRadiusPx = (waferDiameterMM / 2) * pxPerMM;
    const centerX = waferRadiusPx;
    const centerY = waferRadiusPx;

    // Define chip type colors
    const chipColors = {
      1: '#FF6666',
      2: '#FFCC66',
      3: '#99CC66',
      4: '#66CCCC',
      5: '#6699FF',
      6: '#9966CC',
      7: '#CC6699',
      8: '#CCCCCC',
      9: '#666666'
    };

    const getChipType = (col, row) => {
      const localCol = col % 3;
      const localRow = row % 3;
      return localRow * 3 + localCol + 1;
    };

    // Draw wafer circle
    const wafer = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    wafer.setAttribute("cx", centerX);
    wafer.setAttribute("cy", centerY);
    wafer.setAttribute("r", waferRadiusPx);
    wafer.setAttribute("fill", "#eee");
    wafer.setAttribute("stroke", "#333");
    svg.appendChild(wafer);

    const chipW = chipWidthMM * pxPerMM;
    const chipH = chipHeightMM * pxPerMM;

    const cols = Math.floor(waferDiameterMM / chipWidthMM);
    const rows = Math.floor(waferDiameterMM / chipHeightMM);

    const offsetX = centerX - (cols * chipW) / 2;
    const offsetY = centerY - (rows * chipH) / 2;

    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const x = offsetX + col * chipW;
        const y = offsetY + row * chipH;

        // Check if chip center is inside the wafer
        const chipCenterX = x + chipW / 2;
        const chipCenterY = y + chipH / 2;
        const dx = chipCenterX - centerX;
        const dy = chipCenterY - centerY;

        if (Math.sqrt(dx * dx + dy * dy) <= waferRadiusPx) {
          const chipType = getChipType(col, row);
          const fillColor = chipColors[chipType] || '#bbb';

          const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
          rect.setAttribute("x", x);
          rect.setAttribute("y", y);
          rect.setAttribute("width", chipW);
          rect.setAttribute("height", chipH);
          rect.setAttribute("class", "chip");
          rect.setAttribute("fill", fillColor);
          rect.addEventListener("click", () => {
            descriptionBox.innerHTML = `<strong>Chip at col ${col}, row ${row}</strong><br>Type: ${chipType}<br>X: ${(col * chipWidthMM).toFixed(1)} mm<br>Y: ${(row * chipHeightMM).toFixed(1)} mm`;
          });
          svg.appendChild(rect);
        }
      }
    }

  }

  getHTML(param) {
    return `<div class="parameter" style="resize: both; overflow:auto;">
  <span style="font-size: large;">${param.name}</span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)"
    style="float:right;">-</button>
  <style>
    #wafer {
      border: 1px solid #aaa;
      background-color: #f9f9f9;
      display: block;
      margin: 0 auto;
    }

    .chip {
      cursor: pointer;
      stroke: #d42e63;
      stroke-width: 0.5;
    }

    .chip:hover {
      opacity: 0.8;
    }

    #description {
      margin-top: 1em;
      font-family: sans-serif;
      text-align: center;
    }
  </style>
  <div style="height: auto;">
    <h1 style="text-align:center;">300mm Wafer Viewer</h1>
    <svg id="wafer" width="600" height="600" viewBox="0 0 600 600"></svg>
    <div id="description"><strong>Click a chip</strong> to see its position.</div>
  </div>
</div>`
  }

  call(data) {
    
  }
}

constructors['WaferSpaceViewer'] = WaferSpaceViewer;


class Zorg extends GuiParameter {
  constructor(param, div) {
    super(param, div);
    this.term = gid(`${this.pid}_term`);

    // set up tabs
    this.tab_buttons = {
      msg_sender: gid(`${this.pid}_msg_sender_tab_button`),
      push_subs: gid(`${this.pid}_push_subs_tab_button`),
      single_sub: gid(`${this.pid}_single_sub_tab_button`),
      devices: gid(`${this.pid}_devices_tab_button`),
      esp32: gid(`${this.pid}_esp32_tab_button`),
    }
    for (const [name, button] of Object.entries(this.tab_buttons)) {
      button.onclick = (event) => { this.change_tab(event, name) };
    }

    this.tabs = {
      msg_sender: gid(`${this.pid}_msg_sender`),
      push_subs: gid(`${this.pid}_push_subs`),
      single_sub: gid(`${this.pid}_single_sub`),
      devices: gid(`${this.pid}_devices`),
      esp32: gid(`${this.pid}_esp32`),
    }

    for (const button of Object.values(gid(`${this.pid}_esp32`).children)) {
      button.onclick = (event) => { this._call(button.innerHTML) }
    }
    
  }

  call(data) {
    const self = this;
    // console.log(data)
    const order = JSON.parse(data);
    const cmd = order.cmd;

    function post(order) {
      const msg = order.state.replaceAll('\n', '<br>')
      self.term.innerHTML = self.term.innerHTML + '<br>' + msg;
    }

    if (cmd == 'term') {post(order)}
    else if (cmd == 'devices') {this.create_device_table(order)}
    else if (cmd == 'cluster') {this.create_cluster_list(order)}
    else if (cmd == 'files') {this.create_file_table(order)}
  }

  _call(cmd, other) {
    console.log(cmd, other);
    let type;
    let msg;
    let load;
    if (cmd == 'send') {
      if (gid(`${this.pid}_radio_string`).checked) {
        type = 'string';
        msg = gid(`${this.pid}_string`).value;
      }
      else {
        type = 'bytes';
        msg = [
          gid(`${this.pid}_bytes_0`).value,
          gid(`${this.pid}_bytes_1`).value,
          gid(`${this.pid}_bytes_2`).value,
          gid(`${this.pid}_bytes_3`).value,
          gid(`${this.pid}_bytes_4`).value,
          gid(`${this.pid}_bytes_5`).value,
          gid(`${this.pid}_bytes_6`).value,
          gid(`${this.pid}_bytes_7`).value,
        ]
      }
      load = {
        cmd: cmd,
        adr: gid(`${this.pid}_adr`).value,
        pid: gid(`${this.pid}_pid`).value,
        type: type,
        msg: msg,
        write: gid(`${this.pid}_read`).checked
      }
    }
    else if (cmd == 'create_sub') {
      load = {
        cmd: cmd,
        sender: {
          adr: gid(`${this.pid}_sub_s_adr`).value,
          pid: gid(`${this.pid}_sub_s_pid`).value,
        },
        recvr: {
          adr: gid(`${this.pid}_sub_adr`).value,
          pid: gid(`${this.pid}_sub_pid`).value,
        },
        struct: gid(`${this.pid}_struct`).value,
      }
    }
    else if (cmd == 'ide_subs') {
      load = {
        cmd: cmd,
        subs: gid(`${this.pid}_ide_subs`).value,
      }
    }
    else if (cmd == 'save_subs') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'clear_subs') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'reset_self') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'ping') {
      load = { cmd: cmd }
      gid(`${this.pid}_device_table`).innerHTML = "pinging<br>please wait";
    }
    else if (cmd == 'show_files') {
      load = { cmd: cmd }
      gid(`${this.pid}_files`).innerHTML = "fetching files<br>please wait";
    }
    else if (cmd == 'reset') {
      load = { cmd: cmd }
      gid(`${this.pid}_files`).innerHTML = "fetching files<br>please wait";
    }
    else if (cmd == 'lightshow') {
      load = { cmd: cmd }
      gid(`${this.pid}_files`).innerHTML = "fetching files<br>please wait";
    }
    else if (cmd == 'send_file') {
      load = other
    }
    else if (cmd == 'cluster') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'get_file') {
      load = {
        cmd: cmd,
        filename: other
      }
    }
    else if (cmd == 'test') {
      load = {cmd: cmd}
    }
    console.log(load);
    hermes.send_json(this.pid, load)
  }

  post(line) {
    console.log(line);
    this.term.innerHTML = this.term.innerHTML + '<br>' + line;
  }

  create_cluster_list(order) {
    const cluster = gid(`${this.pid}_cluster`);
    let html = "Cluster Info<br>";
    for (const clust of order.state) {
      html = html + `${clust[0]}: ${clust[1]}<br>`
    }
    html = html + "---------<br><br><br>";
    console.log(html)
    cluster.innerHTML = html;
  }

  create_device_table(devices) {
    const table = document.createElement('table');
    const tbody = document.createElement('tbody');

    // create headings
    const row = document.createElement('tr');
    const adr = document.createElement('td');
    adr.textContent = "adr";

    const dev_id = document.createElement('td');
    dev_id.textContent = "device id";

    const name = document.createElement('td');
    name.textContent = "name";

    row.appendChild(adr);
    row.appendChild(dev_id);
    row.appendChild(name);
    tbody.appendChild(row);

    for (const [adr, device] of Object.entries(devices)) {
      const row = document.createElement('tr');
      const adrCell = document.createElement('td');
      adrCell.textContent = adr;
      row.appendChild(adrCell);

      const device_id = document.createElement('td');
      device_id.textContent = device[0];
      row.appendChild(device_id);

      const name = document.createElement('td');
      if (device[1] == 'unknown device') {
        name.innerHTML = '<button>feature coming soon</button>';
      }
      else {
        name.innerHTML = "<button>mate</button>";
      }
      name.id = `${device[0]}_name`
      row.appendChild(name);
      // Append the row to the table body
      tbody.appendChild(row);
    }
    // Append the table body to the table
    table.appendChild(tbody);

    // Get the table_div element
    const tableDiv = document.getElementById(`${pid}_device_table`);
    tableDiv.innerHTML = '';
    // Append the table to the table_div element
    tableDiv.appendChild(table);
  }

  create_file_table(order) {
    const file_div = gid(`${this.pid}_files`)
    file_div.innerHTML = ""
    const table = document.createElement('table');
    const tbody = document.createElement('tbody');

    // create headings
    const row = document.createElement('tr');
    const _filename = document.createElement('td');
    _filename.textContent = "filename";

    const actions = document.createElement('td');
    actions.textContent = "actions";

    row.appendChild(_filename);
    row.appendChild(actions);
    tbody.appendChild(row);

    for (const filename of order.state.sort()) {
      const row = document.createElement('tr');
      const name = document.createElement('td');
      name.textContent = filename;
      row.appendChild(name);
      const act = document.createElement('td');
      if (filename.charCodeAt(0) >= 65 && filename.charCodeAt(0) <= 90) {
        act.innerHTML = `
        <button onclick="hermes.p[${this.pid}].craft_file_message(this, '${filename}')">send to</button>
        <input style="width: 100px;" type="number">
        <button class="xsm_button blue" onclick="hermes.p[${this.pid}]._call('get_file', '${filename}')">update</button>
        `
      }
      else {
        act.innerHTML = `
      <button onclick="hermes.p[${this.pid}].craft_file_message(this, '${filename}')">send to</button>
      <input style="width: 100px;" type="number">
      `
      }

      row.appendChild(act);
      tbody.appendChild(row);
    }
    // Append the table body to the table
    table.appendChild(tbody);
    file_div.appendChild(table);
  }
  craft_file_message(button, filename) {
    let adr = parseInt(button.nextElementSibling.value)
    if (isNaN(adr)) {
      this.post('enter valid address')
      return
    }
    let load = {
      cmd: 'send_file',
      adr: adr,
      filename: filename,
    }
    hermes.send_json(this.pid, load)
  }

  change_tab(event, tab_name) {
    // handle tabs
    let buttons = document.getElementById(`${this.pid}_tabs`).children;
    for (var i = 0; i < buttons.length; i++) {
      let button = buttons[i];
      if (button.classList.contains('green')) {
        console.log(button)
        button.classList.remove('green');
        button.classList.add('grey');
      }
    }
    event.target.classList.remove('grey');
    event.target.classList.add('green');

    for (const [name, tab] of Object.entries(this.tabs)) {
      if (name == tab_name) {
        tab.style.display = "block";
      }
      else {
        tab.style.display = "none";
      }
    }
  }

  getHTML(param, self) {
    return `<div class="parameter">
  <span style="font-size: large; color: white">${param.name} </span>
  <span style="float:right;">pid: ${param.pid}</span><button class="toggler" onclick="toggleCollapsible(this)" style="float:right;">-</button>
  <div>
    <div>
      <span style="font-size:.7em; color: white">terminal</span>
      <button onclick="toggleCollapsible(this)">-</button>
      <div id="${param.pid}_term" class="terminal"
           style="border: white 2px solid; min-height:100px; overflow:scroll; resize: vertical; height:200px;">
      </div>
    </div><br>
    <div id="${param.pid}_tabs">
      <button class="xsm_button green" id="${param.pid}_msg_sender_tab_button">msg_sender</button>
      <button class="xsm_button grey" id="${param.pid}_push_subs_tab_button">push_subs</button>
      <button class="xsm_button grey" id="${param.pid}_single_sub_tab_button">single_sub</button>
      <button class="xsm_button grey" id="${param.pid}_devices_tab_button">devices</button>
      <button class="xsm_button grey" id="${param.pid}_esp32_tab_button">esp32</button>
    </div>
    <div id="${param.pid}_msg_sender">
      <table>
        <td>write: </td>
        <td><input type="checkbox" id="${param.pid}_read" checked></td>
        <td>unchecked is event</td>
      </table>
      <div>
        <table style="width: 100%">
          <tr>
            <td>adr: </td>
            <td><input id="${param.pid}_adr"></td>
          </tr>
          <tr>
            <td>pid: </td>
            <td><input id="${param.pid}_pid"></td>
          </tr>
          <tr>
            <td>msg: </td>
            <td>
              <input type="radio" id="${param.pid}_radio_string" name="zorg_radio" checked>
              <label for="${param.pid}_radio_string">string: </label>
              <input type="text" id="${param.pid}_string" style="max-width: 500px"><br>
              <input type="radio" id="${param.pid}_radio_bytes" name="zorg_radio">
              <label for="${param.pid}_radio_bytes">bytes: </label>
              <input type="number" id="${param.pid}_bytes_0" style="width: 55px;">
              <input type="number" id="${param.pid}_bytes_1" style="width: 55px;">
              <input type="number" id="${param.pid}_bytes_2" style="width: 55px;">
              <input type="number" id="${param.pid}_bytes_3" style="width: 55px;">
              <input type="number" id="${param.pid}_bytes_4" style="width: 55px;">
              <input type="number" id="${param.pid}_bytes_5" style="width: 55px;">
              <input type="number" id="${param.pid}_bytes_6" style="width: 55px;">
              <input type="number" id="${param.pid}_bytes_7" style="width: 55px;">
            </td>
          </tr>
        </table>
      </div>
      <button id="${param.pid}_send" class="xsm_button green" onclick="hermes.p[${param.pid}]._call('send')">send</button>
    </div>
    <div id="${param.pid}_single_sub" style="display: none;">
      <br>
      send adr: <input type="number" id="${param.pid}_sub_s_adr" style="width: 50%"><br>
      send pid: <input type="number" id="${param.pid}_sub_s_pid" style="width: 50%"><br>
      recv adr: <input type="number" id="${param.pid}_sub_adr" style="width: 50%"><br>
      recv pid: <input type="number" id="${param.pid}_sub_pid" style="width: 50%"><br>
      struct: <input type="text" id="${param.pid}_struct" style="width: 100px"><br>

      <button id="${param.pid}_single_sub_button" class="xsm_button green"
              onclick="hermes.p[${param.pid}]._call('create_sub')">send</button>
    </div>
    <div id="${param.pid}_push_subs" style="display: none;">
      <br>
      subs: <input type="text" id="${param.pid}_ide_subs" style="width: 50%"><br>
      <button id="${param.pid}_ide_sub" class="xsm_button green"
              onclick="hermes.p[${param.pid}]._call('ide_subs')">send</button>
      <button id="${param.pid}_clear_subs" class="xsm_button red" onclick="hermes.p[${param.pid}]._call('clear_subs')">clear
        subs</button>
      <button id="${param.pid}_save_subs" class="xsm_button blue" onclick="hermes.p[${param.pid}]._call('save_subs')">save
        subs</button>
    </div>
    <div id="${param.pid}_devices" style="display: none;">\
      <h3>Devices</h3>
      <div id="${param.pid}_cluster"><button class="xsm_button green" onclick="hermes.p[${param.pid}]._call('cluster')">Get
        Cluster Info</button></div>
      <div id="${param.pid}_device_table">Ping for Devices</div>
      <br>
      <button class="xsm_button green" onclick="hermes.p[${param.pid}]._call('ping')">Ping Devices</button>
      <button class="xsm_button coral" onclick="hermes.p[${param.pid}]._call('show_files')">Show Files</button>
      <button class="xsm_button blue" onclick="hermes.p[${param.pid}]._call('save_subs')">save subscriptions</button>
      <button class="xsm_button red" onclick="hermes.p[${param.pid}]._call('clear_subs')">clear all subscriptions</button>
      <br><br>
      <label for="${param.pid}_file_progress">send file progress:</label>
      <progress id="65501_file_progress" value="0" max="100"></progress><br>
      Local_files<br>
      <div id="${param.pid}_files" style="max-height:400px; resize:vertical; overflow:scroll;">press show_files</div>
    </div>
    <div id="${param.pid}_esp32" style="display: none;">
      <hr>
      <button class="xsm_button green">reset</button>
      <button class="xsm_button coral">lightshow</button>
      <button class="xsm_button coral">test</button><br>
    </div>
  </div>
</div>`;
  }
}
constructors['Zorg'] = Zorg;


function build_from_json(json) {
  // function used by pyscript
  // console.log(json);
  if (json.startsWith("[, ")) {
    // if there are no gui elements, formatting is wrong. fix it
    json = "[" + json.slice(3);
  }
  let params = JSON.parse(json);
  build_params(params);
}

function build_params(params) {
  parameters.innerHTML = "";
  params.sort((a, b) => a.name.localeCompare(b.name)); // Sort by 'name'
  params.forEach(obj => {
    if (obj.type == '_canvas_info') {
      console.log(obj);
      gid('canvas_name').innerHTML = obj.name;
      gid('canvas_id').value = obj.canvas_id;
      gid('canvas_link').href = `../ide/${obj.canvas_id}`;
      document.title = obj.name;
      hermes.id = obj.id;
    } else {
      build_param(obj);
    }
  });
}

function build_param(param) {
  console.log(param);
  var new_div = document.createElement('div');
  parameters.appendChild(new_div);
  let _param = new constructors[param.type](param, new_div);
  hermes.p[param.pid] = _param;
}

// collapse child divs
function toggleCollapsible(button, direction) {
  var content = button.nextElementSibling;

  if (direction == 'collapse' || content.style.display === 'block' || content.style.display == '') {
    display = 'none';
    button.innerHTML = '+';
    content.style.display = 'none';
  }
  else {
    display = 'block';
    button.innerHTML = '-';
    content.style.display = 'block';
  }
}
